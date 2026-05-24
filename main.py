import os
from dotenv import load_dotenv
from google import genai

def main():
    try:
        # Load environment variables from .env file
        load_dotenv()
        
        # Get the Gemini API key from environment variables
        api_key = os.getenv('GEMINI_API_KEY')
        
        if not api_key:
            raise ValueError("GEMINI_API_KEY is not set in the environment variables.")
        
        # Initialize the Gemini client with the API key
        client = genai.Client(api_key = api_key)
        model_id = "gemini-2.5-flash"
        prompt="What is the capital of France?",
        # Example usage: Generate a response from the Gemini model
        response = client.models.generate_content(
            model=model_id,
            contents=prompt,
        )
        
        print("Response from Gemini:", response.text)
    except Exception as e:
        print("An error occurred:", e)

if __name__ == "__main__":
    main()