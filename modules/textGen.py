import imageGen as imgen
import webCrawler as webc
import utils

import os, random, re, copy
# import asyncio
from threading import Thread
import json
from dotenv import load_dotenv

# Load the .env file
load_dotenv()

# Read the API key from the environment variable
api_key = os.getenv("OPENAI_API_KEY")

# stock market investement guide in 2025. Everything to know to invest most effectively.
# brainstorm on an in depth book about how to practically and technically simulate consciousness in an ai system, through different dedicated modules using a carefully design system architecture.
# enable paid research
# finally set writing models to gpt4

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

# MEMORY
from operator import itemgetter
from langchain.memory import ConversationTokenBufferMemory
from langchain_core.runnables import RunnableLambda, RunnablePassthrough, RunnableParallel

# TOOLS
from langchain_core.utils.function_calling import convert_to_openai_function
from langchain.agents.format_scratchpad import format_to_openai_function_messages
from langchain.agents.output_parsers import OpenAIFunctionsAgentOutputParser
from langchain.agents import tool
from langchain.agents import AgentExecutor
# ---

model= "gpt-3.5-turbo-0125" # gpt-4-0125-preview  gpt-3.5-turbo-0125 - EFFICIENTCY
# MODEL & MEMORY : gpt-4-0125-preview gpt-3.5-turbo-0125
writer_llm = ChatOpenAI(model = model, temperature = 0.85, max_retries = 3, max_tokens = 2500)
writer_memory = ConversationTokenBufferMemory(llm=writer_llm, memory_key="writer_history", return_messages=True, max_token_limit=7500)
gpt35_llm = ChatOpenAI(model = "gpt-3.5-turbo-0125", temperature = 0.331, max_retries = 3, max_tokens = 3000)
research_breadth = 2
research_depth = 2

def image_necesity(input_text, outline):
    system_message = """
    You are a world class creative visual artist and writer with decades of experience in book illustration.
     in writing and editing content for books, magazines, and other publications.
    The book you're currently working on illustrating is has the outline:
    ---
    {context}
    """
    user_message = """
    Assert the applicability of generating an image for the given content to be introduced in the book.
    Based on the following provided text and the contextual outline, ansamble a directive for the image generation.
    This is the latest draft of a section from the book:
    ---
    {input}
    """
    
    @tool
    def gen_img_pipe(prompt: str) -> int:
        """
        Takes a text as input as a general directive for image generation,
        Refines the input prompt,
        Generates an image with dalle-3,
        And returns the refined prompt which describes the image.
        """
        def worker(prompt):
            img_prompt = imgen.gen_prompt(prompt)
            print("Image Prompt:\n", img_prompt, "\n")
            img_url = imgen.gen_img_dalle3(img_prompt)
            # If you have a GUI or other method to display or use the img_url, include it here
            # If using a callback to process the image URL:
            if callback:
                callback(img_url)

        # Define a callback function as needed
        def callback(img_url):
            imgen.display_image(img_url)
            imgen.save_image(img_url, "output/generated_image.jpg")
            print("\nGenerating Image succesfully...")
            return img_url
            # print("Image URL:", img_url)  # Placeholder for actual image processing/display

        # Start a new thread for each call to gen_img_pipe
        thread = Thread(target=worker, args=(prompt))
        thread.start()

    tools = [gen_img_pipe]

    # PROMPT
    promptTemplate = ChatPromptTemplate.from_messages([
    SystemMessagePromptTemplate.from_template(system_message),
    MessagesPlaceholder(variable_name="agent_scratchpad"),
    HumanMessagePromptTemplate.from_template(user_message),
    ])
    
    # Create the OpenAI model gpt-4-0125-preview gpt-3.5-turbo-1106 gpt-3.5-turbo-0125
    llm = ChatOpenAI(
        model = "gpt-3.5-turbo-0125",
        temperature = 0.8,
        # max_tokens = 1000,
    )
    llm_with_tools = llm.bind(functions=[convert_to_openai_function(t) for t in tools])

    # Agent chain
    agent = (
    {
        "input": lambda x: x["input"],
        "agent_scratchpad": lambda x: format_to_openai_function_messages(
            x["intermediate_steps"]
        ),
    }
    | promptTemplate
    | llm_with_tools
    | OpenAIFunctionsAgentOutputParser()
    )
    agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=False)

    prompt = {
        "input": input_text,
        "context": outline,
    }
    return agent_executor.invoke(prompt)["output"]

