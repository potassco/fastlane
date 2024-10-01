.. _ref_guide:

Guide
============

In his section we will illustrate an example workflow using this framework step by step. All python code snippets shown here can
also be found in :file:`./examples/demo.py`.
The problem we will be looking at is the `Social golfer problem <https://en.wikipedia.org/wiki/Social_golfer_problem>`_ with 
3 players, 3 groups and 3 weeks. We choose a small instance, to keep the run-time as low as possible, while still being able to
observe the effects of different approaches.


.. _ref_g_enc:

Encoding
----------

The corresponding encoding is located in :file:`./examples/golf_demo.lp` and can be divided into three parts.
The first part represents the basic clingo encoding of the problem, seen below.

.. code-block::

    #const g=3.
    #const p=3.
    #const w=3.

    player(1..g*p).
    group(1..g).
    week(1..w).

    { plays(P,W,G) : group(G) } = 1 :- player(P), week(W).
    { plays(P,W,G) : player(P) } = p :- week(W), group(G).

    meets(P1,P2,W) :- plays(P1,W,G), plays(P2,W,G), P1 < P2.
    #show plays/3.

The second part is used to determine the cost of each solution, our optimization criterion.
In the first line we define our optimization criterion "min" with a priority of 1.
The second line then describes, that for each occurrence of the player pair (P1,P2) a penalty/cost of 1 should be inferred,
if the players of the given pair meet more than once.

.. code-block::

    _lns_priority("min",1).
    _lns_penalty("min",(P1,P2),1) :- #count { W : meets(P1,P2,W) } > 1, player(P1), player(P2), P1 < P2.

And the last part can be used for declarative relaxation, with the first line defining possible terms to be selected
during relaxation, in this case weeks "W". The second line then connects the terms "W" with corresponding atoms to be fixed
(complement of relaxed atoms during search), here all plays/3 atoms in the corresponding week W.

.. code-block::

    _lns_select(W) :- week(W).
    _lns_fix(plays(P,W,G),W) :- _lns_select(W), plays(P,W,G).

Basics
-----------------

.. currentmodule:: large_neighbourhood_search.lib.solvers.clingo_solver

As described in the :ref:`usage<ref_usage>` section, to work this framework requires a solver and strategy object.
Our :ref:`library<ref_lib>` provides several different solvers and strategies.
For our first search, lets use the default clingo solver with assumptions :class:`ClingoSolver`.

.. currentmodule:: large_neighbourhood_search.lib.strategies.classic_weighted_sum_rnd

As a strategy we use the basic LNS implementation in :class:`ClassicWeightedSumRnd`. This strategy uses weighted sum optimization
combined with a fully random relaxation.

Now we can run our first search by using the lines below:

.. code-block:: python

    from large_neighbourhood_search import LNS
    from large_neighbourhood_search.lib.solvers.clingo_solver import ClingoSolver
    from large_neighbourhood_search.lib.strategies.classic_weighted_sum_rnd import (
    ClassicWeightedSumRnd
    )

    lns = LNS(["examples/golf_demo.lp"], ClingoSolver(), ClassicWeightedSumRnd(), {"seed": 123})
    lns.main()

You should see 1149 LNS steps, during which the optimization value is reduced from initially 8 to 0. The iterations
are marked every 50 steps to be able to tell the current state of the search. We can see the amount of steps required to
improve from 2 to 0 are significant. As expected, as the search nears the optimum, here 0, the number of steps required to randomly find
a better solution become bigger and bigger.
Feel free to try around with different seeds to see how the random relaxation effects the search.

Lets rework our code above to make use of configurations as seen below.

.. code-block:: python

    def config1():
        solver = ClingoSolver()
        strategy = ClassicWeightedSumRnd()
        params: Dict[str, Any] = {
            "seed": 123,
        }
    return solver, strategy, params

    def main():
    solver, strategy, params = config1()
    lns = LNS(["examples/golf_demo.lp"], solver, strategy, params)
    lns.main()

    if __name__ == "__main__":
        main()

While doing our search, we used the default relax rate of 0.2 or 20% of all shown atoms, in this case plays/3. 
Lets try some other relax rates by adjusting the configuration.

.. code-block:: python

    def config1_1():
        solver = ClingoSolver()
        strategy = ClassicWeightedSumRnd()
        params: Dict[str, Any] = {
            "seed": 123,
            "relax_rate": 0.4,
        }
    return solver, strategy, params

This time we see, the best solution was not found in 1208 steps, after which the search was interrupted due to the
"stuck_after_no_improv" parameter. Try around with some other relax rates. You should notice that classic LNS is highly dependant
on its search parameters and luck.
These effects become only more apparent once you look at bigger instances.

