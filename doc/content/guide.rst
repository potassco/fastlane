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

The corresponding encoding is located in :file:`./examples/golf_demo.lp` and can be divided into two parts.
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
    :~ #count { W : meets(P1,P2,W) } > 1, player(P1), player(P2), P1 < P2. [1,P1]
    #show plays/3.

The second part can be used for declarative relaxation, with the first line defining possible terms to be selected
during relaxation, in this case weeks "W". The second line then connects the terms "W" with corresponding atoms to be fixed
(complement of relaxed atoms during search), here all plays/3 atoms in the corresponding week W.

.. code-block::

    _lns_select(W) :- week(W).
    _lns_fix(plays(P,W,G),W) :- _lns_select(W), plays(P,W,G).

Basics
-----------------

.. currentmodule:: mod_lns.lns_config

As descibed in the :ref:`usage<ref_usage>` section in the most basic case the LNS can be started by only providing
the corresponding ASP encoding. In this case the default configuration described by :class:`LNSConfig` is used.

.. code-block:: python

    from mod_lns.lns import LNS

    lns = LNS(["examples/golf_demo.lp"])
    lns.main()

We can configure the search my passing a new :class:`LNSConfig` object. During initialization of the the :class:`LNSConfig` the
following arguments can be provided:

- lns_options: A dictionary of lns specific parameters, such as relax_rate or step limit (see :ref:`lns implementation<ref_lns>` section for more details)
- clingo_options: A list of clingo options directly passed to the solver during initialization.
- solver: The solver used for the search. Depending on the configuration class the solver can be modified through different lns_options. The default configuration allows the switch between using assumptions and heuristics when repairing, using the "heuristics" option.
- strategy: The strategy used for the search. Depending on the configuration class the strategy can be modified through different lns_options. The default configuration allows the switch between classic and constrained LNS using the "constrained" option and the choice of random or declarative relaxation using the "declarative" option.

For now lets just modify the lns_options as seen below (0.2 is also the default relax rate):

.. code-block:: python

    from mod_lns.lns_config import LNSConfig

    cl_config = LNSConfig(
        lns_options={
            "seed": 123,
            "relax_rate": 0.2,
        })
    lns = LNS(["examples/golf_demo.lp"], cl_config)
    lns.main()

You should see 2000 LNS steps, during which the optimization value is reduced relatively quickly from initially 5 to 2.
The iterations are marked every 50 steps to be able to tell the current state of the search. We can see the that,
while first improvements come quickly the number of steps required to find the best solutions (cost 0) can not be found
in the first 2000 steps (found at step 2518).
Feel free to play around with different seeds and or relax rates to see how that effects the search.

An alternative approach is to "guide" the search by enforcing a strictly better solution by the solver. While in the
classic approach the solutions are either "worse/equal" or "better", in this approach the solutions are either "unsatisfiable"
or "better". This leads to signiﬁcantly fewer steps but increases the solve time for each step. Lets try it out.

.. code-block:: python

    hc_config = LNSConfig(
        lns_options={
            "constrained": True,
            "seed": 123,
            "relax_rate": 0.2,
            "solve_time_limit": 10
        })

We can see we need only 34 steps to find the best solution. The increased solve time is on such small instances not visible.
Feel free to try the above configuration on the 5-5-5 golf instance to see the difference (CTRL + C to interrupt search).
In the time takes the constrained approach to produce one new solution the classic approach produces 50 or more. Once again
the correct usage of parameters significantly influences the search. The performance of the constraint approach is for
example strongly connected to the chosen "solve_time_limit" parameter, try 2s.

.. note::
    Constrained approach with a relax rate of 1 corresponds to branch-and-bound search.

All of the above approaches use fully random relaxation, i.e. atoms to be fixed are randomly selected from all shown atoms.
We can enable declarative relaxation to define a set of atoms from which our fixed atoms are randomly chosen.
The lower part of the :ref:`encoding<ref_g_enc>` section above, describes how the encoding has to be modified to support
declarative relaxation. In this case a certain number of weeks are randomly selected and all matches in those weeks fixed.
The declarative relaxation can be enabled as follows:

.. code-block:: python

    cl_decl_config = LNSConfig(
            lns_options={
                "declarative": True,
                "seed": 123
            })


Advanced
---------

The purpose of this framework is to not only plug different building blocks together and enable certain options
but also allow them to be easily modifiable. Lets try modifying the default configuration, by adding a new option, which,
when enabled, modifies the provided strategy so that the fixed atoms are printed and we can observe the declarative relaxation.

.. note::
    Example solver and strategy modifications are located inside the :code:`mod_lns.lib.mods` submodule.

To do so we first nees to understand how the :class:`LNSConfig` class works. Inside the :meth:`__init__` method the different
parameters are registered and, depending on the options, different methods to make changes to strategy and/or solver are called.
Such methods expand upon or overwrite certain parts of a given class by inheriting said class while creating a new one.

Below is the implementation of our new configuration class:

.. code-block:: python

    from mod_lns.utils.conversions import symbol_to_str

    class NewLNSConfig(LNSConfig):

        def __init__(self, lns_options = {}, clingo_options = []):
            # add new default value
            default_options = {
                "new_opt": False,
            }
            self.lns_options = {**default_options, **lns_options}

            # keep functionality of LNSConfig
            super().__init__(self.lns_options, clingo_options)

            # add new functionality
            if self.lns_options["new_opt"] == True:
                self._enable_new_opt()

        def _enable_new_opt(self):
            # get current strategy to modify

            def relax(
                self,
                model,
                relax_parameters,
            ):
                # keep functionality
                r = super(EnNewOpt, self).relax(model,relax_parameters)
                # new functionality
                for s in r:
                    print(symbol_to_str(s[0]))
                print("--")
                return r
            # set new strategy
            base = type(self.strategy)
            EnNewOpt = type("EnNewOpt", (base,), {"relax": relax})
            self.strategy = EnNewOpt()

While this approach keeps all features of the default :class:`LNSConfig`, another approach would be to simply
overwrite :meth:`self.solver` with a completely new strategy implementing the StrategyInterface.

The new configuration class can then be used exactly the same as :class:`LNSConfig` before:

.. code-block:: python

    cl_decl_custom_config = NewLNSConfig(
        lns_options={
            "new_opt": True,
            "declarative": True,
            "seed": 123,
            "max_steps": 5
        })

When running the search we can see that at each step all plays/3 atoms of two (int(3*(1-0.2))) random weeks are fixed.

After this brief guide you should now have a basic understanding of how to run the LNS framework and how to modify the performed
search through parameters and perform more in-depth modifications to the solver and/or strategy through the configuration class.
