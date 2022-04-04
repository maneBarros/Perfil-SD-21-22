#!/usr/bin/env python3

from ms import *#send, reply, run, addHandlers
import random

node_id = 0
node_ids = []
known_messages = []
fanout = 3

def otherServers():
    return [id for id in node_ids if id != node_id]

def handle_init(msg):
    global node_id, node_ids

    node_id = msg.body.node_id
    node_ids = msg.body.node_ids
    reply(msg, type='init_ok')

def handle_broadcast(msg):
    global known_messages

    content = msg.body.message
    if content not in known_messages: # new "desease"
        known_messages.append(content)
        if fanout >= len(node_ids) - 1:
            targets = otherServers()
        else:
            targets = random.sample(otherServers(), fanout)
        for server in targets:
            send(node_id, server, type='server_broadcast', message=content)
    if msg.body.type == 'broadcast':
        reply(msg, type='broadcast_ok')

def handle_read(msg):
    reply(msg, type='read_ok', messages=known_messages)

def handle_topology(msg):
    reply(msg, type='topology_ok')

if __name__ == '__main__':
    addHandlers({
        'init' : handle_init,
        'topology' : handle_topology,
        'broadcast' : handle_broadcast,
        'read' : handle_read,
        'server_broadcast' : handle_broadcast
    })
    run()
