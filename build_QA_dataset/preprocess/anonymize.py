import json
import os
def anonymize():
    verb_path = "./verb.json"
    with open(verb_path, "r") as fin:
        verb_ls = json.load(fin)

    with open("./supplement_triples.json", "r") as fin:
        triples = json.load(fin)

    anonymized_triples = []
    unanonymized_triples = []

    for idx in range(len(triples)):
        triple = triples[idx]
        start_point = 10000
        start_verb = ""
        # Find the first verb
        for verb in verb_ls:
            if verb in triple[2]:
                verb_loc = triple[2].index(verb)
                if verb_loc < start_point:
                    start_point = verb_loc
                    start_verb = verb
        if triple[0] == "56927879":
            print(start_verb)
            print(triple)
        if start_verb != "":
            verb_loc = triple[2].index(start_verb)
            name = triple[2][:verb_loc]
            triple[2] = triple[2].replace(name, "This molecule")
            name = name + " "
            triple[2] = triple[2].replace(name.lower(), " this molecule")
        if triple[0] == "56927879":
            print(triple[2])
        if not triple[2].startswith("This molecule"):
            unanonymized_triples.append(triple)
        else:
            anonymized_triples.append(triple)
    with open("./anonymized_triples.json", "w") as fout:
        json.dump(anonymized_triples, fout, indent=4)
    with open("./unanonymized_triples.json", "w") as fout:
        json.dump(unanonymized_triples, fout, indent=4)

    with open("./merged_triples.json", "w") as fout:
        json.dump(anonymized_triples + unanonymized_triples, fout, indent=4)

def merge_output():
    file_ls = os.listdir("./")
    cls_res = []
    cls2num = {
        "Source": 0,
        "Architecture": 1,
        "Property":2,
        "Usage":3
    }
    for file_name in file_ls:
        if file_name.startswith("cls_res_"):
            with open(file_name, "r") as fin:
                cls_ls = json.load(fin)
            for data in cls_ls:
                res = data[3]
                if ":" in res:
                    res = res.split(":")[1]
                res = res.strip()
                try:
                    # convert str to list
                    res = eval(res)
                    data[2] = data[2].strip()
                    if res[0] in cls2num and not data[2].startswith("(") and cls2num[res[0]] > 1:
                        cls_res.append((data[0], data[1], data[2], cls2num[res[0]]))
                except Exception as e:
                    continue
    with open("./cls_res.json", "w") as fout:
        json.dump(cls_res, fout, indent=4)
    print(len(cls_res))

if __name__ == "__main__":
    anonymize()
    # merge_output()
# 18956