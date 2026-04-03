import os
from dotenv import load_dotenv
from anthropic import Anthropic

load_dotenv()

def main():
    print("""
        Gmail emails summary:\n
          Specify the Gmail label associated to the emails and the number of days to consider:
          \n\n
          """)
    label = input("Enter the Gmail label:")
    days = int(input("Enter the days:"))

    consent=input("Enter Y to confirm or N to stop the process:")
    if consent.lower() != 'y':
        exit()

    print(f"Summarising the emails with label {label} received in the last {days} days")


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