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
PUBCHEM_DATA_PATH = "./CheBI-20/Hug"
BIOT5_DATA_PATH = "./BioT5/data"
dataset_suffix = "_reverse_biot5_v3"
MOLT5_DATA_PATH = f"./moleculeqa{split_method}{dataset_suffix}"
task_definition = ""
def generate_id():
    n = ''.join(random.sample(string.ascii_letters+string.digits,32))

    # print(n)  #结果是：WIxj4L605dowP9t3g7fbSircqpTOZ2VK

    #然后再将n进行md5加密

    import hashlib

    m = hashlib.md5() #创建Md5对象

    m.update(n.encode('utf-8')) #生成加密串，其中n是要加密的字符串

    result = m.hexdigest() #经过md5加密的字符串赋值
    return result


def convert_moleculeQA_to_biot5_style(desc_cls, split):
    smile2selfies_path = f"{BIOT5_DATA_PATH}/moleculeQA/smile2selfies.json"
    biot5_template_path = f"{BIOT5_DATA_PATH}/task4_chebi20_mol2text_train.json"
    if split_method == "_scaffold":
        if split == "validation":
            split_cid_path = f"./moleculeQA/scaffold/valid_cid.json"
        else:
            split_cid_path = f"./moleculeQA/scaffold/{split}_cid.json"
        with open(split_cid_path, 'r') as f:
            cid_sets = json.load(f)
    elif split_method == "_sep_scaffold":
        if split == "validation":
            split_qid_cid_path = f"./moleculeQA/scaffold/{desc_cls}/valid_qid_cid.json"
        else:
            split_qid_cid_path = f"./moleculeQA/scaffold/{desc_cls}/{split}_qid_cid.json"
        with open(split_qid_cid_path, 'r') as f:
            qid_cid = json.load(f)
            qid_ls, cid_ls = qid_cid
            qid2cid = {}
            for i in range(len(qid_ls)):
                qid2cid[qid_ls[i]] = cid_ls[i]
    else:
        if split == "validation":
            split_cid_path = f"{PUBCHEM_DATA_PATH}/valid.csv"
        else:
            split_cid_path = f"{PUBCHEM_DATA_PATH}/{split}.csv"
        with open(split_cid_path, 'r') as f:
            reader = csv.reader(f, delimiter='\t')
            next(reader)
            cid_sets = [row[0] for row in reader]
    dataset = MoleculeQADataset(data_path=f"{BIOT5_DATA_PATH}/option_added_QA_pairs_{desc_cls}{dataset_suffix}.json", cid2smile_path=f"{BIOT5_DATA_PATH}/cid2smile.json", tokenizer=None)
    task_definition = dataset.task_definition
    task_definition = task_definition.replace("SMILES", "SELFIES")
    with open(smile2selfies_path, 'r') as f:
        smile2selfies_ls = json.load(f)
    smile2selfies = {}
    for i in range(len(smile2selfies_ls)):
        for smiles, selfies in smile2selfies_ls[i].items():
            smile2selfies[smiles] = selfies

    with open(biot5_template_path, 'r') as f:
        biot5_template = json.load(f)
    biot5_template.pop("Instances")
    biot5_template["Instances"] = []
    biot5_template["Definition"] = task_definition
    biot5_template["Input_language"] = "English"
    biot5_template["Source"] = "Choose right option for the question according to the molecule SELFIES."
    for instance_idx in range(len(dataset)):
        smile, raw_text, question, options, choices = dataset.get_instance(instance_idx)
        cid = dataset.cids[instance_idx]
        if split_method != "_sep_scaffold":
            if cid not in cid_sets:
                continue
        else:
            if instance_idx not in qid_ls:
                continue
            assert qid2cid[instance_idx] == cid, f"{instance_idx}: {cid}/{cid_ls[instance_idx]}"
        
        if not smile in smile2selfies:
            print(f"{dataset.cids[instance_idx]}: {smile} not in smile2selfies")
            continue
        selfies = f"<bom>{smile2selfies[smile]}<eom>"
        instance_input = dataset.add_selfies("", selfies)
        instance_input = dataset.add_question(instance_input, question)
        instance_input = dataset.add_option(instance_input, options, choices)
        instance_output = choices[0]
        instance_id = f"{split2taskid[split]}-" + generate_id()
        instance = {"id": instance_id, "input": instance_input, "output": [instance_output]}
        biot5_template["Instances"].append(instance)
    print(f"{desc_cls} {split} has {len(biot5_template['Instances'])} instances")
    # if not os.path.exists(f"{BIOT5_DATA_PATH}/moleculeQA/biot5{split_method}{dataset_suffix}/{desc_cls}"):
    #     os.makedirs(f"{BIOT5_DATA_PATH}/moleculeQA/biot5{split_method}{dataset_suffix}/{desc_cls}")
    
    # with open(f"{BIOT5_DATA_PATH}/moleculeQA/biot5{split_method}{dataset_suffix}/{desc_cls}/task{split2taskid[split]}_chebi20_mol2text_{split}.json", 'w') as f:
    #     json.dump(biot5_template, f, indent=4)


