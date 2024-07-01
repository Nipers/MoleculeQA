import getopt
import math
import random
import token
from turtle import pos
from nh3 import clean
# from sklearn.model_selection import LeavePGroupsOut
import torch
import json
from tqdm import tqdm
from transformers import AutoTokenizer, AutoModelForTextEncoding, T5ForConditionalGeneration
import numpy as np
import os

BERT_PATH = "./scibert_scivocab_uncased"
BIOT5_PATH = "./biot5-base"
BATCH_SIZE = 128
tokenizer = AutoTokenizer.from_pretrained(BIOT5_PATH, model_max_length=512)
# model = None
model = AutoModelForTextEncoding.from_pretrained(BIOT5_PATH).to('cuda:0')
print_details = False


def cosine_similarity(opt_embs):
    opt_embs = opt_embs / torch.norm(opt_embs, dim=1, keepdim=True)
    similarity = torch.mm(opt_embs, opt_embs.transpose(0, 1))
    return np.array(similarity.cpu().detach().numpy())

def count_parameters(model):
    return sum(p.numel() for p in model.parameters() if p.requires_grad) / 1024 / 1024

def average_pooling(hidden_states, attention_mask):
    # use attention_mask to remove padding
    seq_len = attention_mask.sum(dim=1)
    hidden_states[attention_mask == 0] = 0
    pooled = hidden_states.sum(dim=1) / seq_len.unsqueeze(-1)
    return pooled

def biot5_encode(options):
    global print_details
    global tokenizer
    global model
    # divide options into batches
    batch_num = math.ceil(len(options) / BATCH_SIZE)
    encoded_options = []
    for i in range(batch_num):
        batch = options[i * BATCH_SIZE: (i + 1) * BATCH_SIZE]
        if len(batch) == 0:
            continue
        input_ids = tokenizer(batch, return_tensors="pt", padding=True, truncation=True).input_ids.to('cuda:0')
        attention_mask = tokenizer(batch, return_tensors="pt", padding=True, truncation=True).attention_mask.to('cuda:0')
        with torch.no_grad():
            outputs = model.forward(input_ids)
        hidden_states = outputs.last_hidden_state
        # average pooling
        pooled = average_pooling(hidden_states, attention_mask)
        if not print_details:
            print(type(model))
            print(type(tokenizer))
            print(batch)
            print(hidden_states)
            print(pooled)
            print_details = True
        encoded_options.append(pooled)
    encoded_options = torch.cat(encoded_options, dim=0)
    # print(encoded_options.shape)
    return encoded_options



def negative_sample(options_emb, reverse=False):

    # cal sim_matrix by 
    # if len(options) <= 4:
    #     return options
    function = np.argmax if reverse else np.argmin
    neg_options = []
    sim_matrix = cosine_similarity(options_emb)
    global print_details
    if not print_details:
        print(options_emb)
    pos_sim = sim_matrix[0]
    # get the index of the least similar option
    assign_value = 0 if reverse else 1
    for i in range(len(sim_matrix)):
        sim_matrix[i][i] = assign_value

    neg_index_1 = function(pos_sim)
    neg_options.append(neg_index_1)
    # get the index of the second least similar option and it should be different from the first one
    neg_sim = sim_matrix[neg_index_1]
    pos_sim[neg_index_1] = assign_value
    neg_sim[0] = assign_value
    neg_index_2 = function(neg_sim + pos_sim)
    neg_options.append(neg_index_2)
    neg_sim_2 = sim_matrix[neg_index_2]
    pos_sim[neg_index_2] = assign_value
    neg_sim[neg_index_2] = assign_value
    neg_sim_2[0] = assign_value
    neg_sim_2[neg_index_1] = assign_value
    neg_index_3 = function(neg_sim_2 + pos_sim + neg_sim)
    neg_options.append(neg_index_3)
    if not print_details:
        print(reverse)
        print(function)
        print(sim_matrix)
        print(neg_options)
        print_details = True
    return neg_options

# step 1, merge two sources into one set and get options for each topic
# source 1 ./Chebi_Sup/refine_expression/Usage/no_dup_gpt_answer_merged_Usage.json
# source 2 ./Chebi_Sup/refine_expression/Usage/gpt_answer_merged_Usage.json

# "54675783",
# "This molecule is a tetracycline antibiotic with excellent absorption and tissue penetration that is used for several bacterial infections as well as treatment of acne",
# "Which kind of antibiotic is this molecule?",
# "Tetracycline antibiotic",
# "It is a tetracycline antibiotic used for several bacterial infections as well as treatment of acne."

