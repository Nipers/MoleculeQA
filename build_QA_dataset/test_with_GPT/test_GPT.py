import math
import random
import time
import json
import os
from nh3 import clean
from numpy import add
from tqdm import tqdm
import openai
# from openai import OpenAI
import requests
# openai pip install openai==0.28`
# openai 1.2.0
from openai.error import APIError, APIConnectionError, InvalidRequestError
openai.api_base = 'https://ai.com/v1'
from transformers import AutoTokenizer
BATCH_SIZE = 40

# model = 'gpt-3.5-turbo-1106'
# model = "gpt-4-1106-preview"
model = "claude-2"


task_definition = "You are a chemistry research assistant, and I'd like to test your professional ability on molecule understanding, please complete the following task: You are given the SMILEs of a molecule, which describe its sturctural information, a question about the molecule's {} and four options for this question, three of given options are descriptions of other molecules, you need to choose the right option for the given molecule."

cid2smiles = json.load(open("./cid2smile.json", "r"))

def select_samples(cid_path, desc_cls):

    instance_path = f"./Chebi_Sup/test_with_GPT/option_added_QA_pairs_{desc_cls}_reverse_biot5_v2.json"

    with open(cid_path, "r") as fin:
        test_cid = json.load(fin)
    
    with open(instance_path, "r") as fin:
        instances = json.load(fin)
    
    selected_instances = {}
    num = 0

    for topic in instances:
        selected_instances[topic] = []
        for instance in instances[topic]:
            if instance[0] in test_cid:
                selected_instances[topic].append(instance)
                num += 1
    
    print(f"Total number of selected instances: {num}")

    with open(f"./Chebi_Sup/test_with_GPT/GPT_test_result/{desc_cls}/selected_test_instances.json", "w") as fout:
        json.dump(selected_instances, fout, indent=4)
    return selected_instances

def select_examples(desc_cls):
    train_cid_path = "train_cid.json"
    option_added_path = f"./Chebi_Sup/test_with_GPT/option_added_QA_pairs_{desc_cls}_reverse_biot5_v2.json"
    example_path = f"./Chebi_Sup/test_with_GPT/GPT_test_result/{desc_cls}/example.json"
    output_path= f"./Chebi_Sup/test_with_GPT/GPT_test_result/{desc_cls}/option_added_example.json"

    with open(train_cid_path, "r") as fin:
        train_cids = json.load(fin)

    with open(option_added_path, "r") as fin:
        option_added = json.load(fin)
    
    with open(example_path, "r") as fin:
        examples = json.load(fin)
    
    option_added_example = {}

    for topic in examples:
        topic_instances = option_added[topic]
        option_added_example[topic] = []
        for example in examples[topic]:
            if example[0] in train_cids:
                for instance in topic_instances:
                    if instance[0] == example[0] and instance[1] == example[1] and instance[2] == example[2]:
                        if instance[3][0] == example[3]:
                            option_added_example[topic].append(instance)
                            break
    
    with open(output_path, "w") as fout:
        json.dump(option_added_example, fout, indent=4)


rules_prefix = "Notice that here are some rules you need to follow:\n"

example_prefix = "Here are several examples to show how to finish the Question Answering task:\n"
# example_prefix = "Here are several examples to show several kinds of mismatched quesiont-answer pairs to help you finish this task:\n"

instance_suffix = "Please give me your CHOICEs for these instances in above examples' styles. No other information is required."
instance_prefix = "Here comes several task instances for you to complete: \n"

rules = [
    # "If phrases or sentences from original descriptions can perfectly answer the question, no need to overwrite them.",
    'Your answer for each question should be one of A/B/C/D, which corresponds to the four options.',
    "For my convenience, please give me a list of ANSWERs for the given instances in format 'Answer 1: ...\nAnswer 2: ...\n', without any other information."
]

def add_rules_prompt(origin_prompt, rules):
    formatted_notice = ""
    for rule_idx, rule in enumerate(rules):
        formatted_notice += f"Notice {rule_idx + 1}:\n{rule}\n\n"
    return origin_prompt + rules_prefix + formatted_notice

