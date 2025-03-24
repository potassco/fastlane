#const g=3.
#const p=3.
#const w=3.

player(1..g*p).
group(1..g).
week(1..w).

{ plays(P,W,G) : group(G) } = 1 :- player(P), week(W).
{ plays(P,W,G) : player(P) } = p :- week(W), group(G).

meets(P1,P2,W) :- plays(P1,W,G), plays(P2,W,G), P1 < P2.
%:~ #count { W : meets(P1,P2,W) } > 1, player(P1), player(P2), P1 < P2. [1,P1]

_lns_priority("min",1).
_lns_penalty("min",P1,1) :- #count { W : meets(P1,P2,W) } > 1, player(P1), player(P2), P1 < P2.
#show plays/3.

_lns_select(W) :- week(W).
_lns_fix(plays(P,W,G),W) :- _lns_select(W), plays(P,W,G).