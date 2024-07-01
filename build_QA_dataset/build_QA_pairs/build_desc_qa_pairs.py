import os
import json

from matplotlib import table


def get_disc_options(desc_cls, topic, options):
    # if topic == "antiviral activity":
    #     print(options)
    disc_options = []
    prefixes = {
        "Property": [
            "exhibit",
            "exhibits",
            "and",
            "has",
            "has a role as a",
            "has a role as an",
        ],
        "Usage": [
            "exhibits",
            "exhibit",
            "used as a",
            "used as an"
            "has a role as a",
            "has a role as an",
        ]
    }
    suffixes = {
        "Structure": [
            " and",
            ".",
            ", "
        ],
        "Property": [
            ".",
            " and",
            " properties.",
            " property.",
            " activities.",
            ",",
            " agent."
        ],
        # Exhibits anticancer activities.
        "Usage": [
            " activities.",
            " activity.",
            " properties.",
            " property.",
            " agents."
            " agent.",
            ".",
            ", a ",
            ", an ",
            " agents, a ",
            " agent, an ",
            " drug, a ",
            " drugs, an ",            
            " and a ",
            " and an "
        ]
    }
    # cas = "Exhibits anticancer activities."
    for prefix in prefixes[desc_cls]:
        for suffix in suffixes[desc_cls]:
            for option in options:
            # "Exhibits inhibitory activity against protein kinase C.",
                
                # if option == cas:
                #     print(f"{prefix} {topic}{suffix}")
                if option.lower().find(f"{prefix} {topic}{suffix}") != -1 and option.lower().find(f"{prefix} {topic}{suffix}specifically") == -1:
                    if desc_cls == "Usage" and option.find(". ") != -1: 
                        continue
                    disc_options.append(option)
                    # if option == cas:
                    #     print(f"{prefix} {topic}{suffix}")
                if desc_cls == "Property" and topic.find("activity") != -1:
                    if option.lower() == f"{topic}{suffix}":
                        disc_options.append(option)
                        continue
                    t = topic.split(" ")[0]
                    if option.lower().find(f"{prefix} {t}{suffix}") != -1:
                        disc_options.append(option)
                if desc_cls == "Usage":
                    t = topic.split(" ")[0]
                    if option.lower().find(f"{prefix} {t} {suffix}") != -1 and option.find(". ") == -1:
                        disc_options.append(option)
                        # if option == cas:
                        #     print(f"{prefix} {t}{suffix}")


    return disc_options

def refine_structure_options():
    # remove useless
    ques2options_path = f"./Structure/ques2options.json"
    with open(ques2options_path) as f:
        ques2options = json.load(f)
    quesion = "Which kind of {} does this molecule have?"
    topic2options = ques2options[quesion]
    for topic in topic2options:
        options = topic2options[topic]
        # print(topic)
        disc_options = get_disc_options("Structure", topic, options)
        # print(disc_options)
        # remove_useless(options)
    
    # remove disc



def extract_desc_ques(desc_cls):
    origin_path = f"./{desc_cls}/annotated_no_dup_topic2options.json"
    no_dup_desc_topic2options_path = f"./{desc_cls}/no_dup_desc_topic2options.json"
    no_dup_desc_topic2options = {}

    with open(origin_path) as f:
        origin_topic2options = json.load(f)
    for topic in origin_topic2options:
        options = origin_topic2options[topic]
        if options[-1] == 1:
            no_dup_desc_topic2options[topic] = options[:-1]
    with open(no_dup_desc_topic2options_path, "w") as f:
        json.dump(no_dup_desc_topic2options, f, indent=4)

