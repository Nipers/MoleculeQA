import math
import random
from transformers import AutoTokenizer
import os
import json
import torch
from nomic import atlas
import argparse
from statistic import info_files
from torch.utils.data import Dataset, DataLoader
import torch.nn as nn
from torch.nn import CrossEntropyLoss
import numpy as np
from tqdm import tqdm
from transformers.models.bert.modeling_bert import BertModel, BertForSequenceClassification, BertConfig
from transformers.models.bert.tokenization_bert import BertTokenizer
from transformers.models.t5.modeling_t5 import T5ForQuestionAnswering, T5Config
from transformers.models.t5.tokenization_t5 import T5Tokenizer

import pytorch_lightning as pl
from pytorch_lightning import Trainer, seed_everything
from pytorch_lightning.callbacks import ModelCheckpoint
from pytorch_lightning.loggers import TensorBoardLogger
from torch.optim import AdamW
from transformers import get_linear_schedule_with_warmup

SOURCE_DIR = "./ST_pairs_invalid"
TARGET_DIR = "./PubChem/cls_by_rule"
min_length = 15
CLASSES2TYPE = {
    "Source": 0, 
    "Derive": 0,
    "Architecture": 1, 
    "New":1, 
    "Type": 1, 
    "Usage": 2, 
    "Medical":2, 
    "Function":3, 
    "Physics":3, 
    "Mechianism":3,
}
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
# 1 duplicated sentences between Architecture and New
# 104 duplicated sentences between Physics and New
# 126769 unclassified sentences


PREFIX_PATH = "./PubChem"
DEDUPLICATE_DICT = {
    "Source": [f"{PREFIX_PATH}/cls_by_rule/Source/duplicate_with_Architecture.json",
               f"{PREFIX_PATH}/cls_by_rule/Source/duplicate_with_Function.json",
               f"{PREFIX_PATH}/cls_by_rule/Source/duplicate_with_Type.json"],
    "Type": [f"{PREFIX_PATH}/cls_by_rule/Type/duplicate_with_Physics.json", 
             f"{PREFIX_PATH}/cls_by_rule/Type/duplicate_with_Usage.json", 
             f"{PREFIX_PATH}/cls_by_rule/Type/duplicate_with_New.json"],
    "Usage": [f"{PREFIX_PATH}/cls_by_rule/Usage/duplicate_with_Architecture.json"],
    "Architecture": [f"{PREFIX_PATH}/cls_by_rule/Type/duplicate_with_Architecture.json"],
    "Physics": [f"{PREFIX_PATH}/cls_by_rule/Source/duplicate_with_Physics.json",
                f"{PREFIX_PATH}/cls_by_rule/Function/duplicate_with_Physics.json"],
    "New": [f"{PREFIX_PATH}/cls_by_rule/Usage/duplicate_with_New.json",
            f"{PREFIX_PATH}/cls_by_rule/Architecture/duplicate_with_New.json",
            f"{PREFIX_PATH}/cls_by_rule/Physics/duplicate_with_New.json"],
    "Derive": [],
    "Medical": [],
    "Function": [],
    "Mechianism": [],
}

from torchmetrics.classification import MulticlassConfusionMatrix

