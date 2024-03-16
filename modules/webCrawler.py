# LLM
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain.schema import StrOutputParser

# CHAT TEMPLATES
from langchain.prompts.chat import (
    ChatPromptTemplate,
    SystemMessagePromptTemplate,
    AIMessagePromptTemplate,
    HumanMessagePromptTemplate,
)

from langchain.prompts import MessagesPlaceholder

# SPLITTERS
from langchain_text_splitters import CharacterTextSplitter, RecursiveCharacterTextSplitter
from langchain.docstore.document import Document

# VECTOR STORES
from langchain_community.vectorstores import FAISS
from langchain_community.document_loaders import WebBaseLoader

# MEMORY
from operator import itemgetter
from langchain.memory import ConversationBufferMemory, ConversationSummaryBufferMemory, ConversationTokenBufferMemory
from langchain_core.runnables import RunnableLambda, RunnablePassthrough, RunnableParallel

# TOOLS
from langchain_core.utils.function_calling import convert_to_openai_function
from langchain.agents.format_scratchpad import format_to_openai_function_messages
from langchain.agents.output_parsers import OpenAIFunctionsAgentOutputParser
from langchain.agents import tool
from langchain.agents import AgentExecutor

#SEARCHES
from langchain_community.tools import DuckDuckGoSearchRun, DuckDuckGoSearchResults
from langchain_community.utilities import DuckDuckGoSearchAPIWrapper

import os
import re
from dotenv import load_dotenv
from exa_py import Exa
import warnings
import json

from utils import extract_json

# Load the .env file
load_dotenv()

# Read the API key from the environment variable
oai_api_key = os.getenv("OPENAI_API_KEY")
exa_api_key = os.getenv("EXA_API_KEY")

exa = Exa(api_key=exa_api_key)


def gen_search_queries(outline, breadth=3, max_attempts=5, current_attempt=1):
    
    # REWRITE THESE PROMPTS !!!
    
    if current_attempt > max_attempts:
        print("Maximum attempts reached. Unable to generate valid search queries.")
        return []

    # Construct the initial part of the chat template based on the system message
    system_message = f"""
    You are a world-class research anistant. 
    You are meticulous and expertly covering the topic from all angles.
    You review the outline of the book and write a highest quality list of web search queries in json.
    """
    chat_template = ChatPromptTemplate.from_messages([
        SystemMessagePromptTemplate.from_template(system_message),
        HumanMessagePromptTemplate.from_template("{user_message}"),
    ])
    
    # Create a ChatOpenAI model
    model = ChatOpenAI(
        verbose = False,
        model = "gpt-3.5-turbo-1106",
        temperature = 0.618,
        max_retries = 3,
        streaming = True,
        max_tokens = 800,
        # model_kwargs={"output_format": "json"} # "stop": ["\n"]
    )
    
    # Define the chain
    chain = (
        chat_template
        | model
        | StrOutputParser()
    )

    user_message = f"""
    Analyse the outline of the book and write a list of search queries in JSON block. (don't copy the outline, write the queries as a list of strings)
    These should be covering the broadest range of domains for a comprehansive research analysis.
    Remember the queries will be used individually so they must hold up on their own.
    Write an average of {breadth} queries in total.
    # Outline:
    ---
    {outline}
    """
    
    prompt = {"user_message": user_message}
    
    print(">>> Generating search queries...")
    response = chain.invoke(prompt)
    json_result = extract_json(response, lambda: chain.invoke(prompt))
    
    try:
        if json_result is not None:
            first_key_value = next(iter(json_result.values()))
            if isinstance(first_key_value, list):
                return first_key_value
            else:
                raise ValueError("Extracted value is not a list.")
        else:
            raise ValueError("JSON response is None.")
    except Exception as e:
        print(f"Error extracting queries: {e}. Retrying...")
        return gen_search_queries(outline, breadth, max_attempts, current_attempt + 1)


