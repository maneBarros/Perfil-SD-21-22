-module(priorityqueue1).
%-import(myqueue, [create/0, enqueue/2, dequeue/1]).
-export([create/0, enqueue/3, dequeue/1]).

% Creates list of three queues (3 different priority levels)
create() ->
  [myqueue:create(), myqueue:create(), myqueue:create()].

enqueue([Q|Qs], Item, Priority) ->
  if
    Priority < 0; Priority > 3 ->
      'No such priority';
    Priority == 0 ->
      [myqueue:enqueue(Q,Item)|Qs];
    true ->
      [Q|enqueue(Qs,Item,Priority-1)]
  end.


dequeue([]) -> empty;

dequeue([Q|Qs]) ->
  case myqueue:dequeue(Q) of
    empty ->
      case dequeue(Qs) of
        empty ->
          empty;
        {NewQs, Item} ->
          {[Q|NewQs], Item}
      end;
    {NewQ, Item} ->
      {[NewQ|Qs], Item}
  end.
