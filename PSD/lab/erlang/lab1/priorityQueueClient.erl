-module(priorityQueueClient).
-export([enqueue/3, dequeue/1]).

enqueue(Server, Item, Priority) ->
  Server ! {self(), enqueue, Item, Priority},
  receive {Server, PriQueue} -> PriQueue end.

dequeue(Server) ->
  Server ! {self(), dequeue},
  receive {Server, Item} -> Item end.
