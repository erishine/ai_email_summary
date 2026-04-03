import os
from dotenv import load_dotenv
from anthropic import Anthropic


def main():
    load_dotenv()

    client = Anthropic(
        api_key=os.getenv('ANTHROPIC_API_KEY')
    )

    message = client.messages.create(
        max_tokens=1024,
        messages = [
            {
                "role":"user",
                "content":"hello Claude",
            }
        ],
        model="claude-haiku-4-5-20251001"
    )

    print(message.content[0].text)



if __name__ == "__main__":
    main()