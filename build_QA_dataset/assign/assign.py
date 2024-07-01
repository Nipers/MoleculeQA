import json


taxonomy_path = "./fine_grained_CLS/fine_grained_cls.json"
def get_leaf_nodes(desc_cls):
    all_leaf_nodes = set()
    if not desc_cls == "Source":
        leaf_nodes = set()
        with open(taxonomy_path, "r") as f:
            taxonomy = json.load(f)
            cls_tax = taxonomy[desc_cls]
        
        for sub_attr in cls_tax:
            if isinstance(cls_tax[sub_attr], list):
                leaf_nodes.update(cls_tax[sub_attr])
            else:
                for sub_sub_attr in cls_tax[sub_attr]:
                    assert isinstance(cls_tax[sub_attr][sub_sub_attr], list)
                    leaf_nodes.update(cls_tax[sub_attr][sub_sub_attr])
    # print(leaf_nodes)
        all_leaf_nodes.update(leaf_nodes)
    return all_leaf_nodes


def assign_by_name():
    with open("cls2topic.json", "r") as fin:
        cls2topic = json.load(fin)

    assignment = {}
    for cls in cls2topic:
        with open(f"./fine_grained_CLS/assignment/{cls}/unfound_keys.json", "r") as fin:
            unfound_leaf = json.load(fin)
        
        found_topics = {}
        to_assign_topics = []
        removed_topics = []
        found_num = 0
        to_assign_num = 0
        removed_num = 0
        leaf_node = get_leaf_nodes(cls)
        for key in unfound_leaf:
            leaf_node.add(key)
        topics = cls2topic[cls]
        for topic in topics:
            assigned = False
            name, num = topic
            for leaf in leaf_node:
                if leaf.lower() in name.lower() or name.lower() in leaf.lower():
                    found_topics[name] = leaf
                    found_num += num
                    assigned = True
                    break
            if not assigned:
                if num > 10:
                    to_assign_num += num
                    to_assign_topics.append(name)
                else:
                    removed_num += num
                    removed_topics.append(name)
        
        assignment[cls] = {}
        assignment[cls]["found"] = found_topics
        assignment[cls]["to_assign"] = to_assign_topics
        assignment[cls]["removed"] = removed_topics
        print(f"{cls}: {len(found_topics)}/{found_num}, {len(to_assign_topics)}/{to_assign_num}, {len(removed_topics)}/{removed_num}")
    with open("assignment.json", "w") as fout:
        json.dump(assignment, fout, indent=4)
cls2id = {"Property":2, "Usage":3}
def get_topic2value():
    
    with open("../extracted_content/legal_extracted_contents.json", "r") as fin:
        extracted_contents = json.load(fin)
    with open("./assignment.json", "r") as fin:
        assignment = json.load(fin)
    for cls in assignment:
        assigned_topic2value = {}
        to_assign_key2value = {}
        assigned = assignment[cls]["found"]
        to_assign = assignment[cls]["to_assign"]
        cls_id = cls2id[cls]
        for instance in extracted_contents:
            if instance[3] == cls_id:
                extracted_content = json.loads(instance[4])
                if isinstance(extracted_content[cls], dict):
                    for key in extracted_content[cls]:
                        if key in assigned:
                            topic = assigned[key]
                            if not topic in assigned_topic2value:
                                assigned_topic2value[topic] = []
                            assigned_topic2value[topic].append(extracted_content[cls][key])
                        elif key in to_assign:
                            if not key in to_assign_key2value:
                                to_assign_key2value[key] = []
                            to_assign_key2value[key].append(extracted_content[cls][key])
        with open(f"assigned_topic2value_{cls}.json", "w") as fout:
            json.dump(assigned_topic2value, fout, indent=4)
        with open(f"to_assign_key2value_{cls}.json", "w") as fout:
            json.dump(to_assign_key2value, fout, indent=4)


if __name__ == "__main__":
    # assign_by_name()
    get_topic2value()
# Property: 637/9149, 61/2227, 1975/3057
# Usage: 344/2498, 65/5249, 1774/2878