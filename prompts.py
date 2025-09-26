special_symbols = [
    ":",
    "->"
]

built_in_preds = [
    "Implication",
    "And",
    "Or",
    "Not",
    "Equivalence",
    "Similarity",
    "WithTV",
    "STV",
    "Quantity",
    "Tense",
    "TenseForm"
]

built_in_type_defs = [
    "(: Implication (-> Type Type Type))",
    "(: And (-> Type Type Type))",
    "(: Or (-> Type Type Type))",
    "(: Not (-> Type Type))",
    "(: Equivalence (-> Type Type Type))",
    "(: Similarity (-> Concept Concept Type))",
    "(: WithTV (-> Type TV Type))",
    "(: STV (-> Number Number TV))",
    "(: Quantity (-> Concept Number Type))",
    "(: Tense (-> Concept Concept Type))",
    "(: TenseForm (-> Concept String Type))"
]

built_in_instances = [
    "(TenseForm present_tense 'present tense')",
    "(TenseForm present_continuous_tense 'present continuous tense')",
    "(TenseForm present_perfect_tense 'present perfect tense')",
    "(TenseForm present_perfect_continuous_tense 'present perfect continuous tense')",
    "(TenseForm past_tense 'past tense')",
    "(TenseForm past_continuous_tense 'past continuous tense')",
    "(TenseForm past_perfect_tense 'past perfect tense')",
    "(TenseForm past_perfect_continuous_tense 'past perfect continuous tense')",
    "(TenseForm future_tense 'future tense')",
    "(TenseForm future_continuous_tense 'future continuous tense')",
    "(TenseForm future_perfect_tense 'future perfect tense')",
    "(TenseForm future_perfect_continuous_tense 'future perfect continuous tense')"
]

# TODO: too generic to be practically useful, will insert them when a faster chainer is ready
additional_rules = [
    "(: similarity_1ary (WithTV (Implication (And ($pred $x) (Similarity $x $z)) ($pred $z)) (STV 0.9 0.9)))",
    "(: similarity_2ary_left (WithTV (Implication (And ($pred $x $y) (Similarity $x $z)) ($pred $z $y)) (STV 0.9 0.9)))",
    "(: similarity_2ary_right (WithTV (Implication (And ($pred $x $y) (Similarity $y $z)) ($pred $x $z)) (STV 0.9 0.9)))"
]

pad_str = "\n- "
built_in_preds_str = pad_str + pad_str.join(built_in_preds)
built_in_type_defs_str = pad_str + pad_str.join(built_in_type_defs)
built_in_instances_str = pad_str + pad_str.join(built_in_instances)

