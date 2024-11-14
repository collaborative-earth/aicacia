import os
import logging
import nltk
import numpy as np
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from rank_bm25 import BM25Okapi
from sklearn.feature_extraction.text import CountVectorizer
nltk.download('punkt')
nltk.download('stopwords')


logger = logging.getLogger(__name__)


class InformationRetrievalEvaluatorBM25:
    """
    A class for evaluating information retrieval systems using the BM25 algorithm.
    The class preprocess both the corpus and the query by removing stopwords and lowercasing tokens, 
    and then perform information retrieval. Inspired by the InformationRetrievalEvaluator of SentenceTransformer.

    Attributes:
        queries (dict[str, str]): A dictionary mapping query IDs to query text.
        corpus (dict[str, str]): A dictionary mapping document IDs to document text.
        relevant_docs (dict[str, set[str]]): A dictionary mapping query IDs to sets of relevant document IDs.
        mrr_at_k (list[int]): List of k values for Mean Reciprocal Rank evaluation.
        ndcg_at_k (list[int]): List of k values for Normalized Discounted Cumulative Gain evaluation.
        accuracy_at_k (list[int]): List of k values for accuracy evaluation.
        precision_recall_at_k (list[int]): List of k values for precision and recall evaluation.
        show_progress_bar (bool): Flag to display progress during evaluation.
        batch_size (int): Size of batches for processing.
        name (str): Name identifier for the evaluator.
        write_csv (bool): Flag to write results to a CSV file.
    """
    
    def __init__(
        self,
        queries: dict[str, str],  # qid => query
        corpus: dict[str, str],  # cid => doc
        relevant_docs: dict[str, set[str]],  # qid => Set[cid]
        mrr_at_k: list[int] = [10],
        ndcg_at_k: list[int] = [10],
        accuracy_at_k: list[int] = [1, 3, 5, 10],
        precision_recall_at_k: list[int] = [1, 3, 5, 10],
        show_progress_bar: bool = False,
        batch_size: int = 32,
        name: str = "",
        write_csv: bool = True,
    ) -> None:
        self.queries = queries
        self.corpus = corpus
        self.relevant_docs = relevant_docs

        # BM25 retriever initialization
        self.stop_words = set(stopwords.words('english'))
        corpus_documents = [self.preprocess(doc.split()) for doc in self.corpus.values()]
        self.bm25 = BM25Okapi(corpus_documents)

        # Evaluation parameters
        self.mrr_at_k = mrr_at_k
        self.ndcg_at_k = ndcg_at_k
        self.accuracy_at_k = accuracy_at_k
        self.precision_recall_at_k = precision_recall_at_k

        self.show_progress_bar = show_progress_bar
        self.name = name
        self.write_csv = write_csv
        # Score function names for CSV headers
        self.csv_file: str = "Information-Retrieval_evaluation_bm25_results.csv"

       
        self.csv_headers = ["epoch", "steps"]
        for k in self.accuracy_at_k:
            self.csv_headers.append(f"BM25-Accuracy@{k}")
        for k in self.precision_recall_at_k:
            self.csv_headers.append(f"BM25-Precision@{k}")
            self.csv_headers.append(f"BM25-Recall@{k}")
        for k in mrr_at_k:
            self.csv_headers.append(f"BM25-MRR@{k}")
        for k in ndcg_at_k:
            self.csv_headers.append(f"BM25-NDCG@{k}")

    def __call__(self, model: None = None, output_path: str = None, epoch: int = -1, steps: int = -1, *args, **kwargs) -> dict[str, float]:
        """Evaluate the model and write results to a CSV if required"""
        # Handling output information based on epoch and steps
        if epoch != -1:
            if steps == -1:
                out_txt = f" after epoch {epoch}"
            else:
                out_txt = f" in epoch {epoch} after {steps} steps"
        else:
            out_txt = ""


        logger.info(f"Information Retrieval Evaluation of the model on the {self.name} dataset{out_txt}:")

        # Evaluate the system
        scores = self.compute_metrics()
        

        # Write results to disk
        if output_path is not None and self.write_csv:
            csv_path = os.path.join(output_path, self.csv_file)
            if not os.path.isfile(csv_path):
                fOut = open(csv_path, mode="w", encoding="utf-8")
                fOut.write(",".join(self.csv_headers))
                fOut.write("\n")
            else:
                fOut = open(csv_path, mode="a", encoding="utf-8")

            output_data = [epoch, steps]
     
            for k in self.accuracy_at_k:
                output_data.append(scores["accuracy@k"][k])

            for k in self.precision_recall_at_k:
                output_data.append(scores["precision@k"][k])
                output_data.append(scores["recall@k"][k])

            for k in self.mrr_at_k:
                output_data.append(scores["mrr@k"][k])

            for k in self.ndcg_at_k:
                output_data.append(scores["ndcg@k"][k])

            fOut.write(",".join(map(str, output_data)))
            fOut.write("\n")
            fOut.close()

        metrics = {
            f"{metric_name.replace('@k', '@' + str(k))}": value
            for metric_name, values in scores.items()
            for k, value in values.items()
        }

        metrics = self.prefix_name_to_metrics(metrics, self.name)

        
        return metrics

    def preprocess(self,text):
        tokens = [word.lower() for word in text if word.isalnum() and word not in self.stop_words]
        return tokens


    def compute_metrics(self):
        """Evaluate the retrieval system using BM25 and compute metrics"""
        # Init score computation values
        num_hits_at_k = {k: 0 for k in self.accuracy_at_k}
        precisions_at_k = {k: [] for k in self.precision_recall_at_k}
        recall_at_k = {k: [] for k in self.precision_recall_at_k}
        MRR = {k: 0 for k in self.mrr_at_k}
        ndcg = {k: [] for k in self.ndcg_at_k}
        all_accuracies,all_precisions, all_recalls, all_mrrs, all_ndcgs = [[] for _ in range(5)]

        max_k = max(
            max(self.mrr_at_k),
            max(self.ndcg_at_k),
            max(self.accuracy_at_k),
            max(self.precision_recall_at_k)
        )

        for qid, query in self.queries.items():
            # Tokenize the query
            query_tokens = self.preprocess(query.split())

            # Compute BM25 scores
            scores = self.bm25.get_scores(query_tokens)


            # Get top-k highest scoring documents
            top_k_indices = np.argsort(scores)[::-1][:max_k]
            top_k_docs = [list(self.corpus.keys())[idx] for idx in top_k_indices]

            # Get relevant documents for the current query
            query_relevant_docs = self.relevant_docs.get(qid, set())

            #Accuracy
            for k_val in self.accuracy_at_k:
              for doc in top_k_docs[0:k_val]:
                  if doc in query_relevant_docs:
                    num_hits_at_k[k_val] += 1
                    break
            # Precision and Recall@k
            for k_val in self.precision_recall_at_k:
                num_correct = 0
                for doc in top_k_docs[0:k_val]:
                    if doc in query_relevant_docs:
                        num_correct += 1

                precisions_at_k[k_val].append(num_correct / k_val)
                recall_at_k[k_val].append(num_correct / len(query_relevant_docs))

            # MRR@k
            for k_val in self.mrr_at_k:
                for rank, hit in enumerate(top_k_docs[0:k_val]):
                    if doc in query_relevant_docs:
                        MRR[k_val] += 1.0 / (rank + 1)
                        break
            # NDCG@k
            for k_val in self.ndcg_at_k:
                predicted_relevance = [
                    1 if doc in query_relevant_docs else 0 for doc in top_k_docs[0:k_val]
                ]
                true_relevances = [1] * len(query_relevant_docs)

                ndcg_value = self.compute_dcg_at_k(predicted_relevance, k_val) / self.compute_dcg_at_k(
                    true_relevances, k_val
                )
                ndcg[k_val].append(ndcg_value)



        # Compute averages
        for k in num_hits_at_k:
            num_hits_at_k[k] /= len(self.queries)

        for k in precisions_at_k:
            precisions_at_k[k] = np.mean(precisions_at_k[k])

        for k in recall_at_k:
            recall_at_k[k] = np.mean(recall_at_k[k])

        for k in ndcg:
            ndcg[k] = np.mean(ndcg[k])

        for k in MRR:
            MRR[k] /= len(self.queries)


        return {
            "accuracy@k": num_hits_at_k,
            "precision@k": precisions_at_k,
            "recall@k": recall_at_k,
            "ndcg@k": ndcg,
            "mrr@k": MRR
        }

    def prefix_name_to_metrics(self, metrics: dict[str, float], name: str) -> dict[str, float]:
        if not name:
            return metrics
        metrics = {name + "_" + key: value for key, value in metrics.items()}
        if hasattr(self, "primary_metric") and not self.primary_metric.startswith(name + "_"):
            self.primary_metric = name + "_" + self.primary_metric
        return metrics
      
    @staticmethod
    def compute_dcg_at_k(relevances, k):
        dcg = 0
        for i in range(min(len(relevances), k)):
            dcg += relevances[i] / np.log2(i + 2)  # +2 as we start our idx at 0
        return dcg