import os
import re
import json
import requests
from openai import OpenAI
from openai.lib._parsing._completions import type_to_response_format_param
from datetime import datetime, timezone, timedelta
from pydantic import BaseModel

class PLNExprs(BaseModel):
    type_defs: list[str]
    declares: list[str]
    queries: list[str]
    improvement_advice: str

class AddPLNExprs(BaseModel):
    type_defs: list[str]
    instances: list[str]
    rules: list[str]
    improvement_advice: str

class EngSent(BaseModel):
    sentence: str

class EngQuestions(BaseModel):
    questions: list[str]

def to_openai(prompt, model="gpt-5", effort="high", history=[], output_format=PLNExprs, via_openrouter=True):
    if via_openrouter:
        openrouter_api_key = os.environ.get("OPENROUTER_API_KEY")
        history.append({"role": "user", "content": prompt})
        response = requests.post(
            url = "https://openrouter.ai/api/v1/chat/completions",
            headers = {
                "Authorization": f"Bearer {openrouter_api_key}",
            },
            data = json.dumps({
                "model": f"openai/{model}",
                "reasoning": {
                    "effort": effort
                },
                "response_format": type_to_response_format_param(output_format),
                "messages": history,
                # "provider": {
                #     "order": ["OpenAI"],
                #     "allow_fallbacks": False
                # }
            }),
        )
        response_content = response.json()["choices"][0]["message"]["content"]
        history.append({"role": "assistant", "content": response_content})
        return json.loads(response_content)
    else:
        openai_client = OpenAI(max_retries=3)
        history.append({"role": "user", "content": prompt})
        response = openai_client.responses.parse(
            model = model,
            reasoning = {"effort": effort},
            input = history,
            text_format = output_format,
            store = False
        )
        history.append({"role": "assistant", "content": response.output_text})
        return json.loads(response.output_text)

def output_to_json_file(json_dict, output_file):
    print(f"=== Writing to JSON ===\nFile: {output_file}\nContent: {json_dict}\n")
    with open(output_file, "w") as json_file:
        json.dump(json_dict, json_file, indent=4)

def print_test_case(atoms, query, kb_str="", query_str=""):
    current_time = datetime.now(timezone(timedelta(hours=8))).strftime("%Y-%m-%d-%H-%M-%S")
    tc_file = f"test_case_{current_time}.py"
    atoms_str = "\n".join([f"    '{a}'," for a in atoms])

    with open(tc_file, "w") as fp:
        fstr = f"""
from mork_handler import MorkHandler

# {kb_str}
atoms = [
{atoms_str}
]

# {query_str}
query = '{query}'

handler = MorkHandler()

for a in atoms:
    print("... adding to space: " + a)
    handler.add_atom(a)

print("... chaining for: " + query)
result = handler.query(query)
print("\\n=== Result ===")
print(result)
""".strip()
        fp.write(fstr)
        print(f"... created test case: {tc_file}\n")

# TODO: to be removed when we don't need to care so much about the chaining 'depth'
def flatten_ands_ors(expr: str) -> str:
    tokens = re.findall(r'\(|\)|[^\s()]+', expr)

    def parse(tokens):
        token = tokens.pop(0)
        if token == '(':
            lst = []
            while tokens[0] != ')':
                lst.append(parse(tokens))
            tokens.pop(0)  # Pop ')'
            return lst
        else:
            return token

    tree = parse(tokens)

    def flatten(node):
        if not isinstance(node, list) or not node:
            return node

        flattened_children = [flatten(child) for child in node[1:]]

        head = node[0]
        if head not in ('And', 'Or'):
            return [head] + flattened_children

        merged_children = []
        for child in flattened_children:
            if isinstance(child, list) and child and child[0] == head:
                merged_children.extend(child[1:])
            else:
                merged_children.append(child)

        return [head] + merged_children

    flat_tree = flatten(tree)

    def to_string(node):
        if isinstance(node, list):
            return f"({' '.join(to_string(n) for n in node)})"
        return node

    return to_string(flat_tree)

# TODO: to be removed when floats are properly supported in MORK
def drop_stv_2nd_digit(expr):
    pattern = re.compile(r"(STV (\d)\.(\d)\d* (\d)\.(\d)\d*)")

    def repl(match):
        first_num = match.group(2) + "." + match.group(3)
        second_num = match.group(4) + "." + match.group(5)
        return f"STV {first_num} {second_num}"

    return pattern.sub(repl, expr)

# TODO: just a wrapper, to be removed when we don't need these workarounds anymore
def temp_postprocess(expr):
    return drop_stv_2nd_digit(flatten_ands_ors(expr))
