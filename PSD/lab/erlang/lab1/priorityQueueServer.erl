-module(priorityQueueServer).
-import(priorityqueue_trees, [create/0, enqueue/3, dequeue/1]).
-export([run/0]).

run() ->
  %spawn(priorityQueueServer, loop, [create()]).
  spawn(fun() -> loop(create()) end).

loop(PriQueue) ->
  receive
    {Src, enqueue, Item, Priority} ->
      NewQueue = enqueue(PriQueue, Item, Priority),
      Src ! {self(), NewQueue},
      loop(NewQueue);
    {Src, dequeue} ->
      case dequeue(PriQueue) of
        empty ->
          Src ! {self(), empty},
          loop(PriQueue);
        {NewPriQueue, Item} ->
          Src ! {self(), Item},
          loop(NewPriQueue)
      end
  end.
