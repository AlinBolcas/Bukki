import textGen as tg
import utils

import os, random, re
# from threading import Thread
import io
from zipfile import ZipFile
import uuid
from webCrawler import gen_research

# Define the Bukki system
class Bukki:
    def __init__(self):
        self.category = ""
        self.subcategory = ""
        self.description = ""
    
        self.titles = {}
        self.title_select = ""
        self.bio = ""
        self.style = ""
        self.words = ""
        
        self.research = ""
        self.outline = ""
        self.book = ""
        
    def send_stage1(self, category="", subcategory="", description=""):
        if category == "":
            self.category = "any, most relevant"
        if subcategory == "":
            self.subcategory = "any, most relevant"
        if description == "":
            self.description = "be inventive, think outside the box about a book that humanity needs written."
        
        self.category = category
        self.subcategory = subcategory
        self.description = description
        self.titles = tg.gen_titles(self.category, self.subcategory, self.description)
        return utils.json_to_markdown(self.titles)

    def send_stage2(self, title_id=-1, bio="", style="", words_k=50):
        random_title = self.titles[random.choice(list(self.titles.keys()))]
        if bio == "":
            self.bio = tg.gen_bio(random_title, "create the most relevant identity for the book, invent a name and write about the individual on 3rd person.")
        
        if style == "":
            
            self.style = tg.gen_style(random_title, self.bio, "create the most relevant style of writing example for the title and bio to suit the book.")
        
        if title_id == -1 or title_id < 0 or title_id >= len(self.titles):
            title_id = random.randint(0, len(self.titles)-1)

        title_key = list(self.titles.keys())[title_id]
        title_key_processed = re.sub(r'^[^A-Za-z]*', '', title_key)    
        title_value = self.titles[title_key]

        # Handling different types of title_value
        try:
            if isinstance(title_value, dict):
                # Assuming the dict contains a list and you need the first item
                # Adjust logic here depending on the actual structure of your dict
                first_key = list(title_value.keys())[0]
                title_value_str = title_value[first_key]
            elif isinstance(title_value, str):
                title_value_str = title_value
            else:
                # Fallback for other types
                title_value_str = str(title_value)
        except Exception as e:
            # Handle exceptions, e.g., KeyError, TypeError, IndexError
            print(f"Error processing title_value: {e}")
            # Fallback or error handling strategy here
            title_value_str = "Error processing title, please go back and regenerate."
        
        self.title_select = "## " + title_key_processed + "\n" + title_value_str
        
        self.bio = tg.gen_bio(self.title_select, bio)
        self.style = tg.gen_style(self.title_select, self.bio, style)
        self.words = f"{words_k*1000}"
        
        self.description = f"\n# BOOK TITLE:\n{self.title_select}\n\n# BOOK TARGET WORD COUNT: {self.words}\n\n# ABOUT THE AUTHOR:\n{self.bio} \n\n# STYLE SAMPLE:\n{self.style}\n\n"
        utils.save_markdown(self.description, "description")
        
        self.tite = title_key_processed
        return self.description
    
    def send_research(self):
        self.research = tg.gen_research(self.description)
        return self.research
            
    def send_outline(self):
        self.outline = tg.gen_outline(self.description, self.research)
        return utils.json_to_markdown(self.outline)
        
    def send_book(self):
        self.book = tg.gen_book(self.description, self.research, self.outline)
        return self.book

    def auto_book(self):
        self.send_stage1()
        self.send_stage2()
        print(">>> AUTO DESCRIPTION:\n", self.description, "\n\n")
        self.send_research()
        print(">>> AUTO RESEACH:\n", self.research, "\n\n")
        outline_md = self.send_outline()
        print(">>> AUTO OUTLINE:\n", outline_md, "\n\n")
        self.send_book()    
        print(">>> AUTO BOOK:\n", self.book, "\n")
        return self.description, self.research, outline_md, self.book

    def solo_research(self, description, breadth=2, depth=2):
        print(">>> SOLO RESEARCH:\n", description, "\n\n")
        # try:
        #     # First attempt with free engine
        #     solo_research = gen_research(description, breadth=breadth, depth=depth, paid_engine=False)
        #     utils.save_markdown(solo_research, "solo_research")
        # except Exception as free_engine_error:
        #     print(f"Error with free engine: {free_engine_error}")
        try:
            # Second attempt with paid engine
            solo_research = gen_research(description, breadth, depth)
            utils.save_markdown(solo_research, "solo_research")
        except Exception as paid_engine_error:
            print(f"Error with paid engine: {paid_engine_error}")
            # Return this message when both attempts fail
            return "There are no credits to make research."
        self.research = solo_research
        return solo_research
    
    def export_all(self):
        print(">>> EXPORTING ALL MARKDOWN FILES")
        output_dir = "output"
        
        # Dynamically create unique names for the zip file
        unique_id = uuid.uuid4().hex
        zip_file_name = f"book_package_{unique_id}.zip"
        zip_file_path = os.path.join(output_dir, zip_file_name)

        # Dictionary mapping file names to content
        markdown_contents = {
            "description.md": self.description,
            "research.md": self.research,
            "outline.md": utils.json_to_markdown(self.outline),
            "book.md": self.book,
        }

        # Use a memory buffer for creating the zip file
        with io.BytesIO() as zip_buffer:
            with ZipFile(zip_buffer, 'w') as zipf:
                for file_name, content in markdown_contents.items():
                    if content:  # Ensure there is content to write
                        zipf.writestr(file_name, content)
                    else:
                        print(f"Warning: Content for {file_name} is empty and will not be included in the zip file.")
            
            # Save the zip file to disk
            os.makedirs(output_dir, exist_ok=True)
            with open(zip_file_path, 'wb') as f:
                f.write(zip_buffer.getvalue())

        print(f"Zip file created: {zip_file_path}")
        return zip_file_path
    
if __name__ == "__main__":
    # Create an instance of Bukki and trigger the book writing system
    bukki_instance = Bukki()
    # bukki_instance.auto_book()
    # export_path = bukki_instance.export_all()
    # print(export_path)
    # bukki_instance.send_stage1()
    # bukki_instance.send_stage2()
    # bukki_instance.send_research()
    # bukki_instance.send_outline()
    # bukki_instance.send_book()
