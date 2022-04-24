-module(priorityqueue_trees).
-export([create/0, enqueue/3, dequeue/1]).
-import(gb_trees, [get/2, update/3, insert/3, iterator/1, next/1, is_defined/2, empty/0]).

create() ->
  empty().

enqueue(PriQueue, Item, Priority) ->
  case is_defined(Priority, PriQueue) of
    true ->
      BeforeQueue = get(Priority, PriQueue),
      update(Priority, myqueue:enqueue(BeforeQueue,Item), PriQueue);
    false ->
      NewQueue = myqueue:enqueue(myqueue:create(), Item),
      insert(Priority, NewQueue, PriQueue)
  end.

dequeue(PriQueue) ->
  Iter = iterator(PriQueue),
  case dequeueAux(Iter) of
    empty -> empty;
    {Priority, UpdatedQueue, Item} -> {update(Priority, UpdatedQueue, PriQueue), Item}
  end.


dequeueAux(Iter) ->
  case next(Iter) of
    none ->
      empty;
    {Priority, Queue, Iter2} ->
      case myqueue:dequeue(Queue) of
        empty ->
          dequeueAux(Iter2);
        {UpdatedQueue, Item} ->
          {Priority, UpdatedQueue, Item}
      end
  end.
