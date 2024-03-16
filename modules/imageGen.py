import os
import webbrowser

from PIL import Image
import requests
from io import BytesIO
import json
from pathlib import Path
from dotenv import load_dotenv

from openai import OpenAI

# Load the .env file
load_dotenv()

# Read the API key from the environment variable
api_key = os.getenv("OPENAI_API_KEY")

client = OpenAI()

def display_image(image_url):
    response = requests.get(image_url)
    img = Image.open(BytesIO(response.content))
    img.show()
    
    # # Path to your image file
    # image_path = 'path/to/your/image.jpg'
    # # Convert the image path to a URL by creating a file URI
    # image_url = 'file://' + os.path.abspath(image_path)

    # Open the image in the default web browser
    # webbrowser.open(image_url)
    
    print(">>> Image displayed!")
    

def save_image(image_url, file_path):
    response = requests.get(image_url)
    img = Image.open(BytesIO(response.content))
    img.save(file_path)
    print(f">>> Image saved to {file_path}")

def gen_img_dalle3(prompt):
    print(">>> Generating Image ...")
    result = client.images.generate(
    model="dall-e-3",
    prompt=prompt,
    n=1,
    # quality="standard",
    size="1024x1024"
    )

    image_url = result.data[0].url
    print(">>> Image generated!")
    return image_url

def gen_prompt(user_prompt):
    
    with open('data/image_prompts.json', 'r') as file:
        image_prompts_data = json.load(file)

    with open('data/image_sys_prompt.md', 'r') as md_file:
        instructions = md_file.read()

    # Prepare messages for GPT-4 Completion
    messages = [
        {"role": "system", "content": f"You are a world-class creative visual artist, a master of photography, painting, lighting, composition, poetry and all arts. Use these instructions to generate image prompts: \n {instructions}"},
    ]

    # Adding prompts from JSON data
    for prompt in image_prompts_data:
        messages.append({"role": "user", "content": prompt["user"]})
        messages.append({"role": "assistant", "content": prompt["assistant"]})

    # Optionally, add content from markdown file
    messages.append({"role": "user", "content": f"Generate a prompt in the same format as previous responses, but reffering to this context: \n{user_prompt}"})

    print(">>> Generating prompt ...")
    
    response = client.chat.completions.create(
    model="gpt-3.5-turbo-0125",
    messages=messages,
    max_tokens=300,
    temperature=1.0,
    )
    # return user_prompt + "," + response.choices[0].message.content
    return response.choices[0].message.content

if __name__ == "__main__":

    draft_page = """
    So Now?
    the words have come and gone,
    I sit ill.
    the phone rings, the cats sleep.
    Linda vacuums.
    I am waiting to live,
    waiting to die.
    Charles Bukowski
    """
        
    user = input("Enter p, i:")
        
    if user == "i":
        img_prompt = gen_prompt(draft_page)
        print("Prompt:\n", img_prompt)
        image_url = gen_img_dalle3(img_prompt)
        display_image(image_url)
        save_image(image_url, "output/dalle3_image.jpg")
        
    elif user == "p":
        prompt_refined = gen_prompt(draft_page)
        print("Prompt:\n", prompt_refined)