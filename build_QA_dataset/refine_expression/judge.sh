for url_idx in {0..12}
do
    # Execute the command with the current value of url_idx
    nohup python generate_answer_with_GPT.py --url_idx $url_idx > ./log/judge_${url_idx}.log 2>&1 &
done