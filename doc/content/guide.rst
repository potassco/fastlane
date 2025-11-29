.. _ref_guide:

Guide
============

This section will illustrate how to use this framework by giving some small examples.
All python code snippets shown here can also be found in :file:`./examples/demo.py`.
The problem we will be looking at is the
`Social golfer problem <https://en.wikipedia.org/wiki/Social_golfer_problem>`_ with
5 players, 5 groups and 5 weeks. We choose a small instance, to keep the run-time as
low as possible, while still being able to observe the effects of different approaches.


.. _ref_g_enc:

Encoding
----------

The corresponding encoding is located in :file:`./examples/golf_demo.lp` and can be
divided into two parts. The first part represents the basic clingo encoding of the
problem, seen below.

.. code-block::

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

The second part can be used for declarative relaxation, with the first line defining
possible terms to be selected during relaxation, in this case weeks "W". The second
line then connects the terms "W" with corresponding atoms to be fixed (complement of
relaxed atoms during search), here all plays/3 atoms in the corresponding week W.

.. code-block::

    _lns_select(W) :- week(W).
    _lns_fix(plays(P,W,G),W) :- _lns_select(W), plays(P,W,G).

Basics
-----------------

.. currentmodule:: mod_lns.lib.strategies.default_strategy

As descibed in the :ref:`usage<ref_usage>` section in the most basic case the LNS
can be started by only providing the corresponding ASP encodings. In this case the
:class:`DefaultStrategy` with its default configuration is used.

.. code-block:: python

    from mod_lns.lns import LNS

    lns = LNS(["examples/golf_demo.lp"])
    lns.main()

We can configure the search by creating a new strategy object and adjusting the parameters
of its config attribute, either assigning new values to the existing :class:`LNSConfig`
object or creating a new object from scratch. Alternatively, commandline options can also
be passed as a dictionary during initialization of the `LNS` object.

.. note::
    You can interrupt the framework at any time using `Ctrl+C`. Feel free to interrupt
    the search once the a solution with cost 0 was found. Since the :class:`DefaultStrategy`
    uses assumptions and can therefore not prove optimality, the search will continue
    until the step or time limit is reached, even if an optimal solution was already found.

    The seed can only influence the search to a certain degree but not
    guarantee reproducibility, due to different timings and interrupts. For example, if
    an initial time limit is set, the initial solution can differ between seeds, depending
    on when/where exactly the solver is interrupted after the time limit is reached.

Classic LNS with random relaxation
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
For now lets create a new strategy object `cl_strategy` and assign a new :class:`LNSConfig`
object to its config attribute. We will set a seed for the random number generator to
make the search more predictable, a relax rate of 40%, a time limit of 2 seconds for
the initial solution and a step limit of 500.

.. code-block:: python

    from mod_lns.lib.strategies.default_strategy import DefaultStrategy, LNSConfig

    cl_strategy = DefaultStrategy()
    cl_strategy.config = LNSConfig(
        seed=123, relax_rate=40, init_time_limit=2, max_steps=500
    )
    lns = LNS(["examples/golf_demo.lp"], cl_strategy)
    lns.main()

You should see 500 LNS steps, with the current state of the search printed every 50 steps,
during which the initial optimization value of 7 is reduced step by step by using the
default classic LNS approach:

- Find the initial solution in 2s with cost 7
- Relax 40% of the atoms of the initial solution (randomly chosen)
- Find a new solution with no time limit using the remaining 60% of atoms as assumptions
  (since we wait until the search is finished the new solution is a local optimum and can
  never be worse than the previous solutions (worst case, the previous solution is found
  again))
- Check if the new solution should be used as the starting point for the next step:

  - Accept, if the new solution is different enough (accept_variability) from the previous
    solution (always accept when using default configuration)

- Check if the new solution is better than the best solution found so far:

  - If yes, store it as the new best solution

- Repeat until the step limit is reached

Try running the search multiple times to see how the results can vary.

