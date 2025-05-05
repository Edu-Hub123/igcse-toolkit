import os
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Initialize OpenAI client with your API key
client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY")  # Make sure this is set in your .env
)

def generate_topic_prompt(board, subject):
    """
    Generates a clear, focused prompt for topic extraction based on exam board and subject.
    """
    return (
        f"You are an expert in curriculum design and IGCSE qualifications.\n"
        f"Using reliable and up-to-date sources, list the main topics covered in the subject "
        f"'{subject}' under the '{board}' IGCSE exam board. Present them as a bullet-point list."
    )

def extract_topics_from_ai(board, subject):
    """
    Sends a request to GPT-4 to extract topics based on the board and subject.
    """
    prompt = generate_topic_prompt(board, subject)

    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are a helpful assistant that generates IGCSE topic lists."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.5
    )

    # Extract the message content and return it split by newlines (assuming bullet points)
    return response.choices[0].message.content.strip().split("\n")

def main():
    """
    Main function to run the topic extraction script.
    """
    print("🎓 IGCSE Topic Generator")
    board = input("Enter the exam board (e.g. Cambridge or Edexcel): ").strip()
    subject = input("Enter the subject: ").strip()

    print(f"\n🔍 Generating topics for {subject} under {board} IGCSE...\n")

    try:
        topics = extract_topics_from_ai(board, subject)

        print("📚 Topics:")
        for topic in topics:
            print(f"• {topic.strip('•').strip()}")  # Clean up any bullets or extra spacing
    except Exception as e:
        print(f"❌ An error occurred: {e}")

if __name__ == "__main__":
    main()


