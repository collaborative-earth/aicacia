for algo in pgvector qdrant weaviate milvus-hnsw; 
do python3 run.py --local --definitions ./ann_benchmarks/algorithms --algorithm $algo --dataset nytimes-256-angular; 
done