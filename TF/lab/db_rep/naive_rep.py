#!/usr/bin/env python3

import logging
from asyncio import run, create_task, sleep

from ams import send, receiveAll, reply
from db import DB

logging.getLogger().setLevel(logging.DEBUG)

db = DB()

async def handle(msg):
    # State
    global node_id, node_ids
    global db

    # Message handlers
    if msg.body.type == 'init':
        node_id = msg.body.node_id
        node_ids = msg.body.node_ids
        logging.info('node %s initialized', node_id)

        reply(msg, type='init_ok')

    elif msg.body.type == 'txn':
        logging.info('Replicating txn')

        for node in node_ids:
            send(node_id, node, type='fwd_txn', txn=msg.body.txn, client=msg.src, original_id=msg.body.msg_id)

    elif msg.body.type == 'fwd_txn':
        logging.info('Running transaction')

        ctx = await db.begin([k for op,k,v in msg.body.txn], msg.src+'-'+str(msg.body.original_id))
        rs,wv,res = await db.execute(ctx, msg.body.txn)
        if res:
            await db.commit(ctx, wv)
            if msg.src == node_id:
                send(node_id, msg.body.client, in_reply_to=msg.body.original_id, type='txn_ok', txn=res)
        elif msg.src == node_id:
            send(node_id, msg.body.client, in_reply_to=msg.body.original_id, type='error', code=14, text='transaction aborted')
        db.cleanup(ctx)

    else:
        logging.warning('unknown message type %s', msg.body.type)

# Main loop
run(receiveAll(handle))