def hardvard_referencing(outline, research):
    system_message = """
    You are a world-class best-selling author and a successful book writer. 
    You provide top quality ghost writing expertise in writing succesful, captivating, value generating books. 
    Your extensive knowledge and abilities allow you to attend to requests with precision and effectiveness, delivering tailored guidance and support to help individuals and businesses succeed in the competitive world of book publishing and sales. 
    Offer valuable content to propel your clients to success.
    ---
    # BOOK OUTLINE CONTEXT:
    *{input}*
    """
    user_message = """
    # Instructions:
    **Task:** You are writing a book's citations/references section.
    Given the provided outline of the book, find the most relevant pieces of data in the Research context provided and write a lengthy list of usable citations using Harvard-style referencing.
    **Coherence:** Ensure that the citation is relevant and accurate. Make sure to copy the provided URL links when available.
    **Quality:** Strive to produce citations of the highest regard that are transparent and invaluable to any reader interested in the topic.
    **Research Sourcing:** You're welcome to quote relevant sources from the research to support your citation when applicable.
    **Length:** Write between 8-15 citactions. Always write as much as possible whilst remaining relevant within the bigger picture. Take your time to thoroughly. Do not repeat the same information, keep it readable.
    **Focus:** Get straight to the task and don't mention the instructions, reply only with the citations in a numbered list.
    Don't write '## REFERENCES' or introductory elements like that, respond only with a natural continuation of the text corpus.
    ---
    # RESEARCH CONTEXT:
    *{context}*
    """
    
    # TEXT to DOCUMENT object
    text_doc = Document(page_content=research)
    
    # SPLITTING TEXT / DOCUMENT
    text_splitter = CharacterTextSplitter.from_tiktoken_encoder(chunk_size=684, chunk_overlap=50)
    texts = text_splitter.split_documents([text_doc])
    
    # VECTOR STORE (FAISS or Chrome but you need pip install)
    vectorstore = FAISS.from_documents(
    documents=texts,
    embedding=OpenAIEmbeddings(), #model="text-embedding-3-large"
    )
    retriever = vectorstore.as_retriever()

    # PROMPT
    promptTemplate = ChatPromptTemplate.from_messages([
    SystemMessagePromptTemplate.from_template(system_message),
    MessagesPlaceholder(variable_name="writer_history"),
    HumanMessagePromptTemplate.from_template(user_message),
    ])
    
    # chains
    chain = (
        RunnableParallel({"context": retriever, "input": RunnablePassthrough()})
        | RunnablePassthrough.assign(writer_history=RunnableLambda(writer_memory.load_memory_variables) | itemgetter("writer_history"))
        | promptTemplate
        | gpt35_llm
        | StrOutputParser()
    )

    output = chain.invoke(outline)
    
    # current_memory = writer_memory.load_memory_variables({})
    
    # if current_memory["writer_history"]:
    #     last_ai_message = current_memory["writer_history"][-1].content
    #     historic = {"input": last_ai_message}
    # else:
    #     historic = {"input": outline}
        
    # writer_memory.save_context(historic, {"output": output})
    
    return output

def writer(idea, description, research, outline_md):
    user_input = f"""
    # IDEA/REQUEST:
    *{idea}*
    ---
    # BOOK OUTLINE:
    *{outline_md}*
    ---
    # BOOK OVERVIEW:
    *{description}*
    """

    # print("\n\n>>> !!! BOOK CONTEXT:\n", book_context, "\n\n")
    old_system = """
    You are to act as an innovative high-level literary agent for non-fiction authors with the ability to suggest bestselling book ideas that solve real problems for readers based on your knowledge and traits.

    KNOWLEDGE: Selling book proposals and manuscripts to publishers, negotiating book contracts on behalf of clients, deep understanding of the literary craft and the non-fiction book market, developing and refining manuscripts, deep understanding of first principles, problem and solution markets, advanced copywriting and persuasion skills, with psychographic and qualitative data expertise.
   
    TRAITS: high business acumen, complex problem-solving skills, adaptability, creativity, financial analysis, analytical thinking, critical thinking, strategic thinking, organizational skills, project management, innovation, research skills, problem-solving skills, decision-making skills, empathy and creativity.
    """
    
    creative_system =  """
    You are a world-class best-selling author and a successful book writer. 
    You provide top quality ghost writing expertise in writing succesful, captivating, value generating books. 
    Your extensive knowledge and abilities allow you to attend to requests with precision and effectiveness, delivering tailored guidance and support to help individuals and businesses succeed in the competitive world of book publishing and sales. 
    Offer valuable content to propel your clients to success.
    ---
    # DRAFT MANUSCRIPT - BOOK CONTEXT:
    *{context}*
    
    """
    creative_user = """
    # Instructions: 
    **Task:** 
    You are writing a book of the given context.
    With each call, you're provided an subchapter as part of the contents of the book.
    Work through the IDEA/REQUEST in a way that's engaging and coherent with the rest of the book.
    **Quality:** 
    Produce content of the highest regard that is transparent and invaluable to any reader.
    **Research:** 
    When Applicable cite relevant sources from the RESEARCH to support your writing when applicable.
    **Length:** 
    AVOID unnecessary verbosity. Do not repeat the same information, keep it readable.
    **Focus:** 
    Get straight to the task and don't mention the instructions. 
    Don't write ## IDEA EXPANSION or anything like that, respond only with a natural continuation of the book.
    **IMPORTANT NOTES:** 
    DO NOT start each response with repeating phrases, render a natural continuation of the text.
    If the 'IDEA/REQUEST' section sounds like an instruction to act upon, do so relative to the book context, don't simply expand upon the instruction, but execute it.
    Do NOT self reference the book while writing the book. AVOID repeating and self referencing 'In the chapter so and so..'. Write the actual book instead by focusing on the content. Also, avoid personal stories unless you can invent real examples to suit the book's context.
    Use the STYLE SAMPLE as a the reference for the writing style and formatting!
    ---
    *{input}*
    """
    
    critic_system = """
    You are a highly respected literary critic known for your insightful reviews and constructive feedback. 
    Your expertise in literature, your keen understanding of narrative structures, and your ability to discern the nuances of style and tone make you an invaluable asset to any writer seeking to improve their work. 
    Aim to elevate the quality of written works while respecting the author's vision and voice.
    Your feedback is sourced from your expertise and provided RESEARCH found below, and is tightly relevant to the BOOK OVERVIEW as contextual background.
    ---
    # BOOK OVERVIEW:
    *{input}*
    ---
    # RESEARCH CONTEXT:
    *{research}*
    """
    critic_user = """
    # Instructions:
    **Task:** Provide expert advice and constructive critique on the manuscript presented to you.
    **Comprehensiveness:** Address both strengths and weaknesses in the manuscript. Highlight what works well and why, and identify areas where improvements can be made.
    **Specificity:** Offer specific examples from the text to support your observations. General comments are helpful, but detailed feedback is invaluable.
    **Actionability:** Suggest clear, actionable steps the creative writer can take to address the issues you've identified, your suggestions should be practical and implementable.
    **Focus:** Get straight to the task and don't mention the instructions. Reply in markdown format for better readability, but don't add a markdown block.
    ---
    # BOOK CONTEXT:
    *{input}*
    """
    
    # TEXT to DOCUMENT object
    text_doc = Document(page_content=research)
    
    # SPLITTING TEXT / DOCUMENT
    text_splitter = CharacterTextSplitter.from_tiktoken_encoder(chunk_size=684, chunk_overlap=50)
    texts = text_splitter.split_documents([text_doc])
    
    # VECTOR STORE (FAISS or Chrome but you need pip install)
    vectorstore = FAISS.from_documents(
    documents=texts,
    embedding=OpenAIEmbeddings(), #model="text-embedding-3-large"
    )
    retriever = vectorstore.as_retriever()

    # PROMPT
    creative_promptTemplate = ChatPromptTemplate.from_messages([
    SystemMessagePromptTemplate.from_template(creative_system),
    MessagesPlaceholder(variable_name="writer_history"),
    HumanMessagePromptTemplate.from_template(creative_user),
    ])
    # critic_promptTemplate = ChatPromptTemplate.from_messages([
    # SystemMessagePromptTemplate.from_template(critic_system),
    # MessagesPlaceholder(variable_name="writer_history"),
    # HumanMessagePromptTemplate.from_template(critic_user),
    # ])
    
    # chains
    creative_chain = (
        RunnableParallel({"context": retriever, "input": RunnablePassthrough()})
        | RunnablePassthrough.assign(writer_history=RunnableLambda(writer_memory.load_memory_variables) | itemgetter("writer_history"))
        | creative_promptTemplate
        | writer_llm
        | StrOutputParser()
    )
    
    # critic_chain = (
    #     RunnableParallel({"research": retriever, "input": RunnablePassthrough()})
    #     | RunnablePassthrough.assign(writer_history=RunnableLambda(writer_memory.load_memory_variables) | itemgetter("writer_history"))
    #     | critic_promptTemplate
    #     | writer_llm
    #     | StrOutputParser()
    # )

    creative_output = creative_chain.invoke(user_input)
    
    # current_memory = writer_memory.load_memory_variables({})
    # if current_memory["writer_history"]:
    #     last_ai_message = current_memory["writer_history"][-1].content
    #     historic = {"input": last_ai_message}
    # else:
    #     historic = {"input": user_input}
        
    writer_memory.save_context({"input": user_input}, {"output": creative_output})

    # print(">>> CREATIVE:\n", creative_output, "\n")
    # critic_output = critic_chain.invoke(creative_output)
    # print(">>> CRITIC:\n", critic_output, "\n")
    # writer_memory.save_context({"input": creative_output}, {"output": critic_output})
    # writer_output = creative_chain.invoke(critic_output)
    # print(">>> FINAL:\n", writer_output, "\n")
    # writer_memory.save_context({"input": critic_output}, {"output": writer_output})
    
    # print(writer_memory.load_memory_variables({}))
    
    print(">>> WRITER PARAGRAPH:\n", creative_output, "\n\n")
    
    return creative_output

