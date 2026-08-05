% _project_op(name, signature).
_project_op(plays_3, (plays,3)).
_project(plays_3, plays(P,W,G)) :- plays(P,W,G).

% _destroy_op(name, [auto,p(),n(),(p(),n(),...)]).
_destroy_op((random,N), p(N)) :- N=(10;20).
_destroy((random,(10;20)), plays(P,W,G), (P,W,G)) :- plays(P,W,G).
_destroy_op("week_auto", auto).
_destroy("week_auto", plays(P,W,G), W) :- plays(P,W,G).

% _prioritize_op(name, value, modifier).
_prioritize_op("1_true", 1, true).
_prioritize("1_true", plays(P,W,G)) :- plays(P,W,G).

% _config(name, project_op, destroy_op, prioritize_op).
_config("Random10", "plays_3", (random,10), "1_true").
_config("Random20", "plays_3", (random,20), "1_true").
_config("Week_auto", "plays_3", "week_auto", "1_true").

_strategy("roulette", C) :- _config(C, _, _, _).
