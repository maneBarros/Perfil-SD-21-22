#!/usr/bin/env python3

import threading
import queue
import random
import ms

logging.getLogger().setLevel(logging.DEBUG)

# States
FOLLOWER = 0; CANDIDATE = 1; LEADER = 2

# Timeout range for follower/candidate timeout
timeoutRange = (150,300)

node_id = 0
node_ids = []
state = FOLLOWER
currentTerm = 0
lock = threading.RLock()
log = []
store = []

# Different message handlers for different states
handlers_state = {
    FOLLOWER  : handler_follower,
    CANDIDATE : handler_candidate,
    LEADER    : handler_leader
}

# Data structures for follower state
heardFromLeader = False
condFollower = threading.Condition(lock=lock)

# Data structures for candidate state
votes = {}
condCandidate = threading.Condition(lock=lock) # possibly only one condition needed, but to be safe...

# Data structures for leader state
peerInfo = {}
commitIndex = -1 # Highest index known to be commited

# Some helpful functions
def majority():
    return len(node_ids) // 2 + 1

def random_timeout():
    return random.randint(*timeoutRange)

def otherNodes():
    global node_id
    return [id for id in node_ids if id != node_id]

def handle_init(msg):
    global node_id, node_ids
    node_id = msg.body.node_id
    node_ids = msg.body.node_ids
    becomeFollower(0)

# ======================================================================================== #
# --------------------------------------- FOLLOWER --------------------------------------- #
# ======================================================================================== #

def waitForFollowerTimeout():
    global heardFromLeader
    with condFollower:
        while condFollower.waitFor(lambda:heardFromLeader, timeout=random_timeout()):
            heardFromLeader = False
        # Timeout!
        runForLeader()

def becomeFollower(msg=None):
    global state, currentTerm
        with lock:
            state = FOLLOWER
            if msg:
                handle(msg)
            else:
                currentTerm = 0
                heardFromLeader = False
        threading.Thread(target=waitForFollowerTimeout).start()

def handler_follower(msg):
    type = msg.body.type
    with lock:
        if msg in ['read', 'write', 'cas']:
            reply11(msg)
        elif type in ['AppendEntries', 'RequestVote'] and msg.body.term >= currentTerm:
            heardFromLeader = True
            condFollower.notify_all()
            if type == 'AppendEntries':
                handle_AppendEntries(msg)
            elif msg.body.term > currentTerm and ...:
                currentTerm = msg.body.term
                reply(msg, type='RequestVoteReply', granted=True)
        else:
            pass

def handle_AppendEntries(msg):
    pass

# ======================================================================================== #
# --------------------------------------- CANDIDATE -------------------------------------- #
# ======================================================================================== #

def runForLeader():
    global state, currentTerm, votes

    electedSomeone = False
    with condCandidate:
        while not electedSomeone:
            state = CANDIDATE
            currentTerm += 1
            myterm = currentTerm
            votes = {node_id : True}
            requestVotes()
            threading.Thread(target=retryRequestVote, args=(myterm,))
            electedSomeone = condCandidate.waitFor(lambda: myterm != currentTerm or state != CANDIDATE, random_timeout())

def retryRequestVote(myterm):
    retransmitTimeout = 100 # ms
    with condCandidate:
        while not condCandidate.waitFor(lambda : currentTerm != myterm or state != CANDIDATE, timeout=retransmitTimeout):
            requestVotes()

def requestVotes():
    with lock:
        for node in otherNodes():
            send(node_id, node, type='RequestVote', term=currentTerm, lastLogIndex=len(log)-1, lastLogTerm=log[-1][0])

def handler_candidate(msg):
    global votingEvents, votes, timeoutValue
    type = msg.body.type
    with lock:
        if type in ['read','write','cas']:
            reply11(msg)
        elif type == 'AppendEntries':
            if msg.body.term >= currentTerm:
                becomeFollower(msg=msg)
            else:
                reply(msg, type='AppendEntriesReply', success=False)
        elif type == 'RequestVote':
            if msg.body.term > currentTerm:
                becomeFollower(msg=msg)
            else:
                reply(msg, type='RequestVoteReply', granted=False)
        elif type == 'RequestVoteReply' and msg.body.term == currentTerm:
            votes[msg.src] = msg.body.granted
            if len([id for id in votes if votes[id]]) == majority():
                becomeLeader()
        else:
            pass

