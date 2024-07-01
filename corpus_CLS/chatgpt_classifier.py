from openai import OpenAI
from collections import defaultdict
from typing import List, Dict
from tqdm import tqdm
import json

def write_json(file_path, data):
    with open(file_path, "w") as f:
        json.dump(data, f, indent=4)
  
openai_api_key = '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'
system_message = """
    You are a research assistant for molecular research, familiar with the description text of molecules.
    Given a sentence that describes a molecule, I want you to classify it into four categories: source, structure, usage, and property. Here are the definition and verbal examples for each category:

    ##Source##: which describes the distribution of the compound in nature or from what the compound is extracted. Examples:
    1. 'It is a plant metabolite, a human urinary metabolite', 'Sampangine is extracted from several plants including the stem bark of Cananga odorata',
    2. 'Luteoside B is a natural product found in Markhamia stipulata and Tecoma stans var. velutina with data available.'.


    ##Structure##: which may describe the type of given compound, such as 'salt', 'ether', 'Benzodiazepines', or 'diterpenoid', or depicts numbers and locations of its components like 'Diphenylcyclopropenone has phenyl substituents at the 2- and 3-positions'
    Examples:
    1. 'Melatonin is a member of the class of acetamides that is acetamide in which one of the hydrogens attached to the nitrogen atom is replaced by a 2-(5-methoxy-1H-indol-3-yl)ethyl group', 
    2. 'Orbifloxacin is a fluoroquinolone'


    ##Usage##: which includes medical usage like 'treatment of fungal', 'safener', 'antibiotic', experimental usage like 'solvent', 'reagent', 'be investigated for', agricultural usage like 'herbicide', 'pesticide', 'fertilizer' and other descriptions about how people utilize this compound. 
    Examples:  
    1. 'The prototypical analgesic used in the treatment of mild to moderate pain', 
    2. 'A reversible inhibitor of cholinesterase with a rapid onset, it is used in myasthenia gravis both diagnostically and to distinguish between under- or over-treatment', approvements of FDA is also Usage-related information.


    ##Property##: which includes physical properties like melting/boiling/freezing point, density, smell, taste, color, solid/liquid/gas/powder/crystal, volatileness, solubleness, chemical properties like pH value, half-life, toxicity, ignitability, corrosivity, irritant, reactivity, storage methods, medical effects like various activities (antineoplastic carcinogenesis, antiviral, agonist activity), vasodilation, ion channel activities. 
    Examples: 
    1. 'Tremorgenic mycotoxins affect central nervous system activity, with their defining characteristic being the tremors that they cause', 
    2. 'Insoluble in water but reacts with water to produce a toxic vapor', 'It has dermatotoxic activity causing inflammation of the skin'

    Based on the above knowledge, please help me classify the following sentences. 
    1. The given sentence may contain multiple categories. If so, rewrite the sentence into multiple parts, each part containing only one category, and each split sentence must be complete and smooth. 
    2. Ensure the principle of least splitting. 
    3. Only one sentence is allowed for per category.
    4. Note that the reply should follow the json format: [{"category":..., "sentence":...}, ...].
    5. merge sentences under same category.
"""

client = OpenAI(
    # defaults to os.environ.get("OPENAI_API_KEY")
    api_key=openai_api_key,
)

def chatgpt_annotation(desc:str):
    messages = [ {"role": "system", "content": system_message}]
    messages.append({"role": "user", "content": desc})

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=messages
    )
    reply = response.choices[0].message.content
    return reply

def annotation(descriptions:List[str]):
    result = []
    for desc in tqdm(descriptions):
        reply = chatgpt_annotation(desc)
        try:
            reply = eval(reply)
            assert isinstance(reply, list)
        except:
            print(f"illegal reply format: {reply}")
            continue
        # merge sentences under same category
        keys = list(set([r['category'] for r in reply]))
        res = defaultdict(list)
        for key in keys:
            for r in reply:
                if r['category'] == key:
                    try:
                        res[key].append(r['sentence'])
                    except:
                        print(f"'sentence' not in {r}")
        for key in keys:
            res[key] = ' '.join(res[key])
        
        result.append(res)
        print(res)
    return result

if __name__ == "__main__":
    with open("preExp/momu_100_results.txt", "r") as f:
        descs = f.readlines()
        descs = [desc.strip() for desc in descs]
    
    result = annotation(descs)
    # save result
    write_json("preExp/chatgpt_momu_anno.json", result)