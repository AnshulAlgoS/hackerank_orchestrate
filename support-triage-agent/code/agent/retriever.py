import chromadb
from chromadb.utils import embedding_functions
import json
import os
from typing import List, Dict, Optional, Tuple

class SupportRetriever:
    def __init__(self):
        # Paths are now relative to the code/ directory, matching the hackathon repo structure
        self.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.db_path = os.path.join(self.base_dir, "data", "chroma")
        self.data_dir = os.path.join(self.base_dir, "data")
        self.collection_name = "support_corpus"
        
        # Initialize embedding function
        self.embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="all-MiniLM-L6-v2"
        )
        
        # Initialize Chroma client
        self.client = chromadb.PersistentClient(path=self.db_path)
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            embedding_function=self.embedding_function
        )

    def index_corpus(self):
        """Read local files from data/ folders and index them in ChromaDB."""
        if self.collection.count() > 0:
            print(f"[*] Collection '{self.collection_name}' already contains {self.collection.count()} documents. Skipping indexing.")
            return

        print(f"[*] Indexing documents from {self.data_dir}...")
        
        documents = []
        metadatas = []
        ids = []
        
        # Domains matching the folder names in the hackathon repo
        domains = ["hackerrank", "claude", "visa"]
        
        for domain in domains:
            domain_path = os.path.join(self.data_dir, domain)
            if not os.path.exists(domain_path):
                print(f"    [!] Folder not found: {domain_path}")
                continue
                
            print(f"    [*] Processing {domain}...")
            # Walk through all files in the domain directory
            for root, _, files in os.walk(domain_path):
                for file in files:
                    if file.endswith(('.txt', '.md', '.html', '.json')):
                        file_path = os.path.join(root, file)
                        try:
                            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                                content = f.read()
                                if not content.strip():
                                    continue
                                    
                                # For large files, we might want to chunk, but for now we follow the 3000 char rule
                                # or just take the whole file if it's a support article
                                documents.append(content[:5000]) # Slightly larger limit for local files
                                metadatas.append({
                                    "source": domain,
                                    "file": file,
                                    "path": os.path.relpath(file_path, self.data_dir)
                                })
                                ids.append(f"{domain}_{len(ids)}")
                        except Exception as e:
                            print(f"    [!] Error reading {file_path}: {e}")

        if not documents:
            print("[!] No documents found to index.")
            return

        # Batch add to Chroma
        batch_size = 100
        for i in range(0, len(documents), batch_size):
            self.collection.add(
                documents=documents[i:i+batch_size],
                metadatas=metadatas[i:i+batch_size],
                ids=ids[i:i+batch_size]
            )
            print(f"    [+] Indexed {min(i + batch_size, len(documents))}/{len(documents)} documents")

        print(f"[+] Indexing complete. Total documents: {self.collection.count()}")

    def retrieve(self, query: str, source_filter: Optional[str] = None, top_k: int = 5) -> Tuple[List[str], List[Dict]]:
        """Retrieve relevant documents, optionally filtered by product_area."""
        where_clause = None
        if source_filter:
            where_clause = {"source": source_filter}

        results = self.collection.query(
            query_texts=[query],
            n_results=top_k,
            where=where_clause
        )

        # Chroma results structure: {'documents': [[...]], 'metadatas': [[...]], ...}
        docs = results['documents'][0] if results['documents'] else []
        metas = results['metadatas'][0] if results['metadatas'] else []
        
        return docs, metas

if __name__ == "__main__":
    retriever = SupportRetriever()
    # retriever.index_corpus() # Uncomment to test
    # results = retriever.retrieve("How do I report a lost card?", source_filter="visa")
    # print(results)
