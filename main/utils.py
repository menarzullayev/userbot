import re

MD_ESCAPE_CHARS = r"([_\*\[\]\(\)~`>#+\-=|{}!])"

def escape_markdown(text: str) -> str:
    return re.sub(MD_ESCAPE_CHARS, r"\\\1", text)