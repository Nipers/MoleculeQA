import argparse
import math
import random
from socket import timeout
import time
import json
import os
from nh3 import clean
from tqdm import tqdm
import openai
# from openai import OpenAI
import requests
# openai pip install openai==0.28`
# openai 1.2.0
openai.api_base = 'https://ai.com/v1'
from openai.error import APIError, APIConnectionError



BATCH_SIZE = 40

task_definition = "You are a chemistry research assistant, and I need you to complete the following task: You will be given a detailed description of a molecule's structure information and a question about the molecule, please extract specific information from the given descrption to answer the question. Your answer should just involve the answer for the question without unralated information."


rules_prefix = "Notice that here are some rules you need to follow:\n"

example_prefix = "Here are several examples to show how to answer the given question based on descriptions about a molecule:\n"
# example_prefix = "Here are several examples to show several kinds of mismatched quesiont-answer pairs to help you finish this task:\n"

instance_prefix = "Here comes several task instances about the QUESTION {} for you to complete: \n"
instance_suffix = "Please give me your ANSWERs for these instances in above examples' styles. No other information is required."
# instance_suffix = "Just give me your CHOICE from [yes, no], no other information is needed."

rules = [
    # "If phrases or sentences from original descriptions can perfectly answer the QUESTION, no need to overwrite them.",
    "For my convenience, please give me a list of ANSWERs for the given QUESTION, without any other unrelated information.",
    'If you are sure that there is no infomation to answer the given QUESTION in the description, please just return "Not specified.", ',
    'Please use "It" to indicate the molecule in your answer.',
]

def add_example_prompt(origin_prompt, examples):
    question, descs, answers = examples
    if not question.endswith("?"):
        question += "?"
    formatted_examples = "\nHere is the QUESTION you need to answer: " + question + "\n"
    formatted_examples += example_prefix
    for exp_idx, (desc, answer) in enumerate(zip(descs, answers)):
        formatted_examples += f"DESCRIPTION {exp_idx + 1}: {desc}\nANSWER {exp_idx + 1}: {answer}\n\n"
    return origin_prompt + formatted_examples

def add_rules_prompt(origin_prompt, rules):
    formatted_notice = ""
    for rule_idx, rule in enumerate(rules):
        formatted_notice += f"Notice {rule_idx + 1}:\n{rule}\n\n"
    return origin_prompt + rules_prefix + formatted_notice

def add_instance(origin_prompt, instances):
    question, descs = instances
    if not question.endswith("?"):
        question += "?"
    formatted_instance = origin_prompt
    for idx, desc in enumerate(descs):
        cid, desc = desc
        formatted_instance += f"DESCRIPTION {idx + 1}: {desc}\n"
    return instance_prefix.format(question) + formatted_instance + instance_suffix


def prepare_base_instances():
    file_path = "./Chebi_Sup/refine_expression/Structure/no_dup_gpt_answer_merged_Structure.json"
    with open(file_path, 'r') as f:
        instances = json.load(f)
    instances = instances["base"]
    for idx in range(len(instances)):
        instances[idx] = instances[idx][:2]

    removed_instances = {
        "conjugate acid of": [],
        "enantiomer of": [],
        "conjugate base of": [],
        "tautomer of": []
    }

    illegal_words = [
        "that is",
        "in which",
        "obtained by",
        "formed by",
        "resulting from",
        "arising from",
        "that has",
        "having",
        "obtained"
    ]

    clean_instances = []
    for instance in instances:
        cid, origin_desc = instance
        descriptions = origin_desc.split(". ")
        clean_descriptions = []
        for description in descriptions:
            if any([description.find(keyword) != -1 for keyword in removed_instances.keys()]) and not any([illegal_word in description for illegal_word in illegal_words]):
                for keyword in removed_instances:
                    if keyword in description:
                        # print(description)
                        if not description.endswith("."):
                            description += "."
                        removed_instances[keyword].append([cid, description])
                continue
            clean_descriptions.append(description)
        if len(clean_descriptions) == 0:
            continue
        clean_instances.append([cid, ". ".join(clean_descriptions)])

    with open("./base_clean_instances.json", 'w') as f:
        json.dump(clean_instances, f, indent=4)
    with open("./base_removed_instances.json", 'w') as f:
        json.dump(removed_instances, f, indent=4)

