import uuid


def generate_prefixed_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4()}"