def add_example_prompt(origin_prompt, examples):
    formatted_examples = ""
    for exp_idx, example in enumerate(examples):
        cid, desc, ques, answers, choices = example
        right_choice = choices[0]
        smiles = cid2smiles[cid]
        formatted_choices = ""
        for choice in ["A", "B", "C", "D"]:
            idx = choices.index(choice)
            formatted_choices += f"{choice}: {answers[idx]}\n"

        if not ques.endswith("?"):
            ques += "?"
        formatted_examples += f"Example {exp_idx + 1}:\nMolecular SMILEs: {smiles}\nQUESTION: {ques}\nCHOICES:\n{formatted_choices}ANSWER:{right_choice}\n\n"
    return origin_prompt + example_prefix + formatted_examples


def chatgpt_annotation_yyds(task_context:str, instance:str):
    openai.api_key = "sk-"
    openai.api_base = 'https://ai.com/v1'
    messages = [ {"role": "system", "content": task_context}]
    messages.append({"role": "user", "content": instance})

    response = openai.ChatCompletion.create(
        model=model,
        messages=messages,
        max_tokens=2048,
        temperature=0,
        top_p=0.01,
        seed=42,
    )
    reply = response.choices[0].message.content
    return reply


def add_instance(origin_prompt, instances):
    formatted_instance = origin_prompt
    for idx, instance in enumerate(instances):
        cid, desc, ques, answers, choices = instance
        formatted_choices = ""
        for choice in ["A", "B", "C", "D"]:
            i = choices.index(choice)
            formatted_choices += f"{choice}: {answers[i]}\n"
        smiles = cid2smiles[cid]
        if not ques.endswith("?"):
            ques += "?"
        formatted_instance += f"Instance {idx + 1}:\nMolecular SMILEs: {smiles}\nQUESTION: {ques}\nCHOICES:\n{formatted_choices}\n"
    return instance_prefix + formatted_instance + instance_suffix.format(ques)

if __name__ == "__main__":
    random.seed(2024)
    # 
    for desc_cls in ["Source", "Property", "Usage", "Structure"]:
        examples_path = f"./Chebi_Sup/test_with_GPT/GPT_test_result/{desc_cls}/option_added_example.json"
        with open(examples_path, "r") as example_file:
            origin_examples = json.load(example_file)
        examples = []
        for topic in origin_examples:
            examples += origin_examples[topic]
        random.shuffle(examples)
        
        task_context = task_definition.format(desc_cls)
        task_context =  add_example_prompt(task_context, examples[:10])
        task_context = add_rules_prompt(task_context, rules)
        print(task_context)
        
        test_instances = select_samples("test_cid.json", desc_cls)
        answer_res = {}
        answer_path = f"./GPT_test_result/{desc_cls}/{model}_{desc_cls}.json"
        if os.path.exists(answer_path):
            with open(answer_path, "r") as fin:
                answer_res = json.load(fin)
        for topic_idx, topic in enumerate(test_instances.keys()):
            topic_res = []
            if topic in answer_res.keys():
                start_idx = len(answer_res[topic])
                topic_res = answer_res[topic]
            else:
                start_idx = 0
            print(topic)
            topic_QA_pairs = test_instances[topic]
            # calculate the num of batch with BATCH_SIZE
            batch_num = math.ceil(len(topic_QA_pairs) / BATCH_SIZE)
            for batch_idx in tqdm(range(start_idx, batch_num)):
                instances = topic_QA_pairs[batch_idx * BATCH_SIZE: (batch_idx + 1) * BATCH_SIZE]
                instances = add_instance("", instances)
                error_num = 0
                while error_num < 3:
                    try:
                        reply = chatgpt_annotation_yyds(task_context, instances)
                        break
                    except (APIError, APIConnectionError):
                        error_num += 1
                        if error_num == 3:
                            reply = "Error"
                        continue
                    except (InvalidRequestError):
                        instances = topic_QA_pairs[batch_idx * BATCH_SIZE: (batch_idx + 1) * BATCH_SIZE]
                        half_num = len(instances) // 2
                        instances_a = add_instance("", instances[:half_num])
                        instances_b = add_instance("", instances[half_num:])
                        reply_a = chatgpt_annotation_yyds(task_context, instances_a)
                        reply_b = chatgpt_annotation_yyds(task_context, instances_b)
                        reply = reply_a + reply_b

                topic_res.append(reply)
                
                if (batch_idx + 1) % 10 == 0:
                    with open(answer_path, "w") as fout:
                        answer_res[topic] = topic_res
                        json.dump(answer_res, fout, indent=4)
            with open(answer_path, "w") as fout:
                answer_res[topic] = topic_res
                json.dump(answer_res, fout, indent=4)
        break

        
