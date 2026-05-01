import requests
from bs4 import BeautifulSoup
import json
import os
import time
from typing import List, Dict, Set
from urllib.parse import urljoin, urlparse

class SupportScraper:
    def __init__(self, max_pages: int = 150):
        self.max_pages = max_pages
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        self.domains = {
            "hackerrank": "https://support.hackerrank.com/",
            "claude": "https://support.claude.com/en/",
            "visa": "https://www.visa.co.in/support.html"
        }
        self.corpus_path = os.path.join(os.path.dirname(__file__), "..", "data", "corpus", "corpus.json")

    def is_internal(self, url: str, base_url: str) -> bool:
        """Check if the URL belongs to the same domain as the base URL."""
        return urlparse(url).netloc == urlparse(base_url).netloc

    def scrape_site(self, source_name: str, start_url: str) -> List[Dict[str, str]]:
        """Scrape a single support site up to max_pages."""
        visited: Set[str] = set()
        to_visit: List[str] = [start_url]
        results: List[Dict[str, str]] = []
        
        print(f"[*] Starting scrape for {source_name}: {start_url}")
        
        while to_visit and len(visited) < self.max_pages:
            url = to_visit.pop(0)
            if url in visited:
                continue
            
            try:
                response = requests.get(url, headers=self.headers, timeout=10)
                if response.status_code != 200:
                    continue
                
                visited.add(url)
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Extract text
                # Remove script and style elements
                for script in soup(["script", "style"]):
                    script.decompose()
                
                text = soup.get_text(separator=' ', strip=True)
                truncated_text = text[:3000]
                
                results.append({
                    "url": url,
                    "source": source_name,
                    "text": truncated_text
                })
                
                print(f"    [{len(visited)}/{self.max_pages}] Scraped: {url}")
                
                # Find internal links
                for link in soup.find_all('a', href=True):
                    full_url = urljoin(url, link['href'])
                    # Basic normalization
                    full_url = full_url.split('#')[0].rstrip('/')
                    
                    if self.is_internal(full_url, start_url) and full_url not in visited:
                        to_visit.append(full_url)
                
                # Small delay to be polite
                time.sleep(0.1)
                
            except Exception as e:
                print(f"    [!] Error scraping {url}: {e}")
                continue
                
        return results

    def build_corpus(self):
        """Scrape all domains and save to corpus.json."""
        all_docs = []
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(self.corpus_path), exist_ok=True)
        
        for source, url in self.domains.items():
            docs = self.scrape_site(source, url)
            all_docs.extend(docs)
            
        with open(self.corpus_path, 'w', encoding='utf-8') as f:
            json.dump(all_docs, f, indent=2, ensure_ascii=False)
            
        print(f"\n[+] Scrape complete. Total documents: {len(all_docs)}")
        print(f"[+] Saved to {self.corpus_path}")

if __name__ == "__main__":
    scraper = SupportScraper(max_pages=5) # Default to small for testing
    scraper.build_corpus()