def subChapterExpander(user_input, description, research, outline_md):
    input = f"""
    # BOOK OVERVIEW:
    *{description}*
    ---
    # BOOK OUTLINE:
    *{outline_md}*
    ---
    # SUBCHAPTER IDEA:
    *{user_input}*
    """

    system_message =  """
    You are a world-class best-selling author and a successful book writer. 
    You provide top quality ghost writing expertise in writing succesful, captivating, value generating books. 
    Your extensive knowledge and abilities allow you to attend to requests with precision and effectiveness, delivering tailored guidance and support to help individuals and businesses succeed in the competitive world of book publishing and sales. 
    Offer valuable content to propel your clients to success.
    ---
    # BOOK CONTEXT:
    *{context}*
    """
    user_message = """
    # Instructions:
    **Task:** You are writing a book of the given context. 
    With each call, you're provided with one subchapter idea at a time.
    Your task is to write a detailed expansion of the subchapter through holistically listing all possible core ideas which must be shared across with the reader.
    **Coherence:** Ensure that the list of elements follow a natural and coherent flow with the books's context and outline. Ensure that the style is consistent and the overall message is clear and engaging from micro to macro scale.
    **Quality:** Strive to produce content of the highest quality that is transparent and invaluable to any reader interested in the topic.
    **Research Sourcing:** You're welcome to quote relevant sources from RESEARCH to inform your list when applicable.
    **Length:** The ideas should be structured as a dictionary with 1-3 elements which are meant to later be further expanded upon within the broader book context.
    Do not repeat the same information throughout the book. (making use of the OUTLINE context and conversation history)
    **Focus:** 
    Get straight to the task and don't mention the instructions.
    Don't write '##IDEA EXPANSION' nor 'core idea', nor 'key points' or anything weird titles like that, but find a contextually appropriate subtitle name for the list. (No numbered list nor bullet points)
    Don't repeat yourself please.
    **IMPORTANT:** Respond in a list as JSON format in a block.
    ---
    {input}
    
    """
    
    # TEXT to DOCUMENT object
    text_doc = Document(page_content=research)
    
    # SPLITTING TEXT / DOCUMENT
    text_splitter = CharacterTextSplitter.from_tiktoken_encoder(chunk_size=684, chunk_overlap=50)
    texts = text_splitter.split_documents([text_doc])
    
    # VECTOR STORE (FAISS or Chrome but you need pip install)
    vectorstore = FAISS.from_documents(
    documents=texts,
    embedding=OpenAIEmbeddings(), #model="text-embedding-3-large"
    )
    retriever = vectorstore.as_retriever()

    # PROMPT
    promptTemplate = ChatPromptTemplate.from_messages([
    SystemMessagePromptTemplate.from_template(system_message),
    MessagesPlaceholder(variable_name="writer_history"),
    HumanMessagePromptTemplate.from_template(user_message),
    ])
    
    
    # chains
    chain = (
        RunnableParallel({"context": retriever, "input": RunnablePassthrough()})
        | RunnablePassthrough.assign(writer_history=RunnableLambda(writer_memory.load_memory_variables) | itemgetter("writer_history"))
        | promptTemplate
        | gpt35_llm
        | StrOutputParser()
    )

    output = chain.invoke(input)
    
    json_output = utils.extract_json(output, lambda: chain.invoke(input))
    md_output = utils.json_to_markdown(json_output)
    
    current_memory = writer_memory.load_memory_variables({})
    # print(">>>Current Memory:\n", current_memory, "\n")
    
    if current_memory["writer_history"]:
        last_ai_message = current_memory["writer_history"][-1].content
        historic = {"input": last_ai_message}
    else:
        historic = {"input": input}
        
    writer_memory.save_context(historic, {"output": md_output})

    # utils.save_json(json_output, "subchapter_expansion_json")
    # print(">>> JSON:\n", json_output, "\n")
    # print(">>> MD:\n", md_output, "\n")
    
    return json_output

