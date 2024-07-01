import json
from tqdm import tqdm
# selfies2smiles = {}
# with open("./QA/moleculeQA_bak/biot5_scaffold_reverse_biot5_v2/All/task4_chebi20_mol2text_train.json", "r") as fin:
#     qa_data = json.load(fin)
# instances = qa_data["Instances"]

# with open("")



# for instance in instances:
#     input_text = instance["input"]
#     ls = input_text.split("\n")[:-1]
#     ls[0] = ls[0].split("<eom>")[0].replace("<bom>", "")
#     for i in range(1, 5):
#         ls[i] = ls[i][10:]
    
#     selfies = ls[0]
#     options = set(ls[1:])


from rdkit import Chem
import selfies as sf

def smiles_to_selfies(smiles):
    # Convert SMILES to RDKit molecule object
    molecule = Chem.MolFromSmiles(smiles)
    # if molecule is None:
    #     return "Invalid SMILES string"
    # Chem.MolToSmiles()
    # Convert molecule to SELFIES
    if Chem.MolToSmiles(molecule) == "O=Ic1ccccc1C(=O)O":
        print(smiles)
        return "[O][=I][C][=C][C][=C][C][=C][Ring1][=Branch1][C][=Branch1][C][=O][O]"
    if Chem.MolToSmiles(molecule) == "CCCC[N+]1(C)OI(=O)([O-])c2ccccc21":
        print(smiles)
        return "[C][C][C][C][N+1][Branch1][C][C][O][I][=Branch1][C][=O][Branch1][C][O-1][C][=C][C][=C][C][=C][Ring1][=Branch1][Ring1][N]"
    if Chem.MolToSmiles(molecule) == "O=C1OI(O)c2ccccc21":
        print(smiles)
        return "[O][=C][O][I][Branch1][C][O][C][=C][C][=C][C][=C][Ring1][=Branch1][Ring1][#Branch2]"
        # return "[C][C][C][C][C][C][=C][C][=O][O][C][=C][Ring1][=O][Ring1][=O]"
    if Chem.MolToSmiles(molecule) == "O=C(O)c1ccccc1I(=O)=O":
        print(smiles)
        return "[O][=C][Branch1][C][O][C][=C][C][=C][C][=C][Ring1][=Branch1][I][=Branch1][C][=O][=O]"
    if Chem.MolToSmiles(molecule) == "O=C1OI(=O)(O)c2ccccc21":
        print(smiles)
        return "[O][=C][O][I][=Branch1][C][=O][Branch1][C][O][C][=C][C][=C][C][=C][Ring1][=Branch1][Ring1][O]"
    selfies_string = sf.encoder(Chem.MolToSmiles(molecule))
    return selfies_string

# x = '[C][O][C][=C][C][=C][C][=Branch1][Ring2][=C][Ring1][=Branch1][C@@][C][C][C][C][C@H1][Ring1][=Branch1][C@@H1][Branch1][Ring2][C][Ring1][O][N][Branch1][C][C][C][C][Ring1][N]'
# y = "CN1CC[C@]23CCCC[C@H]2[C@H]1CC4=C3C=C(C=C4)OC"
# print(x == smiles_to_selfies(y))
# x = "[C][O][C@][C][C][C@@][Branch2][Ring1][Ring2][C][C@@H1][Ring1][=Branch1][C@][Branch1][C][C][Branch1][C][O][C][Branch1][C][C][Branch1][C][C][C][C@H1][C][C][=C][C][=C][Branch1][C][O][C][=C][Ring1][#Branch1][C@@][Ring2][Ring1][Ring2][Branch1][N][C][C][N][Ring1][=N][C][C][C][C][Ring1][Ring1][C@H1][Ring2][Ring1][#C][O][Ring1][N]"
# y = "C[C@]([C@H]1C[C@@]23CC[C@@]1([C@H]4[C@@]25CCN([C@@H]3CC6=C5C(=C(C=C6)O)O4)CC7CC7)OC)(C(C)(C)C)O"
# print(x ==smiles_to_selfies(y))
# x = "[O][=C][Branch2][Ring1][C][C][C][=C][NH1][C][=C][C][Branch1][C][Br][=C][C][=C][Ring1][#Branch2][Ring1][#Branch1][N][C@@H1][Branch1][=Branch2][C][C][=C][N][=C][NH1][Ring1][Branch1][C][=Branch1][C][=O][O]"
# y = "C1=CC2=C(C=C1Br)NC=C2CC(=O)N[C@@H](CC3=CN=CN3)C(=O)O"
# print(x ==smiles_to_selfies(y))
def generata_smiles2selfies():
    smiles2selfies = {}

    with open("./QA/moleculeQA_bak/cid2smile.json", "r") as fin:
        cid2smile = json.load(fin)

    for cid in tqdm(cid2smile):
        smile = cid2smile[cid]
        selfies = smiles_to_selfies(smile)
        smiles2selfies[smile] = selfies

    with open("smile2selfies.json", "w") as fout:
        json.dump(smiles2selfies, fout, indent=4)

def test_selfies():
    with open("smile2selfies.json", "r") as fin:
        smiles2selfies = json.load(fin)
    
    selfies = set(smiles2selfies.values())

    origin_selfies = set()
    with open("./QA/moleculeQA_bak/biot5_scaffold_reverse_biot5_v2/All/task4_chebi20_mol2text_train.json", "r") as fin:
        qa_data = json.load(fin)
    instances = qa_data["Instances"]

    for instance in instances:
        input_text = instance["input"]
        ls = input_text.split("\n")[:-1]
        ls[0] = ls[0].split("<eom>")[0].replace("<bom>", "")
        for i in range(1, 5):
            ls[i] = ls[i][10:]
        
        origin_selfies.add(ls[0])
    
    print(origin_selfies - selfies)
    print(len(origin_selfies))


def get_validation_cids():
    with open("./QA/Chebi_Sup/test_with_GPT/test_cid.json", "r") as fin:
        test_cids = set(json.load(fin))
    with open("./QA/Chebi_Sup/test_with_GPT/train_cid.json", "r") as fin:
        train_cids = set(json.load(fin))
    
    with open("./QA/moleculeQA_bak/cid2smile.json", "r") as fin:
        cid2smile = json.load(fin)
    
    validation_cids = set()

    for cid in cid2smile:
        if cid not in train_cids and cid not in test_cids:
            validation_cids.add(cid)
    with open("./QA/Chebi_Sup/valid_cid.json", "w") as fout:
        json.dump(list(validation_cids), fout, indent=4)
    


if __name__ == "__main__":
    # test_selfies()
    get_validation_cids()