def chatgpt_annotation_yyds(task_context:str, instance:list):
    openai.api_key = 'sk-'
    openai.api_base = 'https://ai.com/v1'
    messages = [ {"role": "system", "content": task_context}]
    messages.append({"role": "user", "content": instance})

    response = openai.ChatCompletion.create(
        model='gpt-3.5-turbo-1106',
        messages=messages,
        max_tokens=2048,
        temperature=0,
        top_p=0.01,
        seed=42,
        timeout=120
    )
    reply = response.choices[0].message.content
    return reply

def generate_answer_with_gpt():
    with open("./base_clean_instances.json", "r") as fin:
        base_instances = json.load(fin)
    
    with open("./example_base.json", "r") as fin:
        examples = json.load(fin)
    if os.path.exists("./base_reply.json"):
        with open("./base_reply.json", "r") as fin:
            base_replys = json.load(fin)
    else:
        base_replys = {}
    batch_num = math.ceil(len(base_instances) / BATCH_SIZE)
    print(f"total batch: {batch_num}")
    for question in examples:
        if question in base_replys:
            start_idx = len(base_replys[question])
        else:
            base_replys[question] = []
            start_idx = 0
        ques_examples = examples[question]
        original_prompt = task_definition
        task_context = add_example_prompt(original_prompt, [question] + ques_examples)
        task_context = add_rules_prompt(task_context, rules)
        # print(task_context)
        for batch_idx in tqdm(range(start_idx, batch_num)):
            batch_instances = base_instances[batch_idx * BATCH_SIZE: batch_idx * BATCH_SIZE + BATCH_SIZE]
            instances = add_instance("", [question, batch_instances])
            # print(instances)
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
            # print(reply)
            base_replys[question].append(reply)
            if (batch_idx + 1) % 10 == 0:
                with open("./base_reply.json", "w") as fout:
                    json.dump(base_replys, fout, indent=4)

            # break
        # break
    with open("./base_reply.json", "w") as fout:
        json.dump(base_replys, fout, indent=4)
            
