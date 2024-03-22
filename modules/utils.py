import os, re, json
from dotenv import load_dotenv

# Load the .env file
load_dotenv()

# Read the API key from the environment variable
api_key = os.getenv("OPENAI_API_KEY")

# LLM
from langchain_openai import ChatOpenAI
from langchain.schema import StrOutputParser

# CHAT TEMPLATES
from langchain.prompts.chat import (
    ChatPromptTemplate,
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate,
)

def extract_json(output, retry_function, attempt=1, max_attempts=10):
    """
    Tries to parse the entire output as JSON. If it fails, looks for a JSON block in the output and attempts to parse it.
    If parsing fails or no JSON block is found, it retries by calling the provided retry function.
    
    Args:
        output (str): The output string, potentially containing JSON or a JSON block.
        retry_function (callable): Function to retry generating the output.
        attempt (int): Current attempt number.
        max_attempts (int): Maximum number of attempts allowed.
    
    Returns:
        dict or None: Parsed JSON object if successful, or None if unsuccessful after max attempts.
    """
    try:
        # First, attempt to parse the entire output as JSON
        parsed_json = json.loads(output)
        return parsed_json
    except json.JSONDecodeError:
        # If it fails, look for a JSON block within the output
        try:
            json_block_match = re.search(r'```json\n([\s\S]*?)\n```', output)
            if json_block_match:
                json_block = json_block_match.group(1)  # Extract the JSON block
                parsed_json = json.loads(json_block)  # Attempt to parse the JSON block
                return parsed_json
            else:
                raise ValueError("No JSON block found in the output.")
        except (ValueError, json.JSONDecodeError) as e:
            print(f"Attempt {attempt} failed: {e}")
            if attempt < max_attempts:
                print("Retrying...")
                new_output = retry_function()  # Call the retry function to generate new output
                return extract_json(new_output, retry_function, attempt + 1, max_attempts)
            else:
                print("Maximum attempts reached. Unable to extract or parse JSON.")
                print(output)  # Print the output for debugging purposes
                return None

def json_to_markdown_LLM(json_obj):
    user_message = """
    Convert the following JSON data into a readable Markdown document. 
    Format it with headings for each key and include the associated information as descriptive text under each heading.
    Don't write anything else than the contents of the markdown, get straight to the task.
    Dont' add a markdown block, only the contents.
    JSON data:
    {input}
    """
    # MODEL
    llm = ChatOpenAI(
        model = "gpt-3.5-turbo-0125", #  gpt-4-0125-preview gpt-3.5-turbo-0125
        temperature = 0.0,
        max_retries = 3,
        )
    
    # PROMPT
    promptTemplate = ChatPromptTemplate.from_messages([
    HumanMessagePromptTemplate.from_template(user_message),
    ])
    
    # RAG chain
    chain = (
        promptTemplate
        | llm
        | StrOutputParser()
    )
    
    md_output = chain.invoke({"input": json_obj})
    return md_output

def save_markdown(contents, file_name="undefined"):
    # Implement the logic to compile contents into a Markdown document
    md_path = f"output/{file_name}.md"
    # Check if the file exists and delete it
    if os.path.exists(md_path):
        os.remove(md_path)
    
    with open(md_path, "w") as md_file:
        for content in contents:
            md_file.write(content)

def save_json(data, file_name="undefined"):
    # Implement the logic to compile contents into a Markdown document
    json_path = f"output/{file_name}.json"
    # Check if the file exists and delete it
    if os.path.exists(json_path):
        os.remove(json_path)
    
    with open(json_path, "w") as json_file:
        json.dump(data, json_file, indent=4)

def read_file(file_base_name, extensions=['.md', '.txt', '.json']):
    """
    Attempts to read a file, trying different extensions until the file is found.
    
    Args:
        file_base_name (str): The base name of the file without extension.
        extensions (list): A list of file extensions to try.
    
    Returns:
        str or None: The content of the file if found, None otherwise.
    """
    for ext in extensions:
        file_path = f"output/{file_base_name}{ext}"
        if os.path.exists(file_path):
            print(f"Reading {file_path} from file.")
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()
                return content
    print(f"File {file_base_name} with extensions {extensions} does not exist.")
    return None

