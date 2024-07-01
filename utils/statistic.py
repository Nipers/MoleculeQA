import json
import csv

from numpy import isin



def get_question_ls():
    cls_ques_ls = {}
    cls_truth_ls = {}
    cls2selfies_ls = {}
    for desc_cls in ["Usage", "Property", "Source", "Structure"]:
        test_path =  f"./data/moleculeQA/biot5_scaffold_reverse_biot5_v2/{desc_cls}/task6_chebi20_mol2text_test.json"
        with open(test_path, "r") as fin:
            test_data = json.load(fin)
        instances = test_data["Instances"]
        questions = []
        truths = []
        selfies = []
        for instance in instances:
            question = instance["input"].split("Question about this molecule: ")[1].split("\n")[0]
            # print(question)
            questions.append(question)
            truth = instance["output"][0]
            truths.append(truth)
            selfie = instance["input"].split("<eom>")[0].replace("<bom>", "")
            # print(selfie)
            selfies.append(selfie)
        
        cls_ques_ls[desc_cls] = questions
        cls_truth_ls[desc_cls] = truths
        cls2selfies_ls[desc_cls] = selfies

    


    return cls_ques_ls, cls_truth_ls, cls2selfies_ls



def get_question_set():
    questions = set()
    for filename in [
        "task5_chebi20_mol2text_validation.json",
        "task6_chebi20_mol2text_test.json",
        "task4_chebi20_mol2text_train.json",
    ]:
        test_path =  f"./data/moleculeQA/biot5_scaffold_reverse_biot5_v2/All/{filename}"
        with open(test_path, "r") as fin:
            test_data = json.load(fin)
        instances = test_data["Instances"]

        for instance in instances:
            question = instance["input"].split("Question about this molecule: ")[1].split("\n")[0]
            # print(question)
            questions.add(question)
        

    


        print("Total questions:", len(questions))




def get_t5_base_samples():
    cls_question_ls = {}
    cls_truth_ls = {}
    cls_pred_ls = {}
    for desc_cls in ["Usage", "Property", "Source", "Structure"]:
        answer_path = f"./CHECKPOINTS/OpenBioMed/result/MoleculeQA/t5_base_{desc_cls}_scaffold_reverse_biot5_v2"
        with open(answer_path, "r") as fin:
            reader = csv.reader(fin, delimiter="\t")
            next(reader)
            question_ls = []
            truth_ls = []
            pred_ls = []
            for row in reader:
                context = row[0]
                gt = row[1]
                pred = row[2]
                question = context.split("Question about this molecule: ")[1].split("\n")[0]

                question_ls.append(question)
                truth_ls.append(gt)
                pred_ls.append(pred)
        
        cls_question_ls[desc_cls] = question_ls
        cls_truth_ls[desc_cls] = truth_ls
        cls_pred_ls[desc_cls] = pred_ls
    return cls_question_ls, cls_truth_ls, cls_pred_ls

def get_ques2topic():
    cls_ques2topic = {}
    for desc_cls in ["Usage", "Property", "Source", "Structure"]:
        QA_pairs_path = f"./Chebi_Sup/sample/final_QA_pairs_{desc_cls}_reverse_biot5_v2.json"
        with open(QA_pairs_path, "r") as fin:
            QA_pairs = json.load(fin)
        ques2topic = {}
        for topic in QA_pairs:
            for instances in QA_pairs[topic]:
                ques = instances[2]
                ques2topic[ques] = topic
        cls_ques2topic[desc_cls] = ques2topic
    
    return cls_ques2topic
        
def get_answer_ls():
    cls_answer_ls = {}
    cls_truth_ls = {}
    cls2selfies_ls = {}
    cls_question_ls = {}
    for desc_cls in ["Usage", "Property", "Source", "Structure"]:
        cls_answer_ls[desc_cls] = []
        cls_truth_ls[desc_cls] = []
        cls2selfies_ls[desc_cls] = []
        cls_question_ls[desc_cls] = []
        answer_path = f"./test_mol2text_pred_56000.tsv"
        with open(answer_path, "r") as fin:
            reader = csv.reader(fin, delimiter="\t")
            next(reader)
            for row in reader:
                selfies = row[0].split(" - Input: ")[1].split(" Question about")[0]
                # print(selfies)
                # print(row[0].split("Question about this molecule: "))
                try:
                    question = row[0].split("Question about this molecule: ")[1].split(" Option A")[0]
                except IndexError:
                    print(row[0])
                    continue
                truth = row[1]
                answer = row[2]
                cls_answer_ls[desc_cls].append(answer)
                cls_truth_ls[desc_cls].append(truth)
                cls2selfies_ls[desc_cls].append(selfies)
                cls_question_ls[desc_cls].append(question)
    
    
    return cls_answer_ls, cls_truth_ls, cls2selfies_ls, cls_question_ls

# if __name__ == "__main__":
#     sample_cls_ques_ls, sample_cls_truth_ls, sample_cls_selfies_ls = get_question_ls()
#     cls_ques2topic = get_ques2topic()
#     cls_answer_ls, cls_truth_ls, cls2selfies_ls, cls_question_ls = get_answer_ls()