def desc2sentence(sen_path):
    if os.path.exists(sen_path):
        with open(sen_path, "r") as sen_file:
            sentences = json.load(sen_file)
    # sentence_id = 0
    else:
        sentences = []
        file_ls = os.listdir(SOURCE_DIR)
        # file_ls = ["2244.json", "134601.json", "1983.json", "2349.json", "338.json"]
        error_ls = []
        for file_name in tqdm(file_ls):
            if not file_name in info_files:
                file_name = os.path.join(SOURCE_DIR, file_name)
                with open(file_name, "r") as fin:
                    try:
                        file_js = json.load(fin)
                    except json.decoder.JSONDecodeError:
                        error_ls.append(file_name)
                        continue
                    cid = file_js["cid"]
                    main_name = file_js["main_name"]
                    smile = file_js["smile"]
                    desc_texts = file_js["desc_texts"]
                    for desc_text in desc_texts:
                        desc_contents = desc_text["content"]
                        for content in desc_contents:
                            sentence_ls = content.split(". ")
                            for sentence in sentence_ls:
                                if len(sentence) > min_length:
                                    sentences.append([cid, main_name, smile, sentence.strip()])
        with open(sen_path, "w") as sen_file:
            json.dump(sentences, sen_file)
        with open(os.path.join(TARGET_DIR, "error.json"), "w") as error_file:
            json.dump(error_ls, error_file)
    print(f"{len(sentences)} sentences to encode.")
    return sentences

class SciBertTokenizer():
    def __init__(self, tokenizer, max_length):
        self.tokenizer = tokenizer
        self.max_length = max_length
        self.bos_token_id = tokenizer.cls_token_id
        self.pad_token_id = tokenizer.pad_token_id
    
    def encode(self, cid, text, label=None):
        tokenizer = self.tokenizer
        input_ids = [self.bos_token_id] + tokenizer.convert_tokens_to_ids(tokenizer.tokenize(text))[:510]
        attention_mask = [1] * len(input_ids)
        
        res = {
            "cid": cid,            
            "input_ids": input_ids,
            "attention_mask": attention_mask
        }
        if label != None:
            res["label"] = label
        return res
    
    def padding(self, text_batch):
        max_length = max(len(sample["input_ids"]) for sample in text_batch)
        batch_cid = []
        batch_input_ids = []
        batch_attention_mask = []
        batch_labels = []
        for sample in text_batch:
            input_ids = sample["input_ids"]
            attention_mask = sample["attention_mask"]
            length_to_pad = max_length - len(input_ids)

            input_ids += [self.pad_token_id] * length_to_pad
            attention_mask += [0] * length_to_pad

            batch_cid.append(sample["cid"])
            batch_input_ids.append(input_ids)
            batch_attention_mask.append(attention_mask)
            if "label" in sample:
                batch_labels.append(sample["label"])
        
        res = {
            "cid": batch_cid,
            "input_ids": batch_input_ids,
            "attention_mask": batch_attention_mask
        }
        if len(batch_labels) != 0:
            res["labels"] = batch_labels
        return res
    
    def encode_batch(self, text_batch):
        batch = []
        for sample in text_batch:
            if len(sample) == 2:
                cid, text = sample
                batch.append(self.encode(cid, text, None))
            else:
                cid, text, label = sample
                batch.append(self.encode(cid, text, label))

        return self.padding(batch)

class T5CLSTokenizer():
    def __init__(self, tokenizer:T5Tokenizer, max_length):
        self.tokenizer = tokenizer
        self.max_length = max_length
    
    def encode_batch(self, text_batch):
        text_ls = []
        label_ls = []
        cid_ls = []
        for sample in text_batch:
            if len(sample) == 2:
                cid, text = sample
                text_ls.append(text)
            else:
                cid, text, label = sample
                text_ls.append(text)
                label_ls.append(label)
            cid_ls.append(cid)
        batch = self.tokenizer(text_ls, padding="longest", max_length = self.max_length,truncation=True)
        if len(label_ls) > 0:
            batch["labels"] = label_ls
        batch["cid"] = cid_ls       
        return batch



# 可以保留
class GeneralCollator():
    
    def __init__(self, tokenizer: SciBertTokenizer, pop = False) -> None:
        self.tokenizer = tokenizer
        self.pop = pop

    def __call__(self, text_batch):
        batch = self.tokenizer.encode_batch(text_batch)
        if self.pop and "cid" in batch:
            batch.pop("cid")
        for k, v in batch.items():
            # print(k)
            # print(v)
            # if k != "cid":
            batch[k] = torch.LongTensor(v)
        # print(batch)
        return batch


