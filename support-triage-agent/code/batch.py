import pandas as pd
import os
import sys
from datetime import datetime
from agent.triage import SupportTriageAgent

# Configure logging path based on Hackathon requirements (AGENTS.md)
HOME_DIR = os.path.expanduser("~")
LOG_DIR = os.path.join(HOME_DIR, "hackerrank_orchestrate")
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOG_DIR, "log.txt")

# Standard paths for the HackerRank Orchestrate Challenge
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INPUT_FILE = os.path.join(BASE_DIR, "support_tickets", "support_tickets.csv")
OUTPUT_FILE = os.path.join(BASE_DIR, "support_tickets", "output.csv")

def log_interaction(ticket: str, result: dict):
    """Log the interaction to log.txt with detailed diagnostic data."""
    timestamp = datetime.now().isoformat(timespec='seconds')
    log_entry = (
        f"[{timestamp}] BATCH INPUT: {ticket}\n"
        f"[{timestamp}] CLASSIFICATION: {result['product_area'].upper()}\n"
        f"[{timestamp}] RISK SCORE: {result['risk_score']} ({result['risk_level']})\n"
        f"[{timestamp}] DECISION LOGIC: {', '.join(result['decision_logic'])}\n"
        f"[{timestamp}] FINAL DECISION: {result['status']}\n"
        f"[{timestamp}] RETRIEVAL DOCS: {', '.join(result['sources'])}\n"
        f"[{timestamp}] RESPONSE: {result['response'][:100]}...\n"
        f"{'─' * 40}\n"
    )
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(log_entry)

def find_column(df: pd.DataFrame, candidates: list, default_index: int) -> str:
    """Find the first matching column name from candidates, or return column at default_index."""
    for cand in candidates:
        if cand in df.columns:
            return cand
    return df.columns[default_index]

def main():
    if not os.path.exists(INPUT_FILE):
        print(f"[!] Error: Input file not found at {INPUT_FILE}")
        sys.exit(1)

    print(f"[*] Reading {INPUT_FILE}...")
    try:
        df = pd.read_csv(INPUT_FILE)
    except Exception as e:
        print(f"[!] Error reading CSV: {e}")
        sys.exit(1)

    if df.empty:
        print("[!] CSV is empty. Nothing to process.")
        return

    # Auto-detect columns
    text_col = find_column(df, ["issue", "ticket", "description", "text", "query"], 0)
    subject_col = find_column(df, ["subject", "title"], 1 if len(df.columns) > 1 else -1)
    company_col = find_column(df, ["company", "org", "organization"], 2 if len(df.columns) > 2 else -1)
    id_col = find_column(df, ["ticket_id", "id"], -1)

    print(f"[*] Detected text column: '{text_col}'")
    
    agent = SupportTriageAgent()
    results = []

    total = len(df)
    for index, row in df.iterrows():
        ticket_text = str(row[text_col])
        ticket_subject = str(row[subject_col]) if subject_col in df.columns else ""
        ticket_company = str(row[company_col]) if company_col in df.columns else ""
        ticket_id = str(row[id_col]) if id_col in df.columns else str(index)
        
        print(f"[*] Processing ticket {index + 1}/{total} (ID: {ticket_id})...")
        
        try:
            # Combine subject and text for better context if subject exists
            full_query = f"Subject: {ticket_subject}\nIssue: {ticket_text}" if ticket_subject else ticket_text
            result = agent.triage(full_query, ticket_id=ticket_id)
            
            # Match the final requested output schema
            result_for_csv = {
                "issue": ticket_text,
                "subject": ticket_subject,
                "company": ticket_company,
                "response": result["response"],
                "product_area": result["product_area"],
                "status": result["status"],
                "request_type": result["request_type"],
                "justification": result["justification"]
            }
            results.append(result_for_csv)
            
            # Log to diagnostic log.txt
            log_interaction(ticket_text, result)
        except Exception as e:
            print(f"    [!] Error processing ticket {ticket_id}: {e}")
            results.append({
                "issue": ticket_text,
                "subject": ticket_subject,
                "company": ticket_company,
                "response": f"Error: {str(e)}",
                "product_area": "unknown",
                "status": "error",
                "request_type": "product_issue",
                "justification": f"Internal Error: {str(e)}"
            })

    # Save to output.csv with exact column order
    output_df = pd.DataFrame(results)
    # Ensure column order
    cols = ["issue", "subject", "company", "response", "product_area", "status", "request_type", "justification"]
    output_df = output_df[cols]
    
    output_df.to_csv(OUTPUT_FILE, index=False)
    print(f"\n[+] Batch processing complete. Results saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
