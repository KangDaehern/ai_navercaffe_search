from dataclasses import dataclass, field

@dataclass
class CafeComment:
    author: str = ""
    text: str = ""
    date: str = ""
    is_reply: bool = False

@dataclass
class CafePost:
    title: str
    url: str
    author: str = ""
    date: str = ""
    text: str = ""
    comments: list[CafeComment] = field(default_factory=list)
    has_comments: bool = False