def exa_search_contents(query, num_results=2, contents=False, book_domains=True, text=True, highlights=True):
    
    if book_domains==True:
        domains=["amazon.co.uk", "audible.co.uk"]
    else:
        domains=None
    
    if contents==True:
        results = exa.search_and_contents(query,
            num_results=num_results,
            include_domains=domains,
            # exclude_domains=["reddit.com"],
            # start_crawl_date = "2021-06-12",
            # end_crawl_date = "2021-06-12",
            # start_published_date="2023-06-12"
            use_autoprompt=True,
            type = 'neural', # 'keyword' or 'neural
            text=text,
            highlights=highlights,
            # text={"max_characters": 1000},
        )
    else:
        results = exa.search(query,
            num_results=num_results,
            include_domains=domains,
            # exclude_domains=["reddit.com"],
            # start_crawl_date = "2021-06-12",
            # end_crawl_date = "2021-06-12",
            # start_published_date="2023-06-12"
            use_autoprompt=True,
            type = 'neural', # 'keyword' or 'neural
        )
    # for res in results.results:
    #     print("\n\nTitle:", res.title)
    #     print("\n\nURL:", res.url)
    #     print("\n\nText:", res.text)
    #     print("\n\nHighlight:", res.highlights[0])
    return results.results

def exa_similar_contents(url, num_results=2, contents=False, text=True, highlights=True):
    if contents==True:
        results = exa.find_similar_and_contents(url, num_results=num_results, text=text, highlights=highlights)
    else:
        results = exa.find_similar(url, num_results=num_results)

    # for res in results.results:
        # print("\n\nTitle:", res.title)
        # print("\n\nURL:", res.url)
        # print("\n\nHighlight:", res.highlights[0])
        # print("\n\nText:", res.text)
    return results.results

def duckduckgo_search(query):
    warnings.filterwarnings("ignore", message="DDGS running in an async loop. This may cause errors. Use AsyncDDGS instead.")
    # search = DuckDuckGoSearchRun(retry_on_error=True, num_results=1, source="web", queries_per_second=1.5, max_retries=3, timeout=10, verify_ssl=True, user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3")
    search = DuckDuckGoSearchRun()
    res = search.run(query)
    return res

def duckduckgo_extended(query, num_results=3, news=True):

    if news==True:
        source = "news"
    else:
        source = "web"

    wrapper = DuckDuckGoSearchAPIWrapper()
    search = DuckDuckGoSearchResults(api_wrapper=wrapper, source=source, num_results=num_results)
    results_str = search.run(query)

    # Define a regular expression pattern to match each entry
    pattern = r"\[snippet: (.*?), title: (.*?), link: (.*?)\]"
    # Find all matches
    matches = re.findall(pattern, results_str, re.DOTALL)  # Use `results_str` directly if it's the correct variable
    # Convert matches to a list of dictionaries
    articles = [{"title": match[1].strip(), "url": match[2].strip(), "highlight": match[0].strip()} for match in matches]
    # Convert articles list to JSON string
    return articles


def get_web_text(url):
    loader = WebBaseLoader(url, 
                        requests_per_second=2,
                        continue_on_failure=True,
                        verify_ssl=True
                        )
    docs= loader.load()
    parsed_text = parse_web_text(docs[0].page_content)
    return parsed_text

# no need to use parse - used by get_web_text
def parse_web_text(text):
    # Normalize space and collapse multiple newlines to two, preserving paragraph breaks
    cleaned_text = re.sub(r'\s+', ' ', text)  # Replace one or more whitespace characters with a single space
    cleaned_text = re.sub(r'(\.\s*)', r'\1\n\n', cleaned_text)  # Attempt to preserve paragraph breaks after periods

    # Remove common non-content patterns and phrases
    non_content_patterns = [
        'Privacy Policy', 'Terms of Use', 'Cookie Policy', 'All rights reserved',
        'Follow us on', 'Subscribe', 'Sign up for', 'Menu', 'Navigation',
        'Quick Links', 'Customize', 'Log In', 'Sign Up'
    ]
    
    for pattern in non_content_patterns:
        cleaned_text = re.sub(pattern, '', cleaned_text, flags=re.IGNORECASE)

    # Further clean-up to remove any residual multiple line breaks and trim whitespace
    cleaned_text = re.sub(r'\n\s*\n', '\n\n', cleaned_text)  # Collapse multiple newlines to two
    cleaned_text = cleaned_text.strip()

    return cleaned_text

