import re
import os
from sexpdata import loads, Symbol
from hyperon import *
from prompts import *
from util_functions import *
from mork_handler import MorkHandler

# TODO: fix keyword collision, e.g. `expr_format_check("(: Empty (-> Concept Type))")` will fail

expr_format_check_fn = """
(= (expr-format-check $expr)
   (unify $expr (: $x $y) True False))
""".strip()

sent_expr_format_check_fn = """
(= (sent-expr-format-check $expr)
   (unify $expr (: $prf (WithTV $main (STV $s $c))) True False))
""".strip()

scopeless_conjunction_check_fn = """
(= (scopeless_conjunction_check $expr)
   (unify $expr (: $prf (WithTV (And $x $y) (STV $s $c))) True False))
""".strip()

metta = MeTTa()
metta.run(expr_format_check_fn)
metta.run(sent_expr_format_check_fn)
metta.run(scopeless_conjunction_check_fn)

def expr_format_check(expr):
    try:
        rtn = metta.run(f"!(expr-format-check {expr})")[0][0]
        if isinstance(rtn, GroundedAtom) and rtn.get_object().value == True:
            return (1, None)
    except Exception as e:
        print(f"Got an exception in expr_format_check for '{expr}': {e}")
        return (0, e)
    return (0, None)

def type_def_check(expr):
    match = re.search(r'\(: .+ \(-> (.*)\)\)', expr)
    if not match:
        return 0
    return 1

def sent_format_check(expr):
    try:
        rtn = metta.run(f"!(sent-expr-format-check {expr})")[0][0]
        if isinstance(rtn, GroundedAtom) and rtn.get_object().value == True:
            return (1, None)
    except Exception as e:
        print(f"Got an exception in sent_format_check for '{expr}': {e}")
        return (0, e)
    return (0, None)

def query_format_check(expr):
    match = re.search(r'\(: \$.+ \(.+\)\)', expr)
    if not match:
        return 0
    return 1

def metta_type_check(type_defs, expr):
    temp_metta = MeTTa()
    try:
        for type_def in type_defs:
            type_def_atom = temp_metta.parse_all(type_def)[0]
            temp_metta.space().add_atom(type_def_atom)

        # try to type-check in MeTTa based on the given type definitions and see if we'll get an error
        rtn1 = temp_metta.run(f"!{expr}")[0][0]
        rtn2 = temp_metta.run(f"!(car-atom {rtn1})")[0][0]
        if rtn2.get_name() == "Error":
            return (0, None)
        return (1, None)
    except Exception as e:
        print(f"Got an exception in expr_type_check for '{expr}': {e}")
        return (0, e)

def unused_preds_check(type_defs, exprs):
    preds_used = list(set(sum([re.findall(r'\((.+?) ', expr) for expr in exprs], [])))
    preds_defined = list(set([re.search(r'\(: (.+?) \(-> ', type_def).group(1) for type_def in type_defs]))
    filtered_preds_used = [item for item in preds_used if item not in (built_in_preds + special_symbols) and not item.startswith('$')]
    filtered_preds_defined = [item for item in preds_defined if item not in (built_in_preds + special_symbols)]
    preds_defined_not_used = [item for item in filtered_preds_defined if item not in filtered_preds_used]
    if preds_defined_not_used:
        return (0, preds_defined_not_used)
    else:
        return (1, [])

def undefined_preds_check(type_defs, exprs):
    preds_used = list(set(sum([re.findall(r'\((.+?) ', expr) for expr in exprs], [])))
    preds_defined = list(set([re.search(r'\(: (.+?) \(-> ', type_def).group(1) for type_def in type_defs]))
    filtered_preds_used = [item for item in preds_used if item not in (built_in_preds + special_symbols) and not item.startswith('$')]
    filtered_preds_defined = [item for item in preds_defined if item not in (built_in_preds + special_symbols)]
    preds_used_not_defined = [item for item in filtered_preds_used if item not in filtered_preds_defined]
    if preds_used_not_defined:
        return (0, preds_used_not_defined)
    else:
        return (1, [])

def scopeless_conjunction_check(expr):
    try:
        rtn = metta.run(f"!(scopeless_conjunction_check {expr})")[0][0]
        if isinstance(rtn, GroundedAtom) and rtn.get_object().value == False:
            return (1, None)
    except Exception as e:
        print(f"Got an exception in scopeless_conjunction_check for '{expr}': {e}")
        return (0, e)
    return (0, None)

def connectivity_check(declares):
    def extract_elements(sexp):
        """
        Extract elements that are not predicates, also ignore:
        - strings
        - numbers
        - proof_names
        - variables
        """
        if sexp[0] == Symbol(":"):
            # ignore proof_names
            return extract_elements(sexp[1:])

        ele_lst = []
        # ignore predicates
        for ele in sexp[1:]:
            if isinstance(ele, list):
                ele_lst += extract_elements(ele)
            # ignore strings, numbers, etc that are not parsed as Symbols
            elif isinstance(ele, Symbol):
                # ignoring variables, assuming expressions should not be connected via a variable with the same name globally
                if not str(ele).startswith("$"):
                    ele_lst.append(str(ele))
        return ele_lst

    declare_sexprs = [loads(declare) for declare in declares]
    declare_ele_lst = [extract_elements(sexpr) for sexpr in declare_sexprs]

    # there could be exprs has no elements extracted, like an Implication rule with only predicates and variables, they can be excluded from connectivity check
    filtered_declare_ele_lst = list(filter(lambda x: len(x) > 0, declare_ele_lst))
    # print(f"Extracted elements (filtered): {filtered_declare_ele_lst}")

    if len(filtered_declare_ele_lst) <= 1:
        return True

    connected = {0}
    while True:
        new_connections = set()
        for i in connected:
            for j, other_list in enumerate(filtered_declare_ele_lst):
                if j not in connected and set(filtered_declare_ele_lst[i]) & set(other_list):
                    new_connections.add(j)
        if not new_connections:
            break
        connected.update(new_connections)

    return 1 if len(connected) == len(filtered_declare_ele_lst) else 0

def chaining(type_defs, declares, query, handler=None, timeout=300.0, log=False):
    print(f"Chaining (handler = {handler}):\n```\ntype_defs = {type_defs}\ndeclares = {declares}\nquery = {query}\n```")
    curdir = os.getcwd()
    os.chdir(os.environ.get("MM2CHAINER_DIR"))
    if handler == None:
        handler = MorkHandler()
        try:
            for x in type_defs + declares:
                x = temp_postprocess(x)
                print(f"... adding to space: {x}")
                handler.add_atom(x, log=log)
        except Exception as e:
            print(f"\n!!! EXCEPTION: {e}\n")
            os.chdir(curdir)
            return None
    query = temp_postprocess(query)
    print(f"... chaining for: {query}")
    try:
        result = handler.query(query, timeout=timeout, log=log)
    except Exception as e:
        print(f"\n!!! EXCEPTION: {e}\n")
        os.chdir(curdir)
        return None
    print(f"Chaining result: {result}\n")
    os.chdir(curdir)
    return result