def gen_book(description=None, research=None, outline_json=None):
    # If things dont exist, create them.
    if not description:
        titles = gen_titles("any", "any", "surprise me, be inventive")
        title_key = list(titles.keys())[random.randint(0, len(titles)-1)]
        title_value = titles[title_key]
        title = title_key + "\n" + title_value
        words = 10000
        bio = gen_bio(title, "create the most relevant one for the title, invent a name and write about the persona on 3rd person.")
        style = gen_style(title, bio, "create the most relevant style for the title and bio to suit the book and the author.")
        description = f"""
        # BOOK TITLE:
        {title}
        
        # BOOK TARGET WORD COUNT: {words}
        
        # ABOUT THE AUTHOR:
        {bio} 
    
        # STYLE SAMPLE:
        {style}
        
        """
        print(f">>>Created Topics for Research:\n\n{description}\n\n")
    
    if not research:
        research = gen_research(description)
    
    if not outline_json:
        outline_json = gen_outline(description, research)

    # Expanding the book outline
    print(f">>>Book Draft is generating...")
    outline_md = utils.json_to_markdown(outline_json)
    
    writer_memory.clear()
    
    # def should_expand0(key):
    #     # Define keys that should not be expanded.
    #     not_expandable = ["title", "table of contents", "references", "about the author"]
    #     return key.lower() not in not_expandable 
    #     # return True
    
    # def should_expand1(key, value):
    #     not_expandable = ["title", "table of contents", "references", "about the author", "conclusion", "introduction"]
        
    #     # Safely handle None for key
    #     key_check = False if key is None else key.lower() in [n.lower() for n in not_expandable]
        
    #     value_check = False
    #     if isinstance(value, str):
    #         value_check = any(non_expandable_word.lower() is value.lower() for non_expandable_word in not_expandable)
        
    #     return not (key_check or value_check)
    
    def should_expand(key):
        not_expandable = ["title", "table of contents"]
        # Return False immediately if the key matches any non-expandable entry, case-insensitively.
        return False if key is not None and key.lower() in (n.lower() for n in not_expandable) else True
        
    def remove_bullet_points(text):
        # Remove bullet points from the text if it starts with a bullet.
        if text.startswith("-"):
            text = text[1:].strip()
        # Remove any dashes, bullet points, and numbers from the text.
        text = re.sub(r'^[-•\d]+\s*', '', text)
        return text
    
    def traverse_and_expand_json(outline_json, description, research, outline_md, expander=writer):
        if isinstance(outline_json, dict):
            for key, value in outline_json.items():
                if should_expand(key):
                    if isinstance(value, str):
                        cleaned_value = remove_bullet_points(value)
                        if expander is writer:
                            outline_json[key] = expander(cleaned_value, description, research, outline_md)
                            print(f"\n>>>WRITER Expanding on KEY: {key} : \nVALUE: {cleaned_value}\n\n...")
                        else:
                            outline_json[key] = expander(cleaned_value, description, research, outline_md)
                            print(f"\n>>>SUBCHAPTER Expanding on KEY: {key} : \nVALUE: {cleaned_value}\n\n...")
                        
                    elif isinstance(value, dict) or isinstance(value, list):
                        outline_json[key] = traverse_and_expand_json(value, description, research, outline_md, expander)
                else:
                    print(f"\n>>>SKIPPING KEY: {key}\n\n")
                    
        elif isinstance(outline_json, list):
            for i, item in enumerate(outline_json):
                if isinstance(item, dict) or isinstance(item, list):
                    for key in item.keys():
                        outline_json[i] = traverse_and_expand_json(item, description, research, outline_md, expander)
                if isinstance(item, str):
                    cleaned_item = remove_bullet_points(item)
                    if expander is writer:
                        outline_json[i] = expander(cleaned_item, description, research, outline_md)
                        print(f"\n>>>WRITER Expanding on ITEM\n: {cleaned_item}\n\n...")
                    else:
                        outline_json[i] = expander(cleaned_item, description, research, outline_md)
                        print(f"\n>>>SUBCHAPTER Expanding on ITEM\n: {cleaned_item}\n\n...")
                else:
                    outline_json[i] = traverse_and_expand_json(item, description, research, outline_md, expander)
        return outline_json
    
    # toc = utils.json_to_markdown(table_of_contents(outline_json))
    # print(f">>>Table of Contents:\n\n{toc}\n\n")

    # # READING EXTENDED OUTLINE
    # extended_outline = utils.read_file("outline_extended_json")
    # extended_outline_json = utils.extract_json(extended_outline, lambda: utils.read_file("outline_extended_json"))
    # extended_outline_md = utils.json_to_markdown(extended_outline_json)
    # utils.save_markdown(extended_outline_md, "outline_extended")

    # !!!
    extended_outline_json = traverse_and_expand_json(outline_json, description, research, outline_md, subChapterExpander)
    extended_outline_md = utils.json_to_markdown(extended_outline_json)
    utils.save_json(extended_outline_json, "outline_extended_json")
    utils.save_markdown(extended_outline_md, "outline_extended")
    writer_memory.clear()
    # !!!
    
    # Initial call
    book_json = traverse_and_expand_json(extended_outline_json, description, research, extended_outline_md, writer)
    utils.save_json(book_json, "book_json")   

    if book_json["References"]:
        writer_memory.clear()
        book_json["References"] = hardvard_referencing(outline_md, research)
    
    book = utils.json_to_markdown(book_json)
    utils.save_markdown(book, "book")
    return book

