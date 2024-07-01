import json

cid2sentences = {}

for desc_cls in ["Structure", "Usage", "Property"]:
    final_QA_pairs_path = f"./Chebi_Sup/sample/final_QA_pairs_{desc_cls}.json"
    with open(final_QA_pairs_path, "r") as f:
        final_QA_pairs = json.load(f)
    for topic in final_QA_pairs:
        topic_QA_pairs = final_QA_pairs[topic]
        for QA_pair in topic_QA_pairs:
            cid = QA_pair[0]
            sentence = QA_pair[1]
            if not cid in cid2sentences:
                cid2sentences[cid] = []
            cid2sentences[cid].append(sentence)

print(len(cid2sentences))
sen_num = 0
for cid in cid2sentences:
    cid2sentences[cid] = list(set(cid2sentences[cid]))
    sen_num += len(cid2sentences[cid])
print(sen_num)
# 22249
# 31770