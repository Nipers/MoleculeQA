import json
import os
import re
from tqdm import tqdm
re_formats = [
    "((A)|(An)) [^ ]*"
]
redudant_keywords = [
    "The molecule",
]



if __name__ == "__main__":
    QA_path = "../build_QA_pairs/{}"
    for desc_cls in ["Property", "Usage", "Structure"]:
        redudant_answers = {}
        disc_options = {}
        filtered_questions = []
        file_ls = os.listdir(QA_path.format(desc_cls))
        for file_name in tqdm(file_ls):
            if not file_name.startswith("cls_desc_QA_pairs"):
                continue
            with open(os.path.join(QA_path.format(desc_cls), file_name), "r") as f:
                QA_pairs = json.load(f)
            filtered_questions.append({})
            for topic in QA_pairs:
                QA_pair_ls = QA_pairs[topic]
                for QA_pair in QA_pair_ls:
                    redudant = False
                    disc = False
                    # print(QA_
                    answer = QA_pair[3]

                    for keyword in redudant_keywords:
                        if answer.startswith(keyword):
                            if not topic in redudant_answers:
                                redudant_answers[topic] = []
                            redudant_answers[topic].append(QA_pair)
                            redudant = True
                            break
                    for re_format in re_formats:
                        # full match
                        res = re.match(re_format, answer)
                        if res is not None and res.span() == (0, len(answer)):
                            answer = answer.split(" ")[1]
                            if answer.find(topic) != -1:
                                if not topic in disc_options:
                                    disc_options[topic] = []
                                disc_options[topic].append(QA_pair)
                                disc = True
                                break
                    if not redudant and not disc:
                        if not topic in filtered_questions[-1]:
                            filtered_questions[-1][topic] = []
                        filtered_questions[-1][topic].append(QA_pair)
        # print(f"{desc_cls}: {len(redudant_answers)}")
        # print(f"{desc_cls}: {len(disc_options)}")
        with open(f"./{desc_cls}/redudant_answers.json", "w") as f:
            json.dump(redudant_answers, f, indent=4)
        with open(f"./{desc_cls}/disc_options.json", "w") as f:
            json.dump(disc_options, f, indent=4)
        with open(f"./{desc_cls}/filtered_questions.json", "w") as f:
            json.dump(filtered_questions, f, indent=4)

         