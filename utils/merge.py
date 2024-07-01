import json
import os
import csv
split_method = "_scaffold"
dataset_suffix = "_reverse_biot5_v2"
data_path = f"./moleculeQA/biot5{split_method}{dataset_suffix}"
biot5_file_ls = [
    'task4_chebi20_mol2text_train.json',
    'task5_chebi20_mol2text_validation.json',
    'task6_chebi20_mol2text_test.json'
]
molt5_file_ls = [
    "train.txt",
    "valid.txt",
    "test.txt"
]
MOLT5_DATA_PATH = f"./moleculeqa{split_method}{dataset_suffix}"
def merge_biot5(idx):
    target_suffix = "All"
    file_name = biot5_file_ls[idx]
    merged_data = {}
    for desc_cls in ["Property", "Usage", "Source", "Structure"]:
        with open(os.path.join(data_path, desc_cls, file_name), "r") as f:
            data = json.load(f)
            print(f"{len(data['Instances'])}")
            if len(merged_data) == 0:
                merged_data = data
            else:
                merged_data["Instances"] += data["Instances"]
    if not os.path.exists(os.path.join(data_path, target_suffix)):
        os.mkdir(os.path.join(data_path, target_suffix))
    with open(os.path.join(data_path, target_suffix, file_name), "w") as f:
        json.dump(merged_data, f, indent=4)

def merge_molt5(idx):
    target_suffix = "All"
    file_name = molt5_file_ls[idx]
    if not os.path.exists(os.path.join(MOLT5_DATA_PATH, target_suffix)):
        os.mkdir(os.path.join(MOLT5_DATA_PATH, target_suffix))
    instance_num = 0
    with open(os.path.join(MOLT5_DATA_PATH, target_suffix, file_name), "w") as fout:
        writer = csv.writer(fout, delimiter="\t")
        for desc_cls in ["Property", "Usage", "Source", "Structure"]:
            with open(os.path.join(MOLT5_DATA_PATH, desc_cls, file_name), "r") as fin:
                reader = csv.reader(fin, delimiter="\t")
                if desc_cls != "Property":
                    next(reader)
                for row in reader:
                    writer.writerow(row)
                    instance_num += 1
    print(f"file name: {file_name}, instance_num: {instance_num}")
    
# file name: train.txt, instance_num: 44357
# file name: valid.txt, instance_num: 4702
# file name: test.txt, instance_num: 4626
# V2
# file name: train.txt, instance_num: 49994
# file name: valid.txt, instance_num: 5796
# file name: test.txt, instance_num: 5787
if __name__ == "__main__":
    for idx in range(len(biot5_file_ls)):
        merge_biot5(idx)
    for idx in range(len(molt5_file_ls)):
        merge_molt5(idx)
