from typing import Tuple

ESCALATION_RULES = [
    # FRAUD / SECURITY
    ("fraud", "Potential fraud — requires security team review"),
    ("unauthorized transaction", "Unauthorized transaction — requires security team"),
    ("account hacked", "Account security incident — requires security team"),
    ("identity theft", "Identity theft claim — requires security team"),
    ("stolen card", "Stolen card report — requires security team"),
    
    # LEGAL / COMPLIANCE
    ("legal action", "Legal threat — escalate to legal team"),
    ("lawsuit", "Legal threat — escalate to legal team"),
    ("gdpr", "Data privacy/compliance request — escalate to compliance team"),
    ("data deletion", "Data deletion request — escalate to compliance team"),
    
    # BILLING DISPUTES
    ("dispute charge", "Billing dispute — escalate to billing team"),
    ("chargeback", "Chargeback request — escalate to billing team"),
    ("refund not received", "Refund issue — escalate to billing team"),
    
    # ACCOUNT ACCESS
    ("locked out", "Account lockout — requires manual verification"),
    ("cannot login", "Login failure — may require manual account review"),
    ("account suspended", "Account suspension — requires manual review"),
    ("account banned", "Account ban — requires manual review"),
    
    # ASSESSMENT INTEGRITY
    ("cheating", "Cheating allegation — escalate to integrity/HR team"),
    ("plagiarism", "Plagiarism claim — escalate to integrity team"),
    ("unfair result", "Assessment dispute — requires manual review"),
]

def should_escalate(ticket: str) -> Tuple[bool, str]:
    """
    Check if a ticket should be escalated based on predefined keywords.
    Returns (True, reason) if escalation is needed, otherwise (False, "").
    """
    ticket_lower = ticket.lower()
    
    for keyword, reason in ESCALATION_RULES:
        if keyword.lower() in ticket_lower:
            return True, reason
            
    return False, ""
