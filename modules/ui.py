import os, random
import streamlit as st
from bukki import Bukki 
from webCrawler import gen_research


# CHANGE LLM MODEL TO GPT4 when ready

# Scale up RESEARCH BREADTH & DEPTH >> ADD section for RESEARCH

# ADD IMAGES (during writing)

# ADD VOICED NARRATION (upload file to narrate) 

# ---------------------
# write a highly technical book about neuroevolution, explain the topic in detail and how the branch can be applied towards cognition inspired AI systems & AGI

# Initialize Bukki instance in session state if it doesn't exist
if 'bukki_instance' not in st.session_state:
    st.session_state.bukki_instance = Bukki()
    
categories_json = {
  "Any": ["Any"],
  "Arts & Photography": [
    "Architecture",
    "Decorative Arts & Design",
    "Drawing",
    "Fashion",
    "Graphic Design",
    "Music",
    "Painting",
    "Photography & Video",
    "Sculpture"
  ],
  "Business & Money": [
    "Accounting",
    "Business Culture",
    "Economics",
    "Insurance",
    "Investing",
    "Job Hunting & Careers",
    "Management & Leadership",
    "Marketing & Sales",
    "Personal Finance",
    "Real Estate",
    "Skills",
    "Small Business & Entrepreneurship",
    "Taxation"
  ],
  "Children's Books": [
    "Activities, Crafts & Games",
    "Arts, Music & Photography"
  ],
  "Computers & Technology": [
    "Internet & Social Media",
    "Programming Languages",
    "Web Development & Design"
  ],
  "Cookbooks, Food & Wine": [
    "Beverages & Wine",
    "Canning & Preserving",
    "Kitchen Appliances",
    "Regional & International",
    "Special Diet",
    "Vegetarian & Vegan"
  ],
  "Crafts, Hobbies & Home": [
    "Coloring Books for Grown-Ups",
    "Crafts & Hobbies",
    "Gardening & Landscape Design",
    "Home Improvement & Design",
    "Needlecrafts & Textile Crafts",
    "Pets & Animal Care",
    "Sustainable Living"
  ],
  "Education & Teaching": [
    "Schools & Teaching",
    "Studying & Workbooks",
    "Test Preparation"
  ],
  "Health, Fitness & Dieting": [
    "Addiction & Recovery",
    "Aging",
    "Alternative Medicine",
    "Beauty, Grooming, & Style",
    "Diets & Weight Loss",
    "Diseases & Physical Ailments",
    "Exercise & Fitness",
    "Men's Health",
    "Mental Health",
    "Nutrition",
    "Psychology & Counseling",
    "Safety & First Aid",
    "Women's Health"
  ],
  "Humor & Entertainment": [
    "Puzzles & Games",
    "Trivia & Fun Facts"
  ],
  "Parenting & Relationships": [
    "Adoption",
    "Aging Parents",
    "Babysitting, Day Care & Child Care",
    "Disabilities & Hyperactivity",
    "Family Relationships",
    "Marriage & Adult Relationships",
    "Parenting",
    "Pregnancy & Childbirth"
  ],
  "Religion & Spirituality": [
    "New Age & Spirituality"
  ],
  "Self-Help": [
    "Anger Management",
    "Anxieties & Phobias",
    "Communication & Social Skills",
    "Eating Disorders",
    "Emotions",
    "Hypnosis",
    "Memory Improvement",
    "Neuro-Linguistic Programming",
    "New Age",
    "Relationships",
    "Self-Esteem",
    "Spiritual",
    "Stress Management",
    "Time Management"
  ],
  "Sports & Outdoors": [
    "Coaching",
    "Extreme Sports",
    "Hiking & Camping",
    "Hunting & Fishing",
    "Individual Sports",
    "Mountaineering",
    "Outdoor Recreation",
    "Racket Sports",
    "Survival Skills",
    "Training",
    "Water Sports"
  ],
  "Travel": [
    "Food, Lodging & Transportation"
  ]
}