#     cls_topic_correct_num = {}

#     for desc_cls in ["Usage", "Property", "Source", "Structure"]:
#         sample_ques_ls = sample_cls_ques_ls[desc_cls]
#         sample_truth_ls = sample_cls_truth_ls[desc_cls]
#         sample_selfies_ls = sample_cls_selfies_ls[desc_cls]
#         print(f"Processing {desc_cls}, {len(sample_ques_ls)} samples")

#         answer_ls = cls_answer_ls[desc_cls]
#         truth_ls = cls_truth_ls[desc_cls]
#         selfies_ls = cls2selfies_ls[desc_cls]
#         question_ls = cls_question_ls[desc_cls]
        
#         ques2topic = cls_ques2topic[desc_cls]

#         topic_correct_num = {}
#         for i in range(len(sample_ques_ls)):
#             sample_selfies = sample_selfies_ls[i]
#             sample_truth = sample_truth_ls[i]
#             sample_question = sample_ques_ls[i]
            
#             test_idx = []
#             for idx in range(len(selfies_ls)):
#                 if selfies_ls[idx] == sample_selfies and truth_ls[idx] == sample_truth and question_ls[idx] == sample_question:
#                     test_idx.append(idx)
            
#             if len(test_idx) == 0:
#                 continue
#             test_idx = test_idx[0]
#             # tested_case.add(test_idx)
#             topic = ques2topic[sample_question]
#             if topic not in topic_correct_num:
#                 topic_correct_num[topic] = [0, 0]
#             topic_correct_num[topic][1] += 1
#             if answer_ls[test_idx] == truth_ls[test_idx]:
#                 topic_correct_num[topic][0] += 1
        
#         total_num = 0
#         correct_num = 0
#         for topic in topic_correct_num:
#             correct_num += topic_correct_num[topic][0]
#             total_num += topic_correct_num[topic][1]
#         print(f"acc: {correct_num * 100 / total_num}")
#         cls_topic_correct_num[desc_cls] = topic_correct_num

#     with open("cls_topic_correct_num.json", "w") as fout:
#         json.dump(cls_topic_correct_num, fout, indent=4)


# if __name__ == "__main__":
#     # get_t5_base_samples
#     cls_question_ls, cls_truth_ls, cls_pred_ls = get_t5_base_samples()
#     cls_ques2topic = get_ques2topic()
#     cls_topic_correct_num = {}
#     for desc_cls in ["Usage", "Property", "Source", "Structure"]:
#         topic_correct_num = {}
#         question_ls = cls_question_ls[desc_cls]
#         truth_ls = cls_truth_ls[desc_cls]
#         pred_ls = cls_pred_ls[desc_cls]
#         ques2topic = cls_ques2topic[desc_cls]
#         correct_num = 0
        
#         for i in range(len(question_ls)):
#             if truth_ls[i] == pred_ls[i]:
#                 correct_num += 1
#         print(f"{desc_cls} acc: {correct_num * 100 / len(question_ls)}")
#         for i in range(len(question_ls)):
#             topic = ques2topic[question_ls[i]]
#             if topic not in topic_correct_num:
#                 topic_correct_num[topic] = [0, 0]
#             topic_correct_num[topic][1] += 1
#             if truth_ls[i] == pred_ls[i]:
#                 topic_correct_num[topic][0] += 1
#         cls_topic_correct_num[desc_cls] = topic_correct_num
    
#     with open("cls_topic_correct_num_t5_base.json", "w") as fout:
#         json.dump(cls_topic_correct_num, fout, indent=4)

def get_leaf_topics(instance):
    topics = []
    if isinstance(instance, dict):
        for key in instance:
            topics += get_leaf_topics(instance[key])
    else:
        assert isinstance(instance, list)
        topics += instance
    return topics

def get_sub_categories():
    sub_topics = {
        "Property": {
            "Biological and Pharmacological Activities": [],
            "Types of Reactions": [],
            "Chemical Interaction and Mechanism": [],
            "Chemical Properties": [],
            "Environmental and Safety Concerns": [],
            "Medical and Therapeutic Efficacy": [],
            "Physical and Sensory Properties": [],
        },
        "Usage": {
            "Agricultural Chemicals": [],
            "Biological Agents": [],
            "Chemical Applications and Techniques": [],
            "Pharmacodynamics and Pharmacokinetics": [],
            "Regulatory Status and Approval": [],
            "Research and Development": [],
            "Therapeutic Use": [],
        },
        "Source": {
            "metabolite": ["metabolite"],
            "derives from": ["derives"],
            "isolated from": ["isolated"],
            "found in": ["found in"]
        },
        "Structure": {
            "Biochemical and Biological Terms": [],
            "Chemical Bonding and Interactions": [],
            "Chemical Compounds and Classes": [],
            "Chemical Species and States": [],
            "Functional Groups and Chemical Entities": [],
            "Molecular Structure and Configuration": [],
        }
    }
    taxonomy_path = "./fine_grained_CLS/new_taxonomy.json"
    with open(taxonomy_path, "r") as fin:
        taxonomy = json.load(fin)
    for desc_cls in ["Usage", "Property", "Structure"]:
        cls_taxonomy = taxonomy[desc_cls]

        for sub_topic in sub_topics[desc_cls]:
            print(sub_topic)
            if not sub_topic in cls_taxonomy:
                cls_taxonomy = cls_taxonomy["Chemical Properties and Reactions"]
            assert sub_topic in cls_taxonomy
            sub_topics[desc_cls][sub_topic] += get_leaf_topics(cls_taxonomy[sub_topic])
            
            cls_taxonomy = taxonomy[desc_cls]
    with open("sub_topics.json", "w") as fout:
        json.dump(sub_topics, fout, indent=4)

