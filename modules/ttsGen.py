import os
import webbrowser
from dotenv import load_dotenv

from openai import OpenAI
import warnings

# Load the .env file
load_dotenv()

# Read the API key from the environment variable
api_key = os.getenv("OPENAI_API_KEY")

client = OpenAI()


def gen_speech_and_save(text, file_path):
    
    #'nova - girl', 'shimmer - woman', 'echo - generic', 'onyx - man', 'fable - rainbow', 'alloy - boy' 
    
    response = client.audio.speech.create(
        model="tts-1", #    "tts-1", or "tts-1-hd"
        voice="shimmer", # onyx or shimmer :let it choose voice & intonation based on context input
        input=text,
        speed=1.61,
    )
    warnings.simplefilter("ignore", DeprecationWarning)
    response.stream_to_file(file_path)
    # response.with_streaming_response.method()
    return file_path

def play_audio(file_path):
    # if os.name == 'posix':  # macOS, Linux, Unix, etc.
    #     os.system(f"open '{file_path}'")
    # elif os.name == 'nt':  # Windows
    #     os.system(f"start {file_path}")
    
    # Convert the file path to a URL that the browser can understand
    # This is necessary for local files
    file_url = 'file://' + os.path.abspath(file_path)
    webbrowser.open(file_url)


if __name__ == "__main__":
    # Test the function
    text = "Hello, this is a functionality test!"
    file_path = "output/tts_test.mp3"
    gen_speech_and_save(text, file_path)
    play_audio(file_path)