#!/usr/bin/env python3

from ms import *
from types import SimpleNamespace as sn
from math import ceil
import random

logging.getLogger().setLevel(logging.DEBUG)

id = 0
node_ids = []
quorum_size = -1
server_replies = {}
client_request = None
pending_requests = []
store = {}
locks = {}

def handle(msg):
    handlers = {
        # Init message
        "init"        : handle_init,

        # Client Requests
        "read" : handle_client_request,
        "write": handle_client_request,
        "cas"  : handle_client_request,

        # Server requests and replies
        "server_read" : handle_read,
        "server_write": handle_write,
        "server_reply": handle_reply,
        "ack"         : handle_ack,
        "unlock"      : handle_unlock
    }

    type = msg.body.type
    if type in handlers:
        handlers[type](msg)
    else:
        logging.warning('Unknown message type %s', type)


def handle_init(msg):
    global id, node_ids, quorum_size

    id = msg.body.node_id
    node_ids = msg.body.node_ids
    quorum_size = ceil((len(node_ids) + 1)/2)
    logging.info('node %s initialized', id)

    reply(msg, type='init_ok')

def handle_client_request(msg):
    global pending_requests, client_request

    if client_request:
        pending_requests.append(msg)
    else:
        client_request = msg
        processClientRequest()

def processClientRequest():
    global server_replies

    if client_request:
        target_servers = random.sample(node_ids, quorum_size)
        server_replies = {}
        forWrite = client_request.body.type == 'write' or client_request.body.type == 'cas'
        for server in target_servers:
            send(id, server, type='server_read', forWrite=forWrite, key=client_request.body.key)


# Handles a read request from a server
# Responds with valid = True if the lock was successfully acquired; valid = False otherwise
def handle_read(msg):
    global locks, store

    if msg.body.key in locks and locks[msg.body.key] and locks[msg.body.key] != msg.src:
        reply(msg, type='server_reply', key=msg.body.key, value=None, valid=False)
    else:
        if msg.body.forWrite:
            locks[msg.body.key] = msg.src
        if msg.body.key not in store:
            value = None
        else:
            value = store[msg.body.key]
        reply(msg, type='server_reply', key=msg.body.key, value=value, valid=True)


def handle_write(msg):
    global store, locks

    key = msg.body.key
    if key in locks and locks[key] == msg.src and (key not in store or msg.body.value[1] > store[key][1]):
        store[key] = msg.body.value
        locks[key] = None
    reply(msg, type='ack', key=key)


def handle_reply(msg):
    global server_replies

    server_replies[msg.src] = msg
    if len(server_replies) == quorum_size:
        # Received replies from all servers we contacted
        if not [m for m in server_replies.values() if not m.body.valid]:
            # If all replies are positive...
            existingEntries = [m.body.value for m in server_replies.values() if m.body.value]
            if existingEntries:
                (value, timestamp) = max(existingEntries, key=lambda x: x[1])

            if client_request.body.type == 'read':
                # Handling a read request. Only have to send value to client
                if existingEntries:
                    reply(client_request, type='read_ok', value=value)
                else:
                    reply(client_request, type='error', code=20, text='Key doesn\'t exist')
                nextRequest()

            elif client_request.body.type == 'write':
                # Handling a write request: will send new value to all servers we've read from, with updated timestamp
                # Will have to then wait for acks until I can reply to client
                newValue = client_request.body.value
                if not existingEntries:
                    timestamp = 0

                for server in server_replies:
                    send(id, server, type='server_write', key=client_request.body.key, value=(newValue, timestamp+1))
                server_replies = {} # reset replies dict

            elif client_request.body.type == 'cas':
                # Handling a cas request: will check if currenty value equals 'from' value; if so writes new value, otherwise returns an error
                if not existingEntries or value != client_request.body.__dict__['from']:
                    for server in server_replies:
                        send(id, server, type='unlock', key=client_request.body.key)
                    if not existingEntries:
                        code = 20
                        text = 'No such key in store'
                    else:
                        code = 22
                        text = 'Values don\'t match'
                    reply(client_request, type='error', code=code, text=text)
                    nextRequest()
                else:
                    newValue = client_request.body.to
                    for server in server_replies:
                        send(id, server, type='server_write', key=client_request.body.key, value=(newValue, timestamp+1))
                    server_replies = {}

        else:
            # Some negative reply. Will have to cancel operation
            for server in server_replies:
                send(id, server, type='unlock', key=client_request.body.key)
            reply(client_request, type='error', code=11, text='Some locks already taken')
            nextRequest()

def handle_ack(msg):
    global server_replies

    server_replies[msg.src] = msg
    if len(server_replies) == quorum_size:
        # Received ack from all
        if client_request.body.type == 'write':
            type = 'write_ok'
        else:
            type = 'cas_ok'
        reply(client_request, type=type)
        nextRequest()


def handle_unlock(msg):
    global locks

    key = msg.body.key
    if key in locks and locks[key] == msg.src:
        locks[key] = None

# Resets server_replies dict and starts processing new request if there's any
def nextRequest():
    global server_replies, pending_requests, client_request

    server_replies = {}
    if pending_requests:
        client_request = pending_requests.pop(0)
        processClientRequest()
    else:
        client_request = None


for msg in receiveAll():
    handle(msg)