def load_instances(desc_cls):
    instance_path_ls = [
        f"./Chebi_Sup/filter/{desc_cls}/non_brief_QA_instances.json",
        f"./Chebi_Sup/refine_expression/{desc_cls}/gpt_answer_merged_easy_Source.json"
    ]
    topic2options = {}
    removed_instances = {}
    legal_instances = {}
    removed_num = 0
    legal_num = 0

    instance_path_ls = [instance_path.format(desc_cls) for instance_path in instance_path_ls]
    for instance_path in instance_path_ls:
        if not os.path.exists(instance_path):
            continue
        with open(instance_path, 'r') as f:
            instances = json.load(f)
        for topic in instances:
            if topic not in topic2options:
                topic2options[topic] = {}
            if topic not in removed_instances:
                removed_instances[topic] = []
            if topic not in legal_instances:
                legal_instances[topic] = []
            topic_instances = instances[topic]
            for instance in topic_instances:
                cid, desc, question, t, answer = instance
                if question not in topic2options[topic]:
                    topic2options[topic][question] = []
                if not "not specified" in answer.lower():
                    topic2options[topic][question].append(answer)
                    legal_instances[topic].append(instance)
                    legal_num += 1
                else:
                    removed_instances[topic].append(instance)
                    removed_num += 1
    for topic in topic2options:
        if len(topic2options[topic]) > 1:
            print(list(topic2options[topic].keys()))
    return legal_instances, topic2options, legal_num, removed_num

def normalize_option(option):
    option = option.lower()
    option = option.replace(" an ", " a ")
    if option.endswith("."):
        option = option[:-1]
    return option

def justify_synonyms(option_ls, topic):
    def get_topic_synonyms(topic):
        topic_synonyms_ls = [topic]
        topic_synonyms = [
            [
                "drug",
                "agent"
            ],
            [
                "activity",
                "effect",
                "property",
                "activities",
                "effects",
                "properties"
            ]
        ]
        for synonyms_ls in topic_synonyms:
            for synonym in synonyms_ls:
                if synonym in topic:
                    for s in synonyms_ls:
                        if s != synonym:
                            topic_synonyms_ls.append(topic.replace(synonym, s))
        return topic_synonyms_ls
        
        


    def get_option_synonyms(option, topic_synonyms_ls, synonyms):
        option_synonyms = [option]
        for synonym_ls in synonyms:
            for synonym in synonym_ls:
                if synonym in option:
                    for s in synonym_ls:
                        option_synonyms.append(option.replace(synonym, s))
        for topic_synonym in topic_synonyms_ls:
            if topic_synonym in option:
                for s in topic_synonyms_ls:
                    if s != topic_synonym:
                        option_synonyms.append(option.replace(topic_synonym, s))
        return option_synonyms
        

    with open(f"../filter/synonyms.json", 'r') as f:
        synonyms = json.load(f)
    topic_synonyms_ls = get_topic_synonyms(topic)
    clean_options = []
    option_map = {}
    norm_options = []

    for option in option_ls:
        norm_options.append(normalize_option(option))
    
    for idx, option in enumerate(option_ls):
        if option in option_map:
            continue
        
        clean_options.append(option)

        option_synonyms = get_option_synonyms(norm_options[idx], topic_synonyms_ls, synonyms)
        for n_idx, n_option in enumerate(norm_options):
            if n_idx == idx:
                continue
            if n_option in option_synonyms:
                option_map[option_ls[n_idx]] = option
            
    return clean_options, option_map

def rm_synonyms_options(desc_cls):
    os.makedirs(f"./{desc_cls}", exist_ok=True)
    legal_instances, topic2options, legal_num, removed_num = load_instances(desc_cls)

    for topic in topic2options:
        for question in topic2options[topic]:
            topic2options[topic][question] = list(set(topic2options[topic][question]))
    topic2synonyms_map = {}
    for topic in legal_instances:
        topic2synonyms_map[topic] = {}
        for question in topic2options[topic]:
            topic2options[topic][question], topic2synonyms_map[topic][question] = justify_synonyms(topic2options[topic][question], topic)
    
    meaning_less_prefix = []
    for main_word in ["this molecule", "it"]:
        for be_word in [" is "," has a role as ", " acts as ", " is used as ", " can be used as "]:
            for num_word in ["a ", ""]:
                meaning_less_prefix.append(main_word + be_word + num_word)


    for topic in topic2options:
        for question in topic2options[topic]:
            option_ls = topic2options[topic][question]
            remove_ls = []
            for option_a in option_ls:
                norm_a = normalize_option(option_a)
                for option_b in option_ls:
                    if option_b in remove_ls:
                        continue
                    norm_b = normalize_option(option_b)
                    if norm_a.replace(norm_b, "") in meaning_less_prefix:
                        topic2synonyms_map[topic][question][option_b] = option_a
                        remove_ls.append(option_b)
                        break
            for option in remove_ls:
                topic2options[topic][question].remove(option)

    with open(f"./{desc_cls}/topic2options.json", 'w') as f:
        json.dump(topic2options, f, indent=4)
    
    with open(f"./{desc_cls}/topic2synonyms_map.json", 'w') as f:
        json.dump(topic2synonyms_map, f, indent=4)

    