def run_ui():
    st.markdown("<h1 style='text-align: center;'>Bukki</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center;'> ~ A neural book writing system ~ </p>", unsafe_allow_html=True)
    
    # Main content area
    col1, col2, col3, col4 = st.columns([2, 2, 2, 1])

    if col1.button("Automatic", key="auto"):
            st.session_state['pipeline'] = "Auto"
            st.session_state['bukki_instance'] = Bukki()  # Reinitialize Bukki instance for fresh start
            st.rerun()

    if col2.button("Manual", key="manual"):
            st.session_state['pipeline'] = "Manual"
            st.session_state['bukki_instance'] = Bukki()  # Reinitialize Bukki instance for fresh start
            st.rerun()

    if col3.button("Research", key="research"):
            st.session_state['pipeline'] = "Research"
            st.session_state['bukki_instance'] = Bukki()  # Reinitialize Bukki instance for fresh start
            st.rerun()        

    if col4.button("Restart"):
        # Reset the Bukki instance
            st.session_state['bukki_instance'] = Bukki()
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.session_state.clear()
            # Rerun the app to reflect the changes
            st.rerun()

    if 'pipeline' not in st.session_state:
        # This block only runs when the app is first loaded or reset
        st.markdown("""
        <div style="text-align: center;">
            <p>Welcome to <strong>Bukki</strong>, your neural assistant in the journey of book creation. Bukki harnesses the power of AI to help authors, researchers, and hobbyists generate books from initial concept to completed manuscript.</p>
            <p>Choose one of the pathways to begin:</p>
            <ul>
                <li><strong>Automatic:</strong> Let Bukki guide you through an automated process, generating a book based on a brief direction or theme you provide.</li>
                <li><strong>Manual:</strong> Take control of each step in the book creation process, making selections and providing input at each stage.</li>
                <li><strong>Research:</strong> Focus solely on generating comprehensive research for your book's theme, ideal for gathering information before starting your writing.</li>
            </ul>
            <p>Press <strong>Restart</strong> at any time to return to this page and begin anew.</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Execute the selected pipeline
    if 'pipeline' in st.session_state:
        if st.session_state['pipeline'] == "Auto":
            auto_pipeline()
        elif st.session_state['pipeline'] == "Manual":
            manual_pipeline()
        elif st.session_state['pipeline'] == "Research":
            research_pipeline()
            
def download_button(disabled=True):
    print(">>> Download button pressed...")
    zip_file_path = st.session_state.bukki_instance.export_all()
    
    with open(zip_file_path, "rb") as f:
        bytes_data = f.read()
        st.download_button(
            disabled=disabled,
            label="Download",
            data=bytes_data,
            file_name=zip_file_path,
            mime="application/zip"
        )

def auto_pipeline():
    st.header("Auto Book Creation Process")
    st.write("This process is fully automated and writes a full book from a simple direction prompt.")

    # User input for direction
    direction = st.text_input("Provide a brief direction or theme for your book:", "a non-fiction book which would be a best seller in 2027")
    
    col1, col2, col3 = st.columns([2, 2, 1])
    if col2.button("Generate"):
        st.session_state.bukki_instance = Bukki()
        # Initialize session state variables if not already done
        if 'progress' not in st.session_state:
            st.session_state.progress = 0

        st.session_state.book_generated = False

        if not st.session_state.book_generated:
            # with spinner():
            status_message = st.empty()
            progress_bar = st.progress(0)
            success_field = st.empty()
            
            # Simulate title generation
            status_message.text("Generating titles...")
            titles = st.session_state.bukki_instance.send_stage1(description=direction)
            st.session_state.titles = titles
            progress_bar.progress(15)

            status_message.text("Generating description...")
            description = st.session_state.bukki_instance.send_stage2()
            progress_bar.progress(30)
            st.session_state.description = description
            st.write("# BOOK DESCRIPTION:\n")
            st.write(description)
            
            status_message.text("Generating research...")
            research_res = st.session_state.bukki_instance.send_research()
            progress_bar.progress(60)
            st.session_state.research_res = research_res
            st.write("\n---\n---\n# BOOK RESEARCH:\n")
            st.write(research_res)
            
            status_message.text("Generating outline...")
            outline = st.session_state.bukki_instance.send_outline()
            progress_bar.progress(80)
            st.session_state.outline = outline
            st.write("\n---\n---\n# BOOK OUTLINE:\n")
            st.write(outline)
            
            status_message.text("Generating book...")
            book = st.session_state.bukki_instance.send_book()
            progress_bar.progress(100)
            st.session_state.book = book
            success_field.success("Book ready to Download!")
            st.write("\n---\n---\n# BOOK:\n")
            st.write(book)
            status_message.text("Book generation complete!")
            st.session_state.book_generated = True  # Mark the book generation as complete
            st.rerun()

    elif st.session_state.get('book_generated', False):
        # If book is already generated, directly display saved content from session_state
        st.progress(st.session_state.progress)
        st.success("Book ready to Download!")
        st.write("# BOOK DESCRIPTION:\n")
        st.write(st.session_state.description)
        st.write("\n---\n---\n# BOOK RESEARCH:\n")
        st.write(st.session_state.research_res)
        st.write("\n---\n---\n# BOOK OUTLINE:\n")
        st.write(st.session_state.outline)
        st.write("\n---\n---\n# BOOK:\n")
        st.write(st.session_state.book)
        col1, col2, col3 = st.columns([2, 2, 1])
        with col2:
            download_button(disabled=False)

def manual_pipeline():
    st.header("Manual Book Creation Process")
    stages = ["Select Category and Subcategory", "Enter Book Details", "Generate Research", "Generate Outline", "Finalize Book"]
    
    # Progress bar and current stage tracker
    if 'current_stage' not in st.session_state:
        st.session_state.current_stage = 0

    # Stage-specific logic
    if st.session_state.current_stage == 0:
        stage_select_category_subcategory()
    elif st.session_state.current_stage == 1:
        stage_enter_book_details()
    elif st.session_state.current_stage == 2:
        stage_generate_research()
    elif st.session_state.current_stage == 3:
        stage_generate_outline()
    elif st.session_state.current_stage == 4:
        stage_finalize_book()

def research_pipeline():
    st.header("Research Generation Process")
    st.write("This process generates comprehensive research based on the direction or theme you provide.")

    # User input for direction or theme
    description = st.text_input("Provide a brief direction or theme for research:", "Emerging future technologies by 2027")
    
    # Define mappings for breadth and depth
    breadth_mapping = {'Narrow': 2, 'Moderate': 4, 'Broad': 6}
    depth_mapping = {'Shallow': 2, 'Moderate': 4, 'Deep': 6}
    
    # User input for research breadth and depth with conversion to integers
    research_breadth_option = st.select_slider("Select the breadth of your research:", options=['Narrow', 'Moderate', 'Broad'], value='Narrow')
    research_depth_option = st.select_slider("Select the depth of your research:", options=['Shallow', 'Moderate', 'Deep'], value='Shallow')

    # Convert selections to preset integer values
    research_breadth = breadth_mapping[research_breadth_option]
    research_depth = depth_mapping[research_depth_option]

    if 'research_generated' not in st.session_state:
        st.session_state.research_generated = False
        
    if 'research_result' not in st.session_state or st.session_state.research_generated == False:
        success_field = st.empty()
        research_field = st.empty()
    else:
        success_field = st.empty()
        research_field = st.empty()

    col1, col2 = st.columns([2, 1])

    regenerate_solo_research = col1.button("Regenerate" if st.session_state.get('research_generated', False) else "Generate")
    
    if regenerate_solo_research:
        st.session_state.bukki_instance = Bukki()
        with st.spinner("Generating research..."):
            research_result = st.session_state.bukki_instance.solo_research(description, research_breadth, research_depth)
            st.session_state.research_result = research_result
            success_field.success("Research ready!")
            research_field.write(research_result)
            st.session_state.research_generated = True  # Mark the research generation as complete
            st.rerun()
    elif st.session_state.get('research_generated', False):
        success_field.success("Research ready!")
        research_field.write(st.session_state.research_result)
        with col2:
            disabled=not(st.session_state.get('research_generated', False))
            download_button(disabled)

# ---------------------

def stage_select_category_subcategory():
    st.subheader("Step 1: Select Category and Subcategory")
    # Logic for selecting category and subcategory
    selected_category = st.selectbox("Select Category", options=list(categories_json.keys()))
    selected_subcategory = st.selectbox("Select Subcategory", options=categories_json[selected_category])
    direction = st.text_input("Additional Details:")

    if 'titles' not in st.session_state or st.session_state.titles_sent == False:
        success_field = st.empty()
        titles_field = st.empty()
        # st.write("Titles not existant, not been sent.")
    else:
        success_field = st.empty()
        st.write(st.session_state.titles)
        titles_field = st.empty()
        # st.write("Titles existant, have been sent.")

    title_id = st.empty()

    button_container = st.container()
    col1, col2, col3 = button_container.columns([2, 2, 1])

    # Use a flag in session state to manage title regeneration
    regenerate_titles = col2.button("Regenerate" if st.session_state.get('titles_sent', False) else "Generate")

    if col1.button("Back", disabled=st.session_state['current_stage'] == 0):
        st.session_state['current_stage'] -= 1
        st.rerun()

    if regenerate_titles:
        with st.spinner("Generating titles..."):
            titles = st.session_state.bukki_instance.send_stage1(selected_category, selected_subcategory, direction)
            st.session_state.titles_sent = True
            st.session_state.titles = titles
            titles_field.write(titles)
            success_field.success("Titles generated!")
            st.rerun()
    
    if col3.button("Next", disabled=not(st.session_state.get('titles_sent', False))):
        st.session_state['current_stage'] += 1
        st.rerun()
    
    if st.session_state.get('titles_sent', False):
        st.session_state.title_id = title_id.radio("Select Title Number:", options=[1, 2, 3, 4, 5], horizontal=True)
        st.write("Selected Title:", st.session_state.title_id)
        
def stage_enter_book_details():
    st.subheader("Step 2: Enter Book Details")
    
    # Logic for entering book details (title, bio, etc.)
    title_id = st.session_state.title_id
    st.write("Selected Title:", title_id)
    # words_input = st.number_input("Words Target Count: (k)", min_value=5, step=10, max_value=150, value=10)
    bio_input = st.text_area("Biography:", "Enter a brief description about the author.")
    style_input = st.text_area("Style:", "Enter a brief sample of the target writing style.")

    if 'description' not in st.session_state or st.session_state.description_sent == False:
        success_field = st.empty()        
        description_field = st.empty()
    else:
        success_field = st.empty()
        st.write(st.session_state.description)
        description_field = st.empty()

    # Buttons container
    button_container = st.container()
    col1, col2, col3 = button_container.columns([2, 2, 1])

    # Use a flag in session state to manage title regeneration
    regenerate_description = col2.button("Regenerate" if st.session_state.get('description_sent', False) else "Generate")

    # Back button - always available in this stage as it's not the first stage
    if col1.button("Back"):
        st.session_state['current_stage'] -= 1
        st.rerun()

    # Send button - to generate and display the book details
    if regenerate_description:
        with st.spinner("Generating Description..."):
            description = st.session_state.bukki_instance.send_stage2(title_id-1, bio_input, style_input)
            st.session_state.description_sent = True  # Mark details as sent/generated
            st.session_state.description = description  # Store the generated details in the session state
            success_field.success("Description generated!")
            description_field.write(description)
            st.rerun()

    # Next button - enabled if details have been sent/generated
    if col3.button("Next", disabled=not(st.session_state.get('description_sent', False))):
        st.session_state['current_stage'] += 1
        st.rerun()

def stage_generate_research():
    st.subheader("Step 3: Generate Research")
 
     # Initialize 'research_sent' in session state if it doesn't exist
    if 'research_sent' not in st.session_state:
        st.session_state.research_sent = False
 
    if 'research_out' not in st.session_state or st.session_state.research_sent == False:
        success_field = st.empty()
        research_field = st.empty()
    else:
        success_field = st.empty()
        st.write(st.session_state.research_out)
        research_field = st.empty()

    # Container for buttons
    buttons_container = st.container()
    col1, col2, col3 = buttons_container.columns([2, 2, 1])
    
    # Use a flag in session state to manage title regeneration
    regenerate_research = col2.button("Regenerate" if st.session_state.get('research_sent', False) else "Generate")
    
    # Back button
    if col1.button("Back"):
        st.session_state['current_stage'] -= 1
        st.rerun()

    # Trigger research generation in Bukki instance
    if regenerate_research:
         with st.spinner("Generating Research..."):
            research_out = st.session_state.bukki_instance.send_research()
            st.session_state.research_sent = True
            st.session_state.research_out = research_out
            success_field.success("Research generated!")
            research_field.write(research_out)
            st.rerun()
    
    if col3.button("Next", disabled=not(st.session_state.get('research_sent', False))):
        st.session_state.current_stage += 1
        st.rerun()

def stage_generate_outline():
    st.subheader("Step 4: Generate Outline")
        
    if 'outline' not in st.session_state or st.session_state.outline_sent == False:
        success_field = st.empty()
        outline_field = st.empty()
    else:
        success_field = st.empty()
        st.write(st.session_state.outline)
        outline_field = st.empty()
        
    buttons_container = st.container()
    col1, col2, col3 = buttons_container.columns([2, 2, 1])

    # Use a flag in session state to manage title regeneration
    regenerate_outline = col2.button("Regenerate" if st.session_state.get('outline_sent', False) else "Generate")

    if col1.button("Back"):
        st.session_state['current_stage'] -= 1
        st.rerun()

    if regenerate_outline:
         with st.spinner("Generating Outline..."):
            outline = st.session_state.bukki_instance.send_outline()
            st.session_state.outline_sent = True
            st.session_state.outline = outline
            success_field.success("Outline generated!")
            outline_field.write(outline)
            st.rerun()
    
    if col3.button("Next", disabled=not(st.session_state.get('outline_sent', False))):
        st.session_state.current_stage += 1
        st.rerun()

def stage_finalize_book():
    st.subheader("Step 5: Generate Full Book")
    
    if 'book' not in st.session_state or st.session_state.book_sent == False:
        success_field = st.empty()
        book_field = st.empty()
    else:
        success_field = st.empty()        
        book_field = st.empty()
        
    buttons_container = st.container()
    col1, col2, col3 = buttons_container.columns([2, 2, 1])
    
    # Use a flag in session state to manage title regeneration
    regenerate_book = col2.button("Regenerate" if st.session_state.get('book_sent', False) else "Generate")
    
    if col1.button("Back"):
        st.session_state['current_stage'] -= 1
        st.rerun()
        
    # Finalize button to generate and display the final book content
    if regenerate_book:
        with st.spinner("Generating Book... this may take 15-25 minutes"):
            book = st.session_state.bukki_instance.send_book()
            st.session_state.book_sent = True
            st.session_state.book = book
            success_field.success("Book generated!")
            book_field.write(book)
            st.rerun()
    
    elif st.session_state.get('book_sent', False):
        success_field.success("Book's ready!")
        book_field.write(st.session_state.book)
        with col3:
            disabled=not(st.session_state.get('book_sent', False))
            download_button(disabled)

if __name__ == "__main__":
    run_ui()