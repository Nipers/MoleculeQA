import json
import csv
import os
taxonomy_path = "./fine_grained_CLS/fine_grained_cls.json"
csv_dir = "./fine_grained_CLS/csv"
output_dir = "./fine_grained_CLS/assignment"
name2cls = {
    "Structure": 1,
    "Property": 2,
    "Usage": 3,
}

def assign_by_name():
    with open(taxonomy_path, "r") as f:
        taxonomy = json.load(f)

    for cls in name2cls.keys():
        cls_assignment = {}
        unassigned_keys = []
        cls_file = os.path.join(csv_dir, f"{cls}.csv")
        with open(cls_file, "r") as f:
            reader = csv.reader(f, delimiter=",")
            next(reader)
            for row in reader:
                key = row[0]
                if key.startswith("position"):
                    sub_attr = "Molecular Structure and Configuration"
                    sub_sub_attr = "Basic Structure, Backbone and Configurations"
                    cls_assignment[key] = "%".join(["Structure", sub_attr, sub_sub_attr, "position"])
                    continue
                for c in name2cls.keys():
                    cls_tax = taxonomy[c]
                    for sub_attr in cls_tax:
                        if isinstance(cls_tax[sub_attr], list):
                            if key in cls_tax[sub_attr]:
                                cls_assignment[key] = "%".join([c, sub_attr, key])
                                break
                        else:
                            for sub_sub_attr in cls_tax[sub_attr]:

                                if key in cls_tax[sub_attr][sub_sub_attr]:
                                    cls_assignment[key] = "%".join([c, sub_attr, sub_sub_attr, key])
                                    break
                if key not in cls_assignment:
                    unassigned_keys.append(key)
        print(f"{cls}: {len(cls_assignment)}")
        print(f"Unassigned keys: {len(unassigned_keys)}")
        cls_output_dir = os.path.join(output_dir, cls)
        if not os.path.exists(cls_output_dir):
            os.makedirs(cls_output_dir)
        with open(os.path.join(cls_output_dir, "assignment.json"), "w") as f:
            json.dump(cls_assignment, f, indent=4)
        with open(os.path.join(cls_output_dir, "unassigned_keys.json"), "w") as f:
            json.dump(unassigned_keys, f, indent=4)

def cal_coverage():
    leaf_coverage = {}
    with open(taxonomy_path, "r") as f:
        taxonomy = json.load(f)
        for cls in name2cls.keys():
            for sub_attr in taxonomy[cls]:
                if isinstance(taxonomy[cls][sub_attr], list):
                    for key in taxonomy[cls][sub_attr]:
                        if not key in leaf_coverage:
                            leaf_coverage[key] = []
                        else:
                            print(f"Duplicate key: {key}")
                else:
                    for sub_sub_attr in taxonomy[cls][sub_attr]:
                        for key in taxonomy[cls][sub_attr][sub_sub_attr]:
                            if not key in leaf_coverage:
                                leaf_coverage[key] = []
                            else:
                                print(f"Duplicate key: {key}")

    for cls in name2cls.keys():
        cls_file = os.path.join(csv_dir, f"{cls}.csv")
        with open(cls_file, "r") as f:
            reader = csv.reader(f, delimiter=",")
            next(reader)
            for row in reader:
                key = row[0]
                for c in name2cls.keys():
                    cls_tax = taxonomy[c]
                    for sub_attr in cls_tax:
                        if isinstance(cls_tax[sub_attr], list):
                            if key in cls_tax[sub_attr]:
                                leaf_coverage[key].append(key)
                                break
                        else:
                            for sub_sub_attr in cls_tax[sub_attr]:
                                if key in cls_tax[sub_attr][sub_sub_attr]:
                                    leaf_coverage[key].append(key)
                                    break
    uncovered_keys = []
    for key in leaf_coverage:
        if len(leaf_coverage[key]) == 0:
            uncovered_keys.append(key)
    for key in uncovered_keys:
        leaf_coverage.pop(key)
    print(f"Uncovered keys: {len(uncovered_keys)}")
    print(f"Covered keys: {len(leaf_coverage)}")
    with open(os.path.join(output_dir, "leaf_coverage.json"), "w") as f:
        json.dump(leaf_coverage, f, indent=4)
    with open(os.path.join(output_dir, "uncovered_keys.json"), "w") as f:
        json.dump(uncovered_keys, f, indent=4)
        
if __name__ == "__main__":
    assign_by_name()
    cal_coverage()

# Structure: 510
# Unassigned keys: 235
# Property: 69
# Unassigned keys: 99
# Usage: 81
# Unassigned keys: 99
# Uncovered keys: 46
# Covered keys: 442