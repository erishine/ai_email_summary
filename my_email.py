from dataclasses import dataclass

@dataclass
class MyEmail:
    subject: str
    raw_body: str
    date: str
    message_id: str = ""
    clean_body: str = ""
    gmail_url: str = ""