-module(login_manager).
-export([start/0, create_account/2, close_account/2, login/2, logout/1, online/0]).
-import(maps,[remove/2]).

% interface functions
start() ->
  register(?MODULE, spawn(fun() -> loop(#{}) end)).

send_request(Request, Params) ->
  ?MODULE ! {Request, Params, self()},
  receive {Res, ?MODULE} -> Res end.

create_account(Username, Passwd) ->
  send_request(create_account, {Username, Passwd}).

close_account(Username, Passwd) ->
  send_request(close_account, {Username, Passwd}).

login(Username, Passwd) ->
  send_request(login, {Username, Passwd}).

logout(Username) ->
  send_request(logout, {Username}).

online() ->
  send_request(online, {}).

% server process
loop(Map) ->
  receive
    {create_account, {Username, Passwd}, Src} ->
      case maps:is_key(Username, Map) of
        true ->
          Src ! {user_exists, ?MODULE},
          loop(Map);
        false ->
          Src ! {ok, ?MODULE},
          loop(Map#{Username => {Passwd,false}})
      end;
    {close_account, {Username, Passwd}, Src} ->
      case maps:is_key(Username, Map) of
        true ->
          case maps:get(Username, Map) of
            {Passwd, _} ->
              Src ! {ok,?MODULE},
              loop(remove(Username,Map));
            _ ->
              Src ! {error, ?MODULE},
              loop(Map)
          end;

        false ->
          Src ! {error, ?MODULE},
          loop(Map)
      end;

    {login, {Username, Passwd}, Src} ->
      case maps:find(Username, Map) of
        {ok, {Passwd, false}} ->
          Src ! {ok, ?MODULE},
          loop(Map#{Username := {Passwd, true}});
        _ ->
          Src ! {error, ?MODULE},
          loop(Map)
      end;

    {logout, {Username}, Src} ->
      case maps:find(Username, Map) of
        {ok, {Passwd, true}} ->
          Src ! {ok, ?MODULE},
          loop(Map#{Username := {Passwd, false}});
        _ ->
          Src ! {error, ?MODULE},
          loop(Map)
      end;

    {online, _, Src} ->
      Users = [U || {U, {_, true}} <- maps:to_list(Map)],
      Src ! {Users, ?MODULE},
      loop(Map)

  end.
