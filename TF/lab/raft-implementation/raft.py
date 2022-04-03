#!/usr/bin/env python3

import threading
import queue
import random
from ms import *

logging.getLogger().setLevel(logging.DEBUG)


FOLLOWER  = 0
CANDIDATE = 1
LEADER    = 2
timeoutRange = (150,300)
pendingMessages = queue.Queue()
timeoutValue = 0

node_id = 0
node_ids = []
state = FOLLOWER
currentTerm = 0

# Data structures for candidate state
votes = 0
votingEvents = {}
waitingLimit = 0

handlers_state = {
    FOLLOWER  : handlers_follower,
    CANDIDATE : handlers_candidate,
    LEADER    : handlers_leader
}

handlers_follower = {
    'init' : handle_init
}

timeout_handlers {
    FOLLOWER : runForLeader
}

def handle(msg):
    type = msg.body.type
    if type in handlers_state[state]:
        handlers[state][type](msg)
    else:
        logging.warning(f'Not ready for messages of type {type} in the state {state}')

def handle_init(msg):
    global node_id, node_ids
    node_id = msg.body.node_id
    node_ids = msg.body.node_ids
    reply(msg, type='init_ok')
    timeoutValue = random_timeout()

def random_timeout():
    return random.randint(*timeoutRange)

def handle_read(msg):
    pass

def handle_write(msg):
    pass

def handle_cas(msg):
    pass

def send_AppendEntries(dst, **content):
    pass

def send_RequestVote(dst, **content):
    pass


def handle_msg(msg):
    global pendingMessages
    pendingMessages.put(msg)

def followerLoop():
    global pendingMessages, state
    state = FOLLOWER
    try:
        while(True):
            nextMsg = pendingMessages.get(block=True, timeout=randomtimeout)
    except queue.Empty as e:
        # Timeout!
        runForLeader()


def requestVote(noRequestNeeded):
    sendRequest = True
    while(sendRequest):
        # send vote request
        # wait for event for some time

# When it times out, a follower becomes a candidate and attempts to become leader
def runForLeader():
    global currentTerm, state, votes, votingEvents, timeoutValue, waitingLimit, electionState

    #runningForLeader = True
    currentTerm += 1
    state = CANDIDATE
    votes = 1
    votingEvents = {}
    electionState = 0 # 1 -> won the election; 2 -> another leader; 3 -> timeout
    for peer in [id in node_ids if id != node_id]:
        event = threading.Event()
        votingEvents[peer] = event
        threading.Thread(target=requestVote, args=(event,)).start()

    waitingLimit = time.time() + random_timeout()
    timeoutValue = waitingLimit - time.time()


    while (electionState == 0):
        try:
            msg = pendingMessages.get(timeout=waitingLimit-time.time())

            if msg.body.type == 'AppendEntries' and msg.body.term >= currentTerm:
                electionState = 2

            elif msg.body.type == 'RequestVote':
                reply(msg, type='RequestVoteReply', granted=False)

            elif msg.body.type == 'RequestVoteReply':
                votingEvents[msg.src].set() # Notify that we received a reply from this server
                del votingEvents[msg.src]
                if msg.body.granted:
                    votes += 1
                    if votes == len(node_ids) // 2 + 1:
                        electionState = 1
                        for peer in votingEvents:
                            votingEvents[peer].set() # Notify that we dont need more answers

            elif msg.body.type in ['read', 'write', 'cas']:
                reply(msg, type='error', code=11, text='Not leader')


        except queue.Empty as e:
            # Timeout! Let's try to run again for a new term
            for peer in votingEvents:
                votingEvents[peer].set() # stop threads waiting for answers
                electionState = 3

    if electionState == 1: # I won the election
        becomeLeader()
    elif electionState == 2: # Another leader
        for peer in votingEvents:
            votingEvents[peer].set() # stop threads waiting for answers
            electionState = 3
        followerLoop()



def receiveMsgs():
    for msg in receiveAll():
        pendingMessages.put(msg)

if __name__ == '__main__':
    threading.Thread(target=receiveMsgs).start()
    while(True):
        try:
            msg = pendingMessages.get(timeout=timeoutValue)
            handle(msg)
        except queue.Empty as empty:
            handle_timeout()
