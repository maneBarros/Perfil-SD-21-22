-module(myqueue).
-export([create/0, enqueue/2, dequeue/1]).

create_simple() ->
  [].

enqueue_simple(Q, Item) ->
  Q ++ [Item].

dequeue_simple([]) ->
  empty;
dequeue_simple([H | T]) ->
  {T,H}.

create() ->
  {[],[]}.

enqueue({Q1,Q2}, Item) ->
  {[Item|Q1],Q2}.

dequeue({[],[]}) -> empty;
dequeue({Q1,[H|T]}) -> {{Q1,T}, H};
dequeue(Q) -> dequeue(transfer(Q)).

transfer({[],Q}) -> {[],Q};
transfer({[H|T],Q}) -> transfer({T,[H|Q]}).