def json_to_markdown_bkup(json_obj):
    """
    Converts a JSON object to a markdown string with enhanced formatting, including support for lists, thematic breaks, and various markdown syntaxes for improved readability.
    """
    def process_item(key, value, depth, is_list_item=False):
        """
        Processes each item, applying appropriate markdown based on its type and context.
        """
        md = ""
        if key and not is_list_item:
            if depth == 1:
                # For top-level headings, include a thematic break after the heading
                md += f"# {key}\n"
            else:
                md += f"{'#' * depth} {key}\n\n"
        elif is_list_item:
            # Corrected handling for list items to prevent duplication
            return f"- {value}\n"

        if isinstance(value, dict):
            for sub_key, sub_value in value.items():
                md += process_item(sub_key, sub_value, depth + 1)
            if depth == 2:
                # Add thematic breaks after sections for top-level headings
                md += "---\n\n"
        elif isinstance(value, list):
            # Ensure list items are processed correctly without duplicating the item content
            list_md = "".join([process_item(None, item, depth + 1, True) for item in value])
            md += "- " + list_md + "\n"
        else:
            if not is_list_item:
                # Apply markdown syntax for better formatting of key-value pairs
                if key:
                    md += f"{value}\n\n" # f"**{key}:** {value}\n\n"
                else:
                    md += f"> {value}\n\n"
            else:
                # This part should never hit due to the corrected return in the list item condition above
                md += f"{value}\n"

        return md

    # Initial call to process the JSON object with a depth of 1
    return process_item(None, json_obj, 1)

def json_to_markdown2(json_obj, depth=0):
    """
    Converts a JSON object to a markdown string with enhanced formatting, 
    specially handling lists and dictionaries to ensure a clear and accurate Markdown representation.
    """
    md = ""
    if isinstance(json_obj, dict):
        for key, value in json_obj.items():
            if isinstance(value, (dict, list)):
                # Add section headers for dictionary keys
                if depth > 0:  # Skip the top-level header
                    md += f"{'#' * (depth)} {key}\n\n"
                md += json_to_markdown2(value, depth + 1)
            else:
                # Directly add key-value pairs
                md += f"**{key}:** {value}\n\n"
    elif isinstance(json_obj, list):
        for item in json_obj:
            if isinstance(item, (dict, list)):
                # For list items that are complex, add as subsections or bullet points
                md += "- " + json_to_markdown2(item, depth).lstrip("- ")
            else:
                # For simple list items, format as bullet points
                md += f"- {item}\n"
        md += "\n"
    else:
        # Base case for simple values
        md += f"{json_obj}\n\n"

    return md.strip()

def json_to_markdown3(json_obj):
    """
    Converts a JSON object to a markdown string optimized for book formatting,
    presenting chapters and content directly without bullet points or numbered lists.
    """
    def process_item(key, value, depth=1):
        """
        Processes each item, applying appropriate markdown based on its type and context,
        optimized for direct narrative content presentation.
        """
        md = ""
        if isinstance(value, dict):
            # Combine chapter and its title for a concise presentation
            if key and depth == 1:  # Assuming depth 1 is for Chapters
                md += f"\n## {key}\n\n"
            elif key:
                md += f"**{key}**\n\n"  # Emphasize sub-chapter titles without making them headers
            for sub_key, sub_value in value.items():
                md += process_item(sub_key, sub_value, depth + 1)
        elif isinstance(value, list):
            for item in value:
                if isinstance(item, dict):
                    # Treat each key-value in dict items within lists directly, similar to dict handling
                    for sub_key, sub_value in item.items():
                        md += process_item(sub_key, sub_value, depth + 1)
                else:
                    # Directly append list items as paragraphs
                    md += f"{item}\n\n"
        else:
            # Direct formatting for narrative content without prefixes
            if key:
                md += f"**{key}:** {value}\n\n"  # Keep key-value emphasis format for clarity
            else:
                md += f"{value}\n\n"
        return md

    markdown = process_item(None, json_obj)
    return markdown.strip()  # Strip leading/trailing whitespace for a cleaner output