Constrained LNS with random relaxation
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
An alternative approach is to "guide" the search by enforcing a strictly better solution
during solving. This significantly increases the performance since we avoid optimizing to
the level of our current solution. But this also results in solutions with equal cost
being unsatisfiable, which inturn can not be accepted and used as a starting point for
the next iteration, which can cause the search to get stuck if the relax rate is too low.

.. code-block:: python

    con_strategy = DefaultStrategy()
    con_strategy.config = LNSConfig(
        seed=123, relax_rate=40, init_time_limit=2, max_steps=500, constrained=True
    )

.. note::
    Constrained approach with a relax rate of 100 corresponds to branch-and-bound search.

LNS with declarative relaxation
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
All of the above approaches use fully random relaxation, i.e. atoms to be fixed are
randomly selected from all shown atoms. We can enable declarative relaxation to define
a set of atoms from which our fixed atoms are randomly chosen. The lower part of the
:ref:`encoding<ref_g_enc>` section above, describes how the encoding has to be modified
to support declarative relaxation. In this case a certain number of weeks are randomly
selected and all matches in those weeks fixed. The declarative relaxation can be enabled
using the `declarative` parameter of the :class:`LNSConfig`.

.. code-block:: python

    cl_decl_strategy = DefaultStrategy()
    cl_decl_strategy.config = LNSConfig(
        seed=123, relax_rate=40, init_time_limit=2, max_steps=500, declarative=True
    )

Advanced
---------

One purpose of this framework is to allow users to easily modify and/or create new LNS
components. Lets try modifying the default strategy so that fixed atoms are printed
and we can observe the declarative relaxation.

To do so we create a new strategy called `NewStrategy` by inheriting the
:class:`DefaultStrategy` and overwrite the :meth:`relax` method with our new functionality:

.. code-block:: python

    from mod_lns.utils.conversions import symbol_to_str

    class NewStrategy(DefaultStrategy):
        def relax(self, lns_object):
            r = super().relax(lns_object)
            for s in r:
                print(symbol_to_str(s))
            print("--")
            return r

.. currentmodule:: mod_lns.interfaces.strategy

Similarly we could also create a completely new strategy by implementing the
:class:`StrategyInterface`.

The new strategy class can then be used exactly the same as :class:`DefaultStrategy` before:

.. code-block:: python

    decl_custom = NewStrategy()
    decl_custom.config = LNSConfig(
        seed=123, relax_rate=40, init_time_limit=2, max_steps=5, declarative=True
    )

When running the search we can see that at each step all plays/3 atoms of
three (int(5*(1-0.4))) random weeks are fixed (plays/3: plays(Player,Week,Group)).

Heulingo
---------------------
Another strategy provided by this framework is heulingo, which uses heuristics and
a prioritized search to negate the disadvantages of the above approaches.
Since heulingo was initially developed as a clingo application by Irumi Sugimori,
it provides many options for customization and fine-tuning. Heulingo also
requires additional configuration encodings to select which and how atoms are destroyed
and prioritized. For more information on heulingo and its configuration look
:ref:`here<ref_strat>`.

By default heulingo uses the number of conflicts and restarts to decide when to stop
individual solve calls. For this small example we will set the solve time limits
`init_time_limit` and `lns_time_limit` to 2, to be able to observe the search progress overall
multiple iterations.

.. code-block:: python

    from mod_lns.lib.strategies.heulingo import Heulingo, HeulingoConfig

    heuristic_strategy = Heulingo()
    heuristic_strategy.config = HeulingoConfig(
        seed=123,
        init_time_limit=2,
        lns_time_limit=2,
        max_steps=500,
        clingo_args="-c n=40",
    )
    lns = LNS(["examples/golf_demo.lp", "examples/golf_lnps.lp"], heuristic_strategy)
    lns.main()

Since heulingo uses heuristics rather than assumptions, it can also prove optimality
and stop the search when it does.
