import json

def statistic():

    with open("./BioT5/sub_topics.json", "r") as fin:
        sub_topics = json.load(fin)
    topic2num = {}
    for desc_cls in ["Structure", "Source", "Usage", "Property"]:
        topic2num[desc_cls] = {}
        cls_subtopic = sub_topics[desc_cls]
        with open(f"./Chebi_Sup/sample/final_QA_pairs_{desc_cls}_reverse_biot5_v2.json", "r") as fin:
            cls_instances = json.load(fin)
        for topic in cls_instances:
            for sub in cls_subtopic:
                if topic in cls_subtopic[sub]:
                    sub_topic = sub
                    break
            if not sub_topic in topic2num[desc_cls]:
                topic2num[desc_cls][sub_topic] = 0
            topic2num[desc_cls][sub_topic] += len(cls_instances[topic])

    with open("./Chebi_Sup/sample/statistic.json", "w") as fout:
        json.dump(topic2num, fout, indent=4)

if __name__ == "__main__":
    statistic()