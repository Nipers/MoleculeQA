import requests
import json
import os
from tqdm import tqdm
import argparse

annotated_leaf_topics_path = "./fine_grained_CLS/generate_questions/{}/annotated_leaf_topics.json"
model = "./vicuna-13b-v1.5-16k"

# task_definition = "You are a chemistry research assistant, and I need you to complete the following task: You will be given a detailed description of a molecule and a topic, please extract specific information related to the given topic from the given descrption. Identify key phrases in the description that directly relate to the topic and present them concisely."

task_definition = "You are a chemistry research assistant, and I need you to complete the following task: You will be given a detailed description of a molecule, a question about the molecule and the answer for the question, please give me the  if the identification result about whether the answer is appropriate for the question. Please choose your RESULT from ['Yes', 'No']. "

rules_prefix = "Notice that here are some rules you need to follow:\n"

example_prefix = "Here are several examples to teach you how to extract information from description text of molecules:\n"

instance_prefix = "Here comes a task instance for you to extract: \n"
instance_suffix = "Just give me your OUTPUT about this molecule's {} information. No other information is needed."
url_ls = [
    "http://192.168.0.0:8000/v1/chat/completions",
    "http://192.168.0.0:8000/v1/chat/completions",
    "http://192.168.0.0:8000/v1/chat/completions",
    "http://192.168.0.0:8000/v1/chat/completions",

    "http://192.168.0.0:8000/v1/chat/completions",
    "http://192.168.0.0:8000/v1/chat/completions",
    "http://192.168.0.0:8000/v1/chat/completions",
    "http://192.168.0.0:8000/v1/chat/completions",
    "http://192.168.0.0:8000/v1/chat/completions",
    "http://192.168.0.0:8000/v1/chat/completions",
    "http://192.168.0.0:8000/v1/chat/completions",
    "http://192.168.0.0:8000/v1/chat/completions",
]
# prompts = [prompt_source, prompt_structure, prompt_usage, prompt_property, prompt_isolation]
# examples = [example_source, example_structure, example_usage, example_property, example_isolation]
# TYPE2CLASSES = ["Source", "Structure", "Usage", "Property", "Isolation"]

def add_example_prompt(origin_prompt, examples):
    formatted_examples = ""
    for exp_idx, example in enumerate(examples):
        # desc, topic, output = example
        # formatted_examples += f"Example {exp_idx}:\nDESCRIPTION: {desc}\nTOPIC: {topic}\RESULT: {output}\n\n"
        cid, desc, ques, ques_answer, result = example
        formatted_examples += f"Example {exp_idx}:\nDESCRIPTION: {desc}\nQUESTION: {ques}\nANSWER: {ques_answer}\nRESULT: {result}\n\n"
    # return origin_prompt + example_prefix + formatted_examples
    return origin_prompt + example_prefix + formatted_examples

def add_rules_prompt(origin_prompt, rules):
    formatted_notice = ""
    for rule_idx, rule in enumerate(rules):
        formatted_notice += f"Notice {rule_idx}:\n{rule}\n\n"
    return origin_prompt + rules_prefix + formatted_notice

def add_instance(origin_prompt, instance):
    desc, topic = instance
    formatted_instance = f"DESCRIPTION: {desc}\nTOPIC: {topic}\n"
    return origin_prompt + instance_prefix + formatted_instance + instance_suffix.format(topic)

def get_responce_from_api(instance, url_idx):
    # print(sample)

    headers = {
        'content-type': 'application/json',
    }
    url = url_ls[url_idx]
    for t in [0.1]:
        # print(f"Current temperature: {t}")
        # for i in range(1):
        data = {
            "model": model,     
            "temperature": t,
            "messages": [
                {
                "role": "user", 
                "content": instance
                }
            ],
            "max_tokens": 256
        }
        # print(prompt + example + instance)
        # print(json.dumps(data))
        while True:
            try:
                response = requests.post(url, headers=headers, data=json.dumps(data), timeout=10)
            except requests.exceptions.ReadTimeout:
                return -1
            # print(response)
            content = json.loads(response.content.decode('utf-8'))
            # print(content)
            # print(content)
            try:
                return content["choices"][0]["message"]["content"]
            except KeyError:
                return -2


