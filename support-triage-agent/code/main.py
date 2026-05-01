import os
import sys

# Suppress HuggingFace tokenizers parallelism warning
os.environ["TOKENIZERS_PARALLELISM"] = "false"

from datetime import datetime
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.theme import Theme
from rich.table import Table
from rich.columns import Columns
from agent.triage import SupportTriageAgent

# Custom theme for Rich
custom_theme = Theme({
    "info": "cyan",
    "warning": "bold yellow",
    "error": "bold red",
    "success": "bold green",
    "header": "bold magenta",
    "risk_low": "green",
    "risk_medium": "yellow",
    "risk_critical": "bold red"
})

# Configure logging path based on Hackathon requirements (AGENTS.md)
HOME_DIR = os.path.expanduser("~")
LOG_DIR = os.path.join(HOME_DIR, "hackerrank_orchestrate")
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOG_DIR, "log.txt")

# Re-init console after path setup
console = Console(theme=custom_theme)

def log_interaction(ticket: str, result: dict):
    """Log the interaction to log.txt with detailed diagnostic data."""
    timestamp = datetime.now().isoformat(timespec='seconds')
    
    # Create a structured log entry
    log_entry = (
        f"[{timestamp}] INPUT: {ticket}\n"
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

def main():
    agent = SupportTriageAgent()
    
    console.print(Panel.fit(
        "[header]Multi-Domain Support Triage Agent v2.0[/header]\n"
        "Enhanced with Hybrid Classification & Risk Scoring",
        border_style="magenta"
    ))
    
    console.print("[info]Instructions:[/info] Type your ticket text and press Enter. Type [bold]'exit'[/bold] to quit.\n")

    try:
        while True:
            ticket = Prompt.ask("[bold cyan]Ticket[/bold cyan]")
            
            if ticket.lower() in ["exit", "quit"]:
                console.print("[info]Goodbye![/info]")
                break
            
            if not ticket.strip():
                continue

            with console.status("[bold yellow]Triaging ticket...[/bold yellow]"):
                result = agent.triage(ticket)
            
            # --- Result UI ---
            console.print("\n" + "━" * 60)
            
            # Metadata Table
            table = Table(show_header=False, box=None)
            table.add_column("Key", style="bold grey70")
            table.add_column("Value")
            
            table.add_row("Domain:", f"[bold]{result['product_area'].capitalize()}[/bold]")
            
            action_style = "success" if result['status'] == "replied" else "error"
            table.add_row("Status:", f"[{action_style}]{result['status'].upper()}[/{action_style}]")
            
            table.add_row("Req Type:", f"[yellow]{result['request_type']}[/yellow]")
            
            risk_style = f"risk_{result['risk_level'].lower()}"
            table.add_row("Risk Level:", f"[{risk_style}]{result['risk_level']} (Score: {result['risk_score']})[/{risk_style}]")
            
            console.print(table)
            
            # Decision Reasoning
            if result['decision_logic']:
                console.print("\n[bold grey50]Justification:[/bold grey50]")
                console.print(f"  {result['justification']}", style="grey50")

            # Response Panel
            response_color = "white" if result['status'] == "replied" else "red"
            console.print(Panel(
                result['response'],
                title="[bold]Agent Response[/bold]",
                border_style=response_color,
                padding=(1, 2)
            ))
            
            if result['sources']:
                console.print("[bold]Reference Sources:[/bold]")
                for source in result['sources']:
                    console.print(f"  🔗 [link={source}]{source}[/link]", style="blue")
            
            console.print("━" * 60 + "\n")
            
            log_interaction(ticket, result)

    except KeyboardInterrupt:
        console.print("\n[info]Session ended by user. Goodbye![/info]")
        sys.exit(0)

if __name__ == "__main__":
    main()
