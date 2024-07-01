# This is the program to convert Molecule QA dataset to biot5 style
import csv
import json
import os
import sys


import random
import string

random.seed(42)
split2taskid = {
    "train": 4,
    "validation": 5,
    "test": 6
}
split_method = "_scaffold"
data_source_path = "./sample/similar_options_filtered/final_QA_pairs_{}_reverse_biot5_v3.json"
BIOT5_DATA_PATH = "./DATA/MoleculeQA/BioT5"
MOLT5_DATA_PATH = f"./DATA/MoleculeQA/MolT5"
dataset_suffix = "_reverse_biot5"

cid2simles_path = "./QA/moleculeQA_bak/cid2smile.json"
smiles2selfies_path = "./QA/moleculeQA_bak/smile2selfies.json"

def generate_id():
    n = ''.join(random.sample(string.ascii_letters+string.digits,32))

    # print(n)  #结果是：WIxj4L605dowP9t3g7fbSircqpTOZ2VK

    #然后再将n进行md5加密

    import hashlib

    m = hashlib.md5() #创建Md5对象

    m.update(n.encode('utf-8')) #生成加密串，其中n是要加密的字符串

    result = m.hexdigest() #经过md5加密的字符串赋值
    return result

def add_selfies(instance, selfies):
    return instance + selfies

def add_smiles(instance, smiles):
    return instance + "Molecule SMILES: " + smiles + "\n"

def add_question(instance, question):
    return instance + "Question about this molecule: " + question + "\n"

def add_options(instance, options, choices):
    for option in ["A", "B", "C", "D"]:
        instance += f"Option {option}: {options[choices.index(option)]}\n"
    instance += "Your answer for this question: "
    return instance





def convert_moleculeQA_to_biot5_style(desc_cls, split):
    task_definition = "Please complete the following question answering task: You are given a SELFIES of a molecule and a question about it with several options, please analysis the structure of the molecule and choose the right answer for the question from given options.\n"

    smile2selfies_path = "./smile2selfies.json"
    biot5_template_path = "./biot5_scaffold_reverse_biot5_v2/Property/task4_chebi20_mol2text_train.json"

    split_cid_path = f"./test_with_GPT/{split}_cid.json"
    with open(split_cid_path, 'r') as f:
        cid_sets = json.load(f)
    
    qa_instance_path = data_source_path.format(desc_cls)
    with open(qa_instance_path, 'r') as fin:
        qa_instances = json.load(fin)
    
    with open(cid2simles_path, "r") as fin:
        cid2smiles = json.load(fin)

    with open(smile2selfies_path, "r") as fin:
        smile2selfies = json.load(fin)

    with open(biot5_template_path, 'r') as f:
        biot5_template = json.load(f)
    biot5_template.pop("Instances")
    biot5_template.pop("Contributors")
    biot5_template.pop("URL")
    biot5_template["Instances"] = []
    for key in qa_instances:
        for instance in qa_instances[key]:
            cid, raw_text, question, options, choices = instance
            smile = cid2smiles[cid]
            if cid not in cid_sets:
                continue
            
            if not smile in smile2selfies:
                print(f"{smile} not in smile2selfies")
                continue
            selfies = f"<bom>{smile2selfies[smile]}<eom>"
            instance_input = add_selfies("", selfies)
            instance_input = add_question(instance_input, question)
            instance_input = add_options(instance_input, options, choices)
            instance_output = choices[0]
            instance_id = f"{split2taskid[split]}-" + generate_id()
            instance = {"id": instance_id, "input": instance_input, "output": [instance_output]}
            biot5_template["Instances"].append(instance)
    print(f"{desc_cls} {split} has {len(biot5_template['Instances'])} instances")

    random.shuffle(biot5_template["Instances"])

    if not os.path.exists(f"{BIOT5_DATA_PATH}/{desc_cls}{split_method}{dataset_suffix}"):
        os.makedirs(f"{BIOT5_DATA_PATH}/{desc_cls}{split_method}{dataset_suffix}")
    
    with open(f"{BIOT5_DATA_PATH}/{desc_cls}{split_method}{dataset_suffix}/task{split2taskid[split]}_chebi20_mol2text_{split}.json", 'w') as f:
        json.dump(biot5_template, f, indent=4)