def generate_instances(desc_cls):
    summary_path = "./QA/Category/{}/Orgainzed_compounds.json"
    summary_compounds = []
    for i in range(4):
        with open(summary_path.format(i), "r") as f:
            # print(summary_path.format(i))
            summary_compounds += json.load(f)
    if not os.path.exists("./QA/Category/{}/to_extract_topics.json".format(desc_cls)):
        cls_annotation_path = annotated_leaf_topics_path.format(desc_cls)
        to_extract_topics = {}
        usable_topics = {}
        if not os.path.exists(cls_annotation_path):
            with open("./fine_grained_CLS/generate_questions/{}/leaf_topics.json".format(desc_cls), "r") as f:
                cls_annotation = json.load(f)
            for topic in cls_annotation.keys():
                assigned_topic, attr_value = cls_annotation[topic]
                topic_cls = assigned_topic.split("%")[0]
                if not topic_cls in to_extract_topics:
                    to_extract_topics[topic_cls] = {}
                to_extract_topics[topic_cls][topic] = assigned_topic.split("%")[-1]
        else:
            with open(cls_annotation_path, "r") as f:
                cls_annotation = json.load(f)
            for topic in cls_annotation.keys():
                try:
                    assigned_topic, attr_value, usability = cls_annotation[topic]
                    topic_cls = assigned_topic.split("%")[0]
                    if not topic_cls in to_extract_topics:
                        to_extract_topics[topic_cls] = {}
                except ValueError:
                    print(topic)
                    continue
                if usability == "-":
                    to_extract_topics[topic_cls][topic] = assigned_topic.split("%")[-1]
                elif usability == "+":
                    usable_topics[topic] = attr_value
        
        with open("./fine_grained_CLS/generate_questions/{}/usable_topics.json".format(desc_cls), "w") as f:
            json.dump(usable_topics, f, indent=4)
        
        with open("./fine_grained_CLS/generate_questions/{}/to_extract_topics.json".format(desc_cls), "w") as f:
            json.dump(to_extract_topics, f, indent=4)
    to_extract_topics_path = "./fine_grained_CLS/generate_questions/{}/to_extract_topics.json".format(desc_cls)
    with open(to_extract_topics_path, "r") as f:
        to_extract_topics = json.load(f)

    instances_path = f"./fine_grained_CLS/generate_questions/{desc_cls}/instances"
    if not os.path.exists(instances_path):
        os.mkdir(instances_path)
    
    # reverse to_extract_topics
    tax2topics = {}
    for topic, tax in to_extract_topics[desc_cls].items():
        if not tax in tax2topics:
            tax2topics[tax] = []
        tax2topics[tax].append(topic)
    
    instance_num = 0
    with open("./fine_grained_CLS/generate_questions/{}/tax2topics.json".format(desc_cls), "w") as f:
        json.dump(tax2topics, f, indent=4)
    for tax in tax2topics.keys():
        tax_instance_path = os.path.join(instances_path, "{}.json".format(tax.replace(" ", "+")))
        tax_instances = {}

        for compound in summary_compounds:
            cid = compound["cid"]
            descriptions = compound["descriptions"]
            for description in descriptions:
                desc = description[1]
                summary = description[2]
                if not isinstance(summary, str):
                    continue
                for topic in tax2topics[tax]:
                    if summary.lower().find(f"\"{topic}\"") != -1:
                        if not cid in tax_instances:
                            tax_instances[cid] = []
                        tax_instances[cid].append([desc, tax])
                        instance_num += 1
                        break
        with open(tax_instance_path, "w") as f:
            json.dump(tax_instances, f, indent=4)
    
    print(f"Total instance number: {instance_num}")
    load_instances(desc_cls)

