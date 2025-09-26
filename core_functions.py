from prompts import *
from util_functions import *
from checker_functions import *

# mode = "parsing" | "querying"
def nl2pln(sentence, mode="parsing", max_back_forth_per_sentence=10):
    # reset chat_history for each input sentence
    chat_history = [{
        "role": "system",
        "content": base_instructions + "\n\n" + nl2pln_instructions
    }]

    openai_outputs = to_openai(create_nl2pln_prompt(mode=mode, text=sentence), history=chat_history)

    while True:
        print(f"[history length = {len(chat_history)}]")
        type_defs, declares, queries, improvement_advice = openai_outputs["type_defs"], openai_outputs["declares"], openai_outputs["queries"], openai_outputs["improvement_advice"]

        if (len(chat_history)-1)/2 > max_back_forth_per_sentence:
            print(f"Maximum back-and-forth's ({max_back_forth_per_sentence} times) with the LLM has reached!")
            return None

        print(f"Current outputs:\n```\ntype_defs = {type_defs}\ndeclares = {declares}\nqueries = {queries}\nimprovement_advice = {improvement_advice}\n```\n")

        type_def_check_pass = True
        for type_def in type_defs:
            expr_check_result, expr_check_exception = expr_format_check(type_def)
            e = "" if expr_check_exception == None else f"{expr_check_exception}".strip()
            if not (expr_check_result and type_def_check(type_def)):
                print(f"... retrying type_def_check for type_def: {type_def}\n")
                openai_outputs = to_openai(create_nl2pln_prompt(mode=mode, correction=f"One of your type_defs ('{type_def}') doesn't pass the format check" + (f" with an exception '{e}', " if e else ", ") + "please make the correction and regenerate all the output fields."), history=chat_history)
                type_def_check_pass = False
                break
        if not type_def_check_pass:
            continue

        declare_check_pass = True
        for declare in declares:
            expr_check_result, expr_check_exception = expr_format_check(declare)
            if expr_check_exception == None:
                sent_check_result, sent_check_exception = sent_format_check(declare)
                if sent_check_exception == None:
                    e = ""
                else:
                    e = f"{sent_check_exception}".strip()
            else:
                e = f"{expr_check_exception}".strip()
            if not (expr_check_result and sent_check_result):
                print(f"... retrying sent_format_check for declare: {declare}\n")
                openai_outputs = to_openai(create_nl2pln_prompt(mode=mode, correction=f"One of your declares ('{declare}') doesn't pass the format check" + (f" with an exception '{e}', " if e else ", ") + "please make the correction and regenerate all the output fields."), history=chat_history)
                declare_check_pass = False
                break
        if not declare_check_pass:
            continue

        query_check_pass = True
        for query in queries:
            expr_check_result, expr_check_exception = expr_format_check(query)
            e = "" if expr_check_exception == None else f"{expr_check_exception}".strip()
            if not expr_check_result:
                print(f"... retrying query_format_check for query: {query}\n")
                openai_outputs = to_openai(create_nl2pln_prompt(mode=mode, correction=f"One of your queries ('{query}') doesn't pass the format check" + (f" with an exception '{e}', " if e else ", ") + "please make the correction and regenerate all the output fields."), history=chat_history)
                query_check_pass = False
                break
            if not query_format_check(query):
                print(f"... retrying query_format_check for query: {query}\n")
                openai_outputs = to_openai(create_nl2pln_prompt(mode=mode, correction=f"You need to turn the proof name of your query '{query}' into a variable to make it a valid query. Please make the improvement and regenerate all the output fields."), history=chat_history)
                query_check_pass = False
                break
        if not query_check_pass:
            continue

        metta_type_check_pass = True
        for expr in declares + queries:
            check_result, check_exception = metta_type_check(type_defs + built_in_type_defs, expr)
            e = "" if check_exception == None else f"{check_exception}".strip()
            if not check_result:
                print(f"... retrying metta_type_check for: {expr} | {type_defs}\n")
                openai_outputs = to_openai(create_nl2pln_prompt(mode=mode, correction=f"One of your PLN expressions ('{expr}') doesn't pass type checking in the system based on your type_defs ({type_defs})" + (f" with an exception '{e}', " if e else ", ") + "please make the correction and regenerate all the output fields."), history=chat_history)
                metta_type_check_pass = False
                break
        if not metta_type_check_pass:
            continue

        rtn = unused_preds_check(type_defs, declares + queries)
        if not rtn[0]:
            print(f"... retrying for unused_preds: {rtn[1]}\n")
            openai_outputs = to_openai(create_nl2pln_prompt(mode=mode, correction=f"You have defined one or more predicates but left unused:\n{rtn[1]}\n\nPlease make the correction and regenerate all the output fields."), history=chat_history)
            continue

        rtn = undefined_preds_check(type_defs, declares + queries)
        if not rtn[0]:
            print(f"... retrying for undefined_preds: {rtn[1]}\n")
            openai_outputs = to_openai(create_nl2pln_prompt(mode=mode, correction=f"You have used one or more predicates that are not defined:\n{rtn[1]}\n\nPlease make the correction and regenerate all the output fields."), history=chat_history)
            continue

        scopeless_conjunction_check_pass = True
        for declare in declares:
            check_result, check_exception = scopeless_conjunction_check(declare)
            e = "" if check_exception == None else f"{check_exception}".strip()
            if not check_result:
                print(f"... retrying scopeless_conjunction_check for: {declare}\n")
                openai_outputs = to_openai(create_nl2pln_prompt(mode=mode, correction=f"One of your declares ('{declare}') appears to contain a lot of sub-expressions aggregated by conjunctions without a top-level scope, it's more preferable to just break them down into separated expressions to reduce complexity" + (f", with an exception '{e}'. " if e else ". ") + "Please make the improvement and regenerate all the output fields."), history=chat_history)
                scopeless_conjunction_check_pass = False
                break
        if not scopeless_conjunction_check_pass:
            continue

        if not connectivity_check(declares):
            print(f"... retrying for connectivity_check for: {declares}\n")
            openai_outputs = to_openai(create_nl2pln_prompt(mode=mode, correction=f"Some of your 'declares' are disconnected from the rest. Please make the correction and regenerate all the output fields."), history=chat_history)
            continue

        print(f"PASSED FORMAT CHECK!!\n")
        break

    return (type_defs, declares, queries, improvement_advice)

