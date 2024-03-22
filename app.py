# app.py
import sys
import os

# Assuming app.py is in the root directory and modules is a subdirectory
project_dir = os.path.dirname(os.path.abspath(__file__))
modules_dir = os.path.join(project_dir, 'modules')
sys.path.append(modules_dir)

from ui import run_ui
# from utils import test

def run_app():
    run_ui()

if __name__ == "__main__":
    run_app()
    
    # test()
