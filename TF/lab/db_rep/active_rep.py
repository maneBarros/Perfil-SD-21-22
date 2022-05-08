#!/usr/bin/env python3

# Using active replication to replicate our database
# We replicate every client transaction to be executed at each replica
# We use a consensus protocol (Raft, for example) to agree on an order for client transactions (as a simplification, this code uses the maelstrom's lin-tso service)
# Our database/transactions need to be deterministic in this active-replication model, since each transaction is executed separately in every node

import logging
from asyncio import run, create_task, sleep

from ams import send, receiveAll, reply
from db import DB

logging.getLogger().setLevel(logging.DEBUG)

db = DB(True) # The default constructor DB() creates a non-deterministic database,
              # so it can result in histories with anomalies (e.g. a replica commits transaction 3 and another one aborts it)

txn_to_replicate = []
next_tag = 0
pending_txn = {}

async def run_transaction(msg):
    global node_id, node_ids, db, txn_to_replicate, next_tag, pending_txn

    logging.info(f"Running transaction {msg.body.tag} ({msg.body.txn})")

    ctx = await db.begin([k for op,k,v in msg.body.txn], msg.src+'-'+str(msg.body.original_id))
    rs,wv,res = await db.execute(ctx, msg.body.txn)
    if res:
        await db.commit(ctx, wv)
        logging.info(f"Commited transaction {msg.body.tag} ({msg.body.txn})")
        if msg.src == node_id:
            send(node_id, msg.body.client, in_reply_to=msg.body.original_id, type='txn_ok', txn=res)
    else:
        logging.info(f"Aborted transaction {msg.body.tag}")
        if msg.src == node_id:
            send(node_id, msg.body.client, in_reply_to=msg.body.original_id, type='error', code=14, text='transaction aborted')
    db.cleanup(ctx)


async def handle(msg):
    # State
    global node_id, node_ids
    global db
    global txn_to_replicate, next_tag, pending_txn

    # Message handlers
    if msg.body.type == 'init':
        node_id = msg.body.node_id
        node_ids = msg.body.node_ids
        logging.info('node %s initialized', node_id)

        reply(msg, type='init_ok')

    elif msg.body.type == 'txn':
        txn_to_replicate.append(msg)
        send(node_id, 'lin-tso', type='ts')

    elif msg.body.type == 'ts_ok':
        logging.info(f"Tagging a transaction with [{msg.body.ts}]. Replicating transaction")

        tag = msg.body.ts
        txn = txn_to_replicate.pop(0)
        for node in node_ids:
            send(node_id, node, type='fwd_txn', txn=txn.body.txn, client=txn.src, original_id=txn.body.msg_id, tag=tag)

    elif msg.body.type == 'fwd_txn':
        if msg.body.tag != next_tag:
            logging.info(f'Received transaction {msg.body.tag}, but I\'m waiting for {next_tag}')
            pending_txn[msg.body.tag] = msg
        else:
            await run_transaction(msg)
            next_tag += 1
            while (next_tag in pending_txn):
                await run_transaction(pending_txn[next_tag])
                del pending_txn[next_tag]
                next_tag += 1

    else:
        logging.warning('unknown message type %s', msg.body.type)

# Main loop
run(receiveAll(handle))