def json_to_markdown_almost(json_obj):
    """
    Converts a JSON object to a markdown string with enhanced formatting, including support for thematic breaks between sections,
    hierarchy separation with depth-based headers, and removing bullet points and numbered lists for a clean, readable format.
    """
    def process_item(key, value, depth=0):
        """
        Processes each item, applying appropriate markdown based on its type and context,
        optimized for readability with hierarchical organization and thematic separation.
        """
        md = ""
        # Header formatting based on depth
        if key:
            header = "#" * depth
            md += f"{header} {key}\n\n"

        # Thematic break for top-level entries (e.g., chapters)
        if depth == 2 and key:
            md += "---\n\n"

        if isinstance(value, dict):
            for sub_key, sub_value in value.items():
                md += process_item(sub_key, sub_value, depth+1)
        elif isinstance(value, list):
            for item in value:
                if isinstance(item, dict):
                    for sub_key, sub_value in item.items():
                        md += process_item(sub_key, sub_value, depth+1)
                else:
                    # Directly appending list items as paragraphs
                    md += f"- {item}\n\n"
        else:
            # Formatting non-list, non-dict items as paragraphs directly under their parent key
            md += f"{value}\n\n"

        return md

    markdown = process_item(None, json_obj)
    return markdown.strip()  # Strip leading/trailing whitespace for cleaner output

def json_to_markdown_420(json_obj):
    """
    Converts a JSON object to a markdown string with selective use of bullet points, bold text,
    and numbers for better readability, while maintaining thematic breaks and depth-based headers
    for structure.
    """
    def process_item(key, value, depth=0, is_list=False):
        """
        Processes each item, applying markdown based on its type, context, and whether it's part of a list.
        """
        md = ""
        prefix = ""
        if depth > 0:  # Adjust prefix based on depth to create numbered lists at deeper levels
            prefix = f"{'#' * (depth)} "

        if key:
            md += f"{prefix}{key}\n\n"

        if isinstance(value, dict):
            for sub_key, sub_value in value.items():
                md += process_item(sub_key, sub_value, depth + 1)
        elif isinstance(value, list):
            md += "\n".join([process_item(None, item, depth + 1, is_list=True) for item in value]) + "\n"
        else:
            # Format simple values, applying bold for keys if within a list for clarity
            if key and is_list:
                md += f"**{key}:** {value}\n\n"
            else:
                md += f"- {value}\n\n"

        # Include thematic breaks after top-level sections for clear separation
        if depth == 2:
            md += "---\n\n"

        return md

    markdown = process_item(None, json_obj)
    return markdown.strip()  # Ensure clean output without leading/trailing whitespace

def json_to_markdown_WORKING(json_obj):
    """
    Converts a JSON object to a markdown string with selective use of bullet points, bold text,
    and numbers for better readability, while maintaining thematic breaks and depth-based headers
    for structure, ensuring header levels do not surpass ###.
    """
    def process_item(key, value, depth=1, is_list=False):
        """
        Processes each item, applying markdown based on its type, context, and whether it's part of a list,
        adjusting the depth to manage header levels.
        """
        md = ""
        prefix = ""
        # Adjust the maximum depth for headers to not surpass level 3
        adjusted_depth = min(depth, 4)  # Ensures we don't go beyond ### headers
        
        if adjusted_depth == 0:
            adjusted_depth = 1
        if adjusted_depth > 0:  # Adjust prefix based on depth to create numbered lists at deeper levels
            prefix = f"{'#' * (adjusted_depth)} "

        if key:
            md += f"{prefix}{key}\n\n"

        if isinstance(value, dict):
            for sub_key, sub_value in value.items():
                # Increase depth but do not let it surpass the maximum for headers
                md += process_item(sub_key, sub_value, depth + 1 if depth < 3 else depth, is_list)
        elif isinstance(value, list):
            md += "\n".join([process_item(None, item, depth + 1 if depth < 3 else depth, is_list=True) for item in value]) # + "\n"
        else:
            # Format simple values, applying bold for keys if within a list for clarity
            if key and is_list:
                md += f"{value}\n\n" #\n" # f"**{key}:** {value}\n\n"
            else:
                md += f"- {value}\n\n" #\n"

        # Include thematic breaks after top-level sections for clear separation
        if depth == 2:
            md += "---\n\n" # \n"

        return md

    markdown = process_item(None, json_obj)
    return markdown.strip()  # Ensure clean output without leading/trailing whitespace