def statistic(sub_topics, cls_topic_correct_num):
    acc_dict = {}
    for desc_cls in ["Usage", "Property", "Source", "Structure"]:
        acc_dict[desc_cls] = {}
        cls_sub_topics = sub_topics[desc_cls]
        topic_correct_num = cls_topic_correct_num[desc_cls]
        for sub_topic in cls_sub_topics:
            correct_num = 0
            total_num = 0
            for topic in cls_sub_topics[sub_topic]:
                if topic in topic_correct_num:
                    correct_num += topic_correct_num[topic][0]
                    total_num += topic_correct_num[topic][1]
            if total_num == 0:
                print("No samples for", sub_topic)
                continue
            acc = correct_num * 100 / total_num
            acc_dict[desc_cls][sub_topic] = acc
    return acc_dict

if __name__ == "__main__":
    # get_sub_categories()
    with open("sub_topics.json", "r") as fin:
        sub_topics = json.load(fin)
    
    with open("./cls_topic_correct_num.json", "r") as fin:
        cls_topic_correct_num = json.load(fin)
    
    with open("./cls_topic_correct_num_t5_base.json", "r") as fin:
        cls_topic_correct_num_t5_base = json.load(fin)
    with open("biot5_sub_topic_acc.json", "w") as fout:
        json.dump(statistic(sub_topics, cls_topic_correct_num), fout, indent=4)
    with open("t5_sub_topic_acc.json", "w") as fout:
        json.dump(statistic(sub_topics, cls_topic_correct_num_t5_base), fout, indent=4)

if __name__ == "__main__":
    get_question_set()

# Usage Agricultural Chemicals acc: 35.8974358974359
# Usage Biological Agents acc: 50.0
# Usage Chemical Applications and Techniques acc: 50.0
# Usage Pharmacodynamics and Pharmacokinetics acc: 43.49315068493151
# Usage Regulatory Status and Approval acc: 29.885057471264368
# Usage Research and Development acc: 42.857142857142854
# Usage Therapeutic Use acc: 40.298507462686565
# Property Biological and Pharmacological Activities acc: 52.599388379204896
# Property Types of Reactions acc: 50.0
# Property Chemical Interaction and Mechanism acc: 42.40837696335078
# Property Chemical Properties acc: 54.54545454545455
# Property Environmental and Safety Concerns acc: 44.26229508196721
# Property Medical and Therapeutic Efficacy acc: 59.523809523809526
# Property Physical and Sensory Properties acc: 51.351351351351354
# Source metabolite acc: 80.67796610169492
# No samples for derives from
# No samples for isolated from
# No samples for found in
# Structure Biochemical and Biological Terms acc: 41.666666666666664
# Structure Chemical Bonding and Interactions acc: 50.0
# Structure Chemical Compounds and Classes acc: 50.0
# Structure Chemical Species and States acc: 100.0
# Structure Functional Groups and Chemical Entities acc: 57.89473684210526
# Structure Molecular Structure and Configuration acc: 67.64596504276683
# T5 base
# Usage Agricultural Chemicals acc: 23.076923076923077
# Usage Biological Agents acc: 52.0
# Usage Chemical Applications and Techniques acc: 0.0
# Usage Pharmacodynamics and Pharmacokinetics acc: 47.602739726027394
# Usage Regulatory Status and Approval acc: 36.7816091954023
# Usage Research and Development acc: 71.42857142857143
# Usage Therapeutic Use acc: 37.3134328358209
# Property Biological and Pharmacological Activities acc: 47.706422018348626
# Property Types of Reactions acc: 0.0
# Property Chemical Interaction and Mechanism acc: 42.40837696335078
# Property Chemical Properties acc: 27.272727272727273
# Property Environmental and Safety Concerns acc: 37.704918032786885
# Property Medical and Therapeutic Efficacy acc: 52.38095238095238
# Property Physical and Sensory Properties acc: 56.75675675675676
# Source metabolite acc: 78.98305084745763
# No samples for derives from
# No samples for isolated from
# No samples for found in
# Structure Biochemical and Biological Terms acc: 41.666666666666664
# Structure Chemical Bonding and Interactions acc: 53.57142857142857
# Structure Chemical Compounds and Classes acc: 59.375
# Structure Chemical Species and States acc: 100.0
# Structure Functional Groups and Chemical Entities acc: 52.280701754385966
# Structure Molecular Structure and Configuration acc: 61.53846153846154
