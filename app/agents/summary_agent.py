from typing import Dict, Any, List
import google.generativeai as genai
import json

class SummaryAgent:
    def __init__(self):
        self.model = genai.GenerativeModel('gemini-2.0-flash')

    def _parse_response(self, response_text: str) -> Dict[str, Any]:
        """Safely parse the model's response into a dictionary."""
        try:
            # Clean the response text and ensure it's valid JSON
            cleaned_text = response_text.strip().replace('\n', ' ').replace('\r', '')
            result = json.loads(cleaned_text)
            
            # Handle different response formats
            if isinstance(result, list):
                return {"key_points": result}
            elif isinstance(result, dict):
                if "key_points" in result:
                    points = result["key_points"]
                    if isinstance(points, str):
                        # Split string into list if it contains bullet points
                        points = [p.strip().lstrip('•-*') for p in points.split('\n') if p.strip()]
                        result["key_points"] = points
                return result
            return {"key_points": [str(result)]}
        except json.JSONDecodeError:
            # Fallback response if parsing fails
            return {
                "simplified_text": response_text,
                "terms": [],
                "warnings": [],
                "key_points": [response_text]
            }

    def simplify_text(self, text: str) -> Dict[str, Any]:
        """Convert complex legal text into simple, easy-to-understand language."""
        prompt = f"""Analyze the following legal text and provide a structured response:

{text}

Please provide:
1. A simple explanation in plain language (2-3 paragraphs)
2. A list of key terms and their definitions in the format "term: definition"
3. A list of important warnings or deadlines

Format the response as JSON with the following structure:
{{
    "simplified_text": "your simple explanation here",
    "terms": ["term1: definition1", "term2: definition2"],
    "warnings": ["warning1", "warning2"]
}}"""

        response = self.model.generate_content(prompt)
        return self._parse_response(response.text)

    def create_step_by_step_guide(self, text: str) -> Dict[str, Any]:
        """Create a step-by-step guide from legal procedures."""
        prompt = f"""Convert the following legal procedure into a clear step-by-step guide:

{text}

Format the response as JSON with the following structure:
{{
    "steps": [
        {{
            "title": "Step title",
            "description": "Detailed explanation",
            "requirements": ["requirement1", "requirement2"]
        }}
    ]
}}

Make sure each step is clear, actionable, and includes any necessary requirements or documents."""

        response = self.model.generate_content(prompt)
        return self._parse_response(response.text)

    def extract_key_points(self, text: str) -> Dict[str, Any]:
        """Extract and summarize key points from legal text."""
        prompt = f"""Extract the most important points from this legal text:

{text}

Format the response as a list of key points.
Include:
- Main takeaways
- Deadlines or time-sensitive information
- Required actions
- Rights and protections
- Potential consequences

Format the response as a JSON array of strings:
["Point 1", "Point 2", "Point 3"]"""

        response = self.model.generate_content(prompt)
        return self._parse_response(response.text) 