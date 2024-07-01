# I need a program to convert .xmind file into csv file

import json
import csv
from xmindparser import xmind_to_dict

DESC_CLASSES = ["Property", "Usage", "Source", "Structure"]

def resolve_dict(origin_dict):
    if type(origin_dict) == dict:
        # for k, v in origin_dict.items():
        if "topics" in origin_dict.keys():
            new_dict = {}
            new_dict[origin_dict["title"]] = resolve_dict(origin_dict["topics"])
            return new_dict
        else:
            return [origin_dict["title"]]
    else:
        assert type(origin_dict) == list, f"{type(origin_dict)}"
        if "topics" in origin_dict[0]: # not leaf node
            new_dict = {}
            for item in origin_dict:
                new_dict[item["title"]] = resolve_dict(item["topics"])
            return new_dict

        else: # leaf node
            new_ls = []
            for item in origin_dict:
                new_ls += resolve_dict(item)
            return new_ls




def convert2json(cls_dict_ls):
    new_cls_dicts = resolve_dict(cls_dict_ls)
    with open("fine_grained_cls.json", "w") as output_js_file:
        json.dump(new_cls_dicts, output_js_file, indent=4)
    return new_cls_dicts

def convert2csv(cls_dict_ls):
    new_cls_dicts = resolve_dict(cls_dict_ls)
    with open("fine_grained_cls.csv", "w") as output_csv_file:
        csv_writer = csv.writer(output_csv_file)
        csv_writer.writerow(["Category", "SubTopic", "SubsubTopic", "Keyword"])
        def write_csv(depth, cls_dict):
            for k, v in cls_dict.items():
                if type(v) == list:
                    csv_writer.writerow([""] * depth + [k])
                    for item in v:
                        csv_writer.writerow(["", "", "", item])
                else:
                    csv_writer.writerow([""] * depth + [k])
                    write_csv(depth + 1, v)
        write_csv(0, new_cls_dicts)

                
    # for cls_dict in cls_dict_ls:
    #     cls_topic = cls_dict["topics"]
    #     print(len(cls_topic))
    # pass
    return

def parse_xmind(path):
    # A list, whose length is 1
    xmind_dict = xmind_to_dict(path)[0]
    # print(type(xmind_dict))
    # print(len(xmind_dict))
    cls_dict_ls = xmind_dict["topic"]["topics"] # A list of dicts for four cls 
    # Property
    # Usage
    # Source
    # Structure
    # print(xmind_dict.keys())
    new_cls_dict = convert2json(cls_dict_ls)
    convert2csv(cls_dict_ls)
    return new_cls_dict


if __name__ == "__main__":
    parse_xmind("./fine_grained_CLS/CompoundQA.xmind")