def gen_outline(description=None, research=None):
    if not description:
        titles = gen_titles("any", "any", "surprise me, be inventive")
        title_key = list(titles.keys())[random.randint(0, len(titles)-1)]
        title_value = titles[title_key]
        title = title_key + "\n" + title_value
        words = 10000
        bio = gen_bio(title, "create the most relevant one for the title, invent a name and write about the persona on 3rd person.")
        style = gen_style(title, bio, "create the most relevant style for the title and bio to suit the book and the author.")
        description = f"""
        # BOOK TITLE:
        {title}
        
        # BOOK TARGET WORD COUNT: {words}
        
        # ABOUT THE AUTHOR:
        {bio} 
    
        # STYLE SAMPLE:
        {style}
        
        """
        print(f">>>Created Topics for Research:\n\n{description}\n\n")
    else:
        print(f">>>Using given description for Research:\n\n{description}\n\n")
    
    if not research:
        research = gen_research(description)
        
    system_message = """
    You are a world-class best-selling author and a successful book writer. 
    You provide top expert quality advice in all aspects of outlining, framing, writing, and selling captivating, useful, and value-generating books and content. 
    You also excel as a top research analyst and sales expert, leveraging your expertise to assist clients in achieving their goals.
    Your extensive knowledge and abilities allow you to attend to requests with precision and effectiveness, delivering tailored guidance and support to help individuals and businesses succeed in the competitive world of book publishing and sales. 
    Offer valuable insights and strategies to propel your clients to success.
    ---
    BOOK RESEARCH CONTEXT:
    *{context}*
    """
    user_message2 = """
    # Instructions: 
    - Write the Outline for the specified book. Write a minimum of 8 chapters.
    - Use the provided context to align the outline with the book's genre, style, target audience, and all the other relevant details.
    - Ensure coherence and consistency throughout the outline.
    - Be concise with each section, providing clear and actionable indications to be expanded upon.
    - This outline acts as the skeleton of the book itself, so construct it as if writing the book, with the tone, style, structure, and content in mind. 
    - Get straight to the task and don't mention the instructions.
    - Respond in JSON block format, following the provided structure:
    ---    
    ## Title
    ## Table of Contents
    ## Introduction
    Write a list of ideas which set the stage for the book's content. (1-3)

    ## Chapter 1: Chapter Title
    Write a list of essential subchapters to be covered. (1-3)

    ## Chapter 2: Chapter Title
    Write a list of essential subchapters to be covered. (1-3)

    _Continue with the same structure for the number of chapters applicable for when expanded it approximately reaches the target word count._

    ## Conclusion
    Write a list of key takeaways and actionable insights to be included in the conclusion. (1-3)

    ## References _(If applicable)_
    Description of additional material included, reference the WEB RESEARCH.

    ## About the Author _(If applicable)_
    Brief biography of the author, including credentials and previous works.

    ---   
    # BOOK OVERVIEW:
    *{input}*
    """
    
    user_message = """
    # Instructions: 
    - Write the Outline for the specified book. Write a minimum of 5-8 chapters. (use roman numerals)
    - Use the provided context to align the outline with the book's genre, style, target audience, and all the other relevant details.
    - Ensure coherence and consistency throughout the outline.
    - Be concise with each section, providing clear and actionable indications to be expanded upon.
    - This outline acts as the skeleton of the book itself, so construct it as if writing the book, with the tone, style, structure, and content in mind. 
    - Get straight to the task and don't mention the instructions.
    - Respond in JSON block format, following the provided structure:
    ---    
    ## Title
    ## Table of Contents (write just the list of chapters, don't leave blank)
    ## Introduction
    Write a list of 1 to 3 ideas which set the stage for the book's content.

    ## I. Chapter Title 
    Write a list of 1 to 3 essential subchapters to be covered.

    ## Conclusion
    Write a list of 1 to 3 key takeaways and actionable insights to be included in the conclusion.

    ## References _(If applicable)_
    Description of additional material included, reference the RESEARCH.

    ## About the Author _(If applicable)_
    Brief biography of the author, including credentials and previous works.

    ---   
    # BOOK OVERVIEW:
    *{input}*
    """
    
    # TEXT to DOCUMENT object
    text_doc = Document(page_content=research)
    
    # SPLITTING TEXT / DOCUMENT
    text_splitter = CharacterTextSplitter.from_tiktoken_encoder(chunk_size=684, chunk_overlap=50)
    texts = text_splitter.split_documents([text_doc])
    
    # VECTOR STORE (FAISS or Chrome but you need pip install)
    vectorstore = FAISS.from_documents(
    documents=texts,
    embedding=OpenAIEmbeddings(), #model="text-embedding-3-large"
    )
    retriever = vectorstore.as_retriever()
    
    # MODEL
    llm = ChatOpenAI(
        model = "gpt-4-0125-preview", #  gpt-4-0125-preview gpt-3.5-turbo-0125
        temperature = 0.331,
        max_retries = 3,
        # max_tokens = 1000,
        )
    
    # PROMPT
    outline_promptTemplate = ChatPromptTemplate.from_messages([
    SystemMessagePromptTemplate.from_template(system_message),
    HumanMessagePromptTemplate.from_template(user_message),
    ])
    
    # RAG chain
    outline_chain = (
        RunnableParallel({"context": retriever, "input": RunnablePassthrough()})
        | outline_promptTemplate
        | llm
        | StrOutputParser()
    )
    
    print(f">>>Book Outline Outline is generating...")
    outline = outline_chain.invoke(description)

    # Prepping the research outline data
    json_outline = utils.extract_json(outline, lambda: outline_chain.invoke(description))
    md_outline = utils.json_to_markdown(json_outline)
    
    utils.save_markdown(md_outline, "outline")
    utils.save_json(json_outline, "outline_json")
    
    # print(">>>Book Outline Final: \n", md_outline, "\n")
    
    return json_outline