def seperate_gpt_answers(answer_dir):
    with open(answer_dir, "r") as f:
        gpt_res = json.load(f)
    # lower
    to_remove = ["instance", "answer", "question", "description"]
    seperated_answer = {}
    for question in gpt_res:
        seperated_answer[question] = []
        batch_answers = gpt_res[question]
        for batch_answer in batch_answers:
            # split gpt's output into answers for single instances
            # case 1: "Instance 1:\nANSWER 1: It is a nonselective beta adrenergic receptor blocker.\n\nInstance 2:\nANSWER 2: It is a blocker of both alpha- and beta-adrenergic receptors.\n\nInstance 3:\nANSWER 3: It is a potassium channel blocker.\n\nInstance 4:\nANSWER 4: It is a serotonin antagonist and a histamine H1 blocker."
            # case 2: "1. Serotonin-1b and Serotonin-1d Receptor Agonist\nANSWER: It is a Serotonin-1b and Serotonin-1d Receptor Agonist.\n2. Opioid Agonist\nANSWER: It is an Opioid Agonist.\n3. GABA receptors Agonist\nANSWER: Not specified.\n4. Opioid Agonist\nANSWER: It is an Opioid Agonist.\n5. Opioid Agonist\nANSWER: It is an Opioid Agonist."
            # case 3: "1. It is a tetracycline antibiotic.\n2. It is a nitrofuran antibiotic.\n3. It is a second generation penicillinase-resistant penicillin antibiotic.\n4. It is an aminoglycoside bacteriocidal antibiotic.\n5. It is a broad spectrum antibiotic.\n6. It is a tuberactinomycin antibiotic.\n7. It is a third-generation cephalosporin antibiotic.\n8. It is a second generation cephalosporin antibiotic.\n9. It is a bacteriostatic macrolide antibiotic.\n10. It is a broad spectrum antibiotic of the sulfonamides drug class.\n11. It is a synthetic chemotherapeutic antibiotic of the fluoroquinolone drug class.\n12. It is a third-generation cephalosporin antibiotic.\n13. It is a third-generation antiobiotic agent.\n14. It is an anthracycline antibiotic.\n15. It is a broad spectrum aminoglycoside antibiotic.\n16. It is a fluoroquinolone antibiotic.\n17. It is a broad spectrum antibiotic.\n18. It is a bacteriostatic sulfonamide antibiotic.\n19. It is a broad spectrum antibiotic.\n20. It is a first-generation cephalosporin antibiotic."
            # "Instance 1: It is a transparent, odorless diatomic gas.\nAnswer 1: Gas\n\nInstance 2: This molecule is an odorless white to faint yellow crystalline powder.\nAnswer 2: Solid\n\nInstance 3: This molecule is a colorless liquid with a fruity odor.\nAnswer 3: Liquid\n\nInstance 4: This molecule is a colorless gas.\nAnswer 4: Gas\n\nInstance 5: This molecule is a clear light yellow liquid.\nAnswer 5: Liquid\n\nInstance 6: This molecule appears as a clear colorless volatile liquid having an ether-like odor.\nAnswer 6: Liquid\n\nInstance 7: This molecule appears as a colorless odorless very cold liquid.\nAnswer 7: Liquid\n\nInstance 8: This molecule is a colorless to dark brown liquid.\nAnswer 8: Liquid\n\nInstance 9: This molecule appears as colorless yellowish or reddish liquid with odor of wintergreen.\nAnswer 9: Liquid\n\nInstance 10: This molecule appears as colorless liquid with a mild pleasant odor.\nAnswer 10: Liquid\n\nInstance 11: This colorless, odorless, and hygroscopic crystalline solid is highly soluble in water.\nAnswer 11: Solid\n\nInstance 12: It is a colourless liquid with a chloroform-like odour.\nAnswer 12: Liquid\n\nInstance 13: This molecule appears as a yellow to brown colored oily liquid with a fishlike odor.\nAnswer 13: Liquid\n\nInstance 14: It is a liquid when under pressure, and it dissolves in water very easily.\nAnswer 14: Liquid\n\nInstance 15: This molecule is a colorless thick liquid with a sweet odor.\nAnswer 15: Liquid\n\nInstance 16: This molecule appears as a white crystalline or granular solid with a slight odor.\nAnswer 16: Solid\n\nInstance 17: This molecule appears as colorless leaflets or plates or coarse gold powder with a greenish-yellow fluorescence.\nAnswer 17: Solid\n\nInstance 18: Vapors heavier than air.\nAnswer 18: Not specified\n\nInstance 19: This molecule is a solid.\nAnswer 19: Solid\n\nInstance 20: This molecule appears as a clear colorless liquid with a mustard-like odor.\nAnswer 20: Liquid"
            splited_answers = batch_answer.split("\n")
            # remove ""
            splited_answers = [answer for answer in splited_answers if answer != ""]
            # remove "Instance 1:"
            cleaned_answers = []
            for answer in splited_answers:
                remove = False
                for to_remove_str in to_remove:
                    if to_remove_str in answer.lower() and len(answer) <= len(to_remove_str) + 4 :
                        remove = True
                        break
                if not remove:
                    cleaned_answers.append(answer)
            all_removed = False
            while not all_removed:
                all_removed = True
                for idx in range(len(cleaned_answers)):
                    for to_remove_str in to_remove:
                        if cleaned_answers[idx].lower().startswith(to_remove_str):
                            all_removed = False
                            cleaned_answers[idx] = cleaned_answers[idx][len(to_remove_str):].strip()
                            if cleaned_answers[idx].startswith(":"):
                                cleaned_answers[idx] = cleaned_answers[idx][1:].strip()
            if len(cleaned_answers) > 1:
                if cleaned_answers[0][:3] == cleaned_answers[1][:3] and cleaned_answers[0][0] == "1":
                    # only remain answer in the even position
                    cleaned_answers = cleaned_answers[1::2]
            
            if cleaned_answers[0].startswith("1:") or cleaned_answers[0].startswith("1."):
                for idx, answer in enumerate(cleaned_answers):
                    if answer.startswith(f"{idx + 1}. ") or answer.startswith(f"{idx + 1}: "):
                        cleaned_answers[idx] = answer[len(f"{idx + 1}. "):]
            all_removed = False
            while not all_removed:
                all_removed = True
                for idx in range(len(cleaned_answers)):
                    for to_remove_str in to_remove:
                        if cleaned_answers[idx].lower().startswith(to_remove_str):
                            all_removed = False
                            cleaned_answers[idx] = cleaned_answers[idx][len(to_remove_str):].strip()
                            if cleaned_answers[idx].startswith(":"):
                                cleaned_answers[idx] = cleaned_answers[idx][1:].strip()
            # if topic == "physical state" and len(cleaned_answers) < 20:
            #     print(batch_answers)
            # remove too short answers
            # cleaned_answers = [answer for answer in cleaned_answers if len(answer) > 5]
            seperated_answer[question].append(cleaned_answers)
    with open(answer_dir.replace("_reply", "_reply_seperated"), "w") as f:
        json.dump(seperated_answer, f, indent=4)

