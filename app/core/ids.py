from uuid import uuid4


def new_ticket_id() -> str:
    return f"TKT-{uuid4().hex[:8]}"


def new_usage_id() -> str:
    return f"USG-{uuid4().hex[:12]}"