def convert_moleculeQA_to_molt5_style(desc_cls, split):
    # molt5 style: cid, Question, Answer
    if split_method == "_scaffold":
        if split == "validation":
            split_cid_path = f"./moleculeQA/scaffold/valid_cid.json"
        else:
            split_cid_path = f"./moleculeQA/scaffold/{split}_cid.json"
        with open(split_cid_path, 'r') as f:
            cid_sets = json.load(f)
    elif split_method == "_sep_scaffold":
        if split == "validation":
            split_qid_cid_path = f"./moleculeQA/scaffold/{desc_cls}/valid_qid_cid.json"
        else:
            split_qid_cid_path = f"./moleculeQA/scaffold/{desc_cls}/{split}_qid_cid.json"
        with open(split_qid_cid_path, 'r') as f:
            qid_cid = json.load(f)
            qid_ls, cid_ls = qid_cid
            qid2cid = {}
            for i in range(len(qid_ls)):
                qid2cid[qid_ls[i]] = cid_ls[i]
    else:        
        if split == "validation":
            split_cid_path = f"{PUBCHEM_DATA_PATH}/valid.csv"
        else:
            split_cid_path = f"{PUBCHEM_DATA_PATH}/{split}.csv"
        with open(split_cid_path, 'r') as f:
            reader = csv.reader(f, delimiter='\t')
            next(reader)
            cid_sets = [row[0] for row in reader]
    dataset = MoleculeQADataset(data_path=f"{BIOT5_DATA_PATH}/option_added_QA_pairs_{desc_cls}{dataset_suffix}.json", cid2smile_path=f"{BIOT5_DATA_PATH}/cid2smile.json", tokenizer=None)
    task_definition = dataset.task_definition
    # task_definition = task_definition.replace("SMILES", "SELFIES")
    instance_num = 0
    if not os.path.exists(MOLT5_DATA_PATH):
        os.makedirs(MOLT5_DATA_PATH)
    target_path = f"{MOLT5_DATA_PATH}/{desc_cls}"
    if not os.path.exists(target_path):
        os.makedirs(target_path)
    if split == "validation":
        split = "valid"
    
    with open(os.path.join(target_path, f"{split}.txt"), 'w') as f:
        writer = csv.writer(f, delimiter='\t')
        writer.writerow(["CID", "Question", "Answer"])
        for instance_idx in range(len(dataset)):
            smile, raw_text, question, options, choices = dataset.get_instance(instance_idx)
            cid = dataset.cids[instance_idx]
            if split_method != "_sep_scaffold":
                if cid not in cid_sets:
                    continue
            else:
                if instance_idx not in qid_ls:
                    continue
                assert qid2cid[instance_idx] == cid, f"{instance_idx}: {cid}/{cid_ls[instance_idx]}"
            instance_text = dataset.add_smile(task_definition, smile)
            instance_text = dataset.add_question(instance_text, question)
            instance_text = dataset.add_option(instance_text, options, choices)
            instance_output = choices[0]
            writer.writerow([cid, instance_text, instance_output])
            instance_num += 1
    
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


def generate_general_data():
    for split in ["train", "validation", "test"]:
        if split_method == "_scaffold":
            if split == "validation":
                split_cid_path = f"./moleculeQA/scaffold/valid_cid.json"
            else:
                split_cid_path = f"./moleculeQA/scaffold/{split}_cid.json"
            with open(split_cid_path, 'r') as f:
                cid_sets = json.load(f)
        for desc_cls in ["Source", "Property", "Structure", "Usage"]: #["Source", "Property", "Structure"]
            dataset = MoleculeQADataset(data_path=f"{BIOT5_DATA_PATH}/option_added_QA_pairs_{desc_cls}{dataset_suffix}.json", cid2smile_path=f"{BIOT5_DATA_PATH}/cid2smile.json", tokenizer=None)
            task_definition = dataset.task_definition
            # task_definition = task_definition.replace("SMILES", "SELFIES")
            instance_num = 0
        
 

if __name__ == "__main__":
    for desc_cls in ["Source", "Property", "Structure", "Usage"]: #["Source", "Property", "Structure"]
        for split in ["train", "validation", "test"]:
            convert_moleculeQA_to_biot5_style(desc_cls, split)
            # convert_moleculeQA_to_molt5_style(desc_cls, split)

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