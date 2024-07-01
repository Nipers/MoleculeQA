import json

no_split_words = {"e.g", "U.S", "sp", "Fig", "U.S.A", "i.e"}

with open("./anonymized_triples.json", "r") as fin:
    triples = json.load(fin)
splited_triples = []
for triple in triples:
    cid, source, text = triple
    sentences = text.split(". ")
    splited_sentences = [sentences[0]]
    for sen_idx in range(1, len(sentences)):
        no_split = False
        for ns_word in no_split_words:
            if sentences[sen_idx - 1].endswith(ns_word):
                splited_sentences[-1] += ". "
                splited_sentences[-1] += sentences[sen_idx]
                no_split = True
                break
        if not no_split:
            splited_sentences.append(sentences[sen_idx])
    for sen in splited_sentences:
        if sen.startswith("(") or "metabolite" in sen:
            continue
        splited_triples.append((cid, source, sen))

with open("./splited_triples.json", "w") as fout:
    json.dump(splited_triples, fout, indent=4)

print(len(splited_triples))