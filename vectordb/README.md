# Qdrant Vector Store

## Overview

This project utilizes Qdrant as a vector database to store and manage embedding vectors for documents. Follow the steps below to set up your environment, start the Qdrant server, and load your embedding vectors.

## Setup Instructions

### Step 1: Copy Data

Copy all the data you want to embed into the `../data/` directory. Ensure that the files are in the correct format for embedding.

```bash
cp /path/to/your/data/* ../data/
```

### Step 2: Start the Qdrant Server

Navigate to your project root directory directory. Use Docker Compose to start the Qdrant server.

```bash
docker-compose up -d
```

### Step 3: Access the Qdrant Dashboard

Once the server is running, you can access the Qdrant dashboard by visiting: `http://localhost:6333/dashboard#/collections`

### Step 4: Update Config

We can modify multiple different configs such as the text splitter function to use, embedding model to use, etc in the `config.yml` file in the vectordb directory. A lot of these classes are defined using their class names directly allowing lesser modification of code.


### Step 5: Load Embedding Vectors

Go to the vectordb directory and run the main.py script using the following command to start loading the embedding vectors for the documents in the data directory into the vector store.

```bash
python3 main.py -c <collection_name> -d <data_directory>
```

### Step 6: Upload the vectors

The vectors will be saved in `vectordb/qdrant_storage`. We can also resuse vectors by downloading them into this location.

### Arguments for main.py

The main.py script takes in two arguments:

 - Collection Name: Specify the name of the collection where you want to store the embeddings.
 - Data Directory: Specify the location of the folder with the dataset.

```bash
-c, --collection <collection_name>
-d, -input-dir <data_directory>
```

#### Example Command
Here’s an example command that uses a custom collection name and specifies an embedding model:

```bash
python3 main.py -c aicacia -d ../data/
```