def build_QA_pairs(desc_cls):
    topic2options = {}

    legal_instances, topic2options, legal_num, removed_num = load_instances(desc_cls)

    # for topic in topic2options:
    #     for question in topic2options[topic]:
    #         topic2options[topic][question] = list(set(topic2options[topic][question]))
    
    topic2options_path = f"./{desc_cls}/topic2options.json"
    with open(topic2options_path, 'r') as f:
        topic2options = json.load(f)
    
    topic2synonyms_path = f"./{desc_cls}/topic2synonyms_map.json"
    with open(topic2synonyms_path, 'r') as f:
        topic2synonyms_map = json.load(f)


    final_QA_pairs = {}
    final_QA_nums = 0
    miss_option_QA_pairs = {}
    for topic in tqdm(legal_instances):
        topic_instances = legal_instances[topic]
        if len(topic_instances) == 0:
            continue
        ques2neg_emb = {}
        for question in topic2options[topic]:
            ques2neg_emb[question] = biot5_encode(topic2options[topic][question])
        # neg_embs = biot5_encode(topic2options[topic])
        for instance in topic_instances:
            cid, desc, question, t, answer = instance
            assert question in topic2options[topic]
            neg_options = topic2options[topic][question].copy()
            if not answer in neg_options:
                assert answer in topic2synonyms_map[topic][question]
                while answer in topic2synonyms_map[topic][question]:
                    answer = topic2synonyms_map[topic][question][answer]
                assert answer in neg_options, answer
            if len(neg_options) < 5:
                neg_options.remove(answer)
                if not topic in miss_option_QA_pairs:
                    miss_option_QA_pairs[topic] = []
                miss_option_QA_pairs[topic].append([cid, desc, question, answer, neg_options])
                continue
            
            pos_idx = neg_options.index(answer)
            neg_idx = list(range(len(neg_options)))
            random.shuffle(neg_idx)
            neg_idx = neg_idx[:500]
            if not pos_idx in neg_idx:
                neg_idx[0] = pos_idx
            else:
                # put answer to the first element
                neg_idx.remove(pos_idx)
                neg_idx.insert(0, pos_idx)
            options_embs = ques2neg_emb[question][neg_idx]
            selected_negs = negative_sample(options_embs, True)
            # selected_negs = neg_idx[:4]
            # if pos_idx in selected_negs:
            #     selected_negs.remove(pos_idx)
            # selected_negs = selected_negs[:3]
            neg_options = [neg_options[neg_idx[i]] for i in selected_negs]
            if not topic in final_QA_pairs:
                final_QA_pairs[topic] = []
            final_QA_pairs[topic].append([cid, desc, question, answer, neg_options])
            final_QA_nums += 1



    with open(f"final_QA_pairs_{desc_cls}_reverse_biot5_v2.json", 'w') as f:
        json.dump(final_QA_pairs, f, indent=4)
    
    with open(f"miss_option_QA_pairs_{desc_cls}_reverse_biot5_v2.json", 'w') as f:
        json.dump(miss_option_QA_pairs, f, indent=4)
        
    
    
    print("{} removed instances: {}".format(desc_cls, removed_num))
    print("{} legal instances: {}".format(desc_cls, legal_num))
    print("{} final_QA_nums: {}".format(desc_cls, final_QA_nums))


def get_cid_ls(desc_cls):
    qa_path = f"./Chebi_Sup/sample/final_QA_pairs_{desc_cls}_reverse.json"
    with open(qa_path, 'r') as f:
        qa_pairs = json.load(f)
    qid = 0
    qid_ls = []
    cid_ls = []
    topics = list(qa_pairs.keys())
    topics.sort()
    # print(topics)
    for topic in topics:
        topic_qa_pairs = qa_pairs[topic]
        for qa_pair in topic_qa_pairs:
            cid = qa_pair[0]
            qid_ls.append(qid)
            cid_ls.append(cid)
            qid += 1
    desc_qid_cid = [qid_ls, cid_ls]
    # print(len(qid_ls))
    with open(f"desc_qid_cid_{desc_cls}.json", 'w') as f:
        json.dump(desc_qid_cid, f, indent=4)
            

if __name__ == "__main__":
    # for desc_cls in ["Source"] :# ["Structure", "Usage", "Property"]
    #     build_QA_pairs(desc_cls)

    # for desc_cls in ["Usage"]: #, "Structure", "Usage", "Property"
    #     get_cid_ls(desc_cls)

    for desc_cls in ["Property", "Structure", "Usage", "Source"]:
        # rm_synonyms_options(desc_cls)
        build_QA_pairs(desc_cls)

# removed instances: 10383
# legal instances: 30470
# removed instances: 552
# legal instances: 3433
# removed instances: 499
# legal instances: 6330