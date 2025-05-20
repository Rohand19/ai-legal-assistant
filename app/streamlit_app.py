import streamlit as st
import json
from dotenv import load_dotenv
import os
from pathlib import Path
from agents.query_agent import QueryAgent
from agents.summary_agent import SummaryAgent

# Load environment variables and configure page
load_dotenv()
st.set_page_config(
    page_title="Legal Assistant",
    page_icon="⚖️",
    layout="wide"
)

# Custom CSS with optimized styles
st.markdown("""
<style>
    .main {
        padding: 2rem;
    }
    .stTextArea textarea {
        height: 100px;
    }
    .key-point {
        padding: 1rem;
        background-color: #f8f9fa;
        border-radius: 0.5rem;
        margin: 0.8rem 0;
        border-left: 4px solid #4CAF50;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    .warning {
        padding: 1rem;
        background-color: #fff8e1;
        border-radius: 0.5rem;
        margin: 0.8rem 0;
        border-left: 4px solid #ffa000;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    .term {
        padding: 1rem;
        background-color: #e8f4fd;
        border-radius: 0.5rem;
        margin: 0.8rem 0;
        border-left: 4px solid #1976D2;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    .source {
        padding: 1rem;
        background-color: #fafafa;
        border-radius: 0.5rem;
        margin: 0.8rem 0;
        border-left: 4px solid #757575;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    .step {
        padding: 1rem;
        background-color: #f3f6f9;
        border-radius: 0.5rem;
        margin: 0.8rem 0;
        border-left: 4px solid #1f77b4;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    .explanation {
        padding: 1.5rem;
        background-color: #ffffff;
        border-radius: 0.5rem;
        margin: 1rem 0;
        border: 1px solid #e0e0e0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    h1, h2, h3 {
        color: #1a237e;
        margin-top: 2rem;
    }
    strong {
        color: #1a237e;
    }
    .stButton>button {
        background-color: #1a237e;
        color: white;
        border-radius: 0.5rem;
        padding: 0.5rem 2rem;
        border: none;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .stButton>button:hover {
        background-color: #283593;
        box-shadow: 0 4px 8px rgba(0,0,0,0.15);
    }
</style>
""", unsafe_allow_html=True)

# Initialize agents
def initialize_agents():
    """Initialize the query and summary agents with API key."""
    # Try to get API key from environment first, then from Streamlit secrets
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        try:
            api_key = st.secrets["GOOGLE_API_KEY"]
        except Exception:
            st.error("Please set the GOOGLE_API_KEY in your Streamlit Cloud secrets or environment variables")
            st.markdown("""
            ### How to set up your API key:
            
            #### Local Development:
            1. Create a `.env` file in your project root
            2. Add your API key: `GOOGLE_API_KEY=your-api-key-here`
            
            #### Streamlit Cloud:
            1. Go to your app settings in Streamlit Cloud
            2. Navigate to 'Secrets' section
            3. Add your API key as: `GOOGLE_API_KEY = "your-api-key-here"`
            """)
            st.stop()
    return QueryAgent(api_key), SummaryAgent(api_key)

def process_legal_query(query: str, query_agent: QueryAgent, summary_agent: SummaryAgent) -> dict:
    """Process a legal query using the multi-agent system."""
    try:
        with st.spinner("🔍 Searching legal documents..."):
            query_results = query_agent.search_legal_documents(query)
        
        with st.spinner("📝 Analyzing and simplifying information..."):
            final_response = summary_agent.summarize_legal_information(query_results)
        
        return final_response
    except Exception as e:
        st.error(f"An error occurred: {str(e)}")
        return {
            "simple_explanation": "I apologize, but I encountered an error. Please try again or rephrase your question.",
            "key_points": [],
            "important_terms": [],
            "warnings_and_deadlines": [],
            "step_by_step_guide": [],
            "sources": []
        }

def main():
    """Main application function."""
    # Title and description
    st.title("🤖 Legal Assistant")
    st.markdown("""
    <div style='background-color: #f3f6f9; padding: 1rem; border-radius: 0.5rem; margin-bottom: 2rem;'>
    This AI-powered legal assistant helps you understand legal procedures and requirements in India.
    Simply ask your question, and the assistant will provide detailed information from reliable sources.
    </div>
    """, unsafe_allow_html=True)

    # Initialize agents
    query_agent, summary_agent = initialize_agents()

    # Input form
    with st.form("query_form"):
        query = st.text_area(
            "Enter your legal question:",
            placeholder="Example: What are the steps involved in filing a lawsuit in India?",
            height=100
        )
        col1, col2, col3 = st.columns([1,1,1])
        with col2:
            submit_button = st.form_submit_button("🔍 Get Answer", use_container_width=True)

    # Process query when submitted
    if submit_button and query:
        result = process_legal_query(query, query_agent, summary_agent)

        # Display results
        if result.get("simple_explanation"):
            st.header("📝 Summary")
            st.markdown(f'<div class="explanation">{result["simple_explanation"]}</div>', unsafe_allow_html=True)

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
                    if isinstance(term, dict):
                        formatted_term = f'<div class="term"><strong>{term.get("term", "")}</strong>: {term.get("definition", "")}</div>'
                        st.markdown(formatted_term, unsafe_allow_html=True)

        # Display warnings and deadlines
        with col2:
            if result.get("warnings_and_deadlines"):
                st.header("⚠️ Warnings & Deadlines")
                for warning in result["warnings_and_deadlines"]:
                    if isinstance(warning, dict):
                        warning_text = f'<div class="warning"><strong>Warning</strong>: {warning.get("warning", "")}'
                        if warning.get("deadline"):
                            warning_text += f'<br><strong>Deadline</strong>: {warning.get("deadline")}'
                        warning_text += '</div>'
                        st.markdown(warning_text, unsafe_allow_html=True)
                    elif isinstance(warning, str):
                        st.markdown(f'<div class="warning">{warning}</div>', unsafe_allow_html=True)

        # Display step-by-step guide
        if result.get("step_by_step_guide"):
            st.header("📋 Step-by-Step Guide")
            for i, step in enumerate(result["step_by_step_guide"], 1):
                if isinstance(step, dict):
                    step_title = step.get('title', '') or f"Step {step.get('step', i)}"
                    step_desc = step.get('description', '')
                    st.markdown(f'<div class="step"><strong>{step_title}</strong><br>{step_desc}</div>', unsafe_allow_html=True)

        # Display sources
        if result.get("sources"):
            st.header("📖 Sources")
            for source in result["sources"]:
                if isinstance(source, dict):
                    source_text = f'<div class="source"><strong>{source.get("title", "Reference")}</strong><br>{source.get("description", "")}</div>'
                    st.markdown(source_text, unsafe_allow_html=True)

if __name__ == "__main__":
    main() 