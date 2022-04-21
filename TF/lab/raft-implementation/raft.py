#!/usr/bin/env python3

import logging
import threading
import queue
import random
from ms import *

logging.getLogger().setLevel(logging.DEBUG)

# Raft states
FOLLOWER = 0; CANDIDATE = 1; LEADER = 2

# Timeout range for follower/candidate timeout
timeoutRange = (150,301) # 150 - 300 ms

node_id = 0
node_ids = []
lock = threading.RLock()

state = FOLLOWER
currentTerm = 0
log = []
commitIndex = -1 # Highest index known to be commited (first log index is 0)
store = {}

# For follower state
votedFor = None # Necessary, for example, when leaders revert to followers but don't vote for a leader (received an invalid request vote with higher term than the current one)
heardFromLeader = False

# For candidate state
votes = {}
timeoutCond = threading.Condition(lock=lock)

# For leader state
peerInfo = {}

# Some helpful functions
def majority():
    return len(node_ids) // 2 + 1

def random_timeout():
    return random.randrange(*timeoutRange,10) / 1000

def otherNodes():
    return [id for id in node_ids if id != node_id]

def reply11(msg):
    reply(msg, type='error', code=11, text='Not a leader')

def apply(msg):
    global store
    type = msg.body.type
    with lock:
        if type == 'read':
            return {'type':'read_ok', 'value':store[msg.body.key]} if msg.body.key in store else {'type':'error', 'code':20, 'text':'Key not in store'}
        elif type == 'write':
            store[msg.body.key] = msg.body.value
            return {'type':'write_ok'}
        elif type == 'cas':
            if msg.body.key in store:
                if store[msg.body.key] == msg.body.__dict__['from']:
                    store[msg.body.key] = msg.body.to
                    success = (True,)
                else:
                    success = (False, (22, 'Values don\'t match'))
            else:
                success = (False, (20, 'Key not in store'))
            return {'type':'cas_ok'} if success[0] else {'type':'error', 'code':success[1][0], 'text':success[1][1]}

def handle_init(msg):
    global node_id, node_ids
    node_id = msg.body.node_id
    node_ids = msg.body.node_ids
    reply(msg, type='init_ok')
    becomeFollower()

# ======================================================================================== #
# --------------------------------------- FOLLOWER --------------------------------------- #
# ======================================================================================== #

# Reverts to (or starts as) a follower
# When reverting to follower from candidate/leader state, takes the message that triggered this change as input
def becomeFollower(msg=None):
    global state, currentTerm, heardFromLeader
    with lock:
        state = FOLLOWER
        if msg:
            handler_follower(msg)
    threading.Thread(target=waitForFollowerTimeout).start()

# Function executed by background thread for triggering election process when timeout ocurrs
def waitForFollowerTimeout():
    global heardFromLeader
    with timeoutCond:
        while timeoutCond.wait_for(lambda : heardFromLeader, timeout=random_timeout()):
            heardFromLeader = False
        # Timeout!
        runForLeader()

# How to handle incoming messages as follower
def handler_follower(msg):
    global currentTerm, heardFromLeader, votedFor
    type = msg.body.type
    with lock:
        if type in ['read', 'write', 'cas']:
            reply11(msg)
        else:
            if msg.body.term > currentTerm:
                currentTerm = msg.body.term # Updates current term if incoming term is higher
                votedFor = None

            if type == 'AppendEntries':
                if msg.body.term < currentTerm:
                    reply(msg, type='AppendEntriesReply', success=False, term=currentTerm)
                else:
                    heardFromLeader = True; timeoutCond.notify_all() # Heard from a leader: reset timeout clock
                    handle_AppendEntries(msg)
            elif type == 'RequestVote':
                if msg.body.term < currentTerm or \
                   votedFor != None and votedFor != msg.src or \
                   (log[-1][0] if log else 0, len(log)-1) > (msg.body.lastLogTerm, msg.body.lastLogIndex):
                    reply(msg, type='RequestVoteReply', term=currentTerm, granted=False)
                else:
                    heardFromLeader = True; timeoutCond.notify_all() # Heard from a valid candidate: reset timeout clock
                    votedFor = msg.src
                    reply(msg, type='RequestVoteReply', term=currentTerm, granted=True)

def handle_AppendEntries(msg):
    global log, commitIndex
    with lock:
        if len(log) > msg.body.prevIndex and (msg.body.prevIndex < 0 or log[msg.body.prevIndex][0] == msg.body.prevTerm): # Success! Every log entry up until this index matches wiht leader
            log = log[0:msg.body.prevIndex+1] + msg.body.entries
            if msg.body.commitIndex > commitIndex:
                lastApplied = commitIndex
                commitIndex = min(msg.body.commitIndex, len(log)-1) # To allow more conservative implementations
                applyLogEntries(lastApplied)
            reply(msg, type='AppendEntriesReply', term=currentTerm, success=True, matchIndex=len(log)-1)
        else:
            reply(msg, type='AppendEntriesReply', term=currentTerm, success=False, matchIndex=0)

