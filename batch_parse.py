from core_functions import *
from datetime import datetime, timezone, timedelta

current_time = datetime.now(timezone(timedelta(hours=8))).strftime("%Y-%m-%d-%H-%M-%S")
sp_out_file = f"semantic_parsing_{current_time}.json"

qa_outputs = []
all_outputs = []
failed_cases = []

filename = input("Enter the full name of the file to be parsed: ")

with open(f"{filename}", "r") as fp:
    data = json.load(fp)

    if isinstance(data, list):
        sentences = [d["sentence"] for d in data]
    elif isinstance(data, dict):
        sentences = [data["sentence"]]

    print(f"Successfully loaded {len(sentences)} sentences!\n```\nsentences = {sentences}\n```\n")

start_idx = input("Start parsing from index (default is 0): ")
try:
    start_idx = int(start_idx)
except Exception:
    start_idx = 0

do_qa = input("Enhance parsing with automatic Q&A (Y/N): ")
do_qa = True if do_qa.lower() == "y" else False

for i in range(start_idx, len(sentences)):
    sentence = sentences[i]

    print(f"... parsing sentence (idx = {i}): {sentence}")

    sent_result = nl2pln(sentence, mode="parsing")
    if sent_result is not None:
        type_defs, declares, queries, improvement_advice = sent_result

        if do_qa:
            questions = to_openai(create_gen_ques_prompt(sentence), output_format=EngQuestions)["questions"]
            print(f"Questions generated: {questions}")

            for j in range(0, len(questions)):
                question = questions[j]
                print(f"... parsing question ({j+1} out of {len(questions)}): {question}")

                ques_result = nl2pln(question, mode="querying")
                if ques_result is not None:
                    q_type_defs, q_declares, q_queries, q_improvement_advice = ques_result

                for query in q_queries:
                    qa_result = qa(type_defs + q_type_defs, declares + q_declares, query)
                    if qa_result is not None:
                        chaining_result, r_type_defs, r_instances, r_rules, r_improvement_advice = qa_result
                        print(f"ANSWER FOUND!!\n\n... needed to add:\nr_type_defs = {r_type_defs}\nr_instances = {r_instances}\nr_rules = {r_rules}\n")
                        qa_outputs.append({
                            "question_idx": j,
                            "question": question,
                            "type_defs": q_type_defs,
                            "declares": q_declares,
                            "query": query,
                            # "improvement_advice": q_improvement_advice,
                            "additional_type_defs": r_type_defs,
                            "additional_instances": r_instances,
                            "additional_rules": r_rules,
                            # "improvement_advice": r_improvement_advice,
                        })

        print(f"Sentence #{i}:\n{sentence}\n\ntype_defs:\n{type_defs}\n\ndeclares:\n{declares}\n\nqueries:\n{queries}\n\nimprovement_advice:\n{improvement_advice}\n\nquestions:\n{qa_outputs}\n\n---\n")
        all_outputs.append({
            "sentence_idx": i,
            "sentence": sentence,
            "type_defs": type_defs,
            "declares": declares,
            # "queries": queries,
            "improvement_advice": improvement_advice,
            "questions": qa_outputs
        })
        output_to_json_file(all_outputs, sp_out_file)
    else:
        failed_cases.append(i)

if failed_cases:
    print(f"Failed to parse: {failed_cases}")

finish_time = datetime.now(timezone(timedelta(hours=8))).strftime("%Y-%m-%d %H:%M:%S")
print(f"FINISHED PARSING at {finish_time}")
