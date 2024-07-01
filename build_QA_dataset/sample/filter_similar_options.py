import json
import random
from tqdm import tqdm
import time
import numpy as np
def are_sentences_similar(sentence1, sentence2, max_diff=2):
    # 将句子分割成单词
    words1 = set(sentence1.split())
    words2 = set(sentence2.split())
    
    # 计算两个集合的差集
    differences = words1.symmetric_difference(words2)
    if len(words1) == len(words2) and len(differences) == 2 and len(words1 - words2) == 1 and len(words2 - words1) == 1:
        return False
    if "and" in differences:
        return False
    if len(differences) == 1:
        for word in differences:
            if word.endswith(","):
                return False
    # 检查不同单词的数量是否在允许的范围内
    differences -= set(["can", "a", "exhibits", "exhibit"])
    return len(differences) <= max_diff

def get_similar_options():
    for cate_name in ["Source", "Structure", "Usage", "Property"]:
        with open(f"./sample/final_QA_pairs_{cate_name}_reverse_biot5_v2.json") as fin:
            cate_data = json.load(fin)
            similar_options = {}
            for key in cate_data:
                similar_options[key] = []
                for instance in cate_data[key]:
                    instance_similar_options = []
                    cid, origin_text, question, answer, false_answers = instance
                    
                    all_answers = [answer] + false_answers
                    marks = [1] + [0] * len(false_answers)
                    for i in range(len(all_answers)):
                        for j in range(i+1, len(all_answers)):
                            if marks[j] == 1:
                                continue
                            if are_sentences_similar(all_answers[i], all_answers[j]):
                                instance_similar_options.append([all_answers[i], all_answers[j]])
                                marks[j] = 1
                    similar_options[key].append(instance_similar_options)
        with open(f"./sample/similar_options_filtered/similar_options_{cate_name}.json", "w") as fout:
            json.dump(similar_options, fout, indent=4)
            similar_num = 0
            for key in similar_options:
                for instance in similar_options[key]:
                    similar_num += len(instance)
            print(f"Finish writing {cate_name} similar options, {similar_num} instances in total.")

def get_new_option(selected_options, option_list):
    random.shuffle(option_list)
    for option in option_list:
        legal = True
        if option not in selected_options:
            for selected_option in selected_options:
                if are_sentences_similar(option, selected_option):
                    legal = False
                    break
            if legal:
                return option
    return None


def replace_duplicated_options():
    ranked_options = np.array(["A", "B", "C", "D"])
    for cate_name in ["Source", "Structure", "Usage", "Property"]:
        with open(f"./sample/final_QA_pairs_{cate_name}_reverse_biot5_v2.json") as fin:
            original_samples = json.load(fin)
        with open(f"./sample/similar_options_filtered/similar_options_{cate_name}.json", "r") as fin:
            similar_options = json.load(fin)

        with open(f"./sample/topic2options_{cate_name}.json", "r") as fin:
            topic2options = json.load(fin)
        key1 = set(original_samples.keys())
        key2 = set(similar_options.keys())
        assert key1 == key2

        new_samples = {}
        for key in tqdm(key1):
            all_options = topic2options[key]
            key_samples = original_samples[key]
            key_similar_options = similar_options[key]
            assert len(key_samples) == len(key_similar_options)
            new_samples[key] = []
            for i in range(len(key_samples)):
                cid, origin_text, question, answer, false_answers = key_samples[i]
                sample_similar_options = key_similar_options[i]
                random.seed(time.time())
                if len(sample_similar_options) == 0:
                    np.random.shuffle(ranked_options)
                    new_samples[key].append([cid, origin_text, question, [answer] + false_answers, list(ranked_options)])
                else:
                    original_options = [answer] + false_answers
                    new_options = [answer]
                    to_remove = set()
                    for similar_option_pair in sample_similar_options:
                        if similar_option_pair[0] == answer:
                            # remove the latter one
                            to_remove.add(similar_option_pair[1])
                        else:
                            # remove the shorter one
                            if len(similar_option_pair[0]) < len(similar_option_pair[1]):
                                to_remove.add(similar_option_pair[1])
                            else:
                                to_remove.add(similar_option_pair[0])
                    for option in false_answers:
                        if option not in to_remove:
                            new_options.append(option)
                    
                    # get new options
                    # if answer == "It exhibits decreased central nervous system disorganized electrical activity.":
                    #     print(new_options)
                    while len(new_options) < 4:
                        new_option = get_new_option(new_options, all_options)
                        if new_option is not None:
                            new_options.append(new_option)
                        else:
                            print(f"No enough options for key {key}")
                            break
                    # if answer == "It exhibits decreased central nervous system disorganized electrical activity.":
                    #     print(original_options)
                    #     print(new_options)
                    #     assert False
                    false_answers = new_options[1:]
                    np.random.shuffle(ranked_options)
                    new_samples[key].append([cid, origin_text, question, [answer] + false_answers, list(ranked_options)])
        with open("./sample/similar_options_filtered/final_QA_pairs_{}_reverse_biot5_v3.json".format(cate_name), "w") as fout:
            json.dump(new_samples, fout, indent=4)
            print(f"Finish writing {cate_name} final samples.")
                            

if __name__ == "__main__":
    get_similar_options()
    replace_duplicated_options()

