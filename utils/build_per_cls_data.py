from cgitb import text
import json
import csv
import os
from weakref import ref

from rdkit import Chem
import selfies as sf

CLASSES = ["source", "structure", "property", "usage"]
splits = ["train", "valid", "test"]
SPLITS = ["train", "validation", "test"]
task_idxes = ["4", "5", "6"]
cls_data_path = "/./DATA/momu"
reference = "/./DATA/biot5/tasks/task{}_chebi20_mol2text_{}.json"
data_path = "/./DATA/biot5"
def convert_to_canonical_smiles(smiles:str):
    molecule = Chem.MolFromSmiles(smiles)
    if molecule is not None:
        canonical_smiles = Chem.MolToSmiles(molecule)
        return canonical_smiles
    else:
        return None

def encode_to_selfies(smiles:str)-> str:
    canonical_smiles = convert_to_canonical_smiles(smiles)
    try:
        selfies = sf.encoder(canonical_smiles)
    except:
        selfies = smiles
    return selfies

def get_smile2selfies_dict():
    # dicts for train, val, test
    if os.path.exists(os.path.join(data_path, "smile2selfies.json")):
        with open(os.path.join(data_path, "smile2selfies.json"), "r") as f:
            smile2selfies_dicts = json.load(f)
        with open(os.path.join(data_path, "smile2text.json"), "r") as f:
            smile2text_dicts = json.load(f)
        return smile2selfies_dicts, smile2text_dicts
    smile2selfies_dicts = [{}, {}, {}]
    smile2text_dicts = [{}, {}, {}]
    for idx, split in enumerate(splits):
        with open(os.path.join(cls_data_path, f"{split}.txt"), "r") as f:
            # CID     SMILES  description
            reader = csv.reader(f, delimiter="\t")
            next(reader)
            for row in reader:
                smile = row[1]
                text = row[2]
                selfies = encode_to_selfies(smile)
                smile2selfies_dicts[idx][smile] = selfies
                smile2text_dicts[idx][smile] = text
    if not os.path.exists(os.path.join(data_path, "smile2selfies.json")):
        with open(os.path.join(data_path, "smile2selfies.json"), "w") as f:
            json.dump(smile2selfies_dicts, f, indent=4)
    if not os.path.exists(os.path.join(data_path, "smile2text.json")):
        with open(os.path.join(data_path, "smile2text.json"), "w") as f:
            json.dump(smile2text_dicts, f, indent=4)
    return smile2selfies_dicts, smile2text_dicts

def get_selfies2id_dict():
    # dicts for train, val, test

    if os.path.exists(os.path.join(data_path, "selfies2id.json")):
        with open(os.path.join(data_path, "selfies2id.json"), "r") as f:
            selfies2id_dicts = json.load(f)
        with open(os.path.join(data_path, "selfies2text.json"), "r") as f:
            selfies2text_dicts = json.load(f)
        return selfies2id_dicts, selfies2text_dicts
    
    selfies2id_dicts = [{}, {}, {}]
    selfies2text_dicts = [{}, {}, {}]
    for idx, split in enumerate(SPLITS):
        with open(reference.format(task_idxes[idx], split), "r") as f:
            ref_data = json.load(f)
        instances = ref_data["Instances"]
        for instance in instances:
            selfies = instance["input"]
            text = instance["output"][0]
            # remove <bom> and <eom> in selfies
            selfies = selfies.replace("<bom>", "").replace("<eom>", "")
            selfies2id_dicts[idx][selfies] = instance["id"]
            selfies2text_dicts[idx][selfies] = text

    if not os.path.exists(os.path.join(data_path, "selfies2id.json")):
        with open(os.path.join(data_path, "selfies2id.json"), "w") as f:
            json.dump(selfies2id_dicts, f, indent=4)
    if not os.path.exists(os.path.join(data_path, "selfies2text.json")):
        with open(os.path.join(data_path, "selfies2text.json"), "w") as f:
            json.dump(selfies2text_dicts, f, indent=4)

    return selfies2id_dicts, selfies2text_dicts

def check_consistency():
    selfies2id_dicts, selfies2text_dicts = get_selfies2id_dict()
    smile2selfies_dicts, smile2text_dicts = get_smile2selfies_dict()
    for idx, split in enumerate(SPLITS):
        for smile in smile2selfies_dicts[idx]:
            selfies = smile2selfies_dicts[idx][smile]
            text1 = smile2text_dicts[idx][smile]
            # [O][=I][C][=C][C][=C][C][=C][Ring1][=Branch1][C][=Branch1][C][=O][O]
            # C1=CC=C(C(=C1)C(=O)O)I=O
            if not selfies in selfies2id_dicts[idx]:
                for selfies, text in selfies2text_dicts[idx].items():
                    if text == text1:
                        smile2selfies_dicts[idx][smile] = selfies
                        with open(os.path.join(data_path, "smile2selfies.json"), "w") as f:
                            json.dump(smile2selfies_dicts, f, indent=4)
                        break
            text2 = selfies2text_dicts[idx][selfies]
            if text1 != text2:
                print(f"split: {split}, smile: {smile}, selfies: {selfies}, text1: {text1}, text2: {text2}")

def build_per_cls_data(cls):
    selfies2id_dicts, selfies2text_dicts = get_selfies2id_dict()
    smile2selfies_dicts, smile2text_dicts = get_smile2selfies_dict()
    for idx, split in enumerate(splits):
        with open(reference.format("4", "train"), "r") as f:
            ref_data = json.load(f)
        ref_data.pop("Instances")
        ref_data["Instances"] = []
        with open(os.path.join(cls_data_path, f"{cls}/{split}.txt"), "r") as f:
            reader = csv.reader(f, delimiter="\t")
            next(reader)
            for row in reader:
                smile = row[1]
                text = row[2]
                selfies = smile2selfies_dicts[idx][smile]
                if selfies in selfies2id_dicts[idx]:
                    id = selfies2id_dicts[idx][selfies]
                else:
                    print(f"split: {split}, smile: {smile}, selfies: {selfies}, text: {text}")
                    return
                ref_data["Instances"].append({
                    "id": id,
                    "input": "<bom>" +  selfies + "<eom>",
                    "output": [text]
                })
        if not os.path.exists(os.path.join(data_path, "tasks", f"{cls}")):
            os.mkdir(os.path.join(data_path, "tasks", f"{cls}"))
        with open(os.path.join(data_path, "tasks",  f"{cls}/task{task_idxes[idx]}_chebi20_mol2text_{SPLITS[idx]}.json"), "w") as f:
            json.dump(ref_data, f, indent=4)
    

if __name__ == "__main__":
    check_consistency()
    for cls in CLASSES:
        build_per_cls_data(cls)