class PubChemSTMDataset(Dataset):
    def __init__(self, sentences, collator:GeneralCollator, anonym):
        self.sentences = list(sentences.values())
        self.collator = collator
        self.anonym = anonym

    def __len__(self):
        return len(self.sentences)

    def __getitem__(self, index):
        cid = self.sentences[index][0]
        text = self.sentences[index][3]
        if self.anonym:
            name = self.sentences[index][1]
            text = text.replace(name, "")
        return [cid, text]

    def collate_fn(self, text_batch):
        return self.collator(text_batch)


class CLSDataset(Dataset):
    def __init__(self, sentences, collator:GeneralCollator, anonym):
        self.sentences = sentences
        self.collator = collator
        self.anonym = anonym
        self.statistic()
    def statistic(self):
        ls = [0,0,0,0]
        for sen in self.sentences:
            label = sen[4]
            ls[label] += 1
        print(ls)
    def __len__(self):
        return len(self.sentences)

    def __getitem__(self, index):
        cid = self.sentences[index][0]
        text = self.sentences[index][3]
        label = self.sentences[index][4]
        if self.anonym:
            name = self.sentences[index][1]
            text = text.replace(name, "It")

        return [cid, text, label]

    def collate_fn(self, text_batch):
        return self.collator(text_batch)

def text_emb():
    tokenizer = AutoTokenizer.from_pretrained('allenai/scibert_scivocab_uncased')
    model = BertModel.from_pretrained('allenai/scibert_scivocab_uncased')
    state_dict = torch.load("./SciBert/epoch=0.ckpt", map_location="cpu")
    if "state_dict" in state_dict:
        state_dict = state_dict["state_dict"]
    state_dict.pop("model.classifier.weight")
    state_dict.pop("model.classifier.bias")
    keys = list(state_dict.keys())
    for key in keys:
        value = state_dict.pop(key)
        key = key.replace("model.bert.", "")
        state_dict[key] = value
        
    model.load_state_dict(state_dict)
    device = torch.device("cuda:2")
    target_dir = os.path.join(TARGET_DIR, "UNCLS") 
    sentences = desc2sentence(sen_path = os.path.join(target_dir, "sentences.json"))
    tokenizer = SciBertTokenizer(tokenizer)
    collator = GeneralCollator(tokenizer=tokenizer, pop=False)

    dataset = PubChemSTMDataset(sentences, collator, True)
    model.to(device)
    data_loader = DataLoader(dataset, batch_size = 144, shuffle=False, collate_fn = dataset.collate_fn,num_workers = 16)
    with torch.no_grad():
        cid_ls = []
        emb_ls = []
        # cur_index = 1
        # for index, batch in tqdm(enumerate(data_loader)):
        for batch in tqdm(data_loader):
            cid = batch.pop("cid")
            for k, v in batch.items():
                batch[k] = v.to(device)

            encoder_output = model.forward(**batch).last_hidden_state
            encoder_output = encoder_output[:, 0, :]
            # attention_mask = batch["attention_mask"]
            # encoder_output = ((encoder_output * attention_mask.unsqueeze(-1)).sum(1) / attention_mask.sum(-1).unsqueeze(-1))
            # print(encoder_output.shape)
            # return
            cid_ls += cid
            emb_ls.append(encoder_output.cpu().detach().numpy())
            # if (index + 1) % 10000 == 0:
        emb_ls = np.concatenate(emb_ls, axis=0, dtype=np.float32)
        assert emb_ls.shape[0] == len(cid_ls)
        np.save(os.path.join(target_dir, "mol_desc_emb_cls_ana_trained.npy"), emb_ls)
        with open(os.path.join(target_dir, "mol_cid_cls_ana_trained.json"), "w") as cid_js_file:
            json.dump(cid_ls, cid_js_file)
            #     cur_index += 1



