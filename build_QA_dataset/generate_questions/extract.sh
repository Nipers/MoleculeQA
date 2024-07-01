CLS=Usage
split_num=4
mode=extract
nohup python extract_desc_for_informative_topics.py --desc_cls ${CLS} --split ${split_num} --url_idx 0 --mode ${mode} > ${CLS}_0.log 2>&1 &