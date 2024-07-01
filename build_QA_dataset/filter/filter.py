import json
import math
import os
from nh3 import clean
from sympy import Q

BATCH_SIZE = 40

import openai

openai_api_key = 'sk-'
openai.api_base = 'https://ai.com/v1'

task_definition = "You are a chemistry research assistant, and I need you to complete the following task: You will be given a question and a list of answers for this question, and you need to classify whether some of these answers are too brief without any details and can't answer the given question. Please give me your justification RESULT for each answer.\n"

rules_prefix = "Notice that here are some rules you need to follow:\n"

example_prefix = "Here are several examples to show how to check whether an answer is too brief:\n"
# example_prefix = "Here are several examples to show several kinds of mismatched quesiont-answer pairs to help you finish this task:\n"

instance_prefix = "Here comes a question and corresponding answers for you to judge: \n"
instance_suffix = "Please give me your RESULTs for these instances in above examples' styles. No other information is required."
# instance_suffix = "Just give me your CHOICE from [yes, no], no other information is needed."

rules = [
    "For my convenience, please give me a list of [yes, no] as your justification for the given answer list, without any other information.",
    "If there is any detailed description (even just one or two adjective) about the question in the answer, please label [yes] for this answer.",
    "Some answers have different keywords with the question but still can answer the question, please label [yes] for this answer.",
]

def chatgpt_annotation_yyds(task_context:str, instance:list):
    openai.api_key = 'sk-'
    openai.api_base = 'https://ai.com/v1'
    messages = [ {"role": "system", "content": task_context}]
    messages.append({"role": "user", "content": instance})

    response = openai.ChatCompletion.create(
        model='gpt-3.5-turbo-1106',
        messages=messages,
        max_tokens=512,
        temperature=0,
        top_p=0.01,
        seed=42,
    )
    reply = response.choices[0].message.content
    return reply

def add_example_prompt(origin_prompt, examples):
    # question, 
    formatted_examples = ""
    for question in examples:
        formatted_examples += "QUESTION: " + question + "\n"
        answers, judges = examples[question]
        for ans_idx, answer in enumerate(answers):
            formatted_examples += f"ANSWER {ans_idx + 1}: {answer}\n"
        for res_idx, result in enumerate(judges):
            formatted_examples += f"RESULT {res_idx + 1}: {result}\n"
        formatted_examples += "\n"
    
    return origin_prompt + example_prefix + formatted_examples

def add_rules_prompt(origin_prompt, rules):
    formatted_notice = ""
    for rule_idx, rule in enumerate(rules):
        formatted_notice += f"Rule {rule_idx + 1}:\n{rule}\n"
    return origin_prompt + rules_prefix + formatted_notice

def add_instance(origin_prompt, question, options):
    formatted_instance = origin_prompt
    formatted_instance += instance_prefix
    formatted_instance += f"QUESTION: {question}\n"
    for idx, option in enumerate(options):
        formatted_instance += f"ANSWER {idx + 1}:\n{option}\n"
    return formatted_instance + instance_suffix

def get_question_options(desc_cls, instance_path_ls):
    topic2options = {}

    question2options = {}
    topic2question = {}
    instance_path_ls = [instance_path.format(desc_cls, desc_cls) for instance_path in instance_path_ls]
    for instance_path in instance_path_ls:
        if not os.path.exists(instance_path):
            continue
        with open(instance_path, 'r') as f:
            instances = json.load(f)
        for topic in instances:
            if topic not in topic2options:
                topic2options[topic] = []
            topic_instances = instances[topic]
            for instance in topic_instances:
                cid, desc, question, t, answer = instance
                if not "not specified" in answer.lower():
                    topic2options[topic].append(answer)
                    if topic in topic2question:
                        # assert topic2question[topic] == question
                        if not isinstance(topic2question[topic], list):
                            topic2question[topic] = [topic2question[topic], question]
                        else:
                            topic2question[topic].append(question)
                    else:
                        topic2question[topic] = question
                    if not question in question2options:
                        question2options[question] = []
                    else:
                        question2options[question].append(answer)

    option_num = 0
    for topic in topic2options:
        topic2options[topic] = list(set(topic2options[topic]))
        option_num += len(topic2options[topic])

    print(f"option_num: {option_num}")

    for question in question2options:
        question2options[question] = list(set(question2options[question]))
    # for topic in topic2question:
    #     question = topic2question[topic]
    #     if isinstance(question, list):
    #         question = question[0]
    #     if question not in question2options:
    #         question2options[question] = []
    #     question2options[question].extend(topic2options[topic])

    os.makedirs(f"./{desc_cls}", exist_ok=True)
    with open(f"./{desc_cls}/topic2question.json", "w") as f:
        json.dump(topic2question, f, indent=4)
    with open(f"./{desc_cls}/topic2options.json", "w") as f:
        json.dump(topic2options, f, indent=4)
    with open(f"./{desc_cls}/question2options.json", "w") as f:
        json.dump(question2options, f, indent=4)
    

