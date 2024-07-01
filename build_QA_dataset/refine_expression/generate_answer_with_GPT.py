import argparse
import math
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
# }'
BATCH_SIZE = 20
model = "WEIGHTS/Mixtral-8x7B-Instruct-v0.1/"


task_definition = "You are a chemistry research assistant, and I need you to complete the following task: You will be given a detailed description of a molecule's {} and a question about the molecule's {}, please extract specific information from the given descrption to answer the question. Your answer should just involve the answer for the question without unralated information."
url_ls = [
    "http://192.168.0.0:800/v1/chat/completions",
    "http://102.168.0.0:800/v1/chat/completions",
    "http://102.168.0.0:800/v1/chat/completions",
    "http://102.168.0.0:800/v1/chat/completions",
    "http://102.168.0.0:800/v1/chat/completions",

    "http://192.168.0.0:800/v1/chat/completions",
    "http://192.168.0.0:800/v1/chat/completions",
    "http://192.168.0.0:800/v1/chat/completions",
    "http://192.168.0.0:800/v1/chat/completions",
    "http://192.168.0.0:800/v1/chat/completions",
    "http://192.168.0.0:800/v1/chat/completions",
    "http://192.168.0.0:800/v1/chat/completions",
    "http://192.168.0.0:800/v1/chat/completions",
]
# task_definition = "You are a chemistry research assistant, and I need you to complete the following task: You will be given a detailed description of a molecule, a question about this molecule and the answer for this question, please identify whether the answer is appropriate for the question, select your CHOICE from [yes, no]."

rules_prefix = "Notice that here are some rules you need to follow:\n"

example_prefix = "Here are several examples to show how to answer the given questions based on descriptions about a molecule:\n"
# example_prefix = "Here are several examples to show several kinds of mismatched quesiont-answer pairs to help you finish this task:\n"

instance_prefix = "Here comes several task instances for you to complete: \n"
instance_suffix = "Please give me your ANSWERs for these instances in above examples' styles. No other information is required."
# instance_suffix = "Just give me your CHOICE from [yes, no], no other information is needed."


def add_example_prompt(origin_prompt, examples):
    formatted_examples = ""
    for exp_idx, example in enumerate(examples):
        cid, desc, ques, answer = example
        if not ques.endswith("?"):
            ques += "?"
        formatted_examples += f"Example {exp_idx + 1}:\nDESCRIPTION: {desc}\nQUESTION: {ques}\nANSWER {exp_idx + 1}: {answer}\n\n"
    return origin_prompt + example_prefix + formatted_examples

def add_rules_prompt(origin_prompt, rules):
    formatted_notice = ""
    for rule_idx, rule in enumerate(rules):
        formatted_notice += f"Notice {rule_idx + 1}:\n{rule}\n\n"
    return origin_prompt + rules_prefix + formatted_notice

def add_instance(origin_prompt, instances):
    formatted_instance = origin_prompt
    for idx, instance in enumerate(instances):
        cid, desc, ques, answer = instance
        if not ques.endswith("?"):
            ques += "?"
        formatted_instance += f"Instance {idx + 1}:\nDESCRIPTION: {desc}\nQUESTION: {ques}\n"
    return instance_prefix + formatted_instance + instance_suffix.format(ques)

def load_no_dup_instances(desc_cls): # fine_grained_CLS version.
    sub_dir="../../fine_grained_CLS/build_QA_pairs"
    prefix="cls_desc_QA_pairs"
    QA_path = os.path.join(sub_dir, desc_cls)
    file_ls = os.listdir(QA_path)
    file_ls.sort()
    All_QA_pairs = {}
    for file_name in tqdm(file_ls):
        if not file_name.startswith(prefix):
            continue
        with open(os.path.join(QA_path.format(desc_cls), file_name), "r") as f:
            QA_pairs = json.load(f)
            for topic in QA_pairs.keys():
                All_QA_pairs[topic] = QA_pairs[topic]
    with open(f"../build_QA_pairs/no_dup_QA_pairs_{desc_cls}.json", "w") as f:
        json.dump(All_QA_pairs, f, indent=4)

