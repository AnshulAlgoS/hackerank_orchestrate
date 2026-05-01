import sys
import os

# Add the current directory to sys.path so we can import agent modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from agent.scraper import SupportScraper
from agent.retriever import SupportRetriever

def main():
    print("=== HackerRank Orchestrate: Support Triage Agent Setup ===")
    
    # 1. Index documents in ChromaDB from local data/ folders
    print("\n[Step 1/1] Indexing local support documentation in ChromaDB...")
    retriever = SupportRetriever()
    retriever.index_corpus()
    
    print("\n" + "="*47)
    print("Setup complete. Run 'python main.py' to start interactive mode.")
    print("Or 'python batch.py' to process support_tickets/support_tickets.csv.")
    print("="*47)

if __name__ == "__main__":
    main()