def remap_question(desc_cls):
    with open("./Chebi_Sup/filter/remap_table.json", "r") as fin:
        remap_table = json.load(fin)
    with open(f"./Chebi_Sup/filter/{desc_cls}/question2options.json", "r") as fin:
        question2options = json.load(fin)
    for question in list(question2options.keys()):
        if question in remap_table:
            question2options[remap_table[question]] = question2options[question]
            del question2options[question]
    with open(f"./Chebi_Sup/filter/{desc_cls}/remapped_question2options.json", "w") as fout:
        json.dump(question2options, fout, indent=4)


def filter_brief_option_with_gpt(example_path, question2options_path):
    with open(example_path, "r") as fin:
        examples = json.load(fin)

    task_context = task_definition
    task_context = add_example_prompt(task_context, examples)
    task_context = add_rules_prompt(task_context, rules)
    question2judge = {}
    # mail_stone = "Which kind of phosphatidyl acyl group does this molecule have?"
    # start = False
    with open(question2options_path, "r") as fin:
        question2options = json.load(fin)
    for question in question2options:
        # if question == mail_stone:
        #     start = True
        # if not start:
        #     continue
        options = question2options[question]
        batch_num = math.ceil(len(options) / BATCH_SIZE)
        for batch_idx in range(batch_num):
            batch_options = options[batch_idx * BATCH_SIZE: (batch_idx + 1) * BATCH_SIZE]
            instances = add_instance("", question, batch_options)
            # with open(f"./{question}_{batch_idx}.txt", "w") as fout:
            #     fout.write(prompt)
            # print(task_context)
            # print(instances)
            reply = chatgpt_annotation_yyds(task_context, instances)
            # print(reply)
            # return
            if not question in question2judge:
                question2judge[question] = []
            question2judge[question].append(reply)
        with open(example_path.replace("example.json", "ques2judge.json"), "w") as fout:
            json.dump(question2judge, fout, indent=4)
        print(f"{question} finished")
    # pass