def convert_moleculeQA_to_molt5_style(desc_cls, split):
    # molt5 style: cid, Question, Answer
    task_definition = "Please complete the following question answering task: You are given a SMILES of a molecule and a question about it with several options, please analysis the structure of the molecule and choose the right answer for the question from given options.\n"

    split_cid_path = f"./test_with_GPT/{split}_cid.json"
    with open(split_cid_path, 'r') as f:
        cid_sets = json.load(f)
    qa_instance_path = data_source_path.format(desc_cls)
    with open(qa_instance_path, 'r') as fin:
        qa_instances = json.load(fin)
    
    with open(cid2simles_path, "r") as fin:
        cid2smiles = json.load(fin)

    instance_num = 0
    if not os.path.exists(MOLT5_DATA_PATH):
        os.makedirs(MOLT5_DATA_PATH)
    target_path = f"{MOLT5_DATA_PATH}/{desc_cls}{split_method}{dataset_suffix}"
    if not os.path.exists(target_path):
        os.makedirs(target_path)
    if split == "validation":
        split = "valid"
    
    with open(os.path.join(target_path, f"{split}.txt"), 'w') as f:
        writer = csv.writer(f, delimiter='\t')
        writer.writerow(["CID", "Question", "Answer"])
        rows = []
        for key in qa_instances:
            for instance in qa_instances[key]:
                cid, raw_text, question, options, choices = instance
                smiles = cid2smiles[cid]
                if cid not in cid_sets:
                    continue
                instance_text = add_smiles(task_definition, smiles)
                instance_text = add_question(instance_text, question)
                instance_text = add_options(instance_text, options, choices)
                instance_output = choices[0]
                rows.append([cid, instance_text, instance_output])
                instance_num += 1
        random.shuffle(rows)
        writer.writerows(rows)
    
    print(f"{desc_cls} {split} has {instance_num} instances")
    

        

# {   "id": "4-ce98a69b2fc823de8c1306af7a63a576",
#     "input": "Molecule SELFIES: <bom>[C][C][C@H1][Branch1][C][C][C@H1][Branch1][C][N][C][=Branch1][C][=O][N][C@H1][Branch1][=Branch1][C][=Branch1][C][=O][O][C@@H1][Branch1][C][C][C][C]<eom>\nQuestion about this molecule: Which kind of residue does this molecule have?\nOption A: It has N-(tert-butylcarbamoyl)-3-methyl-L-valyl, cyclopropyl-fused prolyl, 3-amino-4-cyclobutyl-2-oxobutanamide residues.\nOption B: It has Gly, Ile, Gly, Ala, Val, Leu, Lys, Val, Leu, Thr, Thr, Gly, Leu, Pro, Ala, Leu, Ile, Ser, Trp, Ile, Lys, Arg, Lys, Arg, Gln and Gln-NH2 residues joined in sequence.\nOption C: It has L-isoleucine residues.\nOption D: It has 2'-deoxyguanosine units.\nYour answer for this question: ",
#     "output": [
#         "C"
#     ]
# },
# {
#     "id": "4-01b9f61bcaa497dea96c4ab85babc3a4",
#     "input": "Molecule SELFIES: <bom>[C][C@H1][Branch1][C][N][C][=Branch1][C][=O][N][C@@H1][Branch1][#Branch1][C][C][=Branch1][C][=O][O][C][=Branch1][C][=O][O]<eom>\nQuestion about this molecule: Which kind of residue does this molecule have?\nOption A: It has 2-acetamido-2-deox-beta-D-glucoyranosyl, beta-D-mannopyranosyl and 2-acetamido-2-deoxy-D-glucopyranosyl residues.\nOption B: It has N-(tert-butylcarbamoyl)-3-methyl-L-valyl, cyclopropyl-fused prolyl, 3-amino-4-cyclobutyl-2-oxobutanamide residues.\nOption C: It has Gln, Leu, Gly, Pro, Gln, Gly, Pro, Pro, His, Leu, Val, Ala, Asp, Pro, Ser, Lys, Lys, Gln, Gly, Pro, Trp, Leu, Glu, Glu, Glu, Glu, Glu, Ala, Tyr, Gly, Trp, Met, Asp, and Phe residues.\nOption D: It has L-alanyl and L-aspartic acid residues.\nYour answer for this question: ",
#     "output": [
#         "D"
#     ]
# },

