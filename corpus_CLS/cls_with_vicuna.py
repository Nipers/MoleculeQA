# import openai
# # to get proper authentication, make sure to use a valid key that's listed in
# # the --api-keys flag. if no flag value is provided, the `api_key` will be ignored.

import argparse
model = "./vicuna-13b-v1.5-16k"
url_ls = [
    # "http://192.168.0.0:800/v1/chat/completions",
    # "http://192.168.0.0:800/v1/chat/completions",
    # "http://192.168.0.0:800/v1/chat/completions",
    # "http://192.168.0.0:800/v1/chat/completions",

    "http://192.168.0.0:800/v1/chat/completions",
    "http://192.168.0.0:800/v1/chat/completions",
    "http://192.168.0.0:800/v1/chat/completions",
    "http://192.168.0.0:800/v1/chat/completions",
    "http://192.168.0.0:800/v1/chat/completions",
    "http://192.168.0.0:800/v1/chat/completions",
    "http://192.168.0.0:800/v1/chat/completions",
    "http://192.168.0.0:800/v1/chat/completions",
]

prompt =  "You are a research assistant for molecular research, \
you are familiar with description text of moleducles, please help me to classify some corpus.  \
Four kinds of content are included in these corpus. \
The first is Source, which descirbes the distribution of compound in nature or from what the compound is extracted. Examples:  \
'It is a plant metabolite, a human urinary metabolite', 'Sampangine is extracted from several plants including the stem bark of Cananga odorata', \
'Luteoside B is a natural product found in Markhamia stipulata and Tecoma stans var. velutina with data available.'. \
The second is Architecture, which may desciribe the type of given compound, such as 'salt', 'ether', 'Benzodiazepines', 'diterpenoid', \
or depicts numbers and locations of its components like 'Diphenylcyclopropenone has phenyl substituents at the 2- and 3-positions' which . Examples: \
'Melatonin is a member of the class of acetamides that is acetamide in which one of the hydrogens attached to the nitrogen atom is replaced by a 2-(5-methoxy-1H-indol-3-yl)ethyl group', \
'Orbifloxacin is a fluoroquinolone'The third is Usage which includes medical usage like 'treatment of fungal', 'safener', 'antibiotic', experimental usage like 'solvent', 'reagent', 'be investigated for', agricultural usage like 'herbicide', 'pesticide', 'fertilizer' and other descriptions about how people utilize this compound. \
Examples:  'The prototypical analgesic used in the treatment of mild to moderate pain', \
'A reversible inhibitor of cholinesterase with a rapid onset, it is used in myasthenia gravis both diagnostically and to distinguish between under- or over-treatment', approvements of FDA is also Usage-related information.\
The forth is Property, which includes physical properties like melting/boiling/freezing point, density, smell, taste, color, solid/liquid/gas/powder/crystal, volatileness, solubleness, chemical properties like pH value, half-life, toxicity, ignitability, corrosivity, irritant, reactivity, storage methods, medical effects like various activities (antineoplastic carcinogenesis, antiviral, agonist activity), vasodilation, ion channel activities. \
Examples: 'Tremorgenic mycotoxins affect central nervous system activity, with their defining characteristic being the tremors that they cause', 'Insoluble in water but reacts with water to produce a toxic vapor', 'It has dermatotoxic activity causing inflamation of the skin'"



example = f"Here are some examples to teach you to finish classifying: \n\
Example 1:\n\
Sentence: It has a role as a fluorochrome, \n\n\
Classification Result: ['Usage']\n\n\
Analysis: The statement: 'It has a role as a fluorochrome' falls into the following category:\n\nUsage:\nThis sentence highlights a specific application of the substance, identifying it as a 'fluorochrome.' Fluorochromes are agents that can emit light upon being excited by a certain wavelength, and they are widely used in a variety of biochemical and medical applications, particularly in fluorescence microscopy, flow cytometry, and certain types of assay systems. By stating the compound's role, it directly refers to how it is utilized, thereby fitting the 'Usage' category.\n\
The instance does not provide information regarding 'Source,' 'Architecture,' or 'Property':\n\n\
'Source' would imply information about where this compound is derived from or its origin, which is not mentioned in the statement.\n\
'Architecture' would involve a detailed structural or chemical description of the compound, which is not provided here.\n\
'Property' would require more detailed insight into its physical, chemical, or biological characteristics or behaviors (other than its ability to function as a fluorochrome), which are not discussed in this specific context.'\n\n\
Example 2:\n\
Sentence: 'Zizyberanalic acid is a steroid acid isolated from the roots of Breynia fruticosa', \n\n\
Classification Result: ['Source', 'Architecture']\n\n\
Analysis: The statement: 'Zizyberanalic acid is a steroid acid isolated from the roots of Breynia fruticosa' indeed covers two categories:\n\n\
Source:\n\nThe text indicates that zizyberanalic acid is derived from a specific plant, highlighting its natural origin. It pinpoints where the compound comes from, aligning with the 'Source' category, which encompasses details about the origin or extraction of the compound.\n\
Architecture:\n\nThe mention of 'steroid acid' is an essential piece of information regarding the compound's chemical nature and classification. By identifying it as a 'steroid acid,' the statement provides insights into the compound's basic chemical framework and the class of compounds it belongs to. Steroids have a specific molecular structure (four cycloalkane rings composed of 17 carbon atoms). Although it doesn't delve into the detailed molecular structure, knowing it's a steroid gives significant information about its chemical architecture, hence fitting the 'Architecture' category.\n\
While the statement touches upon these categories, it does not provide information about the 'Usage' or 'Property' of zizyberanalic acid:\n\n\
'Usage' would involve its application in medical, industrial, or other fields, which isn't covered in the sentence.\n\
'Property' would entail specific physical, chemical, or biological characteristics or behaviors of zizyberanalic acid, which are also not discussed here.\n\n\
Example 3:\n\
Sentence: 'Sorafenib blocks the enzyme RAF kinase, a critical component of the RAF/MEK/ERK signaling pathway that controls cell division and proliferation; in addition, sorafenib inhibits the VEGFR-2/PDGFR-beta signaling cascade, thereby blocking tumor angiogenesis.'\n\
Classification Result: ['Property']\n\n\
Analysis: The information provided in the statement, 'Sorafenib blocks the enzyme RAF kinase, a critical component of the RAF/MEK/ERK signaling pathway that controls cell division and proliferation; in addition, sorafenib inhibits the VEGFR-2/PDGFR-beta signaling cascade, thereby blocking tumor angiogenesis,' falls into the following category:\n\n\
Property:\n\
The description is centered on the biological activity and specific interactions of Sorafenib at the molecular level. It details how Sorafenib functions by inhibiting certain enzymes and interfering with particular signaling pathways. This explanation of its action on RAF kinase and its role in blocking the signaling processes crucial for cell division, proliferation, and tumor angiogenesis relates to the inherent biological properties of the compound. These are specific biochemical interactions and consequences that define what Sorafenib does on a molecular level.\n\
The information doesn't directly pertain to 'Source,' 'Architecture,' or 'Usage' based on the context provided:\n\n\
There's no mention of the 'Source' from which Sorafenib is derived.\n\
'Architecture' would involve a discussion on the molecular structure or chemical makeup of Sorafenib, which is not covered in the given text.\n\
Regarding 'Usage,' the text doesn't specify any direct application or indication for Sorafenib, such as the treatment of a particular disease or condition, even though the detailed mechanism of action hints at its therapeutic implications, primarily in oncology. However, since it doesn't state this application explicitly, it's more accurate not to classify it under 'Usage' based on the information provided.\n"



import csv
import requests
import json
import os
from tqdm import tqdm

def get_responce_from_api(sample, url_idx):
    instance = f"Here is a sentence for you to classify: {sample}. Please just give me your final Classification Result (only one category with highest confidence), do not provide Analysis, do not repeat origin Sentence, just return Classification Result." # 

    headers = {
        'content-type': 'application/json',
    }
    url = url_ls[url_idx]
    # print(url)
    for t in [0.1]:
        # print(f"Current temperature: {t}")
        # for i in range(1):
        data = {
            "model": model,     
            "temperature": t,
            "messages": [
                {
                "role": "user", 
                "content": prompt + example + instance
                }
            ],
            "max_tokens": 16
        }
        # print(prompt + example + instance)
        # print(json.dumps(data))
        while True:
            try:
                response = requests.post(url, headers=headers, data=json.dumps(data), timeout=10)
            except requests.exceptions.ReadTimeout:
                return -1
            # print(response)
            content = json.loads(response.content.decode('utf-8'))
            # print(content)
            try:
                return content["choices"][0]["message"]["content"]
            except KeyError:
                return -2