def load_judegement(desc_cls, sub_dir = "", prefix="cls_res"):
    judgement_path = f"./{desc_cls}/{sub_dir}"
    file_ls = os.listdir(judgement_path)
    file_ls.sort()
    judgements = {}
    for file_name in tqdm(file_ls):
        if not file_name.startswith(prefix):
            continue
        with open(os.path.join(judgement_path, file_name), "r") as f:
            judgement = json.load(f)
            for topic in judgement.keys():
                judgements[topic] = judgement[topic]
    return judgements

def open_book_QA(example_path = "./examples_sup.json", cls_ls = ["Property", "Usage"], prefix = "QA_pairs", output_prefix = "gpt_answer"):
    # load examples
    with open(example_path, "r") as fin:
        examples = json.load(fin)
    rules = [
        # "If phrases or sentences from original descriptions can perfectly answer the question, no need to overwrite them.",
        "For my convenience, please give me a list of ANSWERs for the given instances, without any other information.",
        'If there is no infomation to answer the given question in the description, please just return "Not specified."',
        'Please use "it" to indicate the molecule in your answer.',
        "Information not related to the question is preferred to be removed."
    ]

    for desc_cls in cls_ls:
        original_prompt = task_definition.format(desc_cls, desc_cls)
        task_context = add_example_prompt(original_prompt, examples[desc_cls])
        task_context = add_rules_prompt(task_context, rules)
        # print(task_context)
        answer_path = f"./{desc_cls}"
        if not os.path.exists(answer_path):
            os.mkdir(answer_path)
        with open(f"../build_QA_pairs/{prefix}_{desc_cls}.json", "r") as fin:
            QA_pairs = json.load(fin)
        answer_res = {}
        if os.path.exists(f"{answer_path}/{output_prefix}_{desc_cls}.json"):
            with open(f"{answer_path}/{output_prefix}_{desc_cls}.json", "r") as fin:
                answer_res = json.load(fin)
        for topic_idx, topic in enumerate(QA_pairs.keys()):
            if topic in answer_res.keys():
                continue
            print(topic)
            topic_QA_pairs = QA_pairs[topic]
            topic_res = []
            # calculate the num of batch with BATCH_SIZE
            batch_num = math.ceil(len(topic_QA_pairs) / BATCH_SIZE)
            for batch_idx in tqdm(range(batch_num)):
                instances = topic_QA_pairs[batch_idx * BATCH_SIZE: (batch_idx + 1) * BATCH_SIZE]
                instances = add_instance("", instances)
                # print(task_context)
                # print(instances)
                if "gpt" in output_prefix:
                    reply = chatgpt_annotation_yyds(task_context, instances)
                else:
                    assert "mixtual" in output_prefix
                    reply = get_responce_from_api(task_context, instances, 0)
                topic_res.append(reply)
                # print(reply)
            #     break
            # break
            answer_res[topic] = topic_res
            with open(f"{answer_path}/{output_prefix}_{desc_cls}.json", "w") as f:
                json.dump(answer_res, f, indent=4)
            # break


openai_api_key = 'sk-'

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
    )
    reply = response.choices[0].message.content
    return reply


def get_responce_from_api(task_context, instance, url_idx):
    # print(sample)

    headers = {
        'content-type': 'application/json',
    }
    url = url_ls[url_idx]
    for t in [0.1]:
        # print(f"Current temperature: {t}")
        # for i in range(1):
        data = {
            "model": model,     
            "temperature": t,
            "messages": [
                # {
                #     "role": "system", 
                #     "content": task_context
                # },
                {
                "role": "user", 
                "content": task_context + instance
                }
            ],
            "max_tokens": 2048
        }
        # print(prompt + example + instance)
        # print(json.dumps(data))
        while True:
            try:
                response = requests.post(url, headers=headers, data=json.dumps(data), timeout=100)
            except requests.exceptions.ReadTimeout:
                return -1
            # print(response)
            content = json.loads(response.content.decode('utf-8'))
            # print(content)
            # print(content)
            try:
                return content["choices"][0]["message"]["content"]
            except KeyError:
                return -2