def json_to_markdown(json_obj):
    """
    Converts a JSON object to a markdown string with selective use of bullet points, bold text,
    and numbers for better readability, while maintaining thematic breaks and depth-based headers
    for structure, ensuring header levels do not surpass ###.
    """
    def process_item(key, value, depth=1, is_list=False):
        """
        Processes each item, applying markdown based on its type, context, and whether it's part of a list,
        adjusting the depth to manage header levels.
        """
        md = ""
        prefix = ""
        # Adjust the maximum depth for headers to not surpass level 3
        adjusted_depth = min(depth, 4)  # Ensures we don't go beyond ### headers
        
        if adjusted_depth == 0:
            adjusted_depth = 1
        if adjusted_depth > 0:  # Adjust prefix based on depth to create numbered lists at deeper levels
            prefix = f"{'#' * (adjusted_depth)} "

        if key:
            md += f"{prefix}{key}\n\n"

        if isinstance(value, dict):
            for sub_key, sub_value in value.items():
                # Increase depth but do not let it surpass the maximum for headers
                md += process_item(sub_key, sub_value, depth + 1 if depth < 4 else depth, is_list)
        elif isinstance(value, list):
            md += "\n".join([process_item(None, item, depth + 1 if depth < 4 else depth, is_list=True) for item in value]) # + "\n"
        else:
            # Format simple values, applying bold for keys if within a list for clarity
            if key and is_list:
                md += f"{value}\n\n" #\n" # f"**{key}:** {value}\n\n"
            else:
                md += f"{value}\n\n" #\n"

        # Include thematic breaks after top-level sections for clear separation
        if depth == 2:
            md += "---\n\n" # \n"

        return md

    markdown = process_item(None, json_obj)
    return markdown.strip()  # Ensure clean output without leading/trailing whitespace

def test():
    book_json = read_file("book_json")
    book_json2 = json.loads(book_json)
    book_md = json_to_markdown(book_json2)
    save_markdown(book_md, "book_md_TEST")
    
# Example usage
if __name__ == "__main__":
    
    # Example JSON data
    full_json_data = {
    "Introduction": {
    "Purpose": "The purpose of the book is to provide practical strategies and insights to help readers thrive in a rapidly changing world.",
    "Scope": "The report will cover buyer motivation, positive and negative book qualities, topics to include/exclude, target audience demographics and psychographics, common pain points and questions, possible objections, and recommendations.",
    "Outcome": "The intended outcome for readers is to gain the knowledge and tools necessary to navigate technological advancements and societal shifts successfully."
    },
    "Amazon Research": {
    "Buyer Motivation": {
        "Skill Enhancement": "Readers seek out books on this topic to enhance their skills and stay relevant in evolving industries.",
        "Career Aspirations": "The book can aid in career advancement by providing insights into future trends and strategies for success.",
        "Inspiration and Creativity": "Readers can find inspiration and creativity in the book through motivational examples and practical advice."
    },
    "Positive Book Qualities": {
        "Comprehensive Coverage": "Thorough exploration of topics is essential to provide readers with a holistic understanding.",
        "Practical Application": "Actionable content is crucial for readers to implement strategies effectively.",
        "Inspirational Stories": "Motivational examples can inspire readers to embrace change and pursue growth."
    },
    "Negative Book Qualities": {
        "Lack of Specificity": "Avoiding vagueness ensures the content is clear and actionable.",
        "Outdated Information": "Including outdated content can diminish the book's credibility and relevance.",
        "Misleading Titles": "Titles should accurately reflect the content to set proper reader expectations."
    },
    "Topics to Include": {
        "List of Essential Topics": [
        "Future trends in technology and business",
        "Strategies for career advancement in a disruptive age",
        "Personal development in a changing world"
        ]
    }
    }
    }
    
    # # Convert the JSON data to a Markdown-formatted string using LLM
    # json_to_md = convert_json_to_markdown(snippet_json_data)
    # json_to_md = json_to_markdown(full_json_data)
    # print(json_to_md)

    # extended_md = json_to_markdown(extended_json)
    # save_markdown(extended_md, "snippet_research")
    

    # one_expand= expander(json_to_md, "You always rely consisely in 10 words. You are smart and you know it.")
    # print(one_expand)
    
    
    