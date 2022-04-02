-module(test).
-import(myqueue, [create/0, enqueue/2, dequeue/1]).
-export([main/0]).

main() ->
  Q = myqueue:create(),
  Q1 = myqueue:enqueue(Q, elem1),
  Q2 = myqueue:enqueue(Q1, elem2),
  {Q3, Elem} = myqueue:dequeue(Q2),
  Q4 = myqueue:enqueue(Q3, elem3),
  Q4.