base_instructions = f"""
You are helping to build a knowledge base for an AI system to use, by representing natural language sentences in PLN expressions and storing them into the knowledge base, so that the AI system can use and reason upon this knowledge.
You can see PLN as a custom form of a typed probabilistic predicate logic.

Here are some general guidelines you need to follow when converting natural language sentences into PLN expressions:
- all expressions must be in the format of `(: <expr_name> <expr_body>)`
- the `expr_name` (aka `proof_name`) can just be any arbitrary name written in snake_case, but by convention it's preferable to somewhat reflect the meaning of the `expr_body`, and it must be uniquely identifiable globally
- the `expr_name` should not be used/referenced anywhere in the `expr_body`
- for expressions that are not type definitions, you need to give it a sensible truth value by using both the `WithTV` and `STV` built-in predicates, e.g. `(: <expr_name> (WithTV <rest_of_the_expr_body> (STV <some_sensible_truth_value_strength> <some_sensible_truth_value_confidence>)))`
- to denote a variable, prefix the variable name written in snake_case with a '$' symbol; how it's named doesn't matter, but it must be uniquely identifiable within its scope
- to denote an instance, it should be written in snake_case and can be named arbitrarily; how it's named doesn't matter, but it must be uniquely identifiable globally, and by convention it's preferable to have a name that is identical or similar to the word or phrase being used in the original text
- in this representation essentially everything can be considered as an instance of a predicate, e.g. nouns, pronouns, verbs, adjectives, adverbs, or even prepositions etc, grouped together forming expressions like a typical predicate-argument structure, constituting the core of the `expr_body`
- an instance can be understood as the existence of a unique entity or concept being referred to, which is globally scoped in the knowledge base and so can be seen and used by other PLN expressions in the same knowledge base
- you should create an instance for each entity/concept exists in the input sentence; if it's a pronoun and you know what/who it's referring to, you can use the built-in predicate `Similarity` to equate the instance of the pronoun and the instance of that particular entity/concept with a sensible truth value attached
- all instances being created/used should be explicitly associated with a predicate, as long as this information is known from the input sentence
- it's highly preferable to have predicates that are as simple as possible, e.g. a single-word predicate is much more preferable than a multi-word predicate
- by convention, predicates should be named using UpperCamelCase, and instances or variables should be named using snake_case
- you must consistently follow the style of Neo-Davidsonian event semantics to represent all the predicate-argument relationships wherever appropriate
- you should capture the tense information for each verb/event using the built-in predicate `Tense` wherever appropriate, and reuse one of the built-in instances for the corresponding tense
- you must create a type definition for any new predicate that you are creating and using
- for quantification, it's typically represented using the built-in predicate `Implication`, and reflect the level of quantification using `STV`, e.g. 'for all' should have a relatively high truth value close to 1.0 while 'none' should have a relatively low truth value close to 0.0, and fuzzy quantifiers like 'most', 'many', 'some', 'a few', etc... should have a truth value that lies somewhat in between
- you should always try to quantify (and hence carefully and properly scope) each input sentence that contains one or more generic concepts/instances; if specific concepts/instances (or a group of specific concepts/instances) are mentioned, just create the corresponding instances concretely
- you can use the built-in predicate `Quantity` to quantify a concept/instance if a specific quantity is explicitly mentioned, but if the quantity is 1, by convention you can just create an instance for it without using the `Quantity` built-in predicate
- built-in predicates `And` and `Or` are typically used to connect PLN expressions within a particular scope (e.g. within an `Implication`) with variables involved to express a certain probabilistic truth, or in a query being posted to the system to look for an answer; otherwise you can just represent things as smaller, individual, but interconnected PLN expressions instead of putting them all under `And`'s even if they're all in the same sentence
- the PLN expressions should be represented as close to the literal meaning of the given text as possible, and as complete as possible without skipping any words/phrases/clauses
- if there is more than one PLN expression involved in representing the meaning of the given text, these expressions must be connected together, forming something like an interconnected graph

There are some built-in predicates in the system that you can use, as follows:{built_in_preds_str}
And their corresponding type definitions are:{built_in_type_defs_str}
There are also some built-in instances that you can use:{built_in_instances_str}

The above type definitions of the built-in predicates also show how a typical PLN expression for a type definition should look like, i.e.:
(: <predicate_name> (-> <input_type> <return_type>))
Which can be read as: there is this predicate `predicate_name` that takes an input argument of type `input_type` and returns something of type `return_type`.
Again, it can take more than one input type as needed.
As a start, the system is currently taking only two types for all newly created type definitions:
1) `Concept`: used if an input argument is an instance
2) `Type`: typically used as the return type, but can also be used if the input argument itself is a PLN expression

Similarly, a typical PLN expression for a declarative statement should look like:
(: <prf_name> (WithTV (<predicate> <instance_1> <instance_2>) (STV <strength> <confidence>)))
Which can be read as: there is a proof `prf_name` that this statement, represented by the sub-expression formed by a predicate (`predicate`) and two arguments (`instance_1` and `instance_2`), is true probabilistically as stated by the given `strength` and `confidence`.
Again, the sub-expression can have fewer or more than two instances as needed.

Finally, a typical PLN expression for a question being posted to the system as a query should look like:
(: $prf (WithTV ($predicate $instance) $tv))
Which can be read as: find a proof `$prf` of something represented in a relational structure formed by variables `$predicate` and `$instance`, is true probabilistically to what degree `$tv`.
Typically, you'll need to keep the proof (`$prf`) and the truth value (`$tv`) as variables since that's what the query wants to find in the knowledge base through reasoning, but you can of course change any of the variables in the expr_body (i.e. `$predicate` and `$instance`) to specific values according to what the question is asking;
and the sub-expression can have a more complex structure, or have multiple sub-expressions interconnected together using the built-in predicates `And` or `Or` to express the needed logical structure.

The above are the general guidelines for representing natural language sentences in PLN expressions. You are required to extrapolate them in a similar and most coherent way if you encounter something that is not explicitly mentioned above.
At the same time, whenever you encounter something that you feel unclear how it should be represented as PLN expressions based on the above instructions, you can also leave your reasoning as well as your suggestions in the `improvement_advice` output field as to how to improve the above instructions to make them more complete and consistent for parsing more varieties of sentences.
""".strip()

# TODO: properly classify and handle declarative, imperative, interrogative, exclamatory?
nl2pln_instructions = f"""
As a task, you will be given the following as inputs:
- mode: should be either 'parsing' or 'querying', which determines how the `input_text` should be processed and returned in the output fields
- input_text: the text written in natural language that needs to be converted into PLN expressions
- correction_comments: optional, but when it is given, you should check your previous outputs and make the corrections accordingly
The `input_text` can just be a statement, or a question, or a mix of both, etc. There is a slight difference in handling it depending on the `mode`.
If the `mode` is 'parsing', you should treat the `input_text` as declarative in nature (even if there may be questions in it), represent them as one or more PLN expressions and return them all in the `declares` output field.
If the `mode` is 'querying', you should try to identify any questions in the `input_text`, consider and represent them as questions being posted to the system as a query, and return them all in the `queries` output field; in case there is some declarative information along with the question in the `input_text`, you should also represent and return them in the `declares` output field.
Eventually, you need to return the following as outputs:
- type_defs: type definitions for any predicate being created/used in the rest of the PLN expressions in the `declares` and/or `queries` output fields
- declares: one or more PLN expressions representing the semantic meaning of the declarative statements in 'input_text'; you must return at least one PLN expression here if the `mode` is 'parsing', but you can leave it empty if and only if the `mode` is 'querying' and there are no declarative statements in the `input_text`
- queries: one or more PLN expressions representing the semantic meaning of any question in 'input_text'; you must return at least one PLN expression here if the `mode` is `querying`, but you should leave it empty if and only if the `mode` is 'parsing'
- improvement_advice: optional, you should leave it empty unless you encounter an `input_text` that you are not sure how to convert it into PLN expressions based on the above instructions
No extra comments or explanations, etc., are needed in the `type_defs`, `declares`, and `queries` output fields.
""".strip()

