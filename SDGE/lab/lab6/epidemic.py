#!/usr/bin/env python3

from ms import *#send, reply, run, addHandlers
import random
import threading
import time

FANOUT = 3
K = 3

node_id = 0
node_ids = []
known_messages = {}
known_ids = {}


def otherServers():
    return [id for id in node_ids if id != node_id]

def handle_init(msg):
    global node_id, node_ids

    node_id = msg.body.node_id
    node_ids = msg.body.node_ids
    reply(msg, type='init_ok')

def handle_ihave(msg):
    id = msg.body.id
    if id not in known_messages:
        with lock:
            if id in known_ids:
                known_ids[id][1].append(msg.src)
            else:
                known_ids[id] = (threading.Condition(lock),[msg.src])
                reply(msg, type='iwant', id=id)
                threading.Thread(target=pullMessage, args=(id,)).start()

def pullMessage(id):
    index = 0
    with lock:
        while not wait_for(lambda : id not in known_ids, timeout=0.5):
            index = (index + 1) % len(known_ids[id])
            send(node_id, known_ids[id][index], type='iwant', id=id)

def handle_iwant(msg):
    id = msg.body.id
    if id in known_messages:
        reply(msg, type='server_broadcast', message=known_messages[id], hops=K)

def handle_broadcast(msg):
    global known_messages

    id = msg.body.message
    content = msg.body.message
    hops = msg.body.hops
    if id not in known_messages: # new "desease"
        with lock:
            if id in known_ids: # we had asked for this message
                known_ids[id][0].notify()
                del known_ids[id]

        known_messages[id] = content
        if FANOUT >= len(node_ids) - 1:
            targets = otherServers()
        else:
            targets = random.sample(otherServers(), FANOUT)

        if hops < K:
            # Eager behaviour
            for server in targets:
                send(node_id, server, type='server_broadcast', message=content, hops=hops+1)
        else:
            # Lazy behaviour
            for server in targets:
                send(node_id, server, type='ihave', id=id)

    if msg.body.type == 'broadcast':
        reply(msg, type='broadcast_ok')

def handle_read(msg):
    reply(msg, type='read_ok', messages=known_messages)

def handle_topology(msg):
    reply(msg, type='topology_ok')

def addTTLfield(msg):
    msg_dict = vars(msg)
    msg_dict['body']['hops'] = 0
    return sn(msg_dict)

if __name__ == '__main__':
    addHandlers({
        'init' : handle_init,
        'topology' : handle_topology,
        'broadcast' : lambda msg: handle_broadcast(addTTLfield(msg)),
        'read' : handle_read,
        'server_broadcast' : handle_broadcast,
        'iwant' : handle_iwant,
        'ihave' : handle_ihave
    })
    run()
