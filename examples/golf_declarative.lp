% _project_op(name, signature).
_project_op(plays_3, (plays,3)).
_project(plays_3, plays(P,W,G)) :- plays(P,W,G).

% _destroy_op(name, [auto,p(),n(),(p(),n(),...)]).
_destroy_op("week_60", p(60)).
_destroy("week_60", plays(P,W,G), W) :- plays(P,W,G).

% _prioritize_op(name, value, modifier).
_prioritize_op("1_true", 1, true).
_prioritize("1_true", plays(P,W,G)) :- plays(P,W,G).

% _config(name, project_op, destroy_op, prioritize_op).
_config("Week_60", "plays_3", "week_60", "1_true").

_strategy("static", C) :- _config(C, _, _, _).