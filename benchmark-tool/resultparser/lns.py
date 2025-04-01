'''
Based on clasp.py resultparser by Roland Kaminski.
'''

import os
import re
import sys
import codecs

lns_re = {
    "steps"       : ("int", re.compile(r"^(c )?Overall steps[ ]*:[ ]*(?P<val>[0-9]+)\+?[ ]*$")),
    "lns_time"    : ("float", re.compile(r"^(c )?Overall time[ ]*:[ ]*(?P<val>[0-9]+(\.[0-9]+)?)s")),
    "cost"        : ("string", re.compile(r"^(c )?Cost[ ]*:[ ]*(?P<val>(-?[0-9]+)( -?[0-9]+)*)[ ]*$")),
    "interrupted" : ("string", re.compile(r"(c )?(?P<val>INTERRUPTED):")),
    "error"       : ("string", re.compile(r"^\*\*\* ERROR: (?P<val>.*)$")),
    "time"        : ("float", re.compile(r"^(Real time \(s\):|\[runlim\] real:)\s*(?P<val>[0-9]+(\.[0-9]+)?)")),
    
}

def lns(root, runspec, instance):
    """
    Extracts some clasp statistics.
    """

    timeout = runspec.project.job.timeout
    res     = { "time": ("float", timeout) }
    for f in ["runsolver.solver", "runsolver.watcher"]:
        for line in codecs.open(os.path.join(root, f), errors='ignore', encoding='utf-8'):
            for val, reg in lns_re.items():
                m = reg[1].match(line)
                if m: res[val] = (reg[0], float(m.group("val")) if reg[0] == "float" else m.group("val"))
    if "memerror" in res:
        res["error"]  = ("string", "std::bad_alloc")
        del res["memerror"]
    result   = []
    error    = "error" in res and res["error"][1] != "std::bad_alloc"
    memout   = "error" in res and res["error"][1] == "std::bad_alloc"
    
    timedout = memout or error or res["time"][1] >= timeout or "interrupted" in res;
    if timedout: res["time"] = ("float", timeout)
    if error: sys.stderr.write("*** ERROR: Run {0} failed with unrecognized status or error!\n".format(root))
    result.append(("error", "float", int(error)))
    result.append(("timeout", "float", int(timedout)))
    result.append(("memout", "float", int(memout)))

    #if "optimum" in res and not " " in res["optimum"][1]:
    #    result.append(("optimum", "float", float(res["optimum"][1])))
    #    del res["optimum"]
    if "interrupted" in res: del res["interrupted"]
    if "error" in res: del res["error"]
    for key, val in res.items(): result.append((key, val[0], val[1]))

    return result
