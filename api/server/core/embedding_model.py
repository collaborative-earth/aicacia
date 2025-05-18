from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from server.core.config import settings

model = HuggingFaceEmbedding(model_name=settings.EMBEDDING_MODEL_NAME)
