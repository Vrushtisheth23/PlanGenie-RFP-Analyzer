# retriever_hf_api.py
from huggingface_hub import InferenceClient
import numpy as np
import os
from dotenv import load_dotenv

load_dotenv()

HF_TOKEN = os.getenv("Huggingface_API")
if not HF_TOKEN:
    raise ValueError("Huggingface_API token not found in .env")

class RFP_Retriever:
    def __init__(self, model_name="sentence-transformers/all-MiniLM-L6-v2"):
        self.client = InferenceClient(token=HF_TOKEN)
        self.model_name = model_name
        self.index = None
        self.text_chunks = []

    def chunk_text(self, text, chunk_size=500):
        words = text.split()
        chunks = [" ".join(words[i:i+chunk_size]) for i in range(0, len(words), chunk_size)]
        self.text_chunks = chunks
        return chunks

    def embed(self, texts):
        """Get embeddings from HF API (fully remote)"""
        embeddings = []
        for txt in texts:
            response = self.client.feature_extraction(txt, model=self.model_name)
            embeddings.append(response)
        return np.array(embeddings).astype("float32")

    def build_index(self, chunks):
        embeddings = self.embed(chunks)
        import faiss
        self.index = faiss.IndexFlatL2(embeddings.shape[1])
        self.index.add(embeddings)

    def query(self, query_text, top_k=3):
        query_embedding = self.embed([query_text])
        D, I = self.index.search(query_embedding, top_k)
        return [self.text_chunks[i] for i in I[0]]
