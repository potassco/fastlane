% currently used for testing, will be reworked/cleaned for demo
%#program config.
#const n = 60.
%_project((plays,3), plays(P,W,G)) :- plays(P,W,G).

% _lns_select
% _project_op(name, signature).
_project_op("plays_3", (plays,3)).
_project(plays_3, plays(P,W,G)) :- plays(P,W,G).

_project_op("plays_4", (plays,3)).
_project(plays_4, plays(P,W,G)) :- plays(P,W,G).

% _lns_relax
% _destroy_op(name, parameter[auto,p(),n(),(p(),n(),...)]).
_destroy_op("random_n", p(n)).
_destroy("random_n", plays(P,W,G), W) :- plays(P,W,G).

_destroy_op("random_auto", auto).
_destroy("random_auto", plays(P,W,G), W) :- plays(P,W,G).

% _destroy_op("week", "random_n", plays(P,W,G), W) :- plays(P,W,G).

% _lns_prioritize
% _prioritize_op(name, value, modifier).
_prioritize_op("1_true", 1, true).
_prioritize("1_true", plays(P,W,G)) :- plays(P,W,G).

% _lns_config
% _config(name, project_op, destroy_op, prioritize_op).
% multiple configs allowed
_config("Random", "plays_3", "random_auto", "1_true").
%_config("Random_auto", "plays_4", "random_auto", "1_true").

% _lns_strategy
% currently only 1 strat supported?
_strategy("roulette", "Random").
%_strategy("roulette", "Random2").
