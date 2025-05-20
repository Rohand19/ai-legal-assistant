import streamlit.web.cli as stcli
import sys
import os

if __name__ == "__main__":
    # Get the absolute path to the streamlit_app.py
    current_dir = os.path.dirname(os.path.abspath(__file__))
    streamlit_app_path = os.path.join(current_dir, "app", "streamlit_app.py")
    
    # Add the current directory to Python path
    sys.path.append(current_dir)
    
    # Run the Streamlit app
    sys.argv = ["streamlit", "run", streamlit_app_path]
    sys.exit(stcli.main()) 