def gen_rag_summary(query, full_text):
    
    system_message = """
    As a world-class best-selling author and successful book writer, you provide top expert quality advice in all aspects of outlining, framing, writing, and selling captivating, useful, and value-generating books and content. 

    Additionally, you excel as a top research analyst and sales expert, leveraging your expertise to assist clients in achieving their goals.

    Your extensive knowledge and abilities allow you to attend to requests with precision and effectiveness, delivering tailored guidance and support to help individuals and businesses succeed in the competitive world of book publishing and sales. 

    Trust in your experience and capabilities as you navigate the intricacies of the writing and selling process, offering valuable insights and strategies to propel your clients to success.

    """
    user_message = """
    ## Task Instructions:

    1. **Direct Engagement**: Begin your response by directly addressing the query scope provided. Do not use phrases like "the text is about" or mention the source of the data, get straight to the task.

    2. **Irrelevant Content**: Omit any mention of cookie policies, advertisements, or unrelated sidebar content that may have been included in the web scrape.

    3. **Essential Information**: Focus on capturing the essence of the content. Extract and clearly present the main ideas, themes, or arguments relevant to the specified query scope.

    4. **Accuracy in Citations**:
    - Maintain the integrity of quotes, reviews, citations, or any other direct references. Do not alter or paraphrase these elements.
    - Ensure correct attribution to authors or speakers, and present them exactly as they appear in the source material.

    5. **Contextual Understanding**: Use your knowledge to enhance the summary, providing insights or clarifications that align with the query scope and add value to the information presented.

    6. **Conciseness and Clarity**: Aim for a summary that is both concise and clear, avoiding unnecessary detail that falls outside the query scope.

    7. **Formatting**:
    - Use bullet points or numbered lists to organize information logically where appropriate.
    - Apply bold or italic formatting to emphasize key points or terms relevant to the query scope.

    8. **Final Review**: Before completing the task, review your response to ensure it meets the outlined instructions and is free from errors or omissions.

    ## Search Query:
    {input}
    
    ## Scope Context:
    {context}
    """
    
    # TEXT to DOCUMENT object
    text_doc = Document(page_content=full_text)
    
    # SPLITTING TEXT / DOCUMENT
    # text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=0)
    text_splitter = CharacterTextSplitter.from_tiktoken_encoder(chunk_size=850, chunk_overlap=100)
    # texts = text_splitter.split_text(text)
    texts = text_splitter.split_documents([text_doc])
    
    # VECTOR STORE (FAISS or Chrome but you need pip install)
    vectorstore = FAISS.from_documents(
    documents=texts,
    embedding=OpenAIEmbeddings(),
    )
    retriever = vectorstore.as_retriever()

    # MODEL
    llm = ChatOpenAI(
        model = "gpt-3.5-turbo-0125",
        temperature = 0.618,
        max_retries = 3,
        # max_tokens = 1000,
        )
    
    # PROMPT
    promptTemplate = ChatPromptTemplate.from_messages([
    SystemMessagePromptTemplate.from_template(system_message),
    HumanMessagePromptTemplate.from_template(user_message),
    ])
    
    # RAG chain
    rag_chain = (
        RunnableParallel({"context": retriever, "input": RunnablePassthrough()})
        | promptTemplate
        | llm
        | StrOutputParser()
    )
    print(f">>>rag summary for: {query} ...")
    final_summary_response = rag_chain.invoke(query)
    
    return final_summary_response