An alternative approach is to "guide" the search by using constraints. In this approach the value of the previous best
solution is directly integrated into the solving process, by enforcing a better solution via constraints. While in the
classic approach the solutions are either "worse/same" or "better", in this approach the solution are either "unsatisfiable"
or "better". This usage of constraints leads to signiﬁcantly fewer steps but increases the solve time for each step. Lets try it out.

.. code-block:: python
    
    from large_neighbourhood_search.lib.strategies.hc_weighted_sum_rnd import HCWeightedSumRnd

    def config2():
        solver = ClingoSolver()
        strategy = HCWeightedSumRnd()
        params: Dict[str, Any] = {
            "seed": 123,
            "solve_time_limit": 10,
        }
    return solver, strategy, params

We can see we need only 32 steps to find the best solution. The increased solve time is on such small instances not visible.
Feel free to try the above configuration on the 5-5-5 golf instance to see the difference (CTRL + C to interrupt search). 
In the time takes the constrained approach to produce one new solution the classic approach produces 50 or more. Once again 
the correct usage of parameters significantly influences the search. The performance of the constraint approach is for
example strongly connected to the chosen "solve_time_limit" parameter, try 2s.

.. note::
    Constrained approach with a relax rate of 1 corresponds to branch-and-bound search.


Both of the above approaches use the default clingo solver with assumptions to fix non-relaxed atoms.
Another approach is to use heuristics instead of assumptions. While assumptions are fixed in stone, heuristics are comparable
recommendations to the solver. Lets try it out with the :class:`ClassicWeightedSumRnd` strategy.

.. code-block:: python

    from large_neighbourhood_search.lib.solvers.clingo_heu_solver import ClingoHeuSolver

    def config3():
        solver = ClingoHeuSolver()
        strategy = ClassicWeightedSumRnd()
        params: Dict[str, Any] = {
            "seed": 123,
            "stuck_after_no_improv": 300,
        }
    return solver, strategy, params

We see the search is significantly slower than when using assumptions. This is caused by introducing overhead without any real gain.
Since we do not optimize in each solve call the previous solution is always a valid new solution without needing to "break" any of
the suggestions. This is why heuristics should only be used in solve calls with optimization or when using strategies, where 
unsatisfiable results are possible when using assumptions, for example constrained approaches.

.. code-block:: python

    def config3_1():
        solver = ClingoHeuSolver()
        strategy = HCWeightedSumRnd()
        params: Dict[str, Any] = {
            "seed": 123,
            "solve_time_limit": 10,
        }
    return solver, strategy, params

We can see unsatisfiable solutions do not occur anymore, every step results in a better solution.
Once again feel free to try this configuration with bigger instances.

For clingo-dl encodings our library also provides corresponding clingo-dl solver. If multiple optimization criteria are present,
lexicographic strategies should be used.


Advanced
---------

While we have a strategy using declarative relaxation for lexicographic optimization we do not for weighted sum optimization (yet).
The purpose of this framework is to not only plug different building blocks together but also allow them to be easily modifiable and
expandable. Lets try implementing ClassicWeightedSumDecl. When looking at the existing :class:`ClassicWeightedSumRnd`, we really only
have to edit one part, the relax function. Since we work with assumptions and heuristics, the relax function return the atoms to be fixed.
Fortunately for us, the relax function used in the other declarative strategies can be found in the library. Lets use it to build our
new strategy.

.. code-block:: python

    from large_neighbourhood_search.lib.relaxation import relax_declarative

    class ClassicWeightedSumDecl(ClassicWeightedSumRnd):
        def relax(self, model, relax_parameters):
            return relax_declarative(model, relax_parameters)

Use our new strategy in a configuration to try it out.

.. code-block:: python

    def config4():
        solver = ClingoSolver()
        strategy = ClassicWeightedSumDecl()
        params: Dict[str, Any] = {
            "seed": 123,
        }
    return solver, strategy, params

As described in the lower part of the :ref:`encoding<ref_g_enc>` section above, we select a random number of weeks and fix all
corresponding plays/3 atoms.

Lets adjust our code so we can observe this.

.. code-block:: python

    from large_neighbourhood_search.lib.relaxation import relax_declarative
    from large_neighbourhood_search.lib.utils import symbol_to_str

    class ClassicWeightedSumDecl(ClassicWeightedSumRnd):
        def relax(self, model, relax_parameters):
            r = relax_declarative(model, relax_parameters)
            for s in r:
                print(symbol_to_str(s[0]))
            print("--")
            return r
    
    def config4_1():
        solver = ClingoSolver()
        strategy = ClassicWeightedSumDecl()
        params: Dict[str, Any] = {
            "seed": 123,
            "max_steps": 8,
        }
    return solver, strategy, params

We can see that at each step all plays/3 atoms of two (int(3*(1-0.2))) random weeks are fixed.

After this brief guide you should now be able to use different solvers and strategies and modify them to create your own.


