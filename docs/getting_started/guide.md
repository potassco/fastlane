# Guide

This section will illustrate how to use this framework by giving some small examples.
All python code snippets shown here can also be found in [`./examples/demo.py`][demo].
The problem we will be looking at is the
[Social golfer problem](https://en.wikipedia.org/wiki/Social_golfer_problem) with
5 players, 5 groups and 5 weeks. We choose a small instance, to keep the run-time as
low as possible, while still being able to observe the effects of different approaches.


## Encoding

The corresponding encoding is located in [`./examples/golf.lp`][golf]:

```
#const g=5.
#const p=5.
#const w=5.

player(1..g*p).
group(1..g).
week(1..w).

{ plays(P,W,G) : group(G) } = 1 :- player(P), week(W).
{ plays(P,W,G) : player(P) } = p :- week(W), group(G).

meets(P1,P2,W) :- plays(P1,W,G), plays(P2,W,G), P1 < P2.
:~ #count { W : meets(P1,P2,W) } > 1, player(P1), player(P2), P1 < P2. [1,P1]
#show plays/3.
```

Additionally, for declarative relaxation an example configuration can be found in
[`./examples/golf_config.lp`][golf_config].
The first two lines define the project operator `plays_3` with the signature `(plays,3)`
and project all `plays/3` atoms using said operator.
The next four lines define three destroy operators and specify which terms and their
correlated atoms are subject to destruction. Destroy operators only affect projected atoms.

- (random,10): destroy 10% of all projected `plays/3` atoms
- (random,20): destroy 20% of all projected `plays/3` atoms
- week_auto: automatically destroy a percentage of weeks and their corresponding projected `plays/3` atoms

The prioritize operator in the next lines is only relevant when using `--fix=heuristics` and specifies how fixed (not destroyed) atoms should be prioritized in their respective `#heuristic` statements.
The following lines define three configurations using the previously defined operators.
Finally, the `_strategy` atoms selects the strategy to be used, in this case `RouletteWheelStrategy`,
and adds the configurations to the portfolio. 

```
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

% _strategy(strategy_name, config_name).
_strategy("roulette", C) :- _config(C, _, _, _).
```

## Basics

As described in the [getting started] section, in the most basic case the LNS
can be started by only providing the corresponding ASP encodings. In this case the
default options are used.

=== "CLI"

    ```bash
    mod_lns ./examples/golf_demo.lp
    ```

=== "Python"

    ```python
    from mod_lns.lns import LNS

    lns = LNS(["./examples/golf_demo.lp"])
    lns.main()
    ```

We can configure the search by providing additional parameters or provide a new
`LNSOptions` object during initialization.

!!! note
    You can interrupt the framework at any time using `Ctrl+C`.

    The seed can only influence the search to a certain degree but not
    guarantee reproducibility, due to different timings and interrupts. For example, if
    an initial time limit is set, the initial solution can differ between seeds, depending
    on when/where exactly the solver is interrupted after the time limit is reached.

### Classic LNS
Classic LNS performs a static destruction and fixes the remaining atoms using assumptions.
We use the `lns` preset with some changes. A seed is set to make the search more predictable.
We also limit the initial solving to 2 seconds to start the LNS sooner and limit the search to 100 steps.

=== "CLI"

    ```bash
    mod_lns --preset=lns --seed=42 --init-time-limit=2 --max-steps=100 ./examples/golf_demo.lp
    ```

=== "Python"

    ```python
    from mod_lns.lns import LNS

    lns = LNS(
        ["./examples/golf_demo.lp"],
        {
            "preset": "lns",
            "seed": 42,
            "init_time_limit": 2,
            "max_steps": 100,
        }
    )
    lns.main()
    ```

When running the above search, we can observe the current state of the search printed every 50 steps
or when a better solution was found.
During the search the initial optimization value of 7 is reduced step by step by using the
classic LNS approach:

- Find the initial solution in 2s with cost 7
- Relax 40% of the atoms of the initial solution (randomly chosen)
- Find a new solution with no time limit using the remaining 60% of atoms as assumptions
  (since we wait until the search is finished the new solution is a local optimum and can
  never be worse than the previous solutions (worst case, the previous solution is found
  again))
- Check if the new solution should be used as the starting point for the next step:
    - Accept, if the new solution is different enough (accept_variability) from the previous
      solution (always accept by default)
- Check if the new solution is better than the best solution found so far:
    - If yes, store it as the new best solution
- Repeat until the step limit is reached

Try running the search multiple times to see how the results can vary.
Since optimality can not be proven, feel free to stop the search after the a solution with a
cost of 0 was found.

### LNPS (prioritized search)
Another approach is to use heuristics instead of assumptions. This allows for generally lower
destruction rates and the ability to prove optimality, with the downside of significantly lower
"iteration throughput". The use of heuristics also allows us to use automatic destruction.
Since the choice of the destruction rate has a big impact on performance, it is a big advantage
to dynamically choose the most optimal destruction rate.

=== "CLI"

    ```bash
    mod_lns --preset=lnps --seed=42 --init-time-limit=2 --lns-time-limit=2 ./examples/golf_demo.lp
    ```

=== "Python"

    ```python
    from mod_lns.lns import LNS
    
    lns = LNS(
        ["./examples/golf_demo.lp"],
        {
            "preset": "lnps",
            "seed": 42,
            "init_time_limit": 2,
            "lns_time_limit": 2,
        }
    )
    lns.main()
    ```

## Advanced

### Declarative Destruction, ALNS and ALNPS
All of the above approaches use fully random relaxation, i.e. atoms to be fixed are
randomly selected from all shown atoms. We can enable declarative relaxation to define
a set of atoms from which our fixed atoms are randomly chosen. This is done through an
additional config encoding, as shown above in the [encoding](#encoding) section.
This also enables the use of adaptive approaches ALNS and ALNPS.

To use declarative destruction with classic LNS or LNPS simply use the `--relaxation=declarative`
option and the `static` strategy, which always selects the config first defined,
in the config encoding.

Lets use ALNPS as an example and enable the debug output to see how configs are selected
and the weights updated:

=== "CLI"
    
    ```bash
    mod_lns --preset=alnps --seed=42 --init-time-limit=2 --lns-time-limit=2 --log-level=debug ./examples/golf_demo.lp ./examples/golf_config.lp
    ```

=== "Python"

    ```python
    from mod_lns.lns import LNS
    
    lns = LNS(
        ["./examples/golf_demo.lp", "./examples/golf_config.lp"],
        {
            "preset": "alnps",
            "seed": 42,
            "init_time_limit": 2,
            "lns_time_limit": 2,
            "log_level": 10,
        }
    )
    lns.main()
    ```

In the debug output you should be able to see how in each iteration the weights are updated and a config is selected:

```
DEBUG:  - Week_auto[project_operators={plays_3[(plays,3)]},destroy_operators={week_auto[auto]},prioritize_operators={1_true[1,true]}] weight: 23.328880746956624 -> 13.486218732893388
DEBUG:  - Selected LNPS configuration: Random20[project_operators={plays_3[(plays,3)]},destroy_operators={(random,20)[p(20)]},prioritize_operators={1_true[1,true]}]
```

### Modifying the Algorithm

One purpose of this framework is to allow users to easily modify and/or create new LNS
components. Lets try modifying the `LNS` class so that fixed atoms are printed
and we can observe the declarative relaxation.

To do so we create a new class called `NewLNS` by inheriting the
`LNS` and overwrite the `relax` method with our new functionality:

```python
from mod_lns.lns import LNS
from mod_lns.utils.conversions import symbol_to_str

class NewLNS(LNS):
    def relax(self, lns_object):
        r = super().relax(lns_object)
        for s in r:
            print(symbol_to_str(s))
        print("--")
        return r
lns = LNS(
    ["./examples/golf_demo.lp", "./examples/golf_declarative.lp"],
    {
        "preset": "lns",
        "seed": 42,
        "init_time_limit": 2,
        "lns_time_limit": 2,
        "relaxation": ("declarative",0),
        "max_steps": 3,
    }
)
lns.main()
```

When running the search we can see that at each step all `plays/3` atoms of
two (`int(5*(1-0.6))`) random weeks are fixed (`plays/3: plays(Player,Week,Group)`).

[getting started]: index.md
[demo]: examples/demo.md
[golf]: examples/golf.md
[golf_config]: examples/golf_config.md
[portfolio]: examples/portfolio.md