def qa(all_type_defs, all_declares, query, max_back_forth_per_question=1):
    chat_history = [{
        "role": "system",
        "content": base_instructions + "\n\n" + add_missing_exprs_instructions
    }]

    all_r_type_defs = []
    all_r_instances = []
    all_r_rules = []
    all_r_improvement_advice = []

    while True:
        all_type_defs = list(set(all_type_defs + all_r_type_defs))
        all_declares = list(set(all_declares + all_r_instances + all_r_rules))

        chaining_result = chaining(all_type_defs, all_declares, query)

        if chaining_result:
            return (chaining_result, all_r_type_defs, all_r_instances, all_r_rules, all_r_improvement_advice)
        elif (len(chat_history)-1)/2 >= max_back_forth_per_question:
            # TODO: currently it may fail due to insufficient chaining depth, but increasing the depth can be impractically slow
            print(f"Failed to answer '{query}', skipping for now...")
            # for later debugging
            print_test_case([flatten_ands_ors(x) for x in all_type_defs + all_declares], flatten_ands_ors(query))
            break
        else:
            # TODO: have a different prompt if it's making a 2+ attempt?

            print(f"... retrying qa for: {query}\n[history length = {len(chat_history)}]")
            openai_outputs = to_openai(create_missing_rule_prompt(all_declares, query), history=chat_history, output_format=AddPLNExprs)

            # TODO: add format checks for the newly generated type_defs & declares?
            r_type_defs, r_instances, r_rules, r_improvement_advice = openai_outputs["type_defs"], openai_outputs["instances"], openai_outputs["rules"], openai_outputs["improvement_advice"]
            print(f"Newly propose:\n```\nr_type_defs = {r_type_defs}\nr_instances = {r_instances}\nr_rules = {r_rules}\nr_improvement_advice = {r_improvement_advice}\n```\n")

            all_r_type_defs += r_type_defs
            all_r_instances += r_instances
            all_r_rules += r_rules
            all_r_improvement_advice += r_improvement_advice

    return None

def pln2nl(type_defs, declares, chaining_result):
    def extract_grouneded_expr(text: str) -> str | None:
        try:
            content_start = text.find('(: ')
            if content_start == -1:
                return None

            content_start += 3

            items = []
            balance = 0
            item_start_index = 0

            for i, char in enumerate(text[content_start:], start=content_start):
                if char == '(':
                    if balance == 0:
                        item_start_index = i
                    balance += 1
                elif char == ')':
                    balance -= 1
                    if balance == 0:
                        items.append(text[item_start_index : i + 1])

                if balance < 0:
                    break

            if len(items) >= 2:
                return items

        except (IndexError, TypeError):
            return None

        return None

    chat_history = [{
        "role": "system",
        "content": pln2nl_instructions
    }]

    target_expr = extract_grouneded_expr(chaining_result)
    openai_outputs = to_openai(create_pln2nl_prompt(type_defs, declares, target_expr), history=chat_history, output_format=EngSent)
    sentence = openai_outputs["sentence"]

    return sentence