def applyLogEntries(lastApplied):
    with lock:
        for (_,op) in log[lastApplied+1:commitIndex+1]:
            apply(op)

# ======================================================================================== #
# --------------------------------------- CANDIDATE -------------------------------------- #
# ======================================================================================== #

# Function executed when follower times out, after some time has passed without hearing from a leader or a valid candidate
def runForLeader():
    global state, currentTerm, votes, votedFor
    electedSomeone = False
    with timeoutCond:
        state = CANDIDATE
        while not electedSomeone:
            currentTerm += 1
            myterm = currentTerm
            votedFor = node_id
            votes = {node_id : True}
            requestVotes()
            threading.Thread(target=retryRequestVote, args=(currentTerm,)).start()
            electedSomeone = timeoutCond.wait_for(lambda: myterm != currentTerm or state != CANDIDATE, random_timeout())

# Every 100ms, if election is still going, retry to request votes from peers who have not answered yet
# Executed by a background thread after sending first round of RequestVotes
def retryRequestVote(myterm):
    retransmitTimeout = 0.1 # 100 ms
    with timeoutCond:
        while not timeoutCond.wait_for(lambda : currentTerm != myterm or state != CANDIDATE, timeout=retransmitTimeout):
            requestVotes()

# Sends request votes to all peers who haven't answered yet
def requestVotes():
    with lock:
        for node in [node for node in otherNodes() if node not in votes]:
            send(node_id, node, type='RequestVote', term=currentTerm, lastLogIndex=len(log)-1, lastLogTerm=log[-1][0] if log else 0)

# How to handle messages as candidate
def handler_candidate(msg):
    global votes
    type = msg.body.type
    with lock:
        if type in ['read','write','cas']:
            reply11(msg)
        elif type == 'AppendEntries':
            becomeFollower(msg) if msg.body.term >= currentTerm else reply(msg, type='AppendEntriesReply', term=currentTerm, success=False)
        elif type == 'RequestVote':
            becomeFollower(msg) if msg.body.term > currentTerm else reply(msg, type='RequestVoteReply', term=currentTerm, granted=False)
        elif type == 'RequestVoteReply':
            if msg.body.term > currentTerm:
                becomeFollower(msg)
            elif msg.body.term == currentTerm:
                votes[msg.src] = msg.body.granted
                if len([id for id in votes if votes[id]]) == majority():
                    becomeLeader()

# ======================================================================================== #
# ---------------------------------------- LEADER ---------------------------------------- #
# ======================================================================================== #

# Create a thread for each peer in the network. These threads start "serving" the followers
def becomeLeader():
    global state, peerInfo
    with lock:
        state = LEADER
        for id in otherNodes():
            peerInfo[id] = {'cond' : threading.Condition(lock=lock), 'nextIndex' : len(log), 'matchIndex' : 0}
            threading.Thread(target=serveFollower, args=(currentTerm,id,peerInfo[id])).start()

# Serve follower identified by peer_id: that is, send an AppendEntries to this follower whenever it is necessary
def serveFollower(myterm,peer_id,peer):
    timeoutValue = 0.08
    with lock:
        while myterm == currentTerm:
            nextIndex = peer['nextIndex']
            prevIndex = nextIndex - 1
            prevTerm = log[prevIndex][0] if prevIndex >= 0 else 0
            entries = log[nextIndex:len(log)]
            send(node_id, peer_id, type='AppendEntries', term=currentTerm, prevIndex=prevIndex, prevTerm=prevTerm, entries=entries, commitIndex=commitIndex)
            peer['cond'].wait_for(lambda : myterm != currentTerm or nextIndex != peer['nextIndex'] and len(log) > peer['nextIndex'], timeoutValue)

# How to handle messages as leader
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
    global peerInfo, commitIndex
    with lock:
        matchIndex = msg.body.matchIndex
        if msg.body.success:
            peerInfo[msg.src]['matchIndex'] = matchIndex
            peerInfo[msg.src]['nextIndex'] = msg.body.matchIndex + 1
            if matchIndex > commitIndex and \
               log[matchIndex][0] == currentTerm and \
               1 + len([p for p in peerInfo if peerInfo[p]['matchIndex'] >= matchIndex]) >= majority():
                lastApplied = commitIndex
                commitIndex = matchIndex
                apply_and_reply(lastApplied)
        else:
            peerInfo[msg.src]['nextIndex'] -= 1
        peerInfo[msg.src]['cond'].notify()

# Apply operations in log from lastApplied to current commitIndex. Replies to clients if the request was made during this leader's term
def apply_and_reply(lastApplied):
    with lock:
        for (term,req) in log[lastApplied+1 : commitIndex+1]:
            rep = apply(req)
            if term == currentTerm:
                reply(req,**rep)

# Different message handlers for different states
handlers_state = {
    FOLLOWER  : handler_follower,
    CANDIDATE : handler_candidate,
    LEADER    : handler_leader
}

if __name__ == '__main__':
    for msg in receiveAll():
        handle_init(msg) if msg.body.type == 'init' else handlers_state[state](msg)
