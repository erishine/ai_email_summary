from dataclasses import dataclass
import re

@dataclass
class MyEmail:
    subject: str
    raw_body: str
    date: str
    message_id: str = ""
    clean_body: str = ""
    gmail_url: str = ""

    @classmethod
    def from_mcp(cls, email_id, email_data):
        text = email_data.contents[0].text
        # parse stuff
        email_attrs= cls._parse(text)
        email_attrs['message_id'] = email_id
        email_attrs['gmail_url'] = "https://mail.google.com/mail/u/0/#inbox/" + email_id
        email_attrs['clean_body'] = cls._clean_body(email_attrs['raw_body'])
        return cls(**email_attrs)
    
    @staticmethod
    def _parse(text):
        email_attrs={}
        email_attrs['subject'] = re.search(r'\nSubject:\s(.+)', text).group(1)
        email_attrs['date'] = re.search(r'\nDate:\s(.+)', text).group(1)
        email_attrs['raw_body'] = text.split('\n\n', 1)[1]
        return email_attrs
    
    @staticmethod
    def _clean_body(raw_body_text):
        text = raw_body_text
        # normalise line endings
        text = text.replace('\r\n', '\n')
        # strip zero-width spaces
        text = text.replace('\u200b', '')
        # strip mailto links with surrounding text: "Label (mailto:...)"
        text = re.sub(r'\S.*?\(mailto:\S+\)', '', text)
        # strip bare mailto links
        text = re.sub(r'mailto:\S+', '', text)
        # strip parenthesised URLs: ( https://... )
        text = re.sub(r'\(\s*https?://\S+\s*\)', '', text)
        # strip bracket-wrapped URLs: [ https://... ]
        text = re.sub(r'\[\s*https?://\S+\s*\]', '', text)
        # strip inline URLs after text: "some text https://..."
        text = re.sub(r'https?://\S+', '', text)
        # strip bare URLs on their own line (catches any remaining)
        text = re.sub(r'^\s*https?://\S+\s*$', '', text, flags=re.MULTILINE)
        # strip footer from common trigger phrases to end
        text = re.sub(r'(Unsubscribe|Update your profile|© 20\d\d|Partner with US).*', '', text, flags=re.DOTALL)
        # strip dash-only separator lines (2+ dashes)
        text = re.sub(r'^-{2,}\s*$', '', text, flags=re.MULTILINE)
        # strip orphaned --> arrows
        text = re.sub(r'-->', '', text)
        # collapse 3+ blank lines into one
        text = re.sub(r'\n{3,}', '\n\n', text)
        return text.strip()