illegal_keywords = {
    "What components does this molecule have?" :[
        "derived from",
        "obtained by",
        "derives from",
        "resulting from",
        "results from",
        "formed by"
    ],
    "What is the chemical process/reaction of this molecule's formation?":[
        "comprising",
        "consisting",
        "composed",
        "consists",
        "comprises",
        "contains",
        "containing",
        "linked",
        "carries",
        "having",
        "has",
        "in which"
    ]
}
legal_keywords = {
    "What components does this molecule have?": [
        "in which",
        "bearing",
        "comprising",
        "consisting",
        "composed",
        "consists",
        "comprises",
        "contains",
        "containing",
        "linked",
        "substituent",
        "carries",
        "having",
        "has",
        "constructed",
        "group",
    ],
    "What is the chemical process/reaction of this molecule's formation?":[
        "protonation",
        "condensation",
        "obtained by",
        "reduction",
        "resulting from",
        "results from",
        "combination",
        "substitute"
    ]
}



def merge_base_reply():
    cid2num = {}
    with open("./base_reply_seperated.json", "r") as fin:
        seperated_answer = json.load(fin)
    with open("./base_clean_instances.json", "r") as fin:
        base_instances = json.load(fin)
    
    with open("./example_base.json", "r") as fin:
        examples = json.load(fin)
    merged_instances = {
        "base": []
    }
    removed_instances = {
        "base": []
    }
    illegal_instances = {

    }
    ques2cid = []
    saved_num = 0
    removed_num = 0
    illegal_num = 0
    print("QA_pair num: ", len(base_instances) * 3)
    batch_num = math.ceil(len(base_instances) / BATCH_SIZE)
    for question in examples:
        print(question)
        illegal_instances[question] = []
        quesion_reply = seperated_answer[question]
        assert len(quesion_reply) == batch_num
        for batch_idx in range(batch_num):
            batch_instances = base_instances[batch_idx * BATCH_SIZE: batch_idx * BATCH_SIZE + BATCH_SIZE]
            batch_reply = quesion_reply[batch_idx]
            if not len(batch_reply) == len(batch_instances):
                print(f"batch_idx: {batch_idx}, batch_reply: {len(batch_reply)}, batch_instances: {len(batch_instances)}")
                continue
            for idx, instance in enumerate(batch_instances):
                cid, desc = instance
                if not cid in cid2num:
                    cid2num[cid] = 0
                answer = batch_reply[idx]
                if question == "What components does this molecule have?":
                    if answer.startswith("It is"):
                        answer = answer[5:].strip()
                    # Change the start  into Capital
                    if answer[0].islower():
                        answer = answer[0].upper() + answer[1:]
                    if cid in ques2cid:
                        illegal_instances[question].append([cid, desc, question, answer])
                        continue
                if not "not specified" in batch_reply[idx].lower() and cid2num[cid] < 2:
                    # check if the answer contains illegal keywords
                    illegal = False
                    legal = False
                    if question in illegal_keywords:
                        for keyword in illegal_keywords[question]:
                            if keyword in answer:
                                illegal_instances[question].append([cid, desc, question, answer])
                                illegal_num += 1
                                illegal = True
                                break
                    else:
                        illegal = False
                    if question in legal_keywords:
                        for keyword in legal_keywords[question]:
                            if keyword in answer:
                                legal = True
                                break
                    else:
                        legal = True
                    if not illegal and legal:
                        merged_instances["base"].append([cid, desc, question, "base", answer])
                        cid2num[cid] += 1
                        if question == "What is the chemical process/reaction of this molecule's formation?":
                            ques2cid.append(cid)
                        saved_num += 1
                    if not legal:
                        illegal_instances[question].append([cid, desc, question, "base", answer])
                        illegal_num += 1
                else:
                    removed_instances["base"].append([cid, desc, question, "base"])
                    removed_num += 1
    with open("./gpt_answer_merged_base.json", "w") as f:
        json.dump(merged_instances, f, indent=4)
    with open("./gpt_answer_removed_base.json", "w") as f:
        json.dump(removed_instances, f, indent=4)
    
    with open("./gpt_answer_illegal_base.json", "w") as f:
        json.dump(illegal_instances, f, indent=4)

    print(f"saved: {saved_num}, illegal: {illegal_num}, removed: {removed_num}")


