import re


def normalize_entity_name(name: str) -> str:
    """
    Normalize an entity name before resolution.

    Example:
        "Taiwan Semiconductor Manufacturing Co., Ltd."
        ->
        "taiwan semiconductor manufacturing co ltd"
    """
    name = name.lower().strip()

    # Remove punctuation
    name = re.sub(r"[^\w\s]", " ", name)

    # Replace multiple spaces with one space
    name = re.sub(r"\s+", " ", name)

    return name.strip()