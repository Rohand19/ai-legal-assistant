import streamlit as st
import json
from dotenv import load_dotenv
import os
import requests
import google.generativeai as genai
from agents.query_agent import QueryAgent
from agents.summary_agent import SummaryAgent

# Load environment variables
load_dotenv()

# Configure Gemini
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# Get API URL from environment variable with fallback to localhost
API_URL = os.getenv("https://api.render.com/deploy/srv-d0m656pr0fns73cb9ulg?key=mM9KdrmPwV4", "http://localhost:8000")

# Initialize agents
query_agent = QueryAgent()

# Set page config
st.set_page_config(
    page_title="Legal Assistant",
    page_icon="⚖️",
    layout="wide"
)

# Custom CSS
st.markdown("""
<style>
    .main {
        padding: 2rem;
    }
    .stTextArea textarea {
        height: 100px;
    }
    .key-point {
        padding: 0.5rem;
        background-color: #f0f2f6;
        border-radius: 0.3rem;
        margin: 0.5rem 0;
    }
    .warning {
        padding: 0.5rem;
        background-color: #ffe4e4;
        border-radius: 0.3rem;
        margin: 0.5rem 0;
    }
    .term {
        padding: 0.5rem;
        background-color: #e4f1ff;
        border-radius: 0.3rem;
        margin: 0.5rem 0;
    }
    .source {
        padding: 0.5rem;
        background-color: #f5f5f5;
        border-radius: 0.3rem;
        margin: 0.5rem 0;
        font-size: 0.9rem;
    }
    .step {
        padding: 1rem;
        background-color: #f8f9fa;
        border-radius: 0.3rem;
        margin: 0.8rem 0;
        border-left: 4px solid #1f77b4;
    }
</style>
""", unsafe_allow_html=True)

# Title and description
st.title("🤖 Legal Assistant")
st.markdown("""
This AI-powered legal assistant helps you understand legal procedures and requirements in India.
Simply ask your question, and the assistant will provide detailed information from reliable legal sources.
""")

# Input section
with st.form("query_form"):
    query = st.text_area("Enter your legal question:", placeholder="Example: What are the steps involved in filing a lawsuit in India?")
    submit_button = st.form_submit_button("Get Answer")

# Process query when submitted
if submit_button and query:
    with st.spinner("Analyzing your question..."):
        try:
            # Make request to FastAPI backend
            response = requests.post(
                f"{API_URL}/api/query",
                json={"query": query},
                timeout=30
            )
            response.raise_for_status()
            result = response.json()

            # Display simple explanation
            st.header("📝 Summary")
            st.write(result.get("simple_explanation", ""))

            # Display key points
            if result.get("key_points"):
                st.header("🔑 Key Points")
                for point in result["key_points"]:
                    st.markdown(f'<div class="key-point">• {point}</div>', unsafe_allow_html=True)

            # Create two columns for terms and warnings
            col1, col2 = st.columns(2)

            # Display important terms
            with col1:
                if result.get("important_terms"):
                    st.header("📚 Important Terms")
                    for term in result["important_terms"]:
                        st.markdown(f'<div class="term">{term}</div>', unsafe_allow_html=True)

            # Display warnings and deadlines
            with col2:
                if result.get("warnings_and_deadlines"):
                    st.header("⚠️ Warnings & Deadlines")
                    for warning in result["warnings_and_deadlines"]:
                        st.markdown(f'<div class="warning">{warning}</div>', unsafe_allow_html=True)

            # Display step-by-step guide if available
            if result.get("step_by_step_guide"):
                st.header("📋 Step-by-Step Guide")
                for i, step in enumerate(result["step_by_step_guide"], 1):
                    with st.expander(f"Step {i}: {step['title']}", expanded=True):
                        st.markdown(f"**Description:** {step['description']}")
                        if step.get('requirements'):
                            st.markdown("**Requirements:**")
                            for req in step['requirements']:
                                st.markdown(f"- {req}")

            # Display sources
            if result.get("sources"):
                st.header("📖 Sources")
                for source in result["sources"]:
                    with st.expander(f"Source: {source['document']}", expanded=False):
                        st.markdown(f'<div class="source">{source["text"]}</div>', unsafe_allow_html=True)
                        if source.get("relevance"):
                            st.markdown(f"**Relevance:** {source['relevance']}")

        except Exception as e:
            st.error(f"An error occurred: {str(e)}") 