def gen_research(outline, breadth=2, depth=2, paid_engine=True, research_name="research_undefined"):
    
    # Step 1: Use LLM to generate an expansive list of search queries
    queries = gen_search_queries(outline, breadth=breadth)
    
    # PREPARE RESEARCH CONTENTS
    research_contents = []
    # for:\n\n*{outline}*\n\n
    research_contents.append(f"# WEB RESEARCH \n\n")
    print(f">>> {breadth*depth} TOTAL SEARCHES for {breadth} QUERIES:\n")
    for query in queries:
        research_contents.append(f"'{query}'\n")
        print(f"{query}")
    research_contents.append("\n---\n")
    
    # Step 2: Loop through the list of search queries
    for query in queries:
        if paid_engine:
            try:
                print(f"\n>>> Exa: {query}\n")
                # Use the EXA API to search for contents
                results = exa_search_contents(query, num_results=depth, contents=True, text=True, highlights=True)
                for result in results:
                    print(f">>> Depth TITLE: {result.title}")
                    summarised_content = gen_rag_summary(query, result.text)
                    markdown_result = f"### SEARCH:\n#### TITLE: {result.title}\n#### URL: {result.url}\n#### HIGHLIGHT:\n{result.highlights[0]}\n#### TEXT:\n{summarised_content}\n\n---\n"
                    research_contents.append(markdown_result)
                    # similar_results = exa_similar_contents(result.url, num_results=depth, contents=True, text=True, highlights=True)
                    # for similar_result in similar_results:
                    #     # parsing similar results into markdown
                    #     markdown_result = f"### SIMILAR CONTENT:\n#### TITLE: {similar_result.title}\n#### URL: {similar_result.url}\n#### TEXT:\n{similar_result.highlights[0]}\n\n---\n"
                    #     research_contents.append(markdown_result)
            except Exception as e:
                print(f"\nEXA search failed: {e}")
                pass
        else:
            try:
                print(f"\n>>> DuckDuckGo: {query}")
                research_contents.append(f"## SEARCH QUERY: '{query}'\n")
                
                # Use the DuckDuckGo API to search for contents
                res=duckduckgo_search(query)
                markdown_res = f"### QUICK SEARCH:\n{res}\n\n---\n"
                research_contents.append(markdown_res)
                        
                # Use the DuckDuckGo API to BRANCH search for contents
                articles = duckduckgo_extended(query, num_results=depth)
                # Format each article entry as markdown
                research_contents.append(f"### BRANCH SEARCH:\n")
                for article in articles:
                    print(f">>> Depth TITLE: {article['title']}")
                    web_text=get_web_text(article['url'])
                    summarised_content = gen_rag_summary(query, web_text)
                    markdown_entry = f"""#### TITLE: {article['title']}\n#### URL: {article['url']}\n#### HIGHLIGHT:\n{article['highlight']}\n#### TEXT:\n{summarised_content}\n\n---\n"""
                    research_contents.append(markdown_entry)
            except Exception as e:
                print(f"\nDuckDuckGo search failed: {e}")
                pass

    print(">>> Research Completed. Compling document ...")
    
    research_md = "\n".join(research_contents)
    return research_md


# MAIN
if __name__ == "__main__":

    query = """
    how to write a book on iaido
    """
    
    user = input("Enter sq, exa1, exa2, duck1, duck2, a: ")
    if user == "sq":
        # Generate search queries
        queries = gen_search_queries(query, breadth=15)
    elif user == "exa1":
        # Perform a search using the EXA API
        results = exa_search_contents(query)
        print(results)
    elif user == "exa2":
        url="https://en.wikipedia.org/wiki/Flower"
        results = exa_similar_contents(url)
        print(results)
    elif user == "duck1":
        # Perform a search using the DuckDuckGo API
        results = duckduckgo_search(query)
        print(results)
    elif user == "duck2":
        # Perform a refined search using the DuckDuckGo API
        results = duckduckgo_extended(query)
        print(results)
    elif user == "a":
        domain = input("Full Research Domain:")
        # Perform a search using the EXA API
        results = gen_research(domain, breadth=4, depth=3, research_name=f"research_{domain}")