class CLSWrapper(pl.LightningModule):
    def __init__(self, 
        model: nn.Module,
        config,
        learning_rate: float = 5e-5,
        warmup_steps: int = 0,
        weight_decay: float = 0.0,
        l_rank: int = 0,
        threshold: float = 0.0,
        # model_name: str = "SciBert",
    ):
        super().__init__()
        self.loss_fct = CrossEntropyLoss()
        self.hparams.learning_rate = learning_rate
        self.hparams.warmup_steps = warmup_steps
        self.hparams.weight_decay = weight_decay
        self.save_hyperparameters(ignore=['model', "config"])
        self.model = model
        self.num_labels = config.num_labels
        self.metric = MulticlassConfusionMatrix(config.num_labels, normalize="all")
        self.l_rank = l_rank
        self.output_dir = ""
        self.softmax = torch.nn.Softmax(dim = -1)
        self.threshold = threshold
        self.cls_file = None
        # self.model_name = model_name

    def training_step(self, batch, batch_idx):
        # if self.model_name == "SciBert":
        outputs = self.model(**batch, return_dict=True)
        return outputs.loss
        # else:
        #     labels = batch.pop("labels")
        #     scores = self.model(**batch)
        #     loss = self.loss_fct(scores, labels)
        #     return loss

    def validation_step(self, batch, batch_idx):
        labels = batch.pop("labels")
        # batch, labels = batch
        # labels = labels.reshape(-1)
        with torch.no_grad():
            scores = self.model(**batch, return_dict=True).logits

        # print(scores.shape)
        # print(labels.shape)
        # print(scores.size())
        # print(labels.size())
        # loss = self.loss_fct(scores, labels).item()
        self.metric.update(scores, labels)

    def on_test_epoch_start(self) -> None:
        self.test_result = []
        self.test_cid = []
        self.test_prob = []
        return super().on_test_epoch_start()

    def test_step(self, batch, batch_idx):
        # labels = batch.pop("labels")
        # batch, labels = batch
        # labels = labels.reshape(-1)
        batch.pop("labels")
        # if "cid" in batch:
        cid = batch.pop("cid").tolist()
        with torch.no_grad():
            scores = self.model(**batch, return_dict=True).logits
        # print(scores.size())
        # print(labels.size())
        # logits = torch.nn.Softmax()
        labels = scores.max(dim = -1)[1].reshape(-1).cpu().tolist()
        probs = self.softmax(scores)
        probs = probs.max(dim = -1)[0].reshape(-1).cpu().tolist()
        self.test_result += labels
        self.test_cid += cid
        self.test_prob += probs
        # loss = self.loss_fct(scores, labels).item()
        # self.metric.update(scores, labels)

    def on_test_epoch_end(self) -> None:
        with open(f"{PREFIX_PATH}/cls_by_rule/UNCLS/{self.cls_file}", "r") as json_file:
            sentences = json.load(json_file)
        idx = 0
        cls_labels = [0,0,0,0]
        cls_result = []
        for key in sentences:
            cid, name, smile, des = sentences[key]
            assert self.test_cid[idx] == cid, f"{idx} sample wrong"
            if self.test_prob[idx] > self.threshold:
                cls_result.append([cid, des, self.test_result[idx], self.test_prob[idx]])
                cls_labels[self.test_result[idx]] += 1
            idx += 1
        with open(self.output_dir + f"_cls_result_{self.threshold}.json", "w") as output_file:
            json.dump(cls_result, output_file)
        print(cls_labels)
            
        #     json.dump(self.test_result, output_file)
        # with open("cls_cid.json", "w") as output_file:
        #     json.dump(self.test_cid, output_file)

    def on_validation_epoch_end(self) -> None:
        res = self.metric.compute()
        acc = 0
        for i in range(self.num_labels):
            acc += res[i][i]

        self.log(f"val_acc", acc, on_step=False, on_epoch=True, prog_bar=True, logger=True, sync_dist=True)
        # self.log(f"res", res.sum(), on_step=False, on_epoch=True, prog_bar=True, logger=True, sync_dist=True)
        if res.device.index == 2:
            print(res.tolist())
        # print(res.device)
        self.metric.reset()

        return super().on_validation_epoch_end()
    
    def configure_optimizers(self):
        model = self.model
        no_decay = ["bias", "LayerNorm.weight"]
        optimizer_grouped_parameters = [
            {
				"params": [p for n, p in model.named_parameters() if not any(nd in n for nd in no_decay)],
				"weight_decay": self.hparams.weight_decay,
			},
            {
				"params": [p for n, p in model.named_parameters() if any(nd in n for nd in no_decay)],
				"weight_decay": 0.0,
            },
        ]
        optimizer = AdamW(optimizer_grouped_parameters, lr=self.hparams.learning_rate)

        scheduler = get_linear_schedule_with_warmup(
            optimizer,
            num_warmup_steps=self.hparams.warmup_steps,
            num_training_steps=self.trainer.estimated_stepping_batches,
        )
        scheduler = {"scheduler": scheduler, "interval": "step", "frequency": 1}
        return [optimizer], [scheduler]


