import json
import os
from tqdm import tqdm
annotated_leaf_topics_path = "./fine_grained_CLS/generate_questions/{}/annotated_leaf_topics.json"
class_types = {
    "Structure": 1,
    "Usage":2,
    "Property":3,
}

def convert_legal_compounds_to_lower():
    with open("./Chebi_Sup/supplement/missed_samples/legal_compounds.json", "r") as f:
        compounds = json.load(f)
    lower_compounds = []
    for compound in compounds:
        cid = compound["cid"]
        name = compound["name"]
        smile = compound["smile"]
        descs = compound["descriptions"]
        for idx in range(len(descs)):
            descs[idx][2] = descs[idx][2].lower()
        lower_compounds.append({"cid": cid, "name": name, "smile": smile, "descriptions": descs})
    with open("./Chebi_Sup/supplement/missed_samples/legal_compounds.json", "w") as f:
        json.dump(compounds, f, indent=4)

def get_non_leaf_compounds(desc_cls):
    # Instance number: 812
    # Instance number: 1072
    # Instance number: 49
    class_type = class_types[desc_cls]
    with open("./Chebi_Sup/supplement/missed_samples/legal_compounds.json", "r") as f:
        organized_compounds = json.load(f)
    selected_compounds = {}
    with open(f"./Chebi_Sup/supplement/missed_samples/{desc_cls}/non_leaf_topics.json", "r") as f:
        non_leaf_topics = json.load(f)
    instance_num = 0
    for compound in tqdm(organized_compounds):
        cid = compound["cid"]
        descs = compound["descriptions"]
        for desc in descs:
            desc_type, sentence, summary_str = desc
            if desc_type == class_type:
                summary = json.loads(summary_str)
                summary = summary[desc_cls.lower()]

                for topic in summary:
                    if topic in non_leaf_topics and non_leaf_topics[topic][0].startswith(desc_cls):
                        # print(f"Topic: {topic}")
                        if summary[topic] in non_leaf_topics[topic][1]:
                            # print(f"Summary: {summary[topic]}")
                            if not topic in selected_compounds:
                                selected_compounds[topic] = []
                            selected_compounds[topic].append([cid, sentence, topic])
                            instance_num += 1
        # break
    with open(f"./missed_samples/{desc_cls}/non_leaf_compounds.json", "w") as f:
        json.dump(selected_compounds, f, indent=4)
    print(f"Instance number: {instance_num}")

def convert_source_pairs_into_triples():

    topic2ques = {
        "isolated": "Where this molecule can be isolated from?",
        "found": "Where this molecule can be found?",
        "metabolite": "Which kind of metabolite is this molecule?",
        "derives": "Which molecule does this molecule derive from?",
    }

    instance_num = 0
    easy_num = 0

    source_dir = "./Chebi_Sup/supplement/discritpive_samples/Source"
    output_path = "./Chebi_Sup/build_QA_pairs/QA_pairs_Source.json"
    file_ls = os.listdir(source_dir)
    source_triples = {}
    easy_triples = {
        "derives": []
    }
    for file in file_ls:
        if file.startswith("QA_pairs") and file.endswith(".json"):
            with open(os.path.join(source_dir, file), "r") as f:
                source_pairs = json.load(f)
            for topic in source_pairs:
                if not topic in source_triples:
                    source_triples[topic] = []
                for source_pair in source_pairs[topic]:
                    cid, desc, question, options = source_pair
                    question = topic2ques[topic]
                    if topic == "derives":
                        desc_ls = desc.split(". ")
                        if len(desc_ls) == 1 and desc_ls[0].startswith("It derives from"):
                            easy_triples[topic].append([cid, desc, question, desc_ls[0]])
                            easy_num += 1
                            continue
                        elif len(desc_ls) > 1:
                            source_num = 0
                            source = ""
                            for single_desc in desc_ls:
                                if single_desc.find("derives from") != -1:
                                    source = single_desc
                                    source_num += 1
                                    if single_desc.find(", ") != -1 or single_desc.find(" and ") != -1:
                                        source_num += 1
                            if source_num == 1:
                                easy_triples[topic].append([cid, desc, question, single_desc])
                                easy_num += 1
                                continue
                    if isinstance(options, list):
                        options = options[0]
                    source_triples[topic].append([cid, desc, question, options])
                    instance_num += 1
    with open(output_path, "w") as f:
        json.dump(source_triples, f, indent=4)
    
    with open(output_path.replace(".json", "_easy.json"), "w") as f:
        json.dump(easy_triples, f, indent=4)

    print(f"Instance number: {instance_num}")
    print(f"Easy number: {easy_num}")

if __name__ == "__main__":
    convert_source_pairs_into_triples()
    # convert_legal_compounds_to_lower()
    # for desc_cls in class_types:
    #     get_non_leaf_compounds(desc_cls)
    # get_non_leaf_compounds("Usage")