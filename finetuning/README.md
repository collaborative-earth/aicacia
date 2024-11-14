# Finetuning

This repository contains two main scripts for creating, evaluating Question-Answer (QA) datasets based on TEI (Text Encoding Initiative) documents.
These scripts facilitate the ingestion, processing, and generation of QA pairs and evaluate the performance of different embedding models on the generated dataset. 
The main scripts are:

1. `generate_dataset.py`: Processes TEI documents, generates QA pairs, and saves them to a specified dataset.
    The dataset can be generated through an llm or a pre-trained transformers
2. `evaluate_embedding.py`: Evaluates various embedding models on the generated QA dataset to assess their effectiveness in information retrieval.

## QA dataset generator

This tool generates a question-answer (QA) dataset from TEI files using phi-3 and a local instance
of Ollama LLM for question generation.

### How to Use

1. **Configure Settings**: Update `config.json` to adjust parameters such as file paths, chunk size, and the number of questions to generate.
2. **Generate dataset**: Run generate_dataset.py to generate a qa dataset based on document chunks.
3. **Evaluate dataset** : Evaluate a series of models on the generated dataset using IR metrics.