local_rank = None


def rank0_print(*args):
    if local_rank == 0:
        print(*args)


def use_classifier(args):
    def set_output_path(pretrained_ckpt):
        father_dir, file_name = os.path.split(pretrained_ckpt)
        father_dir = father_dir.replace("ckpt", "infer_result")
        if not os.path.exists(father_dir):
            os.mkdir(father_dir)
        file_name = file_name.split("-")[0].replace("=", "_")
        return os.path.join(father_dir, file_name)


    global local_rank
    model_name = args.model_name
    ConfigModule, TokenizerModule, CLSTokenizer, ModelMudule = CONFIG[model_name]
    
    local_rank = args.local_rank
    print(f"LOCAL RANK: {local_rank}")
    seed_everything(42)
    tokenizer = TokenizerModule.from_pretrained(args.model_path)
    tokenizer = CLSTokenizer(tokenizer, args.max_length)
    config = ConfigModule.from_pretrained(args.model_path)
    config.__setattr__("num_labels", 4)
    model = ModelMudule(config)
    if args.model_name == "SciBert":
        config.__setattr__("num_labels", 4)
        model.bert = BertModel.from_pretrained(args.model_path)
    # device = torch.device("cuda:5")
    sentences = []
    cls = "UNCLS"
    target_dir = os.path.join(TARGET_DIR, cls) 
    sens = desc2sentence(sen_path = os.path.join(target_dir, args.cls_file))
    for key in sens:
        sens[key].append(-1)
        sentences.append(sens[key])
    # tokenizer = SciBertTokenizer(tokenizer)
    collator = GeneralCollator(tokenizer=tokenizer, pop=False)
    data_num = len(sentences)
    rank0_print(f"{data_num} sentences for CLS")
    test_dataset = CLSDataset(sentences, collator, False)
    # train_dataset = CLSDataset(sentences[:1000], collator, True)
    # dev_dataset = CLSDataset(sentences[-1000:], collator, False)
    # model.to(device)
    test_loader = DataLoader(test_dataset, batch_size = args.batch_size, shuffle=False, collate_fn = test_dataset.collate_fn, num_workers = 16)

    model = CLSWrapper(model, config, args.learning_rate, local_rank, args.test_threshold)
    model.cls_file = args.cls_file
    model.output_dir = set_output_path(args.pretrained_ckpt)
    state_dict = torch.load(args.pretrained_ckpt, map_location="cpu")
    state_dict = state_dict["state_dict"]
    model.load_state_dict(state_dict)
    trainer = Trainer(accelerator="gpu",
                    # logger=logger,
                    max_epochs=args.num_train_epochs,
                    devices=args.devices,
                    accumulate_grad_batches=args.gradient_accumulation_steps,
                    check_val_every_n_epoch=args.check_val_every_n_epoch,
                    default_root_dir=args.output_dir,
                    gradient_clip_val=1.0,
                    log_every_n_steps=args.log_step,
                    precision="bf16-mixed",
    )
    trainer.test(model, dataloaders=test_loader)

