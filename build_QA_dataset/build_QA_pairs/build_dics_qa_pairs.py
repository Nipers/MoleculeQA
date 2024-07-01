import json
import os

# Build two kinds of QA pairs: disc and desc

# class QA_Pair:
#     def __init__(self, question, options, label):
#         self.question = question
#         self.options = options
#         self.label = label
source_path = "./fine_grained_CLS/generate_questions"
target_path = "./"

def refine_and_gather_answers(desc_cls, file_name): # used to get options for a specific topic
    if file_name == "usable_topics":
        with open(os.path.join(source_path, desc_cls, "usable_topics.json"), "r") as f:
            base_options = json.load(f)
        disc_options = {}
        desc_options = {}
        with open(os.path.join(f"./{desc_cls}", "annotated_usable_topics.json"), "r") as f:
            annotated_options = json.load(f)
        for topic in annotated_options:
            if annotated_options[topic] == "remove":
                base_options.pop(topic)
            elif annotated_options[topic] == 0:
                disc_options[topic] = base_options[topic]
            elif annotated_options[topic] == 1:
                desc_options[topic] = base_options[topic]
        with open(os.path.join(f"./{desc_cls}", "desc_usable_topics.json"), "w") as f:
            json.dump(desc_options, f, indent=4)
        with open(os.path.join(f"./{desc_cls}", "disc_usable_topics.json"), "w") as f:
            json.dump(disc_options, f, indent=4)

    elif file_name == "instances":
        with open("./fine_grained_CLS/generate_questions/Property/answered_instance.json", "r") as f:
            base_options = json.load(f)
        disc_options = {}
        desc_options = {}

def assemble_answered_instances(desc_cls):
    answered_instance_path = os.path.join(source_path, desc_cls, "answered_instance.json")
    with open(answered_instance_path, "r") as f:
        answered_instances = json.load(f)
    dup_options = {}
    no_dup_options = {}
    
    for answered_instance in answered_instances:
        # print(answered_instance)
        cid, desc, topic, answer = answered_instance
        if answer.lower().find("no information found") != -1:
            continue
        if answer in no_dup_options:
            topics = no_dup_options.pop(answer)
            if not answer in dup_options:
                dup_options[answer] = set()
            dup_options[answer].update(topics)
        else:
            no_dup_options[answer] = set()
            no_dup_options[answer].add(topic)
    
    dup_topic2options = {}
    no_dup_topic2options = {}
    multi_topic_dup_options = {}
    multi_topic_no_dup_options = {}
    for answer in no_dup_options:
        if len(no_dup_options[answer]) == 1:
            topic = list(no_dup_options[answer])[0]
            if not topic in no_dup_topic2options:
                no_dup_topic2options[topic] = []
            no_dup_topic2options[topic].append(answer)
        else:
            multi_topic_no_dup_options[answer] = list(no_dup_options[answer])
    for answer in dup_options:        
        if len(dup_options[answer]) == 1:
            topic = list(dup_options[answer])[0]
            if not topic in dup_topic2options:
                dup_topic2options[topic] = []
            dup_topic2options[topic].append(answer)
        else:
            multi_topic_dup_options[answer] = list(dup_options[answer])

    with open(os.path.join(target_path, desc_cls, "no_dup_topic2options.json"), "w") as f:
        json.dump(no_dup_topic2options, f, indent=4)

    with open(os.path.join(target_path, desc_cls, "dup_topic2options.json"), "w") as f:
        json.dump(dup_topic2options, f, indent=4)

    with open(os.path.join(target_path, desc_cls, "multi_topic_no_dup_options.json"), "w") as f:
        json.dump(multi_topic_no_dup_options, f, indent=4)

    with open(os.path.join(target_path, desc_cls, "multi_topic_dup_options.json"), "w") as f:
        json.dump(multi_topic_dup_options, f, indent=4)
        
def generate_discriminative_questions(desc_cls):
    annotated_no_dup_path = f"./fine_grained_CLS/build_QA_pairs/{desc_cls}/annotated_no_dup_topic2options.json"
    with open(annotated_no_dup_path) as f:
        annotated_no_dup_topic2options = json.load(f)
    disc_topics = set()
    for topic in annotated_no_dup_topic2options:
        options = annotated_no_dup_topic2options[topic]
        if options[-1] == 2:
            disc_topics.add(topic)
    annotated_no_dup_path = f"./fine_grained_CLS/build_QA_pairs/{desc_cls}/no_dup_topic2options.json"
    with open(annotated_no_dup_path) as f:
        no_dup_topic2options = json.load(f)
    disc_topic2options = {}
    for topic in disc_topics:
        disc_topic2options[topic] = no_dup_topic2options[topic]
    with open(f"./{desc_cls}/no_dup_disc_topic2options.json", "w") as f:
        json.dump(disc_topic2options, f, indent=4)
    
    questions = {
        "Property": {
            "What activity does the molecule exhibit?": ["antimalarial activity", "radical scavenging activity", "antioxidant activity", "immunosuppressive activity"]
        },
        "Structure": {
            "what kind of compound does this molecule belong to?": [
                "alcohol", 
                "amino compound", 
                "enone", 
                "fatty acyl-coa", 
                "macrocycle", 
                "ketone", 
                "enamide", 
                "lactone", 
                "secondary alpha-hydroxy ketone", 
                "alpha-hydroxy ketone", 
                "oligosaccharide", 
                "oligosaccharide derivative", 
                "monocarboxylic acid", 
                "hapten", 
                "dicarboxylic acid",
                "heterobicyclic",
                "organobromine compound",
                "organic sulfide",
                "dimethoxybenzene",
                "polyphenol",
                "aromatic ether",
                "cyclic ether",
                "organochlorine compound",
                "c-nitro compound"
            ],
        },
        "Usage": {
            "What can this molecule be used as?": [
                "antitussive",
                "antiemetic",
                "analgesic",
                "biomarker",
                "solvent",
                "antimalarial",
                "acaricide",
                "antiinfective agent",
                "anticonvulsant",
                "immunosuppressive agent"
            ]
        }
    }
    cls_disc_QA_pairs = []
    instance_path = f"./fine_grained_CLS/generate_questions/{desc_cls}/answered_instance.json"
    with open(instance_path, "r") as f:
        cls_instances = json.load(f)
    cls_question = questions[desc_cls]
    processed_topic = set()
    for question in cls_question:
        for instance in cls_instances:
            cid, desc, topic, answer = instance
            if topic in cls_question[question] and answer in disc_topic2options[topic]:
                cls_disc_QA_pairs.append([cid, desc, question, topic])
                processed_topic.add(topic)
    
    for topic in disc_topic2options:
        if not topic in processed_topic:
            print(topic)
    
    with open(f"./{desc_cls}/disc_QA_pairs_no_dup.json", "w") as f:
        json.dump(cls_disc_QA_pairs, f, indent=4)


def generate_descriptive_questions_for_source():
    pass

if __name__ == "__main__":
    # refine_and_gather_answers("Property", "usable_topics")
    # refine_and_gather_answers("Property", "instances")
    # assemble_answered_instances("Structure")
    # assemble_answered_instances("Usage")
    # assemble_answered_instances("Property")
    for desc_cls in ["Property", "Structure", "Usage"]:
        generate_discriminative_questions(desc_cls)
    # generate_discriminative_questions("Property")
    # print("------------------")
    # generate_discriminative_questions("Structure")
    # print("------------------")
    # generate_discriminative_questions("Usage")
# in total: 2902