import json

classes = ["", "", "Property", "Usage"]
cls2topic = {
    "Property" : {},
    "Usage": {}
}


def merge_extraction():
    extractions = []
    for i in range(8):
        with open(f"./extracted_contents_{i}.json") as fin:
            ls = json.load(fin)
            extractions += ls
    with open("cls_res.json", "r") as cls_file:
        cls_res = json.load(cls_file)
    assert len(extractions) == len(cls_res), f"{len(extractions)} / {len(cls_res)}"
    merged_res = []
    for idx in range(len(extractions)):
        # print(extractions[idx])
        # print(cls_res[0])
        if isinstance(extractions[idx], str):
            cls_res[idx].append(extractions[idx].strip())
            cls_res[idx][2] =  cls_res[idx][2].replace("moleculeis", "molecule is").replace("  ", " ")
            merged_res.append(cls_res[idx])
    
    with open("extracted_contents.json", "w") as fout:
        json.dump(merged_res, fout, indent=4)
    print(len(merged_res))

def parse_extraction():
    legal_contents = []
    illegal_contents = []
    ls = [0,0,0,0]
    nums = [0,0]
    with open("./extracted_contents.json", "r") as extracted_file:
        extracted_contents = json.load(extracted_file)
    for instance in extracted_contents:
        try:
            res = json.loads(instance[4])
            legal_contents.append(instance)
        except json.JSONDecodeError:
            illegal_contents.append(instance)
            continue
    for instance in legal_contents:
        extracted_content = json.loads(instance[4])
        cls = classes[instance[3]]
        nums[instance[3] - 2] += 1
        if not cls in extracted_content:
            ls[0] += 1
        elif isinstance(extracted_content[cls], str):
            ls[1] += 1
        elif isinstance(extracted_content[cls], dict):
            ls[2] += 1
            for key in extracted_content[cls]:
                cls2topic[cls][key] = cls2topic[cls].get(key, 0) + 1
        elif isinstance(extracted_content[cls], list):
            ls[3] += 1
        else:
            print(type(extracted_content[cls]))
    print(ls)
    for key in cls2topic:
        # cls2topic[key] = list(set(cls2topic[key]))
        print(f"{key}: {len(cls2topic[key])}")
    
    sorted_cls2topic = {}

    for cls in cls2topic:
        sorted_cls2topic[cls] = []
        for topic, num in cls2topic[cls].items():
            sorted_cls2topic[cls].append([topic, num])
        sorted_cls2topic[cls].sort(key=lambda x: x[1], reverse=True)
    with open("legal_extracted_contents.json", "w") as legal_file:
        json.dump(legal_contents, legal_file, indent=4)
    with open("illegal_extracted_contents.json", "w") as illegal_file:
        json.dump(illegal_contents, illegal_file, indent=4)
    print(len(legal_contents))
    print(nums)
    with open("cls2topic.json", "w") as fout:
        json.dump(sorted_cls2topic, fout, indent=4)

if __name__ == "__main__": 
    merge_extraction()
    parse_extraction()
# [0, 3502, 15454, 0]