CONFIG = {
    "SciBert": [
        BertConfig,
        BertTokenizer,
        SciBertTokenizer,
        BertForSequenceClassification
    ],
    "MolT5": [
        T5Config,
        T5Tokenizer,
        T5CLSTokenizer,
        T5ForQuestionAnswering
    ]
}

def train_classifier(args):
    model_name = args.model_name
    ConfigModule, TokenizerModule, CLSTokenizer, ModelMudule = CONFIG[model_name]

    global local_rank
    
    local_rank = args.local_rank
    print(f"LOCAL RANK: {local_rank}")
    seed_everything(42)
    logger = TensorBoardLogger(save_dir=args.output_dir, name=f"logs")
    version = logger.version
    checkpoint_callback = ModelCheckpoint(save_top_k=3, dirpath=os.path.join(args.output_dir, f"logs/version_{version}/ckpt"), monitor="val_acc", mode="max", filename="{epoch}-{step}-{val_acc:.6f}")
    # tokenizer = TokenizerModule.from_pretrained('allenai/scibert_scivocab_uncased')
    tokenizer = TokenizerModule.from_pretrained(args.model_path)
    tokenizer = CLSTokenizer(tokenizer = tokenizer, max_length = args.max_length)
    config = ConfigModule.from_pretrained(args.model_path)
    # if model_name == "SciBert":
    config.__setattr__("num_labels", 4)
    model = ModelMudule(config)
    # Initialize Model Parameter
    if model_name == "SciBert":
        model.bert = BertModel.from_pretrained(args.model_path)
    elif model_name == "MolT5":
        state_dict = torch.load(os.path.join(args.model_path, "pytorch_model.bin"))
        model.load_state_dict(state_dict, strict=False)
    # device = torch.device("cuda:5")
    sentences = []
    for cls in CLASSES2TYPE:
        cls_type = CLASSES2TYPE[cls]
        target_dir = os.path.join(TARGET_DIR, cls) 
        sens = desc2sentence(sen_path = os.path.join(target_dir, "sentences.json"))
        # cls_sens = {}
        dup_set = set()
        if cls in DEDUPLICATE_DICT:
            for dup_path in DEDUPLICATE_DICT[cls]:
                with open(dup_path) as dup_file:
                    dup_js = json.load(dup_file)
                for key in dup_js:
                    dup_set.add(key)
            for key in sens:
                if key not in dup_set:
                    sens[key].append(cls_type)
                    sentences.append(sens[key])
        if os.path.exists(os.path.join(target_dir, "sentence_0.9.json")):
            sens_0_9 = desc2sentence(sen_path = os.path.join(target_dir, "sentence_0.9.json"))
            print(f"Add New Data: {cls}, {cls_type}, {len(sens_0_9)}")
            for key in sens_0_9:
                sens_0_9[key].append(cls_type)
                sentences.append(sens_0_9[key])
    random.shuffle(sentences) 
    collator = GeneralCollator(tokenizer=tokenizer, pop=True)
    data_num = len(sentences)
    rank0_print(f"{data_num} sentences for training")
    train_num = math.ceil(data_num * 0.9)
    
    train_dataset = CLSDataset(sentences[:train_num], collator, True)
    dev_dataset = CLSDataset(sentences[train_num:], collator, True)
    # train_dataset = CLSDataset(sentences[:1000], collator, True)
    # dev_dataset = CLSDataset(sentences[-1000:], collator, False)
    # model.to(device)
    train_loader = DataLoader(train_dataset, batch_size = args.batch_size, shuffle=True, collate_fn = train_dataset.collate_fn, num_workers = 16)
    dev_loader = DataLoader(dev_dataset, batch_size = args.batch_size, shuffle=False, collate_fn = dev_dataset.collate_fn, num_workers = 16)

    model = CLSWrapper(model, config, args.learning_rate, local_rank)
    trainer = Trainer(accelerator="gpu",
                    logger=logger,
                    max_epochs=args.num_train_epochs,
                    devices=args.devices,
                    accumulate_grad_batches=args.gradient_accumulation_steps,
                    check_val_every_n_epoch=args.check_val_every_n_epoch,
                    default_root_dir=args.output_dir,
                    gradient_clip_val=1.0,
                    log_every_n_steps=args.log_step,
                    strategy='ddp_find_unused_parameters_true',
                    precision="bf16-mixed",
                    callbacks=[checkpoint_callback]
    )
    trainer.fit(model, train_dataloaders=train_loader, val_dataloaders=dev_loader, ckpt_path=args.ckpt)

