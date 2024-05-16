.. _ref_lns:

LNS
====

.. currentmodule:: large_neighbourhood_search.__init__

.. note::

    The default LNS object contains the following parameter values.
    These can be changed by using the :meth:`get_params` method.

    .. code-block:: python

        self.param_values: Dict[str, Any] = {
            "files": files,
            "seed": None,
            "relax_rates": [0.2, 0.4, 0.6],
            "bound": 2000,
            "switch_rr_after_no_improv": 3,
        }

.. warning::

    For a correct program execution, during initialization, the :code:`clingo_args` parameter should not 
    contain the :code:`rand_freq` or :code:`seed` options. These values can be adjusted either using :meth:`get_params`
    after initialization or during :ref:`setup<ref_setup>` of the solver.

.. autoclass:: LNS
    :members:
