import re
import os
import json

from tqdm import tqdm

from utils import desc2sentence, SEN_DIR
RE_RULE_TABLE = {
    "Source" : "(.*? ((is)|(has a role as)) a (((((( and a[n]? )?([^ ]* )?metabolite){1,2})|(natural product))[\.]?)( ((found in)|(produced by)).*)?)|(.* ((metabolite)|(natural product))[\.]?))|(.* been isolated from .*)",
    "Type" : "((([^ ]*[ ]?){,2})|(The IMA symbol)) ((is)|(has a role as)) ((a[n]?( .*)? ((.*tide)|(.*choline)|(.*ridine)|(.*ride)|(.*side)|(.*mi[dn]e)|(.*noid)|(.*enol)|(.*ami[dn]e)|(salt)|(ether)|(.*peptide)|(ester)|(organic molecular entity)|(furopyran)|(alkaloid)|(sugar)|(acid)|(alcohol)|(.*compound))[s]?[\.]?)|(((a[n]? ((member)|(enantiomer)))|(one)) of .*))",
    "Usage": "([^ ]* ((((has a role as)|(is a[n]?)) .* ((agent)|([Ii]nhibitor)|(antagonist)|(drug)|(agonist)|(depressant)))|(has been used ((in)|(for)) .*))[\.]?)|(Used (as)|(for)|(to) .*)",
    "Function" : "(([^ ]*) is functionally related to .*)|(Isolated from .*, it .*)|(.* [Cc]orrosive to .*)|((Toxic by )|(.* irritate).*)",
    "Architecture": "(([^ ]*) ((is ((a[n]?)|(the)) ((.* ((consist)|(compos))[e]?((ing)|(s)|(ed)))|(((conjugate [^ ]*)|(enantiomer)|(tautomer)))) of .*)|(contain((s)|(ing)|(ed)) a .*)|(.* ((at position [0-9]+.*)|(((major)|(principal)) (micro)?species at pH.*)))))|(.* at position[s]? ([0-9',]+( (and)?)?){1,}[\.]?)",
    "Physics" : "((((Density)|(pH)|(Tast)|(((Boil)|(Melt)|(Freeze)ing)|(Flash) point)) .*)|(.* solid)|(.*[ -]?(in)?soulable)|(.* dense[r]? than .*)|(.* ((soluble in)|(float[s]? on)) .*)|(.* ((appears as)|(is a)) .* ((crystal)|(solid)|(powder)|(liquid))).*)|(.* (a )?.* odor[\. ,]?)",
    "Useless": "(See also:.*)|([A-Z\(\)0-9, ]*)|(\(From .*\))|(\(.*, p[0-9]*\))",
    "Medical": "(.* is under investigation in .* trial.*)",
    "Derive":"It derives from .*",
    "Mechianism": "The mechanism of action .*",
    "New": "((It)|([^ ]*)) is(( and)? a[n]?( member of)?( (?!and )(?!of )[^ ,.]+){1,4}[,.]?){2,9}"
}
# str_rule_table = {
#     "Type": ["is a member of", "It is a", "It is an", "has a role as "]
# }
CLS_OUT_PATH = "./CheBL-20/Hug/cls_by_rule"
class Rule():
    def __init__(self, base_dir, name):
        self.sentences = {}
        self.base_dir = base_dir
        self.name = name
        self.save_dir = os.path.join(self.base_dir, self.name)
        if not os.path.exists(self.save_dir):
            os.mkdir(self.save_dir)

    def check(self, str): 
        raise NotImplementedError
    
    def add(self, sid, sample):
        self.sentences[sid] = sample

    def save(self):
        output_path = os.path.join(self.save_dir, "sentences.json")
        with open(output_path, "w") as output_file:
            json.dump(self.sentences, output_file, indent=4)
        
    
    def process(self, sid, sample:list):
        sentence = sample[3]
        if self.check(sentence):
            self.add(sid, sample)


class RE_Rule(Rule):
    def __init__(self, base_dir, name, pattern):
        super().__init__(base_dir, name)
        # if type(pattern) == type(""):
        self.pattern = re.compile(pattern)
        # else:
        #     self.pattern = [re.compile(p) for p in pattern]
        # self.pattern = re.compile(".* is a[n]? ([a-zA-Z0-9]|[-])*")
    
    def check(self, sentence):
        # if type(self.pattern) != type([]):
        res = re.match(self.pattern, sentence)
        if res is not None:
            if res.span()[1] == len(sentence):
                return True
        return False
        # else:
        #     res = [re.match(p, sentence) for p in self.pattern]
        #     return any([i != None for i in res])
    

class STR_Rule(Rule):
    def __init__(self, base_dir, name, sub_str):
        super().__init__(base_dir, name)
        self.sub_str = sub_str

    def check(self, sentence:str):
        if type(self.sub_str) == type(""):
            return sentence.find(self.sub_str) != -1
        else:
            res = [sentence.find(sub_str) for sub_str in self.sub_str]
            return any([i != -1 for i in res ])
    

