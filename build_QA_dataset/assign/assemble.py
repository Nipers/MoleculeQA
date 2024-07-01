import json
from assign import get_leaf_nodes
# Used to assemble topics assigned by name and manually assigned topics
# first, put together, then divide into Property and Usage

# Need to build triples in cid, topic and raw text

# Need to remove instance not start with "This molecule" from raw text

cls2id = {"Property":2, "Usage":3}
def assemble_and_devide():
    dup_num = 0
    # with open("./assignment.json", "r") as fin:
    #     assignment = json.load(fin)
    # key2topic = {}
    # for cls in cls2id.keys():
    #     cls_assignment = assignment[cls]
    #     for key in cls_assignment["found"].keys():
    #         key2topic[key] = cls_assignment["found"][key]
    #     with open(f"assigned_key2topic_{cls}.json", "r") as fin:
    #         cls_assigned_key2topic = json.load(fin)
    #     for key in cls_assignment["to_assign"]:
    #         if key in cls_assigned_key2topic:
    #             key2topic[key] = cls_assigned_key2topic[key]
    # with open("final_assignment.json", "w") as fin:
    #     json.dump(key2topic, fout, indent=4)
    
    with open("final_assignment.json", "r") as fin:
        key2topic = json.load(fin)
    
    assembled_instances = []
    topic2value = {}
    cid2topic = {}
    with open("../extracted_content/legal_extracted_contents.json", "r") as fin:
        extracted_contents = json.load(fin)
    for instance in extracted_contents:
        extracted_content = json.loads(instance[4])
        cls = list(extracted_content.keys())[0]
        extracted_content = extracted_content[cls]
        for key in extracted_content:
            if key in key2topic:
                topic = key2topic[key]
                topic = topic.lower()
                if isinstance(extracted_content[key], str):
                    if not topic in topic2value:
                        topic2value[topic] = []
                    topic2value[topic].append(extracted_content[key])
                    if not instance[0] in cid2topic:
                        cid2topic[instance[0]] = []
                    if topic in cid2topic[instance[0]]:
                        dup_num += 1
                        continue
                    else:
                        cid2topic[instance[0]].append(topic)
                        assembled_instances.append([instance[0], instance[2], topic, extracted_content[key]])
    
    # with open("./assembled_instances.json", "w") as fout:
    #     json.dump(assembled_instances, fout, indent=4)
    print(len(assembled_instances))
    print(dup_num)
    
    with open("./topic2value.json", "w") as fout:
        json.dump(topic2value, fout, indent=4)

    cls_assembled_instances = {
        "Property": {},
        "Usage": {},
    }

    with open("./new_topic.json", "r") as fin:
        new_topic = json.load(fin)

    for cls in cls2id.keys():
        cls_leaf_node = get_leaf_nodes(cls)
        with open(f"leaf_node_{cls}.json", "w") as fout:
            json.dump(list(cls_leaf_node), fout, indent=4)
        for assembled_instance in assembled_instances:
            if assembled_instance[2] in cls_leaf_node:
                if not assembled_instance[2] in cls_assembled_instances[cls]:
                    cls_assembled_instances[cls][assembled_instance[2]] = []
                cls_assembled_instances[cls][assembled_instance[2]].append(assembled_instance)
            elif assembled_instance[2] in new_topic and new_topic[assembled_instance[2]] == cls:
                if not assembled_instance[2] in cls_assembled_instances[cls]:
                    cls_assembled_instances[cls][assembled_instance[2]] = []
                cls_assembled_instances[cls][assembled_instance[2]].append(assembled_instance)
    
    with open("./assembled_instances.json", "w") as fout:
        json.dump(cls_assembled_instances, fout, indent=4)
    
    # statistics
    for cls in cls_assembled_instances:
        cls_num = 0
        for topic in cls_assembled_instances[cls]:
            cls_num += len(cls_assembled_instances[cls][topic])
        print(f"{cls}: {cls_num}")

    # print(len(cls_assembled_instances["Property"]))
    # print(len(cls_assembled_instances["Usage"]))
    
    # all_leaf_node = get_leaf_nodes("Property") | get_leaf_nodes("Usage")
    # new_topic = {}
    # for topic in topic2value:
    #     if not topic in all_leaf_node:
    #         new_topic[topic] = ""
    # with open("./new_topic.json", "w") as fout:
    #     json.dump(new_topic, fout, indent=4)
    final_topics = {}
    for cls in cls_assembled_instances:
        final_topics[cls] = list(cls_assembled_instances[cls].keys())
    with open("./final_topics.json", "w") as fout:
        json.dump(final_topics, fout,indent=4)
    removed_topic = {}
    for topic in topic2value:
        if not topic in cls_assembled_instances["Property"] and not topic in cls_assembled_instances["Usage"]:
            removed_topic[topic] = ""
    with open("./removed_topic.json", "w") as fout:
        json.dump(removed_topic, fout, indent=4)
    
    # usable_topics = {}
    # # for manually annotate
    # for cls in cls_assembled_instances:
    #     usable_topics[cls] = {}
    #     for topic in cls_assembled_instances[cls]:
    #         usable_topics[cls][topic] = 0
    # with open("./usable_topics.json", "w") as fout:
    #     json.dump(usable_topics, fout, indent=4)
    
    desc_instances = {
        "Usage": {},
        "Property": {}
    }

    with open("./usable_topics.json", "r") as fin:
        usable_topics = json.load(fin)
    for cls in cls_assembled_instances:
        cls_desc_num = 0
        for topic in cls_assembled_instances[cls]:
            if usable_topics[cls][topic] == 1:
                desc_instances[cls][topic] = cls_assembled_instances[cls][topic]
                cls_desc_num += len(cls_assembled_instances[cls][topic])
        print(f"{cls}: {cls_desc_num}")
    
    with open("./desc_instances.json", "w") as fout:
        json.dump(desc_instances, fout, indent=4)

        
    

if __name__ == "__main__":
    assemble_and_devide()