def load_instances(desc_cls):
    splited_instances_path = f"./fine_grained_CLS/generate_questions/{desc_cls}/instances"

    merged_instances_path = f"./fine_grained_CLS/generate_questions/{desc_cls}/instances.json"
    if not os.path.exists(merged_instances_path):
        instances = []
        for tax in os.listdir(splited_instances_path):
            tax_path = os.path.join(splited_instances_path, tax)
            with open(tax_path, "r") as f:
                tax_instances = json.load(f)
            for cid in tax_instances.keys():
                for instance in tax_instances[cid]:
                    instances.append([cid, instance[0], instance[1]])
        with open(merged_instances_path, "w") as f:
            json.dump(instances, f, indent=4)
    else:
        with open(merged_instances_path, "r") as f:
            instances = json.load(f)
    return instances 

def generat_answers(url_idx, desc_cls, split = 4):
    assert url_idx < split
    examples = {
        "Property": [
            [
                "Isolated from the aerial parts of Ipomoea pes-caprae, it has been found to exhibit potential inhibitory effect against multidrug resistance in the human breast cancer cell line It has a role as a metabolite.",
                "antineoplastic activity",
                "Exhibit potential inhibitory effect against multidrug resistance in the human breast cancer cell line."
            ],
            [
                "The molecule is a ten amino acid peptide formed by renin cleavage of angiotensinogen.",
                "formation",
                "Formed by renin cleavage of angiotensinogen."
                
            ],
            [   
                "The molecule is a pregnane-based steroidal hormone produced by the outer-section (zona glomerulosa) of the adrenal cortex in the adrenal gland, and acts on the distal tubules and collecting ducts of the kidney to cause the conservation of sodium, secretion of potassium, increased water retention, and increased blood pressure. The overall effect of aldosterone is to increase reabsorption of ions and water in the kidney.",
                "Effect",
                "Acts on the distal tubules and collecting ducts of the kidney to cause the conservation of sodium, secretion of potassium, increased water retention, and increased blood pressure; increases reabsorption of ions and water in the kidney."
            ],
            [
                "It inhibits a specific step in the synthesis of the peptidoglycan layer in the Gram-positive bacteria Staphylococcus aureus and Clostridium difficile.",
                "mechanism",
                "Inhibits a specific step in the synthesis of the peptidoglycan layer in the Gram-positive bacteria Staphylococcus aureus and Clostridium difficile."
            ],
            [
                "In contrast to arylboronat-based probes, it shows high specificity for H2O2 over peroxynitrite (which is much more reactive than H2O2, but exists at much lower abundance).",
                "Specificity",
                "Shows high specificity for H2O2 over peroxynitrite."
            ],
            [
                "The molecule is the conjugate acid of (S)-nicotine arising from selective protonation of the tertiary amino group; major species at pH 7.3.",
                "ph value",
                "major species at pH 7.3."
            ]
        ],
        "Structure": [
            [
                "It is an indole phytoalexin and a member of 1,3-thiazoles. The molecule is an indole phytoalexin that is indole substituted at position 3 by a 1,3-thiazol-2-yl group",
                "base",
                "Indole phytoalexin"
            ],
            [
                "The molecule is a carbohydrate sulfonate that is 3-deoxy-D-erythro-hex-2-ulosonic acid in which the hydroxy group at position 6 is replaced by a sulfo group.",
                "base",
                "3-deoxy-D-erythro-hex-2-ulosonic acid"
            ],
            [
                "It is a conjugate acid of a glycerol 1-phosphate(2-).",
                "conjugate acid",
                "A conjugate acid of glycerol 1-phosphate(2-)"
            ],
            [                
                "It is a cyclic terpene ketone, an epoxide and a tirucallane triterpenoid.",
                "epoxide",
                "Epoxide"
            ],
            [
                "The molecule is a beta-diketone that is cyclohexa-1,3-dione which is substituted at position 2 by an N-ethoxybutanimidoyl group and at position 5 by a tetrahydro-2H-thiopyran-3-yl group.",
                "position",
                "Substituted at position 2 by an N-ethoxybutanimidoyl group, at position 5 by a tetrahydro-2H-thiopyran-3-yl group."

            ],
            [                
                "The molecule is a tripeptide composed of one L-phenylalanine and two glycine residues joined in sequence.",
                "residue",
                "Two glycine residues joined in sequence."
            ],
            [
                "The molecule is a steroid ester obtained by the formal condensation of the hydroxy group of beta-sitosterol with acetic acid.",
                "acetic acid",
                "Formal condensation of the hydroxy group of beta-sitosterol with acetic acid."
            ],
            [
                "The molecule is an oxo-5beta-cholanic acid in which three oxo substituents are located at positions 3, 7 and 12 on the cholanic acid skeleton.",
                "position",
                "Three oxo substituents are located at positions 3, 7 and 12 on the cholanic acid skeleton."
            ],
            [
                "It is a tautomer of a 1D-3-amino-1-guanidino-1,3-dideoxy-scyllo-inositol 6-phosphate dizwitterion.",
                "tautomer",
                "A tautomer of a 1D-3-amino-1-guanidino-1,3-dideoxy-scyllo-inositol 6-phosphate dizwitterion."
            ],
            [
                "The molecule is a 1-(alk-1-enyl)-2-acyl-sn-glycero-3-phosphoethanolamine in which the alkyl and the acyl groups at positions 1 and 2 are specified as (1Z,11Z)-octadecadienyl and linoleoyl respectively.",
                "alkyl group",
                "Alkyl group at position 1 is specified as (1Z,11Z)-octadecadienyl."
            ],
            [
                "The molecule is an unsaturated fatty acyl-CoA that results from the formal condensation of the thiol group of coenzyme A with the carboxy group of (8Z,11Z,14Z)-3-oxoicosa-8,11,14-trienoic acid. It is a long-chain fatty acyl-CoA, an unsaturated fatty acyl-CoA and a 3-oxo-fatty acyl-CoA. It is a conjugate acid of an (8Z,11Z,14Z)-3-oxoicosa-8,11,14-trienoyl-CoA(4-).",
                "thiol group",
                "Thiol group of coenzyme A"
            ],
            [
                "The molecule is a hydroxycalciol that is a synthetic analogue of vitamin D3 which contains an oxolane ring and exhibits weak vitamin D receptor agonist activity It has a role as a vitamin D receptor agonist. It is a member of oxolanes, a hydroxycalciol and a member of D3 vitamins.",
                "ring",
                "Contains an oxolane ring."
            ],
            [
                "The molecule is a dipeptide comprising of beta-alanine and 3-methyl-L-histidine units.",
                "unit",
                "Comprising of Beta-alanine and 3-methyl-L-histidine units."
            ]
        ],
        "Usage": [
            [
                "An acaricide used for the control of mites on citrus and cotton crops. It has a role as an acaricide.",
                "acaricide",
                "An Acaricide used for the control of mites on citrus and cotton crops"
            ],
            [
                "It has fungistatic properties (based on release of acetic acid) and has been used in the topical treatment of minor dermatophyte infections. It has a role as a plant metabolite, a solvent, a fuel additive, an adjuvant, a food additive carrier, a food emulsifier, a food humectant and an antifungal drug.",
                "solvent",
                "Has a role as a solvent."
            ],
            [
                "It is a herbicide safener, used in conjunction with the Bayer herbicide tembotrione. It has a role as a herbicide safener.",
                "herbicide safener",
                "A herbicide safener used in conjunction with the Bayer herbicide tembotrione."
            ],
            [
                "The molecule is the fluorescent compound widely used in experimental cell biology and biochemistry to reveal double-stranded DNA and RNA. It has a role as an intercalator and a fluorochrome.",
                "experimental",
                "Widely used in experimental cell biology and biochemistry to reveal double-stranded DNA and RNA. It has a role as an intercalator and a fluorochrome."
            ],
            [
                "It is used as a post-emergence herbicide used (generally as a salt or ester) for the control of annual weeds in wheat and oilseed rape. It is not approved for use with the European Union. It has a role as a proherbicide and a synthetic auxin.",
                "approval",
                "Not approved for use with the European Union."
            ],
            [
                "It exhibits anti-HIV, antimalarial, antineoplastic and anti-inflammatory properties.",
                "antimalarial",
                "Exhibits antimalarial properties."
            ],
            [
                "It is an analgesic which is used for the treatment of moderate to severe pain, including postoperative pain and labour pain. It has a role as an opioid analgesic, a kappa-opioid receptor agonist, a mu-opioid receptor agonist and an antispasmodic drug.",
                "agonist",
                "A kappa-opioid receptor agonist and a mu-opioid receptor agonist."
            ]
        ],

    }
    rules = [
        "Your output should be phrases or sentences from original descriptions, no need to overwrite them.",
        "For my convenience, please directly output the extraction RESULT, without any other information.",
        'If there is no infomation about given topic in the description, please return "No information found"',
    ]
    original_prompt = task_definition
    original_prompt = add_example_prompt(original_prompt, examples[desc_cls])
    original_prompt = add_rules_prompt(original_prompt, rules)

    instances = load_instances(desc_cls)
    print(len(instances))
    batch_size = len(instances) // split + 1
    to_process_instances = instances[batch_size * url_idx: batch_size * (url_idx + 1)]
    outputs_ls = []
    for instance in tqdm(to_process_instances, total=len(to_process_instances)):
        cid, desc, topic = instance
        instance = add_instance(original_prompt, [desc, topic])
        outputs_ls.append(get_responce_from_api(instance, url_idx))
    print(outputs_ls)
    with open(f"./fine_grained_CLS/generate_questions/{desc_cls}/outputs_{url_idx}.json", "w") as f:
        print(f"outputs_{url_idx}.json")
        json.dump(outputs_ls, f, indent=4)
    # instances = [
    #     ["A colourless, odourless gas under normal conditions, it is produced during respiration by all animals, fungi and microorganisms that depend directly or indirectly on living or decaying plants for food.", "Appearance"],
    #     ["Differentiates 5-HT1D sub-types. Also displays affinity for rodent 5-HT5B, 5-HT5A, 5-HT7 and 5-HT6 receptors (pK1 values are 6.6, 7.0, 8.4 and 8.7 respectively).", "affinity"],
    #     ["Isolated from the whole plant of Coleus forskohlii, it shows relaxative effects on isolated guinea pig tracheal spirals in vitro.", "Effect"],
    # ]
    # for instance in instances:
    #     instance = add_instance(original_prompt, instance)
    #     print(instance)
    #     print(get_responce_from_api(instance, url_idx))
    #     # break

