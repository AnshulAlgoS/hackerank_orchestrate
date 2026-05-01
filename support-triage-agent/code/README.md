# HackerRank Orchestrate: Support Triage Agent v2.0

An advanced, terminal-based AI support agent built for the HackerRank Orchestrate Challenge (May 2026). This agent triages support tickets across the HackerRank, Claude, and Visa ecosystems using a strictly grounded RAG system.

## 🚀 Core Features

### 1. Hybrid Domain Detection
Combines **Deterministic Rules** (keyword matching) for speed and reliability with **LLM Nuance** for handling typos, vague queries, and edge cases.

### 2. Risk Analysis & Scoring Engine
Analyzes every ticket for:
- **Financial Risk**: Detects payments, unauthorized transactions, or fraud.
- **Urgency**: Identifies time-sensitive requests.
- **Emotional Tone**: Gauges user stress and frustration.
Scores tickets as **LOW**, **MEDIUM**, or **CRITICAL** to prioritize manual intervention.

### 3. Decision Reason Engine (Justification)
Every action taken by the agent includes a clear "paper trail" of logic (e.g., "Keyword match for Visa," "Risk: Financial transaction detected"). This is exposed in the `justification` column of the output.

### 4. Strictly Grounded RAG
Uses a local **ChromaDB** vector store and `sentence-transformers` to retrieve documentation from the provided local corpus. The system prompt is engineered to prevent hallucinations and ensure responses are strictly derived from the provided data.

### 5. Professional Terminal UI
Built with `Rich`, featuring:
- Color-coded risk visualization.
- Structured metadata tables.
- Detailed reasoning panels.
- Suppressed warnings for a clean experience.

## 📋 Compliance & Requirements
- ✅ **Terminal-based**: Fully interactive CLI.
- ✅ **Local Corpus Only**: No live web calls for ground-truth answers.
- ✅ **Transcript Logging**: Automatically logs to `$HOME/hackerrank_orchestrate/log.txt` (as per AGENTS.md).
- ✅ **Strict Output Schema**: Matches the 8-column format required for submission.

## 🛠 Setup Instructions

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Set Environment Variables**:
   Create a `.env` file in the `code/` directory:
   ```env
   LLM_API_KEY='your-api-key-here'
   LLM_API_BASE='https://api.openai.com/v1' # Or your provider's base URL
   LLM_MODEL='qwen/qwen3-coder-480b-a35b-instruct'
   ```

3. **Initialize the Agent**:
   Run the setup script to index the **provided local corpus** from the `../data/` directory:
   ```bash
   python setup.py
   ```

## ⌨️ Usage

### Interactive Terminal Mode
Chat with the agent in real-time to test edge cases or demonstrate to judges:
```bash
python main.py
```

### Batch Processing Mode
Process the official challenge CSV and generate predictions:
1. Ensure the input file is at `../support_tickets/support_tickets.csv`.
2. Run:
   ```bash
   python batch.py
   ```
3. Results will be saved to `../support_tickets/output.csv`.

## 📊 Output Schema (output.csv)
The agent produces a CSV with the following columns:
1. `issue`: Original ticket text.
2. `subject`: Ticket subject.
3. `company`: User's organization.
4. `response`: Grounded, professional answer.
5. `product_area`: hackerrank, claude, or visa.
6. `status`: replied or escalated.
7. `request_type`: product_issue, feature_request, bug, or invalid.
8. `justification`: Detailed reasoning for the agent's decision.

## 📂 Project Structure
```text
support-triage-agent/
├── code/               # Agent source code, setup, and interactive scripts
├── data/               # Local support corpus (Judges' documentation)
└── support_tickets/    # Input (support_tickets.csv) & Output (output.csv)
```
