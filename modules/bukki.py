import textGen as tg
import utils

import os, random, re
# from threading import Thread
from zipfile import ZipFile
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
        
        if title_id == -1:
            title_id = random.randint(0, len(self.titles)-1)
        
        title_key = list(self.titles.keys())[title_id]
        title_key_processed = re.sub(r'^[^A-Za-z]*', '', title_key)    
        title_value = self.titles[title_key]
        
        # Ensure title_value is a string before concatenation
        if isinstance(title_value, dict):
            # Handle the case where title_value is a dict (customize as needed)
            title_value_str = title_value[0]  # Example access
        elif isinstance(title_value, str):
            title_value_str = title_value
        else:
            # Default handling for unexpected types
            title_value_str = str(title_value)
        
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
        return solo_research
    
    def export_all(self):
        # Directory where markdown files are saved
        print(">>> EXPORTING ALL MARKDOWN FILES")
        output_dir = "output"

        # else:
        file_names = ["description.md", "research.md", "outline.md", "book.md", "solo_research.md"]
        zip_file_name = f"book_package.zip"
            
        # Full path to the zip file
        zip_file_path = os.path.join(output_dir, zip_file_name)

        # Create a zip file and add the markdown files
        with ZipFile(zip_file_path, 'w') as zipf:
            for file_name in file_names:
                # Full path to the markdown file
                file_path = os.path.join(output_dir, file_name)
                # Check if the file exists before adding it to the zip
                if os.path.exists(file_path):
                    zipf.write(file_path, os.path.basename(file_path))
                else:
                    print(f"Warning: {file_path} does not exist and will not be included in the zip file.")
        
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