# Property instance num: 2694
        
def assemble_answers(desc_cls, split):
    outputs = []
    for i in range(split):
        with open(f"./fine_grained_CLS/generate_questions/{desc_cls}/outputs_{i}.json", "r") as f:
            outputs += json.load(f)
    with open(f"./fine_grained_CLS/generate_questions/{desc_cls}/instances.json", "r") as f:
        instances = json.load(f)
    assert len(outputs) == len(instances)
    for i in range(len(outputs)):
        if not isinstance(outputs[i], str):
            answer = "No information found"
        else:
            answer = outputs[i].strip()
        if answer.find(":") != -1:
            answer = outputs[i].split(":")[1:]
            answer = " ".join(answer).strip()
        instances[i].append(answer)
    with open(f"./fine_grained_CLS/generate_questions/{desc_cls}/answered_instance.json", "w") as f:
        json.dump(instances, f, indent=4)



if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--url_idx", type=int, default=0)
    parser.add_argument("--split", type=int, default=4)
    parser.add_argument("--desc_cls", type=str, default="Usage")
    parser.add_argument("--mode", type=str, default="assemble")
    args = parser.parse_args()
    if args.mode == "extract":
        generat_answers(args.url_idx, args.desc_cls, args.split)
    elif args.mode == "assemble":
        assemble_answers(args.desc_cls, args.split)
    else:
        generate_instances(args.desc_cls)