def statistic():
    for desc_cls in ["Usage", "Property", "Structure"]:
        file_ls = os.listdir(f"./{desc_cls}/vicuna")
        judgement_file_ls = []
        total_num = 0
        correct_num = 0
        illegal_ls = []
        for fname in file_ls:
            if not fname.startswith("cls_res"):
                continue
            judgement_file_ls.append(fname)
        for fname in judgement_file_ls:
            with open(f"./{desc_cls}/vicuna/{fname}", "r") as f:
                cls_res = json.load(f)
            for topic in cls_res.keys():
                topic_res = cls_res[topic]
                for res in topic_res:
                    if ":" in res:
                        res = res.split(":")[1]
                    res = res.strip()
                    res = res.lower()
                    if not res in ["yes", "no"]:
                        illegal_ls.append(res)
                        continue
                    total_num += 1
                    if res == "yes":
                        correct_num += 1
        print(f"Total number of {desc_cls}: {correct_num}/{total_num}")
        print(f"Illegal number of {desc_cls}: {len(illegal_ls)}")
                        
def seperate_gpt_answers(answer_dir):
    with open(answer_dir, "r") as f:
        gpt_res = json.load(f)
    # lower
    to_remove = ["instance", "answer", "question", "description"]
    seperated_answer = {}
    for topic in gpt_res:
        seperated_answer[topic] = []
        batch_answers = gpt_res[topic]
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
            seperated_answer[topic].append(cleaned_answers)
    with open(answer_dir.replace("_answer", "_answer_seperated"), "w") as f:
        json.dump(seperated_answer, f, indent=4)
        

def merge_answer(desc_cls, prefix, answer_path):

    not_matched_batch = {}
    not_matched_num = 0
    with open(answer_path, "r") as fin:
        seperated_answers = json.load(fin)
    merged_instances = {}
    with open(f"../build_QA_pairs/{prefix}_{desc_cls}.json", "r") as fin:
        QA_pairs = json.load(fin)
    QA_pair_num = 0
    for topic_idx, topic in enumerate(QA_pairs.keys()):
        merged_instances[topic] = []
        assert topic in seperated_answers.keys()
        topic_answers = seperated_answers[topic]
        # print(topic)
        topic_QA_pairs = QA_pairs[topic]
        # calculate the num of batch with BATCH_SIZE
        batch_num = math.ceil(len(topic_QA_pairs) / BATCH_SIZE)
        for batch_idx in range(batch_num):
            instances = topic_QA_pairs[batch_idx * BATCH_SIZE: (batch_idx + 1) * BATCH_SIZE]
            answers = topic_answers[batch_idx]
            if not len(instances) == len(answers):
                print(f"Not matched!:{len(instances)}/{len(answers)}")
                if topic not in not_matched_batch.keys():
                    not_matched_batch[topic] = []
                not_matched_batch[topic].append([batch_idx, instances, answers])
                not_matched_num += 1
            else:
                for idx, instance in enumerate(instances):
                    instance.append(answers[idx])
                    merged_instances[topic].append(instance)
                    QA_pair_num += 1
    with open(answer_path.replace("seperated", "merged"), "w") as f:
        json.dump(merged_instances, f, indent=4)
    print(f"Number of not matched batch: {not_matched_num}")
    with open(answer_path.replace("seperated", "not_match"), "w") as f:
        json.dump(not_matched_batch, f, indent=4)
    print(f"Number of matched QA pairs: {QA_pair_num}")

# "Please identify which of the following sources this molecule can be isolated from: ",      
      

def merge_easy():
    path1 = "./Chebi_Sup/refine_expression/Source/gpt_answer_merged_Source.json"
    path2 = "./Chebi_Sup/build_QA_pairs/QA_pairs_Source_easy.json"

    with open(path1, "r") as f:
        gpt_res = json.load(f)
    with open(path2, "r") as f:
        easy_res = json.load(f)
    for topic in easy_res.keys():
        for instance in easy_res[topic]:
            instance.append(instance[-1])
            gpt_res[topic].append(instance)
        # gpt_res[topic] = easy_res[topic]
    
    with open(path1.replace("merged", "merged_easy"), "w") as f:
        json.dump(gpt_res, f, indent=4)



