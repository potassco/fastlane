import clingo
from clingo.symbol import SymbolType, parse_term
from typing import Dict, Any
import re
from typing import List


def str_to_symbols(string: str) -> List[clingo.symbol.Symbol]:
    """
    Convert String to List of clingo.Symbol.

    :param string: String to be converted.
    :type string: str
    :return: List of symbols.
    :rtype:  List[clingo.symbol.Symbol]
    """
    terms = string.split()
    symbols = []
    for term in terms:
        symbols.append(parse_term(term))
    return symbols


def symbol_to_str(symbol: clingo.Symbol) -> str:
    """
    Convert clingo.Symbol to String.

    :param symbol: Symbol to be converted.
    :type symbol: clingo.Symbol
    :return: Symbol as string.
    :rtype: str
    """
    if symbol.type == SymbolType.Function:
        return (
            symbol.name
            + "("
            + ",".join([symbol_to_str(s) for s in symbol.arguments])
            + ")"
        )
    if symbol.type == SymbolType.Number:
        return str(symbol.number)
    if symbol.type == SymbolType.String:
        return '"' + symbol.string + '"'
    if symbol.type == SymbolType.Infimum:
        return "#inf"
    return "#sup"

def args_to_dict(args_str: str) -> Dict[str, Any]:
    arg_list = args_str.split()
    d = {}
    for arg in arg_list:
        k = re.match(r'\-[\-]?([\w\-]+)(=([\w\-]+))?', arg)
        if k.group(1) and k.group(3):
            d[k.group(1)] = k.group(3)
        elif k.group(1):
            d[k.group(1)] = True
    return d

