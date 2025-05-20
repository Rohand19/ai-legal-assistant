from typing import Dict, Any, List
import google.generativeai as genai
import json

class SummaryAgent:
    def __init__(self, api_key: str):
        """Initialize the Summary Agent with Google API key."""
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-2.0-flash')

    def summarize_legal_information(self, query_results: Dict[str, Any]) -> Dict[str, Any]:
        """Summarize and simplify legal information from query results."""
        # Check if this is a non-legal query response
        if (len(query_results.get("relevant_sections", [])) == 0 and 
            "simple_explanation" in query_results):
            return query_results

        # Prepare the content for summarization
        sections = "\n\n".join([
            f"Source: {section['source']}\nSection: {section['section']}\nContent: {section['content']}"
            for section in query_results.get("relevant_sections", [])
        ])
        
        prompt = f"""You are a specialized legal summarization agent. Your task is to analyze and structure the following information:

        Content to analyze:
        Legal Context: {query_results.get('legal_context', '')}
        Applicable Laws: {', '.join(query_results.get('applicable_laws', []))}
        Relevant Sections:
        {sections}
        
        Provide a clear, structured response in JSON format with the following components:
        {{
            "simple_explanation": "A clear, concise explanation in plain language",
            "key_points": ["List of important points"],
            "important_terms": [
                {{
                    "term": "The legal term",
                    "definition": "Simple explanation of the term"
                }}
            ],
            "warnings_and_deadlines": [
                {{
                    "warning": "Important warning",
                    "deadline": "Associated deadline (if any)"
                }}
            ],
            "step_by_step_guide": [
                {{
                    "step": "1",
                    "title": "Step title",
                    "description": "What to do"
                }}
            ],
            "sources": [
                {{
                    "title": "Document title",
                    "description": "Clear description of what this source contributes"
                }}
            ]
        }}

        Guidelines:
        1. Use dictionary format for all structured data (terms, warnings, steps)
        2. Make explanations clear and accessible to non-lawyers
        3. Include specific deadlines and requirements in warnings
        4. Break down complex procedures into clear steps
        5. Preserve accuracy while simplifying language"""
        
        try:
            response = self.model.generate_content(prompt)
            result = self._parse_json_response(response.text)
            
            # Ensure consistent structure
            return {
                "simple_explanation": result.get("simple_explanation", ""),
                "key_points": result.get("key_points", []),
                "important_terms": result.get("important_terms", []),
                "warnings_and_deadlines": result.get("warnings_and_deadlines", []),
                "step_by_step_guide": result.get("step_by_step_guide", []),
                "sources": result.get("sources", [])
            }
        except Exception as e:
            return {
                "simple_explanation": f"Error summarizing information: {str(e)}",
                "key_points": [],
                "important_terms": [],
                "warnings_and_deadlines": [],
                "step_by_step_guide": [],
                "sources": []
            }

    def simplify_text(self, text: str) -> Dict[str, Any]:
        """Simplify complex legal text into plain language."""
        prompt = f"""Simplify this legal text into plain language:

        {text}

        Return a JSON object with:
        {{
            "simplified_text": "plain language explanation",
            "terms": [
                {{
                    "term": "legal term",
                    "definition": "simple explanation"
                }}
            ],
            "warnings": ["any important warnings or deadlines"]
        }}"""

        try:
            response = self.model.generate_content(prompt)
            return self._parse_json_response(response.text)
        except Exception:
            return {
                "simplified_text": text,
                "terms": [],
                "warnings": []
            }

    def extract_key_points(self, text: str) -> Dict[str, List[str]]:
        """Extract key points from legal text."""
        prompt = f"""Extract the key points from this legal text:

        {text}

        Return a JSON object with:
        {{
            "key_points": ["list of important points"]
        }}"""

        try:
            response = self.model.generate_content(prompt)
            return self._parse_json_response(response.text)
        except Exception:
            return {"key_points": []}

    def create_step_by_step_guide(self, text: str) -> Dict[str, List[Dict[str, str]]]:
        """Create a step-by-step guide from legal text."""
        prompt = f"""Create a step-by-step guide from this legal text:

        {text}

        Return a JSON object with:
        {{
            "steps": [
                {{
                    "step": "step number",
                    "description": "what to do"
                }}
            ]
        }}"""

        try:
            response = self.model.generate_content(prompt)
            return self._parse_json_response(response.text)
        except Exception:
            return {"steps": []}
    
    def _parse_json_response(self, text: str) -> Dict[str, Any]:
        """Parse and clean JSON response from the model."""
        text = text.strip()
        if text.startswith('```json'):
            text = text[7:]
        if text.startswith('```'):
            text = text[3:]
        if text.endswith('```'):
            text = text[:-3]
        
        try:
            return json.loads(text.strip())
        except json.JSONDecodeError:
            return {
                "simple_explanation": "Error parsing response",
                "key_points": [],
                "important_terms": [],
                "warnings_and_deadlines": [],
                "step_by_step_guide": [],
                "sources": []
            }