add_missing_exprs_instructions = f"""
As a task, you will be given as inputs two sets of PLN expressions that were converted beforehand using the guidelines above:
- knowledge_exprs: a set of PLN expressions that supposedly represent some knowledge in logical form that were converted from one or more sentences using the guidelines above
- query_exprs: a set of PLN expressions that supposedly represent a query being posted by a user to the system, and were converted from a question using the same guidelines above
The backward chainer was used but failed to answer the query (`query_exprs`) based on the given knowledge (`knowledge_exprs`), so it seems that there are some missing rules/knowledge so that the reasoning chain from the query to the knowledge couldn't be established.
Your task is to firstly identify what is missing in order to establish a connection between the query and the knowledge so that the backward chainer can finally find the correct answer;
and secondly, represent the missing rules/knowledge in the form of PLN expressions (created using the guidelines above), and return them in the following output fields:
- type_defs: additional type definitions for any predicate being created and used in the PLN expressions in the rest of the output fields
- instances: additional PLN expressions for creating new instances (typically the ones with variables in the antecedent of an implication in the `knowledge_exprs` input field) so that the consequent of the implication can then be instantiated
- rules: additional PLN expressions representing the missing rule/knowledge
- improvement_advice: optional, you should leave it empty unless you encounter an `input_text` that you are not sure how to convert it into PLN expressions based on the above instructions
No extra comments or explanations, etc., are needed in the `type_defs` and `declares` output fields.

Please note that the missing rules/knowledge can also be seen as a list of transformation rules, which transform one or more of the knowledge PLN expressions (`knowledge_exprs`) in one or more steps, and through this process they will eventually become the query PLN expressions (`query_exprs`) with all of its variables grounded.
Also note that I'm using rules and knowledge interchangeably here, since each piece of knowledge should be represented as a rule here, in the form of an implication using the built-in predicate `Implication`.
""".strip()

pln2nl_instructions = f"""
NL->PLN instructions:
```
{base_instructions}
```
The above (`NL->PLN instructions`) are the instructions for how to convert a natural language sentence into one or more PLN expressions, and as a task, you will be given the following as inputs:
- type_defs: a set of type definitions for the predicates being used
- declares: a set of PLN expressions representing some existing knowledge
- target_expr: the PLN expression needed to be converted back to one or more English sentences
and your task is to convert the `target_expr` back to one or more English sentences by reverse-enginerring the above `NL->PLN instructions`,
you can also reference the type definitions (`type_defs`) and declarative PLN expressions (`declares`) that are related to the `target_expr` for extra info,
and then return the following as output:
- sentence: the English sentence that captures the semantic meaning of the `target_expr`
Please note that the English sentence being outputted should not be a literal conversion of all the `target_expr`, you should instead properly interpret the semantic meaning of all these `target_expr` collectively, and then phrase them into a natural sounding sentence.
""".strip()

def create_nl2pln_prompt(mode="parsing", text="", correction=""):
    return f"""
mode: {mode}

input_text:
```
{text}
```

correction_comments:
```
{correction}
```
""".strip()

def create_missing_rule_prompt(k_exprs, q_exprs):
    return f"""
knowledge_exprs:
```
{k_exprs}
```

query_exprs:
```
{q_exprs}
```
""".strip()

def create_pln2nl_prompt(type_defs, declares, target_expr):
    return f"""
type_defs:
```
{type_defs}
```

declares:
```
{declares}
```

target_expr:
```
{target_expr}
```
""".strip()

def create_gen_ques_prompt(sentence, min_num_ques=3):
    return f"""
target_sentence:
```
{sentence}
```

You are given the above `target_sentence`, and your task is to suggest a few questions that are relevant to this `target_sentence`.
Those questions should:
- be answerable based only on the content in the `target_sentence` (and so no other knowledge is needed)
- be answerable via typical symbolic pattern matching and/or backward chaining algorithms
- cover as many content of the given sentence as possible, if not all
- focus on the semantic instead of the syntax of the given sentence
- as short and concise as possible

The total number of questions to be suggested are not fixed, and should depend on the complexity of the `target_sentence`,
e.g. more questions should be generated for a longer sentence, and it is best to have at least {min_num_ques} even for shorter sentences.
""".strip()
