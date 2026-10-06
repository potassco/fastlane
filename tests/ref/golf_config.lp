#const n=60.

_project_op("plays_3", (plays,3)).
_project(plays_3, plays(P,W,G)) :- plays(P,W,G).

_project_op("meets_3", (meets,3)).
_project(meets_3, meets(P,W,G)) :- meets(P,W,G).

_destroy_op("week_n", p(n)).
_destroy("week_n", plays(P,W,G), W) :- plays(P,W,G).

_destroy_op("week_auto", auto).
_destroy("week_auto", plays(P,W,G), W) :- plays(P,W,G).

_destroy_op("random_auto", auto).
_destroy("random_auto", plays(P,W,G), (P,W,G)) :- plays(P,W,G).

_destroy_op("meets_week_auto", auto).
_destroy("meets_week_auto", meets(P,W,G), W) :- meets(P,W,G).

_prioritize_op("1_true", 1, true).
_prioritize("1_true", plays(P,W,G)) :- plays(P,W,G).

_search_param("cutoff-1s", ("cutoff", 1)).
_search_param("tweety", ("configuration", "tweety")).
_search_param("cutoff-1s", ("configuration", "auto")).

_config("Week", "plays_3", "week_n", "1_true", "cutoff-1s").
_config("Week_auto", "plays_3", "week_auto", "1_true").
_config("Random", "plays_3", "random_auto", "1_true", "cutoff-1s").
_config("Mixed", ("plays_3";"meets_3"), ("week_n";"meets_week_auto"), "1_true", ("cutoff-3s";"tweety")).

_strategy("roulette", C) :- _config(C, _, _, _, _).
_strategy("roulette", C) :- _config(C, _, _, _).