def generate_desc_ques(desc_cls, source_cls=None):
    # ./assign/desc_instances.json
    # if source_cls:
    #     no_dup_desc_topic2options_path = f"./{source_cls}/no_dup_desc_topic2options.json"
    # else:
    #     no_dup_desc_topic2options_path = f"./{desc_cls}/no_dup_desc_topic2options.json"
    # with open(no_dup_desc_topic2options_path) as f:
    #     no_dup_desc_topic2options = json.load(f)
    instance_path = "./assign/desc_instances.json"
    with open(instance_path, "r") as fin:
        desc_instances = json.load(fin)[desc_cls]
    ques2topics = {
        "Property": {
            "Which kind of {} is this molecule?": [
                "irritant",
                "receptor antagonist",
                "mutagen",
            ],
            "Which kind of {} does this molecule have/exhibit?": [
                "inhibitory activity",
                "toxicity",
                "carcinogenicity",
                "action",
                "effects",
                "reactivity",
                "taste",
                "sensitivity",
                "half-life",
                "selectivity",
                "antimicrobial activity",
                "affinity",
                "agonist activity",
                "receptor activity",
                "antineoplastic activity",
                "antibacterial activity",
                "antifungal activity",
                "cytotoxic activity",
                "antiviral activity",
                "specificity",
                "anti-inflammatory activity"
            ],
            "Which kind of {} can this molecule cause?": [
                "reaction",
                "binding",
                "coupling",
                "reduction"
            ],
            "What is the {} of this molecule's potency?":[
            ],
            "How is the {} of this molecule":[
                "solubility",
                "flammability",
                "corrosiveness",
                "ignitability",
                "stability",
                "pharmacological activity",
                "volatileness",
                "tolerability",
                "antioxidant activity",
                "cell permeability",
            ],
            "What is the {} of this molecule?":[
                "physical state",
                "odor",
                "mechanism",
                "potency",
                "color",
                "smell",
                "ph value",

            ],
            "What is the right information about this molecule's {}?": [
                "oxidation",
                "flash point",
                "density",
                "boiling point",
                "absorption",
                "safety concerns",
                "medical effects",
                "conversion",
                "storage",
                "therapeutic effects",
                "physiological effect",
                "melting point",
                "decomposition",
                "bioaccumulation",
                "sublimation",
                "resistance",
                "environmental impact",
                "excretion",
                "metabolism",
                "hydrolysis"
            ]
        },
        "Usage": {
            "Which kind of {} is this molecule?": [
                "antibiotic",
                "antagonist",
                "agonist",
                "sympathomimetic agent",
                "insecticide",
                "inhibitor",
                "agent",
                "antineoplastic agent",
                "antibacterial drug",
                "herbicide",
                "anticonvulsant",
                "antiemetic",
                "antimicrobial",
                "antiviral drug",
                "blocker",
                "orphan drug",
                "analgesic",
                "prodrug",
                "antipsychotic",
                "immunosuppressive agent",

            ],
            "How can the molecule be used as a/an {}": [
                "antiseptic",
                "pesticide",
                "agricultural chemical",
                "antidepressant",
                "intermediate",
                "modulator",
                "antioxidant",
                "biomarker",
                "preservative",
                "antihypertensive"
            ],
            "How can the molecule be used for {}": [
                "treatment",
                "production",
                "therapeutic use",
                "manufacture",
                "research",
                "disease control",
                "experiment"
            ],
            "What is the right {} information about this molecule?": [
                "approval",
                "clinical development",
                "efficacy",
                "potential therapeutic use",
                "safety concern",
                "dosage",
                "testing",
                "withdrawal"
            ]
        }
    }
    replace_table = {
        "antifungal drug": "treatment",
        "anticoronaviral agent": "agent",
        "agricultural chemicals": "agricultural chemical",
        "anticancerous efficacy": "efficacy",
        "withdrawn from market": "withdrawal",
        "sodium channel blocker": "blocker",
        "experimental": "experiment",
        "enzyme inhibition": "inhibitory activity",
    }
    cls_ques2topics = ques2topics[desc_cls]
    cls_QA_num = 0
    qa_pairs = {}
    not_found_topic = []
    for topic in desc_instances:
        instances = desc_instances[topic]
        if topic in replace_table:
            topic = replace_table[topic]
        qa_pairs[topic] = []
        found_question = False
        for question in cls_ques2topics:
            if topic in cls_ques2topics[question]:
                found_question = True
                for instance in instances:
                    cid, raw_text, ins_topic, option = instance
                    qa_pairs[topic].append([cid, raw_text, question.format(topic), option])
                    cls_QA_num += 1
        if found_question == False:
            not_found_topic.append(topic)
    
    with open(f"QA_pairs_{desc_cls}.json", "w") as fout:
        json.dump(qa_pairs, fout, indent=4)
    
    with open(f"Not_found_{desc_cls}.json", "w") as fout:
        json.dump(not_found_topic, fout, indent=4)

    print(f"{desc_cls}: {cls_QA_num}")
    # ques2options = {}
    # for question in cls_ques2topics:
    #     ques2options[question] = {}
    #     for topic in desc_instances:
    #         if topic in replace_table:
    #             topic = replace_table[topic]
    #         if topic in cls_ques2topics[question]:
    #             ques2options[question][topic] = [] # desc_instances[topic]
    #             for instance in desc_instances[topic]:
    #                 ques2options[question][topic].append(instance[3])
    # # if source_cls is not None:
    # #     ques2options_path = f"./{desc_cls}/ques2options_{source_cls}.json"
    # # else:
    # if not os.path.exists(f"./{desc_cls}"):
    #     os.mkdir(f"./{desc_cls}",)
    # ques2options_path = f"./{desc_cls}/ques2options.json"

    # with open(ques2options_path, "w") as f:
    #     json.dump(ques2options, f, indent=4)
    # # question = "Which kind of {} does this molecule have?"
    # for idx, question in enumerate(ques2options.keys()):
    #     print(f"Quesition: {question}")
    #     num_topic = 0
    #     num_qa_pair = 0
    #     topic2options = ques2options[question]
    #     if source_cls is not None:
    #         qa_pairs_path = f"./{desc_cls}/cls_desc_QA_pairs_{idx}_{source_cls}.json"
    #     else:
    #         qa_pairs_path = f"./{desc_cls}/cls_desc_QA_pairs_{idx}.json"
    #     if not num_qa_pair == 0:
    #         with open(qa_pairs_path, "w") as f:
    #             # 3093 QA pairs, 38 topic 
    #             json.dump(qa_pairs, f, indent=4)
    #         print(f"num_topic: {num_topic}, num_qa_pair: {num_qa_pair}")
    # if source_cls is not None:
    #     disc_options_from_desc_path = f"./{desc_cls}/disc_options_from_desc_{source_cls}.json"
    # else:
    #     disc_options_from_desc_path = f"./{desc_cls}/disc_options_from_desc.json"
    # with open(disc_options_from_desc_path, "w") as f:
    #     json.dump(disc_options_from_desc, f, indent=4)

if __name__ == "__main__":
    # for desc_cls in ["Property", "Structure", "Usage"]:
    #     extract_desc_ques(desc_cls)
    # generate_desc_structure_ques()
    # generate_desc_property_ques()
    # generate_desc_usage_ques()
    # refine_structure_options()
    for desc_cls in ["Property", "Usage"]:
        generate_desc_ques(desc_cls)
    # generate_desc_ques("Structure", "Property")
    # pass
