import json
import os
import sys
sys.path.append("..")
from assignment import taxonomy_path
from parse_xmind import DESC_CLASSES
assignment_path = "./fine_grained_CLS/assignment/{}/final_assignment.json"
topics_path = "./fine_grained_CLS/category_topics/{}_dict_conclusion_rm_few.json"
quesion_path = "./fine_grained_CLS/generate_questions/{}"
def get_leaf_nodes():
    all_leaf_nodes = set()
    for desc_cls in DESC_CLASSES:
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

def extract_leaf_topics(desc_cls):
    cls_topics_path = topics_path.format(desc_cls)
    cls_questions_path = quesion_path.format(desc_cls)
    if not os.path.exists(cls_questions_path):
        os.makedirs(cls_questions_path)
    with open(cls_topics_path, "r") as f:
        cls_topics = json.load(f)
    
    leaf_nodes = get_leaf_nodes()
    
    cls_assignment_path = assignment_path.format(desc_cls)
    with open(cls_assignment_path, "r") as f:
        cls_assignment = json.load(f)
    leaf_topics = {}
    for key, tax in cls_assignment.items():
        last_tax = tax.split("%")[-1]
        if last_tax in leaf_nodes:
            for topic, attr_dict in cls_topics:
                if topic == key:
                    leaf_topics[key] = [tax, list(attr_dict.keys())]
                    break
    non_leaf_topics = {}
    for key, tax in cls_assignment.items():
        if not key in leaf_topics:
            for topic, attr_dict in cls_topics:
                if topic == key:
                    non_leaf_topics[key] = [tax, list(attr_dict.keys())]
                    break
    cls_leaf_path = os.path.join(cls_questions_path, "leaf_topics.json")
    cls_non_leaf_path = os.path.join(cls_questions_path, "non_leaf_topics.json")
    with open(cls_leaf_path, "w") as f:
        json.dump(leaf_topics, f, indent=4)
    with open(cls_non_leaf_path, "w") as f:
        json.dump(non_leaf_topics, f, indent=4)
    


def generate_questions(desc_cls):
    # generate questions for leaf topics
    cls_questions_path = quesion_path.format(desc_cls)
    cls_leaf_path = os.path.join(cls_questions_path, "leaf_topics.json")
    with open(cls_leaf_path, "r") as f:
        leaf_topics = json.load(f)

def create_file(parent_dir, sub_dirs, file_name):
    for sub_dir in sub_dirs:
        cur_dir = os.path.join(parent_dir, sub_dir)
        if not os.path.exists(cur_dir):
            continue
        file_path = os.path.join(cur_dir, file_name)
        if not os.path.exists(file_path):
            open(file_path, "w").close()

if __name__ == "__main__":
    for desc_cls in DESC_CLASSES:
        if not desc_cls == "Source":
            w(desc_cls)
    # create_file(quesion_path.format(""), DESC_CLASSES, "processed_.json")
            