if __name__ == "__main__":
    # open_book_QA()
    # with open("./examples_no_dup.json", "w") as f:
    #     json.dump(examples, f, indent=4)
    # for desc_cls in ["Usage", "Property", "Structure"]:
    #     load_no_dup_instances(desc_cls)

# def open_book_QA(example_path = "./examples_sup.json", cls_ls = ["Property", "Usage"], prefix = "QA_pairs", output_prefix = "gpt_answer"):
    # open_book_QA(example_path="./examples_no_dup.json", cls_ls=["Source"], prefix="QA_pairs", output_prefix="gpt_answer")
    # for prefix in ["gpt_answer"]:
    #     for desc_cls in ["Source"]:# ["Usage", "Property", "Structure"]:
    #         seperate_gpt_answers(f"./{desc_cls}/{prefix}_{desc_cls}.json")

    # for desc_cls in ["Source"]:
    #     merge_answer(desc_cls, "QA_pairs", f"./{desc_cls}/gpt_answer_seperated_{desc_cls}.json")
    merge_easy()


# "\nInstance 1:\nANSWER: It is a cell-cycle phase nonspecific alkylating antineoplastic agent.\n\nInstance 2:\nANSWER: Its pharmacological activity occurs as a result of formation of methylcarbonium ions, which alkylate or bind with many intracellular molecular structures including nucleic acids.\n\nInstance 3:\nANSWER: It binds to the dopamine D1 and dopamine D2 receptors and inhibits their activity.\n\nInstance 4:\nANSWER: It was initially characterized as a potential broad-spectrum antineoplastic agent, with activity toward diverse solid and hematopoietic tumors.\n\nInstance 5:\nANSWER: It is a potent and selective oral mitogen-activated protein kinase 1/2 (MEK 1/2) inhibitor.\n\nInstance 6:\nANSWER: It is a competitive kinase inhibitor with activity against BRAF kinase with mutations like V600E.\n\nInstance 7:\nANSWER: It is a commonly used antimicrobial due to its good activity against multi-drug resistant Enterobacteriaceae, its relatively safe adverse effect profile, and its long half-life which allows for the convenience of daily or twice-daily dosing.\n\nInstance 8:\nANSWER: Its activity against the Coronaviridae family was first demonstrated in 2017, leading to considerable interest in it as a possible treatment for COVID-19.\n\nInstance 9:\nANSWER: A low activity was seen during ontogenesis, and a slow and progressive enhancement occurs during maturation and ageing.\n\nInstance 10:\nDESCRIPTION: This molecule is a potent and selective inhibitor of the Janus kinase (JAK) family, which includes JAK1, JAK2, JAK3, and TYK2\nQUESTION: How is the pharmacological activity of this molecule\nANSWER 10: It is a potent and selective inhibitor of the Janus kinase (JAK) family, which includes JAK1, JAK2, JAK3, and TYK2.\n\nInstance 11:\nDESCRIPTION: This molecule is a potent and selective inhibitor of the PI3K/mTOR pathway\nQUESTION: How is the pharmacological activity of this molecule\nANSWER 11: It is a potent and selective inhibitor of the PI3K/mTOR pathway.\n\nInstance 12:\nDESCRIPTION: This molecule is a potent and selective inhibitor of the Hedgehog pathway\nQUESTION: How is the pharmacological activity of this molecule\nANSWER 12: It is a potent and selective inhibitor of the Hedgehog pathway.\n\nInstance 13:\nDESCRIPTION: This molecule is a potent and selective inhibitor of the Notch pathway\nQUESTION: How is the pharmacological activity of this molecule\nANSWER 13: It is a potent and selective inhibitor of the Notch pathway.\n\nInstance 14:\nDESCRIPTION: This molecule is a potent and selective inhibitor of the Wnt/\u03b2-catenin pathway\nQUESTION: How is the pharmacological activity of this molecule\nANSWER 14: It is a potent and selective inhibitor of the Wnt/\u03b2-catenin pathway.\n\nInstance 15:\nDESCRIPTION: This molecule is a potent and selective inhibitor of the NF-\u03baB pathway\nQUESTION: How is the pharmacological activity of this molecule\nANSWER 15: It is a potent and selective inhibitor of the NF-\u03baB pathway.\n\nInstance 16:\nDESCRIPTION: This molecule is a potent and selective inhibitor of the HIF-1\u03b1 pathway\nQUESTION: How is the pharmacological activity of this molecule\nANSWER 16: It is a potent and selective inhibitor of the HIF-1\u03b1 pathway.\n\nInstance 17:\nDESCRIPTION: This molecule is a potent and selective inhibitor of the Akt pathway\nQUESTION: How is the pharmacological activity of this molecule\nANSWER 17: It is a potent and selective inhibitor of the Akt pathway.\n\nInstance 18:\nDESCRIPTION: This molecule is a potent and selective inhibitor of the ERK pathway\nQUESTION: How is the pharmacological activity of this molecule\nANSWER 18: It is a potent and selective inhibitor of the ERK pathway.\n\nInstance 19:\nDESCRIPTION: This molecule is a potent and selective inhibitor of the JNK pathway\nQUESTION: How is the pharmacological activity of this molecule\nANSWER 19: It is a potent and selective inhibitor of the JNK pathway.\n\nInstance 20:\nDESCRIPTION: This molecule is a potent and selective inhibitor of the p38 MAPK pathway\nQUESTION: How is the pharmacological activity of this molecule\nANSWER 20: It is a potent and selective inhibitor of the p38 MAPK pathway.\n\nInstance 21:\nDESCRIPTION: This molecule is a potent and selective inhibitor of the GSK-3\u03b2 pathway\nQUESTION: How is the pharmacological activity of this molecule\nANSWER 21: It is a potent and selective inhibitor of the GSK-3\u03b2 pathway.\n\nInstance 22:\nDESCRIPTION: This molecule is a potent and selective inhibitor of the CDK4/6 pathway\nQUESTION: How is the pharmacological activity of this molecule\nANSWER 22: It is a potent and selective inhibitor of the CDK4/6 pathway.\n\nInstance 23:\nDESCRIPTION: This molecule is a potent and selective inhibitor of the Aurora A/B pathway\nQUESTION: How is the pharmacological activity of this molecule\nANSWER 23: It is a potent and selective inhibitor of the Aurora A/B pathway.\n\nInstance 24:\nDESCRIPTION: This molecule is a potent and selective inhibitor of the PLK1 pathway\nQUESTION: How is the pharmacological activity of this molecule\nANSWER 24: It is a potent and selective inhibitor of the PLK1 pathway.\n\nInstance 25:\nDESCRIPTION: This molecule is a potent and selective inhibitor of the Bcl-2 family\nQUESTION: How is the pharmacological activity of this molecule\nANSWER 25: It is a potent and selective inhibitor of the Bcl-2 family.\n\nInstance 26:\nDESCRIPTION: This molecule is a potent and selective inhibitor of the HSP90 pathway\nQUESTION: How is the pharmacological activity of this molecule\nANSWER 26: It is a potent and selective inhibitor of the HSP90 pathway.\n\nInstance 27:\nDESCRIPTION: This molecule is a potent and selective inhibitor of the HDAC pathway\nQUESTION: How is the pharmacological activity of this molecule\nANSWER 27: It is a potent and selective inhibitor of the HDAC pathway.\n\nInstance 28:\nDESCRIPTION: This molecule is a potent and selective inhibitor of the PARP pathway\nQUESTION: How is the pharmacological activity of this molecule\nANSWER 28: It is a potent and selective inhibitor of the PARP pathway.\n\nInstance 29:\nDESCRIPTION: This molecule is a potent and selective inhibitor of the Topoisomerase I pathway\nQUESTION: How is the pharmacological activity of this molecule\nANSWER 29: It is a potent and selective inhibitor of the Topoisomerase I pathway.\n\nInstance 30:\nDESCRIPTION: This molecule is a potent and selective inhibitor of the Topoisomerase II pathway\nQUESTION: How is the pharmacological activity of this molecule\nANSWER 30: It is a potent and selective inhibitor of the Topoisomerase II pathway.\n\nInstance 31:\nDESCRIPTION: This molecule is a potent and selective inhibitor of the VEGF pathway\nQUESTION: How is the pharmacological activity of this molecule\nANSWER 31"
