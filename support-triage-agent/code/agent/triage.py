import os
import json
from openai import OpenAI
from dotenv import load_dotenv
from typing import Dict, List, Optional, Tuple
from .retriever import SupportRetriever
from .escalation import should_escalate

# Load environment variables from .env file
load_dotenv()

# Domain keywords for rule-based detection
DOMAIN_KEYWORDS = {
    "hackerrank": ["assessment", "test", "candidate", "interview", "coding", "plagiarism", "proctoring", "recruiter", "hackerrank"],
    "claude": ["subscription", "plan", "api", "message limit", "usage", "anthropic", "claude", "model", "billing", "ai"],
    "visa": ["card", "payment", "transaction", "fraud", "chargeback", "merchant", "declined", "pin", "atm", "cvv", "visa"]
}

class SupportTriageAgent:
    def __init__(self):
        api_key = os.environ.get("LLM_API_KEY")
        api_base = os.environ.get("LLM_API_BASE", "https://api.openai.com/v1")
        
        if not api_key:
            print("[!] Warning: LLM_API_KEY not found in environment.")
        
        self.client = OpenAI(api_key=api_key, base_url=api_base)
        self.retriever = SupportRetriever()
        self.model = os.environ.get("LLM_MODEL", "qwen/qwen3-coder-480b-a35b-instruct")

    def analyze_risk(self, ticket: str) -> Dict:
        """Analyze ticket for financial risk, urgency, and emotional tone."""
        ticket_lower = ticket.lower()
        risk_score = 0
        reasons = []

        # Financial/Security Indicators
        financial_keywords = ["payment", "charge", "money", "transaction", "unauthorized", "fraud", "stolen", "refund"]
        if any(k in ticket_lower for k in financial_keywords):
            risk_score += 3
            reasons.append("Financial transaction detected")

        # Urgency Indicators
        urgency_keywords = ["urgent", "immediately", "asap", "emergency", "lost", "blocked", "locked"]
        if any(k in ticket_lower for k in urgency_keywords):
            risk_score += 2
            reasons.append("High urgency detected")

        # Emotional/Stress Indicators
        emotional_keywords = ["please help", "frustrated", "angry", "worried", "scam", "unfair"]
        if any(k in ticket_lower for k in emotional_keywords):
            risk_score += 1
            reasons.append("High emotional intensity")

        risk_level = "LOW"
        if risk_score >= 5: risk_level = "CRITICAL"
        elif risk_score >= 3: risk_level = "MEDIUM"

        return {
            "score": risk_score,
            "level": risk_level,
            "reasons": reasons
        }

    def detect_domain_hybrid(self, ticket: str) -> Tuple[str, List[str]]:
        """Hybrid Domain Detection: Keywords (Rules) + LLM (Nuance)."""
        ticket_lower = ticket.lower()
        scores = {domain: 0 for domain in DOMAIN_KEYWORDS}
        reasoning = []

        # 1. Rule-based scoring
        for domain, keywords in DOMAIN_KEYWORDS.items():
            matches = [k for k in keywords if k in ticket_lower]
            scores[domain] += len(matches)
            if matches:
                reasoning.append(f"Keyword match for {domain}: {', '.join(matches)}")

        # 2. LLM-based refinement for edge cases (vague, mixed, typos)
        if max(scores.values()) == 0 or len([s for s in scores.values() if s == max(scores.values())]) > 1:
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": "Classify the support ticket into one domain: hackerrank, claude, or visa. Return ONLY the domain name."},
                        {"role": "user", "content": ticket}
                    ],
                    max_tokens=10
                )
                llm_domain = response.choices[0].message.content.strip().lower()
                if llm_domain in DOMAIN_KEYWORDS:
                    reasoning.append(f"LLM refined domain detection to: {llm_domain}")
                    return llm_domain, reasoning
            except:
                pass

        # Fallback to highest score
        detected = max(scores, key=scores.get) if max(scores.values()) > 0 else "hackerrank"
        return detected, reasoning

    def triage(self, ticket: str, ticket_id: str = "") -> Dict:
        """Enhanced Triage with Hackathon-specific Schema (status, product_area, request_type, justification)."""
        # 1. Risk Analysis
        risk = self.analyze_risk(ticket)
        
        # 2. Hybrid Domain Detection (Product Area)
        domain, detection_reasons = self.detect_domain_hybrid(ticket)
        
        # 3. Check Escalation (Rules)
        escalate, escalation_reason = should_escalate(ticket)
        
        # 4. Request Type Classification (LLM)
        try:
            req_type_prompt = f"Classify this support ticket into one of these types: product_issue, feature_request, bug, invalid. Return ONLY the type name.\nTicket: {ticket}"
            req_type_response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": req_type_prompt}],
                max_tokens=10
            )
            request_type = req_type_response.choices[0].message.content.strip().lower()
            if request_type not in ["product_issue", "feature_request", "bug", "invalid"]:
                request_type = "product_issue"
        except:
            request_type = "product_issue"

        decision_reasons = detection_reasons.copy()
        if risk['reasons']:
            decision_reasons.extend([f"Risk: {r}" for r in risk['reasons']])
        
        justification = " | ".join(decision_reasons)

        if escalate:
            return {
                "ticket_id": ticket_id,
                "product_area": domain,
                "status": "escalated",
                "request_type": request_type,
                "response": f"🚨 [CRITICAL ESCALATION] {escalation_reason}. This ticket has been prioritized for immediate manual intervention due to {risk['level'].lower()} risk indicators.",
                "justification": f"Escalated: {escalation_reason}. {justification}",
                "risk_level": risk['level'],
                "risk_score": risk['score'],
                "decision_logic": decision_reasons,
                "sources": []
            }
            
        # 5. Retrieve Context
        docs, metas = self.retriever.retrieve(ticket, source_filter=domain, top_k=3)
        sources = [m.get('path', m.get('url', 'local_corpus')) for m in metas]
        context = "\n\n".join(docs)
        
        # 6. Build Authoritative Prompt (Ensuring strictly grounded response)
        prompt = f"""You are a Senior Support Engineer for {domain.capitalize()}.
You have detected a ticket with {risk['level']} risk level.

INSTRUCTIONS:
1. Provide a direct, authoritative, and helpful response.
2. If there is financial risk (duplicate charges, fraud), explicitly acknowledge the urgency and safety steps.
3. Use ONLY the provided documentation. If the answer is not there, state that you require specific account access to resolve this and provide the exact escalation path.
4. DO NOT use generic 'contact support' filler unless you've explained exactly WHY.
5. NEVER mention internal document details or URLs in the text response itself.

DOCUMENTATION:
{context}

USER TICKET:
{ticket}

Response:"""

        # 7. Call LLM API
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                max_tokens=800,
                temperature=0.2,
                messages=[{"role": "user", "content": prompt}]
            )
            response_text = response.choices[0].message.content
        except Exception as e:
            response_text = f"Error generating response: {str(e)}"
            
        return {
            "ticket_id": ticket_id,
            "product_area": domain,
            "status": "replied",
            "request_type": request_type,
            "response": response_text,
            "justification": justification,
            "risk_level": risk['level'],
            "risk_score": risk['score'],
            "decision_logic": decision_reasons,
            "sources": sources
        }
