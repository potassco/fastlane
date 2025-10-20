"""
Result parser for the mod_lns framework.
"""

import codecs
import os
import re
import sys

lns_re = {
    "steps": (
        "int",
        re.compile(r"^(c )?Overall steps[ ]*:[ ]*(?P<val>[0-9]+)\+?[ ]*$"),
    ),
    "lns_time": (
        "float",
        re.compile(r"^(c )?Overall time[ ]*:[ ]*(?P<val>[0-9]+(\.[0-9]+)?)s"),
    ),
    "optimum": (
        "string",
        re.compile(r"^(c )?Optimization[ ]*:[ ]*(?P<val>(-?[0-9]+)( -?[0-9]+)*)[ ]*$"),
    ),
    "interrupted": ("string", re.compile(r"(c )?(?P<val>INTERRUPTED)")),
    "error": ("string", re.compile(r"^\*\*\* ERROR: (?P<val>.*)$")),
    "time": (
        "float",
        re.compile(
            r"^(Real time \(s\):|\[runlim\] real:)\s*(?P<val>[0-9]+(\.[0-9]+)?)"
        ),
    ),
    "mem": (
        "float",
        re.compile(r"^\[runlim\] space:[\t]*(?P<val>[0-9]+(\.[0-9]+)?) MB"),
    ),
    "rstatus": ("string", re.compile(r"^\[runlim\] status:\s*(?P<val>.*)$")),
    "status": (
        "string",
        re.compile(
            r"^(s )?(?P<val>SATISFIABLE|UNSATISFIABLE|UNKNOWN|OPTIMUM FOUND)[ ]*$"
        ),
    ),
}


def parse(root, runspec, instance) -> dict:
    """
    Extracts some clasp statistics.
    """

    timeout = runspec.project.job.timeout
    res = {"time": ("float", timeout)}
    for f in ["runsolver.solver", "runsolver.watcher"]:
        with codecs.open(
            os.path.join(root, f), errors="ignore", encoding="utf-8"
        ) as file:
            for line in file:
                for val, reg in lns_re.items():
                    m = reg[1].match(line)
                    if m:
                        res[val] = (
                            reg[0],
                            float(m.group("val"))
                            if reg[0] == "float"
                            else m.group("val"),
                        )

    if "rstatus" in res and res["rstatus"][1] == "out of memory":
        res["error"] = ("string", "std::bad_alloc")
        res["status"] = ("string", "UNKNOWN")
    result = {}
    error = "status" not in res or (
        "error" in res and res["error"][1] != "std::bad_alloc"
    )
    memout = "error" in res and res["error"][1] == "std::bad_alloc"

    timedout = memout or error or res["time"][1] >= timeout or "interrupted" in res
    if timedout:
        res["time"] = ("float", timeout)
    if error:
        sys.stderr.write(
            "*** ERROR: Run {0} failed with unrecognized status or error!\n".format(
                root
            )
        )
    result["error"] = ("float", int(error))
    result["timeout"] = ("float", int(timedout))
    result["memout"] = ("float", int(memout))

    if "optimum" in res and not " " in res["optimum"][1]:
        result["optimum"] = ("float", float(res["optimum"][1]))
        del res["optimum"]
    if "interrupted" in res:
        del res["interrupted"]
    if "error" in res:
        del res["error"]
    for key, val in res.items():
        result[key] = (val[0], val[1])

    return result