def merge_judgement_with_option(desc_cls):
    ques2option_path = f"./Chebi_Sup/filter/{desc_cls}/remapped_question2options.json"
    ques2judge_path = f"./Chebi_Sup/filter/{desc_cls}/ques2judge.json"

    with open(ques2option_path, "r") as fin:
        ques2option = json.load(fin)
    with open(ques2judge_path, "r") as fin:
        ques2judge = json.load(fin)
    
    def split_judgement(judge_ls):
        splited_judge_ls = []
        for idx, batch_judge in enumerate(judge_ls):
            # "RESULT 1: yes\nRESULT 2: yes\nRESULT 3: yes\nRESULT 4: yes\nRESULT 5: yes\nRESULT 6: yes\nRESULT 7: yes\nRESULT 8: yes\nRESULT 9: yes\nRESULT 10: yes\nRESULT 11: yes\nRESULT 12: yes\nRESULT 13: yes\nRESULT 14: yes\nRESULT 15: yes\nRESULT 16: yes\nRESULT 17: yes\nRESULT 18: yes\nRESULT 19: yes\nRESULT 20: yes\nRESULT 21: yes\nRESULT 22: yes\nRESULT 23: yes\nRESULT 24: yes\nRESULT 25: yes\nRESULT 26: yes\nRESULT 27: yes\nRESULT 28: yes\nRESULT 29: yes\nRESULT 30: yes\nRESULT 31: yes\nRESULT 32: yes\nRESULT 33: yes\nRESULT 34: yes\nRESULT 35: yes\nRESULT 36: yes\nRESULT 37: yes\nRESULT 38: yes\nRESULT 39: yes\nRESULT 40: yes",
            judges = batch_judge.split("\n")
            # remove RESULT n:
            clean_judge = []
            for judge in judges:
                if "yes" not in judge and "no" not in judge:
                    continue
                if "yes" in judge:
                    if "no" in judge:
                        print(judge)
                        assert False
                    clean_judge.append("yes")
                elif "no" in judge:
                    clean_judge.append("no")
            if len(clean_judge) > BATCH_SIZE:
                clean_judge = clean_judge[:BATCH_SIZE]
            splited_judge_ls.extend(clean_judge)
        return splited_judge_ls



    ques2option_judge = {}
    brief_options = {}
    for question in ques2option:
        options = ques2option[question]
        judges = ques2judge[question]
        splited_judges = split_judgement(judges)
        if not len(splited_judges) == len(options):
            print(question)
            print(len(splited_judges))
            print(len(ques2option[question]))
            continue
        brief_options[question] = []
        for option, judge in zip(options, splited_judges):
            if judge == "no":
                brief_options[question].append(option)
        ques2option_judge[question] = [options, splited_judges]
    with open(f"./Chebi_Sup/filter/{desc_cls}/ques2option_judge.json", "w") as fout:
        json.dump(ques2option_judge, fout, indent=4)
        # ques2option_judge[question] = [options, judges]
    
    with open(f"./Chebi_Sup/filter/{desc_cls}/brief_options.json", "w") as fout:
        json.dump(brief_options, fout, indent=4)

def generate_brief_option(topic):
    brief_option_ls = []
    for main_role in ["it", "this molecule"]:
        for verb in ["is", "has a role as", "has", "exhibits"]:
            brief_option_ls.append(f"{main_role} {verb} a {topic}")
            brief_option_ls.append(f"{main_role} {verb} {topic}")
            for suffix in ["drug", "agent", "activity", "property"]:
                if topic.find(suffix) == -1:
                    brief_option_ls.append(f"{main_role} {verb} {topic} {suffix}")
                else:
                    for s in ["drug", "agent", "activity", "property"]:
                        if suffix != s:
                            brief_option_ls.append(f"{main_role} {verb} {topic.replace(suffix, s)}")
                            brief_option_ls.append(f"{main_role} {verb} a {topic.replace(suffix, s)}")
            
    return brief_option_ls

def normalize_option(option):
    option = option.lower()
    option = option.replace(" an ", " a ")
    if option.endswith("."):
        option = option[:-1]
    return option

def rule_base_filter(desc_cls):
    
    illegal_options_human_path = "./illegal_options_human.json"
    illegal_options_rule = {

    }
    with open(illegal_options_human_path, "r") as fin:
        illegal_options_human = json.load(fin)
    topic2option_path = f"./{desc_cls}/topic2options.json"
    with open(topic2option_path, "r") as fin:
        topic2option = json.load(fin)
    for topic in topic2option:
        options = topic2option[topic]
        brief_option_ls = generate_brief_option(topic)
        for option in options:
            if normalize_option(option) in brief_option_ls:
                if topic in illegal_options_human and option in illegal_options_human[topic]:
                    continue
                if not topic in illegal_options_rule:
                    illegal_options_rule[topic] = []
                illegal_options_rule[topic].append(option)
    with open(f"./{desc_cls}/illegal_options_rule.json", "w") as fout:
        json.dump(illegal_options_rule, fout, indent=4)

