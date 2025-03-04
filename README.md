# MoleculeQA
_The largest existing Question Answering Dataset for molecular research._

[![Code License](https://img.shields.io/badge/Code%20License-Apache_2.0-green.svg)](LICENSE)
[![arXiv](https://img.shields.io/badge/arXiv-2403.08192-b31b1b.svg)](https://arxiv.org/abs/2403.08192)

## Intro
Large language models are playing an increasingly significant role in molecular research, yet existing models often generate erroneous information, posing challenges to accurate molecular comprehension. Traditional evaluation metrics for generated content fail to assess a model’s accuracy in molecular understanding. To rectify the absence of factual evaluation, we present MoleculeQA, a novel question answering (QA) dataset which possesses 62K QA pairs over 23K molecules. Each QA pair, composed of a manual question, a positive option and three negative options, has consistent semantics with a molecular description from authoritative molecular corpus. MoleculeQA is not only the first benchmark for molecular factual bias evaluation but also the largest QA dataset for molecular research. A comprehensive evaluation on MoleculeQA for existing molecular LLMs exposes their deficiencies in specific areas and pinpoints several particularly crucial factors for molecular understanding.