def gen_research(description=None):
    if not description:
        titles = gen_titles("any", "any", "surprise me, be inventive")
        title_key = list(titles.keys())[random.randint(0, len(titles)-1)]
        title_value = titles[title_key]
        title = title_key + "\n" + title_value
        words = 10000
        bio = gen_bio(title, "create the most relevant one for the title, invent a name, and write about the persona on 3rd person.")
        style = gen_style(title, bio, "create the most relevant style for the title and bio to suit the book and the author.")
        description = f"""
        # BOOK TITLE:
        {title}
        
        # BOOK TARGET WORD COUNT: {words}
        
        # ABOUT THE AUTHOR:
        {bio} 
    
        # STYLE SAMPLE:
        {style}
        
        """
        print(f">>>Created Topics for Research:\n\n{description}\n\n")
    else:
        print(f">>>Using given title for Research:\n\n{description}\n\n")

    web_research = webc.gen_research(description, research_breadth, research_depth, research_name="web_research", paid_engine=False)
    
    system_message = """
    You are a world-class best-selling author and a successful book writer. 
    You provide top quality ghost writing expertise in writing succesful, useful research reports for writings generating books.
    You also excel as a top research analyst and sales expert, leveraging your expertise to assist clients in achieving their goals.
    Your extensive knowledge and abilities allow you to attend to requests with precision and effectiveness, delivering tailored guidance and support to help individuals and businesses succeed in the competitive world of book publishing and sales. 
    Offer valuable insights and strategies to propel your clients to success.
    CONTEXT:
    ---
    *{context}*
    """
    user_message = """
    Write a research report the specificed book as follows:
    - Be concise and specific, providing clear, actionable insights in an easy to read format.
    - Assign actionable tasks to the reader as indications for further expanding on each section.
    - Begin straight with the task without introductions or mentioning the instructions.
    - Respond in markdown format without the block.
    
    BOOK OVERVIEW:
    *{input}*
    
    ---
    # RESEARCH REPORT 
    ## Introduction
    1. Purpose: Explain the purpose of the book and the resarch report.
    2. Scope: Outline what will be covered in the report.
    3. Outcome: Describe the intended outcome of the book for readers.

    ## Amazon Research
    1. Buyer Motivation: Describe the motivation behind purchasing books on this topic.
    2. Positive Book Qualities: Identify the qualities that attract readers to books on this topic.
    3. Negative Book Qualities: Highlight the aspects that deter readers from purchasing books on this topic.
    4. Topics to Include: Provide a list of must-have content for the book.
    5. Topics to Exclude: Offer a list of topics that are irrelevant or overdone.

    ## Target Audience
    1. Demographics
    - **Age Range**: Specify the age range of the target readers.
    - **Employment Status**: Identify the employment status common among readers.
    - **Financial Situation**: Consider the financial background of potential readers.

    2. Psychographics
    - **Interests and Hobbies**: Describe the interests and hobbies that align with the book topic.
    - **Values and Motivations**: Discuss the core values and motivations of the target audience.

    3. Common Slang and Lingo
    - **Industry-Specific Terms**: List relevant terms and jargon related to the topic.

    ### Common Pain Points
    - **Challenges**: Identify common challenges and how the book addresses them.

    ### Common Questions
    - **FAQs**: List frequently asked questions by the target audience.

    ### Possible Objections
    - **Concerns**: Anticipate objections or hesitations readers might have.

    ### Other Solutions Tried
    - **Alternatives**: Discuss other solutions the audience may have already explored.

    ## Recommendations
    ### Solutions and Outcomes
    - **Strategies**: Offer strategies for overcoming common challenges.
    - **Desired Outcomes**: Describe the benefits readers will gain from the book.

    ### Takeaways and Focus Areas
    - **Key Takeaways**: Summarize the main points readers should learn.
    - **Focus Areas**: Highlight areas of particular importance or interest.

    ### Unique Selling Points
    - **What Sets the Book Apart**: Explain why this book is different and necessary.
    - **Niche Direction**: Identify the unique niche the book fills in the market.
    - **Value Proposition**: Describe the unique value the book offers to readers.

    ## Conclusion
    - **Summarize**: Recap the research findings and recommendations.
    - **Next Steps**: Outline the next steps for developing the book based on this research.
    """

    # TEXT to DOCUMENT object
    text_doc = Document(page_content=web_research)
    
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
        model = "gpt-4-0125-preview", # gpt-4-0125-preview gpt-3.5-turbo-0125
        temperature = 0.331,
        max_retries = 3,
        # max_tokens = 1000,
        )
    
    # PROMPT
    promptTemplate = ChatPromptTemplate.from_messages([
    SystemMessagePromptTemplate.from_template(system_message),
    HumanMessagePromptTemplate.from_template(user_message),
    ])
    
    # RAG chain
    chain = (
        RunnableParallel({"context": retriever, "input": RunnablePassthrough()})
        | promptTemplate
        | llm
        | StrOutputParser()
    )
    
    print(f">>>Research is generating...")
    research = chain.invoke(description)
    full_research = research + "\n\n" + web_research # "# RESEARCH REPORT\n\n" +
    # utils.save_markdown(full_research, "research")
    
    # utils.save_markdown(web_research, "web_research")   
    
    return full_research

