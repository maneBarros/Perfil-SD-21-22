-module(rwlock).
-export([create/0, acquire/2, release/1]).

create() ->
  spawn(fun() -> released() end).

acquire(Lock, Mode) ->
  Lock ! {Mode, self()},
  receive {acquired, Lock} -> true end.

release(Lock) ->
  Lock ! {release, self()}.

released() ->
  receive
    {read, From} ->
      From ! {acquired, self()},
      reading([From],none);

    {write, From} ->
      From ! {acquired, self()},
      writing(From)
  end.

reading([], none) -> released();
reading([],Writer) ->
  Writer ! {acquired, self()},
  writing(Writer);
reading(L,Writer) ->
  case Writer of
    none ->
      receive
        {read, From} ->
          From ! {acquired, self()},
          reading([From | L], none);

        {write, From} ->
          reading(L, From);

        {release, From} ->
          reading(L -- [From], none)
      end;

    Writer ->
      receive
        {release, From} -> reading(L -- [From], Writer)
      end
  end.

writing(Writer) ->
  receive
    {release, Writer} ->
      released()
  end.
