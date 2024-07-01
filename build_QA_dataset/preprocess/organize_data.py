import json
import os

cid_path = "./multi_source.json"

with open(cid_path, "r") as fin:
    cid_set = set(json.load(fin))
source2num = {}
data_path = "./chembl_Desc_multi_source.json"
with open(data_path, "r") as fin:
    data_dict = json.load(fin)
data_triples = []
abb_path = "./abb.json"
with open(abb_path, "r") as fin:
    abb_dict = json.load(fin)

# only keep the data in cid_dict
for cid in data_dict.keys():
    compound = data_dict[cid]
    if cid not in cid_set:
        continue
    for desc in compound["DESCRIPTION"]:
        if not desc["SOURCE"] == "ChEBI" and not abb_dict[desc["SOURCE"]] == "LOTUS":
            data_triples.append((cid, abb_dict[desc["SOURCE"]], desc["TEXT"]))
            source2num[desc["SOURCE"]] = source2num.get(desc["SOURCE"], 0) + 1

with open("./supplement_triples.json", "w") as fout:
    json.dump(data_triples, fout, indent=4)

source2num["Total"] = len(data_triples)
with open("./source2num.json", "w") as fout:
    json.dump(source2num, fout, indent=4)

    
        