def merge_all_datas():
    for split in ["train", "validation", "test"]:
        biot5_template_path = "./QA/moleculeQA_bak/biot5_scaffold_reverse_biot5_v2/Property/task4_chebi20_mol2text_train.json"
        with open(biot5_template_path, 'r') as f:
            biot5_template = json.load(f)
        biot5_template.pop("Instances")
        biot5_template.pop("Contributors")
        biot5_template.pop("URL")
        biot5_template["Instances"] = []
        for desc_cls in ["Source", "Property", "Structure", "Usage"]:
            with open(f"{BIOT5_DATA_PATH}/{desc_cls}{split_method}{dataset_suffix}/task{split2taskid[split]}_chebi20_mol2text_{split}.json", 'r') as f:
                data = json.load(f)
            biot5_template["Instances"] += data["Instances"]
        random.shuffle(biot5_template["Instances"])
        print(f"All {split} has {len(biot5_template['Instances'])} instances")
        if not os.path.exists(f"{BIOT5_DATA_PATH}/All{split_method}{dataset_suffix}"):
            os.makedirs(f"{BIOT5_DATA_PATH}/All{split_method}{dataset_suffix}")
        with open(f"{BIOT5_DATA_PATH}/All{split_method}{dataset_suffix}/task{split2taskid[split]}_chebi20_mol2text_{split}.json", 'w') as f:
            json.dump(biot5_template, f, indent=4)
    for split in ["train", "valid", "test"]:
        datas = []
        for desc_cls in ["Source", "Property", "Structure", "Usage"]:
            with open(f"{MOLT5_DATA_PATH}/{desc_cls}{split_method}{dataset_suffix}/{split}.txt", 'r') as f:
                data = csv.reader(f, delimiter='\t')
                rows = list(data)
                header = rows[0]
                rows = rows[1:]
                datas += rows
        random.shuffle(datas)
        if not os.path.exists(f"{MOLT5_DATA_PATH}/All{split_method}{dataset_suffix}"):
            os.makedirs(f"{MOLT5_DATA_PATH}/All{split_method}{dataset_suffix}")
        with open(f"{MOLT5_DATA_PATH}/All{split_method}{dataset_suffix}/{split}.txt", 'w') as f:
            writer = csv.writer(f, delimiter='\t')
            writer.writerow(header)
            writer.writerows(datas)
        print(f"All {split} has {len(datas)} instances")

if __name__ == "__main__":
    # for desc_cls in ["Source", "Property", "Structure", "Usage"]: #["Source", "Property", "Structure"]
    #     for split in ["train", "validation", "test"]:
    #         convert_moleculeQA_to_biot5_style(desc_cls, split)
    #         convert_moleculeQA_to_molt5_style(desc_cls, split)

    merge_all_datas()

# Source train has 11062 instances
# Source validation has 1225 instances
# Source test has 1343 instances
# Property train has 4838 instances
# Property validation has 698 instances
# Property test has 731 instances
# Structure train has 32176 instances
# Structure validation has 3314 instances
# Structure test has 3113 instances
# Usage train has 1917 instances
# Usage validation has 558 instances
# Usage test has 599 instances
# All train has 49993 instances
# All validation has 5795 instances
# All test has 5786 instances
# All train has 49993 instances
# All valid has 5795 instances
# All test has 5786 instances