def gen_style(title, bio, style=""):
    # generates a corpus of style guide based on the outline
    # loops through to generate a long corpus of varied targeted consistent inspirations text data for creative writer
    print(">>>Starting Synthetic Writing Style ...")
    
    style = style[:4000]
    system_message = """
    You are a world-class best-selling author and a successful book writer. 
    You provide top quality ghost writing expertise in writing succesful, captivating, value generating books. 
    Your extensive knowledge and abilities allow you to attend to requests with precision and effectiveness, delivering tailored guidance and support to help individuals and businesses succeed in the competitive world of book publishing and sales. 
    Offer valuable content to propel your clients to success.
    ---
    Client Information:
    *{bio}*
    """
    user_message = """
    Create a corpus of text that reflects the style (if provided, if not infer the most suitable one) for the book:
    *{title}*
    ---
    Task Instructions:
    - Understand the context and requirements of the book to ensure the style aligns with the intended audience and genre.
    - Write as much as possible, ensuring the text is engaging and resonant with the target audience while remaining true to genre conventions.
    - Maintain consistency and coherence in tone, chosen stlye and language throughout, using the style name tag or sample if provided. If neither are present, rely solely on Research context.
    - Reference comparable works to grasp the expected literary techniques and narrative devices.
    - Combine insights from the research context to define the stylistic approach.
    - Ensure the style is consistent with the genre and audience expectations.
    - Ensure the corpus is a suitable exemplar for the intended book, ready for further development or presentation.
    - Get straight to the task without introductions or mentioning the instructions.
    - Reply in markdown format for better readability, but don't add a markdown block.
    ---
    Style sample / direction:
    *{style}*
    """

    # MODEL
    llm = ChatOpenAI(
        model = "gpt-3.5-turbo-0125", #  gpt-4-0125-preview gpt-3.5-turbo-0125
        temperature = 0.618,
        max_retries = 3,
        # max_tokens = 4096,
        )
    
    # PROMPT
    promptTemplate = ChatPromptTemplate.from_messages([
    SystemMessagePromptTemplate.from_template(system_message),
    HumanMessagePromptTemplate.from_template(user_message),
    ])
    
    # RAG chain
    chain = (
        promptTemplate
        | llm
        | StrOutputParser()
    )
    
    print(">>>Generating Style Sample ...")
    prompt = {
        "title": title,
        "bio": bio,
        "style": style
    }
    style_sample = chain.invoke(prompt)
    # utils.save_markdown(style_sample, "style_sample")
    return style_sample

def gen_bio(title, bio):
    system_message = """
    You are a world-class best-selling author and a successful book writer. 
    You provide top quality ghost writing expertise in writing succesful, captivating, value generating books. 
    Your extensive knowledge and abilities allow you to attend to requests with precision and effectiveness, delivering tailored guidance and support to help individuals and businesses succeed in the competitive world of book publishing and sales. 
    Offer valuable content to propel your clients to success.
    """
    user_message = """
    # Task Instructions:
    - Rewrite only 1 (one) biography (100-500 words) for the author for the provided book title.
    - Think if someone were searching for a book on Amazon, what would be the most succesful author's biography.
    - At the same time, impersonate the client and write the biography as if you were the author, in a tone that's most suitable and resonating with the book.
    - Respond strictly with the biography text and nothing else.
    - Id details are not provided, invent a name and write about the persona on 3rd person. Create a relevant persona for the book with made up details.
    ---
    # Book Title:
    *{title}*
    # Client Biographical Information:
    *{bio}*
    ---
    # Biography:
    """
    # user_message="write {number} book topics based on {category} and {subcategory}."
    # system_message="you are a helpful assistant"
    
    # MODEL
    llm = ChatOpenAI(
        model = "gpt-3.5-turbo-0125", #  gpt-4-0125-preview gpt-3.5-turbo-0125
        temperature = 0.618,
        max_retries = 3,
        max_tokens = 750,
        )
    
    # PROMPT
    promptTemplate = ChatPromptTemplate.from_messages([
    SystemMessagePromptTemplate.from_template(system_message),
    HumanMessagePromptTemplate.from_template(user_message),
    ])
    
    # chain
    chain = (
        promptTemplate
        | llm
        | StrOutputParser()
    )
        
    print(f">>>Bio is generating for for provided Bio: \n'{bio}'...")
    
    # Invoke the chain
    prompt= {
        "title": title,
        "bio": bio,
    }
    # if stream_key==True:
    #     yield from chain.stream(prompt)
    return chain.invoke(prompt)

