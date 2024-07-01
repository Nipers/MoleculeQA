import json
import os

file_ls = [
    "./fine_grained_CLS/generate_questions/Usage/non_leaf_topics.json",
    "./fine_grained_CLS/generate_questions/Property/non_leaf_topics.json",
    "./fine_grained_CLS/generate_questions/Structure/non_leaf_topics.json"
]

for file in file_ls:
    num = 0
    with open(file, "r") as f:
        data = json.load(f)
        # print(file, len(data))
        for topic in data:
            # print(topic, len(data[topic]))
            num += len(data[topic][1])

    print(num)