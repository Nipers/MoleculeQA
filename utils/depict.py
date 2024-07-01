import math
import matplotlib.pyplot as plt
import json

# 根据二级节点弄一下topic，然后调一调配色

with open("biot5_sub_topic_acc.json", "r") as fin:
    biot5topic_acc = json.load(fin)

with open("t5_sub_topic_acc.json", "r") as fin:
    t5topic_acc = json.load(fin)

t5_aspect2color = {}
bio_t5_aspect2color = {}
colors = ['#80BA8A', '#87B5B2', '#797BB7', '#998DB5', '#F1C89A', '#F9E9A4','#E58579', '#ED9F9B']# , '#E18E6D'

for idx, aspect in enumerate(["Structure", "Source", "Property", "Usage"]):
    t5_aspect2color[aspect] = colors[2 * idx]
    bio_t5_aspect2color[aspect] = colors[2 * idx + 1]
t5_acc = {
    "Source": 66.42,
    "Structure": 60.42,
    "Property": 45.83,
    "Usage": 43.74
}
biot5_acc = {
    "Source": 66.42,
    "Structure": 60.42,
    "Property": 45.83,
    "Usage": 43.74
}

plt.figure(figsize=(23,10))
# Set the y-axis range from 30% to 90%
plt.ylim(0, 80)

# Plot bars
bar_width = 0.8
offset = 0

# T5 base first
all_topics = []
for aspect in ["Structure", "Source", "Property", "Usage"]:
    topics = list(t5topic_acc[aspect].keys())
    all_topics += topics
    values = list(t5topic_acc[aspect].values())
    # for i in range(len(values)):
    #     values[i] = values[i] -30
    row = list(range(offset, offset + 2 * len(topics), 2))
    # save 2 decimal places
    acc = t5_acc[aspect]
    acc = math.ceil(acc)
    plt.bar(row, values, color=t5_aspect2color[aspect], width=bar_width, label=f'T5-{aspect.replace("Usage", "Application")} - {acc}%')
    topics = list(biot5topic_acc[aspect].keys())
    values = list(biot5topic_acc[aspect].values())
    row = list(range(offset + 1, offset + 1 + 2 * len(topics), 2))
    acc = biot5_acc[aspect]
    acc = math.ceil(acc)
    plt.bar(row, values, color=bio_t5_aspect2color[aspect], width=bar_width, label=f'BioT5-{aspect.replace("Usage", "Application")} - {acc}%', hatch="/")
    offset += 2 * len(topics)
# Add labels and title
# plt.xlabel('Topic', fontweight='bold')
# offset = 1

# for idx, aspect in enumerate(biot5topic_acc.keys()):
#     # for i in range(len(values)):
#     #     values[i] = values[i] -30
#     # save 2 decimal places
#     offset += 2 * len(topics)

replace_table = {
    "Agricultural Chemicals": "Agri. Chems",
    "Biological Agents": "Bio. Agents",
    "Chemical Applications and Techniques": "Chem. Apps",
    "Pharmacodynamics and Pharmacokinetics": "Pharmaco.",
    "Regulatory Status and Approval": "Approval",
    "Research and Development": "Reasearch",
    "Therapeutic Use": "Therapy",
    "Biological and Pharmacological Activities": "Pharmac",
    "Types of Reactions": "Reactions",
    "Chemical Interaction and Mechanism": "Mechanism",
    "Chemical Properties": "Chem. Prop",
    "Environmental and Safety Concerns": "Env. Safety",
    "Medical and Therapeutic Efficacy": "Medical",
    "Physical and Sensory Properties": "Physical",
    "metabolite": "metabilite",
    "derives from": "derivation",
    "isolated from": "isolateion",
    "Biochemical and Biological Terms": "Bio. Terms",
    "Chemical Bonding and Interactions": "Bonding",
    "Chemical Compounds and Classes": "Classes",
    "Chemical Species and States": "Species",
    "Functional Groups and Chemical Entities": "Groups",
    "Molecular Structure and Configuration": "Config"
}

for i in range(len(all_topics)):
    all_topics[i] = replace_table[all_topics[i]]
plt.xticks([2 * r + 0.5 for r in range(len(all_topics))], all_topics, rotation=60)
plt.ylabel('Accuracy')
# plt.title('Bar Chart Representation')
ax = plt.gca()
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.spines['left'].set_visible(False)
ax.yaxis.grid(True)  # Horizontal gridlines
ax.set_axisbelow(True)  # Set gridlines behind bars


# Create legend at the top of the figure
plt.legend(loc='upper center', bbox_to_anchor=(0.5, 1.05), ncol=len(biot5topic_acc.keys()) * 2, fontsize='large')

# Adjust layout and save the figure
plt.tight_layout()
# Create legend & Show graphic
# plt.legend()
# plt.tight_layout()
plt.savefig('bar_chart.pdf', format="pdf", bbox_inches="tight")