def get_lm_cls_res(url_idx, split):
    supplement_triples_path = "./Chebi_Sup/splited_triples.json"
    output_path = "./Chebi_Sup/cls_res_{}.json"

    with open(supplement_triples_path, "r") as fin:
        triples = json.load(fin)
    triples = triples
    cls_triples = []
    batch_size = len(triples) // split + 1
    to_process_instances = triples[batch_size * url_idx: batch_size * (url_idx + 1)]
    # print(len(to_process_instances))
    for triple in tqdm(to_process_instances):
        desc = triple[2]
        res = get_responce_from_api(desc, url_idx)
        triple.append(res)
        cls_triples.append(triple)
    with open(output_path.format(url_idx), "w") as output_file:
        json.dump(cls_triples, output_file, indent=4)




def get_chebi_cls_res():
    chebi_path = "./PubChem/invalid/{}"

    sen_path = chebi_path.format("sentences.json")
    sentences = json.load(open(sen_path, "r"))

    output_path = chebi_path.format("res_vicuna_13B_all.jsonl")
    with open(output_path, "w") as output_file:
        for sid in tqdm(sentences, total = len(sentences)):
            sample = sentences[sid]
            sen = sample[3]
            res = get_responce_from_api(sen)
            # print(f"{sen}:{res}")
            # break
            output_file.write(str({sid:res}) + "\n")
            # break


                
            

def parse_cls_res():
    res_pathes = [
        "./PubChem/invalid/res_vicuna_13B_all.jsonl"
    ]
    # cls_res_path = 

    name2type = {
        'Source':0,
        'Architecture':1,
        'Usage':2,
        'Property':3
    }
    sid2type = {}
    
    for res_path in res_pathes:
        with open(res_path, "r") as res_file: 
            for line in res_file:
                single_res = eval(line.strip())
                # [65015, "Plerixafor", "C1CNCCNCCCN(CCNC1)CC2=CC=C(C=C2)CN3CCCNCCNCCCNCC3", "It is used in combination with grulocyte-colony stimulating factor (G-CSF) to mobilize hematopoietic stem cells to the perpheral blood for collection and subsequent autologous transplantation in patients with non-Hodgkin's lymphoma and multiple myeloma"], 
                sid, cls = list(single_res.items())[0]
                # cid, name, smile, desc = uncls_js[sid]
                cls = cls.replace("Classification Result: ", "")
                # cls = json.loads(cls)
                try:
                    cls = eval(cls)
                except SyntaxError:
                    continue
                if not isinstance(cls, list):
                    continue
                try:
                    # for i in range(len(cls)):
                    #     cls[i] = name2type[cls[i]]
                    # cls = [cid, desc] + cls
                    # writer.writerow(cls)
                    cls = name2type[cls[0]]
                    sid2type[sid] = cls
                except KeyError:
                    continue
    return sid2type


def write_res():
    # uncls_path = "./cls_by_rule/UNCLS/sentence_rm_0.9.json"
    uncls_path = "./PubChem/invalid/sentences.json"
    output_path = "./PubChem/cls_by_rule"
    # output_path = "./CheBL-20/Hug/cls_by_rules"
    sid2type = parse_cls_res()

    with open(uncls_path, "r") as uncls_file:
        uncls_js = json.load(uncls_file)
    for key in uncls_js:
        if key not in sid2type:
            print(key)
    cls_res = [{}, {}, {}, {}]
    CLS_DIRS = ["Source", "Architecture", "Usage", "Function"]
    for sid in sid2type:
        assert sid in uncls_js
        cls_type = sid2type[sid]
        cls_res[cls_type][sid] = uncls_js[sid]
    
    for cls_idx, cls in enumerate(CLS_DIRS):
        cls_output_dir = os.path.join(output_path, cls)
        if not os.path.exists(cls_output_dir):
            os.mkdir(cls_output_dir)
        cls_output_dir = os.path.join(cls_output_dir, "sentence_vicuna_invalid.json")
        cls_sen = cls_res[cls_idx]
        with open(cls_output_dir, "w") as cls_output_file:
            json.dump(cls_sen, cls_output_file, indent=4)
    # cls_num = [len(cls_sen) for cls_sen in cls_res]
    # print(cls_num)




if __name__ == "__main__":
    # get_lm_cls_res()
    # parse_cls_res()
    # write_res()
    # get_chebi_cls_res()
    parser = argparse.ArgumentParser()
    parser.add_argument("--url_idx", type=int, default=0)
    parser.add_argument("--split", type=int, default=8)
    args = parser.parse_args()
    get_lm_cls_res(args.url_idx, args.split)