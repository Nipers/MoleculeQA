import csv
import os
import json
SOURCE_DIR = "./fine_grained_CLS/category_topics"
TARGET_DIR = "./fine_grained_CLS/csv"

name2cls = {
    "Source": 0,
    "Structure": 1,
    "Property": 2,
    "Usage": 3,
}

if not os.path.exists(TARGET_DIR):
    os.makedirs(TARGET_DIR)

if __name__ == "__main__":
    target_file_template = "{}.csv"
    for file_name in os.listdir(SOURCE_DIR):
        cur_cls = -1
        cur_key = None
        for key in name2cls.keys():
            if key in file_name:
                cur_cls = name2cls[key]
                cur_key = key
                break
        assert cur_key, f"{cur_cls}: {file_name}"
        print(file_name)
        with open(os.path.join(SOURCE_DIR, file_name), "r") as f:
            data = json.load(f)
        print(type(data))
        target_file_name = target_file_template.format(cur_key)
        with open(os.path.join(TARGET_DIR, target_file_name), "w") as f:
            writer = csv.writer(f, delimiter=",")
            writer.writerow(["Keyword", "Option", "Reason"])
            if cur_key != "Source":
                for key, value in data:
                    writer.writerow([key])            
            else:
                for key, value in data.items():
                    writer.writerow([key])
        



        

