import csv
import random
import json
def add_option(source_path, target_path):
    option_chars = ["A", "B", "C", "D"]
    random.seed(42)
    with open(source_path, 'r') as fin:
        topic_QA_pairs = json.load(fin)
    option_added_QA_pairs = {}
    for topic in topic_QA_pairs:
        option_added_QA_pairs[topic] = []
        for QA_pair in topic_QA_pairs[topic]:
            neg_options = QA_pair[-1]
            option_num = len(neg_options) + 1
            cur_option_chars = option_chars[:option_num]
            QA_pair[3] = [QA_pair[3]] + QA_pair[-1]
            random.shuffle(cur_option_chars)
            QA_pair[-1] = cur_option_chars
            option_added_QA_pairs[topic].append(QA_pair)
    
    with open(target_path, 'w') as fout:
        json.dump(option_added_QA_pairs, fout, indent=4)

def get_cid2smile():
    cid2smile = {}
    for split in ["train", "valid", "test"]:
        # ./CheBI-20/Hug/test.csv
        path = f"./CheBI-20/Hug/{split}.csv"
        with open(path, 'r') as fin:
            reader = csv.reader(fin, delimiter='\t')
            next(reader)
            for row in reader:
                cid = row[0]
                smile = row[1]
                cid2smile[cid] = smile
    with open("./data/cid2smile.json", "w") as fout:
        json.dump(cid2smile, fout, indent=4)
if __name__ == "__main__":
    # for suffix in ["", "_random", "_reverse"]:
    for suffix in ["_reverse_biot5_v2"]:
        for desc_cls in ["Source", "Property", "Usage", "Structure"]:
            source_path = f"./final_QA_pairs_{desc_cls}{suffix}.json"
            target_path = f"./option_added_QA_pairs_{desc_cls}{suffix}.json"
            add_option(source_path, target_path)
    # get_cid2smile()