def replace_base():
    original_structure_instances_path = "./Chebi_Sup/refine_expression/Structure/no_dup_gpt_answer_merged_Structure.json"
    with open(original_structure_instances_path, "r") as f:
        original_structure_instances = json.load(f)
    with open("./gpt_answer_merged_base.json", "r") as f:
        gpt_answer_merged_base = json.load(f)
    
    random.shuffle(gpt_answer_merged_base["base"])
    original_structure_instances["base"] = gpt_answer_merged_base["base"][:len(original_structure_instances["base"])]

    with open("./base_replaced_Structure_instances.json", "w") as f:
        json.dump(original_structure_instances, f, indent=4)
    
    
    

if __name__ == "__main__":
    # prepare_base_instances()
    # pass
    # generate_answer_with_gpt()
    # seperate_gpt_answers("./base_reply.json")
    # merge_base_reply()
    replace_base()


# QA_pair num:  48324
# Which kind of compound does this molecule belong to?
# batch_idx: 19, batch_reply: 39, batch_instances: 40
# batch_idx: 65, batch_reply: 39, batch_instances: 40
# batch_idx: 332, batch_reply: 39, batch_instances: 40
# batch_idx: 375, batch_reply: 39, batch_instances: 40
# What is the chemical process/reaction of this molecule's formation?
# batch_idx: 28, batch_reply: 31, batch_instances: 40
# batch_idx: 30, batch_reply: 34, batch_instances: 40
# batch_idx: 74, batch_reply: 9, batch_instances: 40
# batch_idx: 102, batch_reply: 16, batch_instances: 40
# batch_idx: 169, batch_reply: 34, batch_instances: 40
# batch_idx: 186, batch_reply: 27, batch_instances: 40
# batch_idx: 281, batch_reply: 33, batch_instances: 40
# batch_idx: 345, batch_reply: 31, batch_instances: 40
# batch_idx: 386, batch_reply: 34, batch_instances: 40
# batch_idx: 393, batch_reply: 34, batch_instances: 40
# batch_idx: 394, batch_reply: 36, batch_instances: 40
# What components does this molecule have?
# batch_idx: 75, batch_reply: 29, batch_instances: 40
# batch_idx: 78, batch_reply: 38, batch_instances: 40
# batch_idx: 93, batch_reply: 39, batch_instances: 40
# batch_idx: 137, batch_reply: 39, batch_instances: 40
# batch_idx: 144, batch_reply: 39, batch_instances: 40
# batch_idx: 192, batch_reply: 27, batch_instances: 40
# batch_idx: 199, batch_reply: 39, batch_instances: 40
# batch_idx: 215, batch_reply: 36, batch_instances: 40
# batch_idx: 229, batch_reply: 35, batch_instances: 40
# batch_idx: 278, batch_reply: 39, batch_instances: 40
# batch_idx: 292, batch_reply: 8, batch_instances: 40
# batch_idx: 344, batch_reply: 39, batch_instances: 40
# batch_idx: 348, batch_reply: 10, batch_instances: 40
# batch_idx: 354, batch_reply: 34, batch_instances: 40
# batch_idx: 362, batch_reply: 39, batch_instances: 40
# batch_idx: 369, batch_reply: 38, batch_instances: 40
# batch_idx: 372, batch_reply: 39, batch_instances: 40
# batch_idx: 375, batch_reply: 35, batch_instances: 40
# batch_idx: 380, batch_reply: 34, batch_instances: 40
# batch_idx: 384, batch_reply: 37, batch_instances: 40
# batch_idx: 385, batch_reply: 39, batch_instances: 40
# batch_idx: 387, batch_reply: 32, batch_instances: 40
# batch_idx: 390, batch_reply: 39, batch_instances: 40
# batch_idx: 392, batch_reply: 39, batch_instances: 40
# batch_idx: 396, batch_reply: 37, batch_instances: 40
# saved: 37000, removed: 9724