import os
import random
from collections import defaultdict
from itertools import compress

import numpy as np
import json
from rdkit.Chem.Scaffolds import MurckoScaffold
from sklearn.model_selection import StratifiedKFold

scaffold_output_path = "./moleculeQA/scaffold"

# 需要给每一个类的smile生成scaffold，

def generate_scaffold(smiles, include_chirality=False):
    """ Obtain Bemis-Murcko scaffold from smiles
    :return: smiles of scaffold """
    scaffold = MurckoScaffold.MurckoScaffoldSmiles(
        smiles=smiles, includeChirality=include_chirality)
    return scaffold

def scaffold_split(smiles_list, cid_ls, frac_train=0.8, frac_valid=0.1, frac_test=0.1, return_idx=False):
    np.testing.assert_almost_equal(frac_train + frac_valid + frac_test, 1.0)


    non_null = np.ones(len(smiles_list)) == 1
    smiles_list = list(compress(enumerate(smiles_list), non_null))
    # print(smiles_list[0])
    # create dict of the form {scaffold_i: [idx1, idx....]}
    all_scaffolds = {}
    for i, smiles in smiles_list:
        scaffold = generate_scaffold(smiles, include_chirality=True)
        if scaffold not in all_scaffolds:
            all_scaffolds[scaffold] = [i]
        else:
            all_scaffolds[scaffold].append(i)

    # sort from largest to smallest sets
    all_scaffolds = {key: sorted(value) for key, value in all_scaffolds.items()}
    all_scaffold_sets = [
        scaffold_set for (scaffold, scaffold_set) in sorted(
            all_scaffolds.items(), key=lambda x: (len(x[1]), x[1][0]), reverse=True)
    ]

    # get train, valid test indices
    train_cutoff = frac_train * len(smiles_list)
    valid_cutoff = (frac_train + frac_valid) * len(smiles_list)
    train_idx, valid_idx, test_idx = [], [], []
    for scaffold_set in all_scaffold_sets:
        if len(train_idx) + len(scaffold_set) > train_cutoff:
            if len(train_idx) + len(valid_idx) + len(scaffold_set) > valid_cutoff:
                test_idx.extend(scaffold_set)
            else:
                valid_idx.extend(scaffold_set)
        else:
            train_idx.extend(scaffold_set)
    if return_idx:
        return train_idx, valid_idx, test_idx
    train_smiles = [smiles_list[i][1] for i in train_idx]
    valid_smiles = [smiles_list[i][1] for i in valid_idx]
    test_smiles = [smiles_list[i][1] for i in test_idx]
    train_cid = [cid_ls[i] for i in train_idx]
    valid_cid = [cid_ls[i] for i in valid_idx]
    test_cid = [cid_ls[i] for i in test_idx]
    return train_cid, valid_cid, test_cid, train_smiles, valid_smiles, test_smiles


def split_chebi_20():
    with open("./cid2smile.json", "r") as f:
        cid2smile = json.load(f)
    cid_ls = []
    smile_ls = []
    for cid in cid2smile:
        cid_ls.append(cid)
        smile_ls.append(cid2smile[cid])
    
    train_cid, valid_cid, test_cid, train_smiles, valid_smiles, test_smiles = scaffold_split(smile_ls, cid_ls, frac_train=0.8, frac_valid=0.1, frac_test=0.1)
    target_path = "./moleculeQA/scaffold"
    with open(os.path.join(target_path, "train_cid.json"), "w") as f:
        json.dump(train_cid, f, indent=4)
    with open(os.path.join(target_path, "valid_cid.json"), "w") as f:
        json.dump(valid_cid, f, indent=4)
    with open(os.path.join(target_path, "test_cid.json"), "w") as f:
        json.dump(test_cid, f, indent=4)
    with open(os.path.join(target_path, "train_smiles.json"), "w") as f:
        json.dump(train_smiles, f, indent=4)
    with open(os.path.join(target_path, "valid_smiles.json"), "w") as f:
        json.dump(valid_smiles, f, indent=4)
    with open(os.path.join(target_path, "test_smiles.json"), "w") as f:
        json.dump(test_smiles, f, indent=4)
    
    print(len(train_cid), len(valid_cid), len(test_cid))


# 只要搞到四个CID list就行了
def split_moleculeQA(desc_cls): 
    
    with open("./cid2smile.json", "r") as f:
        cid2smile = json.load(f)
    with open(f"./moleculeQA/scaffold/desc_qid_cid_{desc_cls}.json", "r") as f:
        qid_cid = json.load(f)
        qid_ls, cid_ls = qid_cid

    smile_ls = []
    for cid in cid_ls:
        smile_ls.append(cid2smile[cid])
    
    train_idx, valid_idx, test_idx = scaffold_split(smile_ls, cid_ls, frac_train=0.8, frac_valid=0.1, frac_test=0.1, return_idx=True)
    target_path = os.path.join(scaffold_output_path, desc_cls)
    if not os.path.exists(target_path):
        os.makedirs(target_path)
    train_cid = [cid_ls[i] for i in train_idx]
    valid_cid = [cid_ls[i] for i in valid_idx]
    test_cid = [cid_ls[i] for i in test_idx]
    train_qid = [qid_ls[i] for i in train_idx]
    valid_qid = [qid_ls[i] for i in valid_idx]
    test_qid = [qid_ls[i] for i in test_idx]

    with open(os.path.join(target_path, "train_qid_cid.json"), "w") as f:
        json.dump([train_qid, train_cid], f, indent=4)
    with open(os.path.join(target_path, "valid_qid_cid.json"), "w") as f:
        json.dump([valid_qid, valid_cid], f, indent=4)
    with open(os.path.join(target_path, "test_qid_cid.json"), "w") as f:
        json.dump([test_qid, test_cid], f, indent=4)
    
    print(f"{desc_cls}: ", end="")
    print(len(train_qid), len(valid_qid), len(test_qid))

def get_test_data():
    source_path = "./final_QA_pairs_{}_reverse_v2.json"
    cid_ls_path = "./moleculeQA/scaffold/test_cid.json"
    with open(cid_ls_path, "r") as fin:
        cid_ls = json.load(fin)
    test_QA_pairs = {}
    test_num = 0
    for cls in ["Usage", "Property", "Source", "Structure"]:
        cls_source_path = source_path.format(cls)
        with open(cls_source_path, "r") as fin:
            cls_qa_pairs = json.load(fin)
            for topic in cls_qa_pairs:
                topic_QA_pairs = cls_qa_pairs[topic]
                for QA_pair in topic_QA_pairs:
                    if QA_pair[0] in cid_ls:
                        QA_pair[4] = 1
                        if not topic in test_QA_pairs:
                            test_QA_pairs[topic] = []
                        test_QA_pairs[topic].append(QA_pair)
                        test_num += 1
    print(test_num)

    with open("./moleculeQA/scaffold_test_QA_pairs_v2.json", "w") as fout:
        json.dump(test_QA_pairs, fout, indent=4)



# # 26406 3301 3301
# if __name__ == "__main__":
#     # split_chebi_20()
#     for desc_cls in ["Property", "Structure"]:
#         split_moleculeQA(desc_cls)    


if __name__ == "__main__":
    get_test_data()