def classification():
    sentences = desc2sentence(os.path.join(SEN_DIR, "sentences.json"))

    for rule_name in RE_RULE_TABLE:
        print(f"Match with rule {rule_name}, {RE_RULE_TABLE[rule_name]}")
        rule = RE_Rule(CLS_OUT_PATH, rule_name, RE_RULE_TABLE[rule_name])
        for sid, sentence in tqdm(sentences.items()):
            # sid, sentence = sentence
            # print(sid)
            # print(sentence)
            rule.process(sid, sentence)
        rule.save()

def check_dup_and_uncls():
    sentences = desc2sentence(os.path.join(SEN_DIR, "sentences.json"))
    uncls_sentences = {}
    cls_sets = {}
    rule_names = list(RE_RULE_TABLE.keys())
    for rule_idx, rule_name in enumerate(rule_names):
        with open(os.path.join(CLS_OUT_PATH, rule_name, "sentences.json"), "r") as rule_file:
            cls_sets[rule_idx] = set(json.load(rule_file).keys())
            print(f"{len(cls_sets[rule_idx])} sentences in rule {rule_name}")
    
    for rule_idx, rule_name in enumerate(rule_names):
        for another_idx in range(rule_idx + 1, len(rule_names)):
            another_rule_name = rule_names[another_idx]
            dup = cls_sets[rule_idx] & cls_sets[another_idx]
            if len(dup) != 0:
                print(f"{len(dup)} duplicated sentences between {rule_name} and {another_rule_name}")
            if not len(dup) == 0:
                dup_sentences = {}
                for sid in dup:
                    dup_sentences[sid] = sentences[sid]
                with open(os.path.join(CLS_OUT_PATH, rule_name, f"duplicate_with_{another_rule_name}.json"), "w") as dup_output:
                    json.dump(dup_sentences, dup_output, indent=4)
    
    for sid, sentence in sentences.items():
        if not any([(str(sid) in cls_set) for cls_set in cls_sets.values()]):
            uncls_sentences[sid] = sentence
        # print(cls_sets[3])
        # print(str(sid))
        # print([(str(sid) in cls_set) for cls_set in cls_sets.items()])
        # break
    UNCLS_PATH = os.path.join(CLS_OUT_PATH, "UNCLS")
    if not os.path.exists(UNCLS_PATH):
        os.mkdir(UNCLS_PATH)
    print(f"{len(uncls_sentences)} unclassified sentences")
    with open(os.path.join(UNCLS_PATH, "sentences.json"), "w") as uncls_output:
        json.dump(uncls_sentences, uncls_output, indent=4)



if __name__ == "__main__":
    classification()
    check_dup_and_uncls()

# There are 500866 sentences.
# 206230 sentences in rule Source
# 91227 sentences in rule Type
# 6330 sentences in rule Usage
# 14109 sentences in rule Function
# 32545 sentences in rule Architecture
# 5176 sentences in rule Physics
# 1850 sentences in rule Useless
# 1131 sentences in rule Medical
# 1558 sentences in rule Derive
# 887 sentences in rule Mechianism
# 33835 sentences in rule New
# 9 duplicated sentences between Source and Type
# 1 duplicated sentences between Source and Function
# 29 duplicated sentences between Source and Architecture
# 1 duplicated sentences between Source and Physics
# 13 duplicated sentences between Type and Usage
# 6111 duplicated sentences between Type and Architecture
# 15 duplicated sentences between Type and Physics
# 14415 duplicated sentences between Type and New
# 3 duplicated sentences between Usage and Architecture
# 87 duplicated sentences between Usage and New
# 3 duplicated sentences between Function and Physics
# 1 duplicated sentences between Function and Medical
# 1 duplicated sentences between Architecture and New
# 104 duplicated sentences between Physics and New
# 126769 unclassified sentences
# Source, property, usage, structure

# There are 104988 sentences.
# 9679 sentences in rule Source
# 18426 sentences in rule Type
# 4163 sentences in rule Usage
# 785 sentences in rule Function
# 25090 sentences in rule Architecture
# 10 sentences in rule Physics
# 0 sentences in rule Useless
# 0 sentences in rule Medical
# 11449 sentences in rule Derive
# 0 sentences in rule Mechianism
# 17281 sentences in rule New
# 10 duplicated sentences between Source and Type
# 1 duplicated sentences between Source and Function
# 23 duplicated sentences between Source and Architecture
# 8 duplicated sentences between Type and Usage
# 4701 duplicated sentences between Type and Architecture
# 8705 duplicated sentences between Type and New
# 62 duplicated sentences between Usage and New
# 31605 unclassified sentences