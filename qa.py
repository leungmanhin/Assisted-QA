from core_functions import *
from util_functions import *
from datetime import datetime, timezone, timedelta

while True:
    mode = input("Enter either:\n- '1' to parse a sentence as the KB\n- '2' to read a KB from a file\n- '3' to use a simple test KB\n")
    if mode == "1":
        sentence = input("Enter a sentence: ")

        print(f"\n... parsing: {sentence}")
        sent_result = nl2pln(sentence, mode="parsing")
        if sent_result == None:
            print(f"Failed parsing the sentence: '{sentence}', please try another one.")
            continue
        else:
            type_defs, declares, _, _ = sent_result
            break
    elif mode == "2":
        kb_filename = input("Enter the file name in path: ")
    elif mode == "3":
        kb_filename = "qa_test_kb.json"
    if mode == "2" or mode == "3":
        with open(f"{kb_filename}", "r") as fp:
            data = json.load(fp)
            if isinstance(data, list):
                while True:
                    max_idx = len(data) - 1
                    sentence_idx = int(input(f"Enter a sentence index (0-{max_idx}): "))
                    if sentence_idx < 0 or sentence_idx > max_idx:
                        print("Invalid sentence index!")
                        continue
                    else:
                        break
                sentence, type_defs, declares = [(s["sentence"], s["type_defs"], s["declares"]) for s in data if s["sentence_idx"] == sentence_idx][0]
            elif isinstance(data, dict):
                sentence, type_defs, declares = data["sentence"], data["type_defs"], data["declares"]
            print(f"Successfully loaded!\n```\nsentence = \"{sentence}\"\ntype_defs = {type_defs}\ndeclares = {declares}\n```\n")
            break

while True:
    question = input("\n====== ['/exit' to exit | '/save' to save] ======\n\nEnter a question: ")

    if question == "/exit":
        print("... exiting")
        break
    elif question == "/save":
        current_time = datetime.now(timezone(timedelta(hours=8))).strftime("%Y-%m-%d-%H-%M-%S")
        qa_out_file = f"qa_{current_time}.json"
        print(f"... saving to {qa_out_file}\n")
        output_to_json_file({
                "sentence": sentence,
                "type_defs": type_defs,
                "declares": declares,
                "question": question,
                "q_type_defs": q_type_defs,
                "q_declares": q_declares,
                "query": query,
                "r_type_defs": r_type_defs,
                "r_instances": r_instances,
                "r_rules": r_rules,
                "chaining_result": chaining_result
            },
            qa_out_file)
        continue

    print(f"\n... parsing: {question}")
    ques_result = nl2pln(question, mode="querying")
    if ques_result == None:
        print(f"Failed parsing the question: '{question}', please try another one.")
        continue
    else:
        q_type_defs, q_declares, q_queries, _ = ques_result

    for query in q_queries:
        qa_result = qa(type_defs + q_type_defs, declares + q_declares, query)
        if qa_result is not None:
            chaining_result, r_type_defs, r_instances, r_rules, _ = qa_result
            print(f"ANSWER FOUND!!\n\n... needed to add:\nr_type_defs = {r_type_defs}\nr_instances = {r_instances}\nr_rules = {r_rules}\n")

            print(f"... constructing the answer")
            answer = pln2nl(
                type_defs + q_type_defs + r_type_defs,
                declares + q_declares + r_instances + r_rules,
                chaining_result[0]
            )

            print(f"Answer: {answer}\n")