def visualize(emb_path, sen_path):
    embeddings = np.load(emb_path)
    sentences = desc2sentence(sen_path)
    sentences = list(sentences.values())
    for index, sen in enumerate(sentences):
        if len(sen[3]) < 50:
            label = 0
        else:
            label = 1
        sentences[index] = {
            "text": sen[3],
            "label": label
        }
    atlas.map_embeddings(embeddings=embeddings,
                                data=sentences,
                                colorable_fields=['label'],
                                name="PubChem sentence visualize",
                                description="Visualization of 500000 desc sentences from PubChem.",
                                reset_project_if_exists=True)

    # print(response)

# if __name__ == "__main__":
#     text_emb()
    
#     target_dir = os.path.join(TARGET_DIR, "UNCLS") 
#     visualize(os.path.join(target_dir, "mol_desc_emb_cls_ana.npy"), sen_path = os.path.join(target_dir, "sentences.json"))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--model_name', type=str, default="MolT5")
    parser.add_argument('--model_path', type=str, default="./MolT5-base-caption2smiles")
    # Used for inference
    
    parser.add_argument('--pretrained_ckpt', type=str, default="allenai/scibert_scivocab_uncased")
    parser.add_argument('--test_threshold', type=float, default=0)
    parser.add_argument('--cls_file', type=str, default="sentences_rm_ref.json")
    # parser.add_argument('--train_file', type=str, required=True)
    # parser.add_argument('--data_path', type=str, required=True)
    # parser.add_argument('--dev_file', type=str, required=True)
    parser.add_argument("--max_length", type=int, default=512)
    parser.add_argument('--output_dir', type=str, required=True, default="./CLS_logs")
    parser.add_argument('--num_train_epochs', type=int, default=3)
    parser.add_argument('--gradient_accumulation_steps', type=int, default=8)
    parser.add_argument('--dataloader_num_workers', type=int, default=2)
    parser.add_argument('--batch_size', type=int, default=2)
    parser.add_argument('--learning_rate', type=float, default=5e-5)
    parser.add_argument('--check_val_every_n_epoch', type=int, default=1)
    parser.add_argument('--log_step', type=int, default=5000)
    parser.add_argument('--devices', default=[0], type=int, nargs="+")
    parser.add_argument('--ckpt', type=str, default=None)
    parser.add_argument("--local_rank", type=int, default=0)

    args = parser.parse_args()
    args.output_dir = os.path.join(args.output_dir, args.model_name)
    if not os.path.exists(args.output_dir):
        os.makedirs(args.output_dir, exist_ok=True)
    use_classifier(args)
    # train_classifier(args)

# if __name__ == "__main__":
#     # text_emb()
#     target_dir = os.path.join(TARGET_DIR, "UNCLS") 
#     visualize(os.path.join(target_dir, "mol_desc_emb_cls_ana_trained.npy"), sen_path = os.path.join(target_dir, "sentences.json"))