# ======================================================================================== #
# ---------------------------------------- LEADER ---------------------------------------- #
# ======================================================================================== #

# Handler for messages while in leader state
def handler_leader(msg):
    global log
    type = msg.body.type
    with lock:
        if type in ['read','write','cas']:
            log.append((currentTerm,msg))
            for follower in peerInfo:
                peerInfo[follower]['cond'].notify()
        elif msg.body.term > currentTerm:
            becomeFollower(msg)
        elif type == 'AppendEntriesReply' and msg.body.term == currentTerm:
            handle_AppendEntriesReply(msg)
        elif type == 'RequestVotes':
            reply(msg, type='RequestVotesReply', term=currentTerm, granted=False)

def handle_AppendEntriesReply(msg):
    with lock:
        matchIndex = msg.body.matchIndex
        if msg.body.success:
            peerInfo[msg.src]['matchIndex'] = matchIndex
            peerInfo[msg.src]['nextIndex'] = msg.body.matchIndex + 1
            if matchIndex > commitIndex and log[matchIndex][0] == currentTerm and 1 + len([peer for peer in peerInfo if peerInfo[peer]['matchIndex'] >= matchIndex]) >= majority():
                lastApplied = commitIndex
                commitIndex = matchIndex
                apply_and_reply(lastApplied)
        else:
            peerInfo[msg.src]['nextIndex'] -= 1
        peerInfo[msg.src]['cond'].notify()

# Create a thread for each peer in the network and start "serving" them
def becomeLeader():
    # init peer info
    for id in otherNodes():
        threading.Thread(target=serveFollower, args=(currentTerm,peerInfo[id]))

def serveFollower(myterm,peerInfo):
    timeoutValue = 0.05
    with lock:
        while myterm == currentTerm:
            if peerInfo['matchIndex'] >= 0 and len(log) >= peerInfo[peer_id]['nextIndex']:
                prevIndex = peerInfo[peer_id]['nextIndex'] - 1
                prevTerm = log[prevIndex][0]
                entries = [log[peerInfo[peer_id]['nextIndex']]]
                commitIndex = min(commitIndex, peerInfo['nextIndex'])
                send(node_id, peer_id, type='AppendEntries', term=currentTerm, prevIndex=, prevTerm=log[-1][0], entries=[], commitIndex=commitIndex)
            else:
                send(node_id, peer_id, type='AppendEntries', term=currentTerm, prevIndex=len(log)-1, prevTerm=log[-1][0], entries=[], commitIndex=commitIndex)
            #peerInfo[peer_id]['cond'].wait_for(lambda : myterm != currentTerm or peerInfo[peer_id]['matchIndex'] >= 0 and len(log) > peerInfo[peer_id]['nextIndex'], timeoutValue):

def apply_and_reply(lastApplied):
    for (term,req) in log[lastApplied+1 : commitIndex+1]:
        type = req.body.type
        if type == 'read' and term == currentTerm:
            if req.body.key in store:
                reply(req,type='read_ok',value=store[req.body.key])
            else:
                reply(req,type='error', code='20', text='Key not in store')
        elif type == 'write':
            store[msg.body.key] = msg.body.value
            if term == currentTerm:
                reply(req, type='write_ok')
        elif type == 'cas':
            if msg.body.key in store:
                if store[msg.body.key] == msg.body.from:
                    store[msg.body.key] = msg.body.to
                    success = (True, None)
                else:
                    success = (False, (22, 'Values don\'t match'))
            else:
                success = (False, (20, 'Key not in store'))
            if term == currentTerm:
                if success[0]:
                    reply(req, type='cas_ok')
                else:
                    reply(req, type='error', code=success[1][0], text=success[1][1])



def handle(msg):
    with lock:
        if not handlers_state[state](msg):
            logging.warning(f'Not ready for messages of type {type} in the state {state}')

if __name__ == '__main__':
    for msg in ms.receiveAll():
        handle(msg)
