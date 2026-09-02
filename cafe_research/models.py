from dataclasses import dataclass

@dataclass
class CafePost:
    title: str
    url: str
    author: str = ""
    date: str = ""
    text: str = ""