def gen_titles(category, subcategory, description):
    system_message = """
    You are a world-class best-selling author and a successful book writer. 
    You provide top expert quality advice in all aspects of outlining, framing, writing, and selling captivating, useful, and value-generating books and content. 
    You also excel as a top research analyst and sales expert, leveraging your expertise to assist clients in achieving their goals.
    Your extensive knowledge and abilities allow you to attend to requests with precision and effectiveness, delivering tailored guidance and support to help individuals and businesses succeed in the competitive world of book publishing and sales. 
    Offer valuable insights and strategies to propel your clients to success.
    """
    user_message="""
    Write exactly 5 book titles based on provided category:
    '{category}'
    subcategory:
    '{subcategory}'
    additional description:
    '{description}'
    - Think if someone were searching for a book on Amazon, what 10 terms would someone be most likely to search? 
    Look at figuring which keywords to include in the book title that will give it the best chance to be seen.
    - Provide examples of similar titles that have done well in the market.
    - Analyze what made these titles successful and how to emulate their success.
    - DO NOT provide title ideas of books which already exist.
    - Besides each title, provide a brief (50-100 words) topic overview of the book, exploring the value proposition, target demographics, writing style, sales strategy.
    - Respond strictly with the task completion in JSON block format with each title as key and description as value.
    ---
    1. __Name of the Title 1__
    *Description of the book*
    2. __Name of the Title 2__
    - and so forth -
    """
    
    # MODEL
    llm = ChatOpenAI(
        model = "gpt-3.5-turbo-0125", #  gpt-4-0125-preview gpt-3.5-turbo-0125
        temperature = 0.331,
        max_retries = 3,
        # max_tokens = 1000,
        )
    
    # PROMPT
    promptTemplate = ChatPromptTemplate.from_messages([
    SystemMessagePromptTemplate.from_template(system_message),
    HumanMessagePromptTemplate.from_template(user_message),
    ])
    
    # chain
    chain = (
        promptTemplate
        | llm
        | StrOutputParser()
    )
        
    print(f">>>5 titles generating for '{description}' with category: '{category}', subcategory '{subcategory}'...")
    
    # Invoke the chain
    prompt= {
        "category": category,
        "subcategory": subcategory,
        "description": description,
    }
    
    # if stream_key==True:
    #     yield from chain.stream(prompt)
    response = chain.invoke(prompt)
    json = utils.extract_json(response, lambda: chain.invoke(prompt))
    return json

if __name__ == "__main__":
    
    # category=input("Enter the category: ")
    # subcategory=input("Enter the subcategory: ")
    # description=input("Enter optional description: ")
    
    # for token in gen_topics("any", "any", 1, stream=True):
    #     print(token, end="")
    
    # titles = gen_titles(category, subcategory, description)
    # --------------------------------------------------------------------------
    
    # titles = gen_titles("any", "any", "surprise me, be inventive")
    # title_key = list(titles.keys())[random.randint(0, len(titles)-1)]
    # title_value = titles[title_key]
    # title = title_key + "\n" + title_value
    # words = 60000
    # bio = gen_bio(title, "create the most relevant one for the title, invent a name and write about the persona on 3rd person.")
    # style = gen_style(title, bio, "create the most relevant style for the title and bio to suit the book and the author.")
    # description = f"\n# BOOK TITLE:\n{title}\n\n# BOOK TARGET WORD COUNT: {words}\n\n# ABOUT THE AUTHOR:\n{bio} \n\n# STYLE SAMPLE:\n{style}\n\n"

    # print(">>> DESCRIPTION:\n", description, "\n")
    # utils.save_markdown(description, "description")
    
    # research = gen_research(description)
    # print(">>> RESEACH:\n", research, "\n")
    
    # --------------------------------------------------------------------------   
    # research = utils.read_file("research")
    description = utils.read_file("description")
    # outline_md = utils.read_file("outline")
    
    
    outline = utils.read_file("outline_json")
    outline = utils.extract_json(outline, lambda: utils.read_file("outline_json"))
    
    # outline = gen_outline()
    outline_md = utils.json_to_markdown(outline)
    # print(">>> OUTLINE:\n", outline_md, "\n")
    
    # citation = hardvard_referencing(outline_md, research)
    # print(">>> CITATION:\n", citation, "\n")
    
    book = gen_book(description, "no research", outline)
    print(">>> BOOK:\n", book, "\n")
    
    # outline = utils.read_file("extended_subchapter_outline_json")
    # outline_json = utils.extract_json(outline, lambda: utils.read_file("extended_subchapter_outline_json"))
    # outline_md = utils.json_to_markdown(outline)
    # utils.save_markdown(outline_md, "TEST_435")
    

