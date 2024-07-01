from parse_xmind import *
import os
xmind_path = "./fine_grained_CLS/CompoundQA.xmind"
assignment_path = "./fine_grained_CLS/assignment"
attr_value_path = "./fine_grained_CLS/assignment/{}/dict_conclusion_rm_few.json"
new_taxonomy_path = "./fine_grained_CLS/new_taxonomy.json"
def get_att2str():
    topic_dict = parse_xmind(xmind_path)
    attr2str = {}
    for desc_cls in topic_dict:
        attr2str[desc_cls] = desc_cls
        cls_topic = topic_dict[desc_cls]
        if isinstance(cls_topic, list):
            for attr in cls_topic:
                attr2str[attr] = "%".join([desc_cls, attr])
        else:
            for sub_topic in cls_topic:
                attr2str[sub_topic] = "%".join([desc_cls, sub_topic])
                if isinstance(cls_topic[sub_topic], list):
                    for attr in cls_topic[sub_topic]:
                        attr2str[attr] = "%".join([desc_cls, sub_topic, attr])
                elif isinstance(cls_topic[sub_topic], dict):
                    for sub_sub_topic in cls_topic[sub_topic]:
                        attr2str[sub_sub_topic] = "%".join([desc_cls, sub_topic, sub_sub_topic])
                        assert isinstance(cls_topic[sub_topic][sub_sub_topic], list)
                        for attr in cls_topic[sub_topic][sub_sub_topic]:
                            attr2str[attr] = "%".join([desc_cls, sub_topic, sub_sub_topic, attr])
    
    # add some new attrs
    attr2str["Industrial Applications"] = "Usage%Industrial Applications"
    attr2str["food additive"] = "Usage%Industrial Applications%food additive"
    
    return attr2str

def assign_topic_for_unassigned_keys(desc_cls, unassigned_keys):
    unfound_path = os.path.join(assignment_path, desc_cls, "unfound_keys.json")
    assigned_path = os.path.join(assignment_path, desc_cls, "assignment4unassigned.json")
    attr2str = get_att2str()
    attr_assignment = {}
    unfound_keys = {}
    for attr, assignment in unassigned_keys.items():
        if assignment.endswith("-"):
            assignment = assignment[:-3]
            if not assignment in attr2str:
                unfound_keys[attr] = assignment
                continue
            attr_str = attr2str[assignment] + f"-{assignment}"
        else:
            if assignment.endswith("+"):
                assignment = assignment[:-3]
            if not assignment in attr2str:
                unfound_keys[attr] = assignment
                continue
            attr_str = attr2str[assignment]
        attr_assignment[attr] = attr_str
    with open(unfound_path, "w") as unfound_file:
        json.dump(unfound_keys, unfound_file, indent=4)
    with open(assigned_path, "w") as assigned_file:
        json.dump(attr_assignment, assigned_file, indent=4)

def get_cls_attr_value(desc_cls):
    cls_attr_value_path = attr_value_path.format(desc_cls)
    key2value = {}
    with open(cls_attr_value_path, "r") as f:
        cls_attr_value = json.load(f)
    for attr, value in cls_attr_value:
        key2value[attr] = list(value.keys())
    return key2value


def process_unassigned_keys():
    for desc_cls in DESC_CLASSES:
        split_path = os.path.join(assignment_path, desc_cls, "to_split.json")
        removed_path = os.path.join(assignment_path, desc_cls, "removed.json")
        to_split = []
        removed = []
        unassigned_keys_path = os.path.join(assignment_path, desc_cls, "unassigned_keys.json")
        if os.path.exists(unassigned_keys_path):
            with open(unassigned_keys_path, "r") as unassigned_keys_file:
                unassigned_keys = json.load(unassigned_keys_file)
            filtered_unassigned_keys = {}
            for key, assignment in unassigned_keys.items():
                if assignment == "split":
                    to_split.append(key)
                elif assignment == "remove":
                    removed.append(key)
                else:
                    filtered_unassigned_keys[key] = assignment
            assign_topic_for_unassigned_keys(desc_cls, filtered_unassigned_keys)

            key2value = get_cls_attr_value(desc_cls)
            to_split_key_value = {}
            with open(split_path, "w") as split_file:
                for key in to_split:
                    # add attr value
                    if key in key2value:
                        to_split_key_value[key] = key2value[key]
                    else:
                        # to_split_key_value.append([key, []])
                        to_split_key_value[key] = []
                json.dump(to_split_key_value, split_file, indent=4)

            
            with open(removed_path, "w") as removed_file:
                json.dump(removed, removed_file, indent=4)

def merge_assignment():
    for desc_cls in DESC_CLASSES:
        by_name_assignment_path = os.path.join(assignment_path, desc_cls, "assignment.json")
        newly_assignment_path = os.path.join(assignment_path, desc_cls, "assignment4unassigned.json")
        final_assignment_path = os.path.join(assignment_path, desc_cls, "final_assignment.json")
        if not os.path.exists(by_name_assignment_path):
            continue
        with open(by_name_assignment_path, "r") as f:
            by_name_assignment = json.load(f)
        with open(newly_assignment_path, "r") as f:
            newly_assignment = json.load(f)
        for key, assignment in newly_assignment.items():
            by_name_assignment[key] = assignment
        with open(final_assignment_path, "w") as f:
            json.dump(by_name_assignment, f, indent=4)

def merge_taxonomy():
    taxonomy_dict = parse_xmind(xmind_path)
    for desc_cls in DESC_CLASSES:
        by_name_assignment_path = os.path.join(assignment_path, desc_cls, "assignment.json")
        newly_assignment_path = os.path.join(assignment_path, desc_cls, "assignment4unassigned.json")
        if not os.path.exists(by_name_assignment_path):
            continue
        with open(by_name_assignment_path, "r") as f:
            by_name_assignment = json.load(f)
        with open(newly_assignment_path, "r") as f:
            newly_assignment = json.load(f)
            
        for key, assignment in by_name_assignment.items():
            assignments = assignment.split("%")
            # check if the assignment is valid
            cur_taxonomy = taxonomy_dict
            for idx, assignment in enumerate(assignments):
                assert assignment in cur_taxonomy, f"{assignment} not in original taxonomy"
                if not idx == len(assignments) - 1:
                    cur_taxonomy = cur_taxonomy[assignment]

        for key, assignment in newly_assignment.items():
            assignments = assignment.split("%")
            # check if the assignment is valid
            cur_taxonomy = taxonomy_dict
            for idx, assignment in enumerate(assignments):
                if assignment in cur_taxonomy:
                    if not idx == len(assignments) - 1:
                        cur_taxonomy = cur_taxonomy[assignment]
                else:
                    print(f"{assignment} not in original taxonomy")
                    if isinstance(cur_taxonomy, list):
                        cur_taxonomy.append(assignment)
                    else:
                        cur_taxonomy[assignment] = []

    with open(new_taxonomy_path, "w") as f:
        json.dump(taxonomy_dict, f, indent=4)

if __name__ == "__main__":
    process_unassigned_keys()
    merge_assignment()
    merge_taxonomy()