def merge_illegal_options():
    illegal_options_human_path = "./illegal_options_human.json"
    with open(illegal_options_human_path, "r") as fin:
        illegal_options_human = json.load(fin)
    for desc_cls in ["Structure", "Property", "Usage"]:
        illegal_options_rule_path = f"./{desc_cls}/illegal_options_rule.json"
        with open(illegal_options_rule_path, "r") as fin:
            illegal_options_rule = json.load(fin)
        for topic in illegal_options_rule:
            if topic in illegal_options_human:
                illegal_options_human[topic].extend(illegal_options_rule[topic])
            else:
                illegal_options_human[topic] = illegal_options_rule[topic]
    
    illegal_options_path = "./illegal_options.json"
    with open(illegal_options_path, "w") as fout:
        json.dump(illegal_options_human, fout, indent=4)

        

def load_instance(desc_cls):
    instance_path_ls = [
        "./Chebi_Sup/refine_expression/{}/no_dup_gpt_answer_merged_{}.json",
        "./Chebi_Sup/refine_expression/{}/gpt_answer_merged_{}.json"
    ]
    instance_path_ls = [instance_path.format(desc_cls, desc_cls) for instance_path in instance_path_ls]
    if desc_cls == "Structure":
        instance_path_ls = [            
            "./Chebi_Sup/refine_expression/base_replaced_Structure_instances.json"
        ]
    QA_instances = {}
    for instance_path in instance_path_ls:
        if not os.path.exists(instance_path):
            continue
        with open(instance_path, "r") as fin:
            instances = json.load(fin)
        for topic in instances:
            if not topic in QA_instances:
                QA_instances[topic] = []
            QA_instances[topic].extend(instances[topic])
    return QA_instances

            
def filter_brief_QA_instance(desc_cls):
    illegal_options_path = "./illegal_options.json"
    with open(illegal_options_path, "r") as fin:
        illegal_options = json.load(fin)
    
    QA_instances = load_instance(desc_cls)
    brief_QA_instances = {}
    non_brief_QA_instances = {}
    brief_num = 0
    non_brief_num = 0
    for topic in QA_instances:
        brief_QA_instances[topic] = []
        non_brief_QA_instances[topic] = []
        for instance in QA_instances[topic]:
            cid, desc, question, t, answer = instance
            if topic in illegal_options and answer in illegal_options[topic]:
                brief_QA_instances[topic].append(instance)
                brief_num += 1
            else:
                non_brief_QA_instances[topic].append(instance)
                non_brief_num += 1
    
    with open(f"./{desc_cls}/brief_QA_instances.json", "w") as fout:
        json.dump(brief_QA_instances, fout, indent=4)
    
    with open(f"./{desc_cls}/non_brief_QA_instances.json", "w") as fout:
        json.dump(non_brief_QA_instances, fout, indent=4)

    print(f"brief_num: {brief_num}")
    print(f"non_brief_num: {non_brief_num}")
    





if __name__ == "__main__":  
    for desc_cls in ["Structure", "Usage", "Property"]:# "Source"
        # example_path = f"./Chebi_Sup/filter/{desc_cls}/example.json"
        # question2options_path = f"./Chebi_Sup/filter/{desc_cls}/remapped_question2options.json"
        # if not desc_cls == "Source":            
        #     instance_path_ls = [
        #         "./Chebi_Sup/refine_expression/{}/no_dup_gpt_answer_merged_{}.json",
        #         "./Chebi_Sup/refine_expression/{}/gpt_answer_merged_{}.json",
        #     ]
        # else:
        #     instance_path_ls = [
        #         "./Chebi_Sup/refine_expression/{}/gpt_answer_merged_easy_{}.json"
        #     ]
        # get_question_options(desc_cls, instance_path_ls)
        # remap_question(desc_cls)
        # filter_brief_option_with_gpt(example_path, question2options_path)
        # merge_judgement_with_option(desc_cls)
    #     rule_base_filter(desc_cls)
    # merge_illegal_options()
        filter_brief_QA_instance(desc_cls)
    # print(generate_brief_option("antibacterial drug"))

# brief_num: 188
# non_brief_num: 40665
# brief_num: 317
# non_brief_num: 3668
# brief_num: 30
# non_brief_num: 6799