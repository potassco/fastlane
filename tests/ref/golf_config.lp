#const n=60.

_project_op("plays_3", (plays,3)).
_project(plays_3, plays(P,W,G)) :- plays(P,W,G).

_destroy_op("week_n", p(n)).
_destroy("week_n", plays(P,W,G), W) :- plays(P,W,G).

_destroy_op("week_auto", auto).
_destroy("week_auto", plays(P,W,G), W) :- plays(P,W,G).

_destroy_op("random_auto", auto).
_destroy("random_auto", plays(P,W,G), (P,W,G)) :- plays(P,W,G).

_prioritize_op("1_true", 1, true).
_prioritize("1_true", plays(P,W,G)) :- plays(P,W,G).

_config("Week", "plays_3", "week_n", "1_true").
_config("Week_auto", "plays_3", "week_auto", "1_true").
_config("Random", "plays_3", "random_auto", "1_true").

_strategy("roulette", C) :- _config(C, _, _, _).
