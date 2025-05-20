from typing import List, Dict, Any
import google.generativeai as genai
from pathlib import Path
import PyPDF2
import chromadb
from chromadb.utils import embedding_functions
import json
from .summary_agent import SummaryAgent

class QueryAgent:
    def __init__(self):
        """Initialize the QueryAgent with ChromaDB and embedding function."""
        self.embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="all-MiniLM-L6-v2"
        )
        self.client = chromadb.Client()
        self.collection = self.client.create_collection(
            name="legal_docs",
            embedding_function=self.embedding_function
        )
        self._initialize_documents()
        self.model = genai.GenerativeModel('gemini-2.0-flash')
        self.summary_agent = SummaryAgent()

    def _initialize_documents(self):
        """Load and index legal documents."""
        docs_path = Path("data/legal_docs")
        for pdf_file in docs_path.glob("*.pdf"):
            with open(pdf_file, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                text = ""
                for page in pdf_reader.pages:
                    text += page.extract_text()
                
                # Split text into chunks
                chunks = self._split_text(text)
                
                # Add chunks to the collection
                self.collection.add(
                    documents=chunks,
                    ids=[f"{pdf_file.stem}_chunk_{i}" for i in range(len(chunks))]
                )

    def _split_text(self, text: str, chunk_size: int = 1000) -> List[str]:
        """Split text into chunks of approximately equal size."""
        words = text.split()
        chunks = []
        current_chunk = []
        current_size = 0
        
        for word in words:
            current_size += len(word) + 1  # +1 for space
            if current_size > chunk_size:
                chunks.append(" ".join(current_chunk))
                current_chunk = [word]
                current_size = len(word)
            else:
                current_chunk.append(word)
        
        if current_chunk:
            chunks.append(" ".join(current_chunk))
        
        return chunks

    def query(self, query: str, n_results: int = 3) -> List[Dict[str, Any]]:
        """Query the document collection for relevant information."""
        results = self.collection.query(
            query_texts=[query],
            n_results=n_results
        )
        
        # Format results
        formatted_results = []
        for i, doc in enumerate(results['documents'][0]):
            formatted_results.append({
                'content': doc,
                'score': results['distances'][0][i] if 'distances' in results else None
            })
        
        return formatted_results

    def _parse_response(self, response_text: str) -> Dict[str, Any]:
        """Safely parse the model's response into a dictionary."""
        try:
            # Clean the response text and ensure it's valid JSON
            cleaned_text = response_text.strip().replace('\n', ' ').replace('\r', '')
            return json.loads(cleaned_text)
        except json.JSONDecodeError:
            # Fallback response if parsing fails
            return {
                "result": response_text
            }

    def is_procedural_query(self, query: str) -> bool:
        """Determine if the query is asking about a procedure or process."""
        prompt = f"""Determine if this query is asking about a legal procedure or process:

Query: {query}

A procedural query would ask about steps, processes, or how to do something.
A non-procedural query would ask about definitions, explanations, or general information.

Return only "true" or "false" as a JSON string."""

        response = self.model.generate_content(prompt)
        result = self._parse_response(response.text)
        return result.get("result", "false").lower() == "true"

    def extract_relevant_info(self, query: str, documents: List[Dict[str, str]]) -> Dict[str, Any]:
        """Extract relevant information from documents based on the query."""
        # Format documents for the prompt
        docs_text = "\n\n".join([f"Document {i+1}:\n{doc['content']}" 
                                for i, doc in enumerate(documents)])

        prompt = f"""Based on this query and documents, extract relevant information:

Query: {query}

Documents:
{docs_text}

Please:
1. Identify the most relevant passages
2. Note which documents they came from
3. Explain why they are relevant

Format the response as JSON with the following structure:
{{
    "relevant_passages": [
        {{
            "text": "passage text",
            "document_index": document_number,
            "relevance": "explanation of relevance"
        }}
    ]
}}"""

        response = self.model.generate_content(prompt)
        result = self._parse_response(response.text)
        
        # Handle missing fields
        if 'relevant_passages' not in result:
            return {
                'relevant_passages': [
                    {
                        'text': doc['content'],
                        'document_index': i,
                        'relevance': 'Potentially relevant to the query'
                    }
                    for i, doc in enumerate(documents)
                ]
            }
        return result

    def process_query(self, query: str) -> Dict[str, Any]:
        """Process a query and return a structured response."""
        # Get relevant document chunks
        relevant_chunks = self.query(query)
        
        # Extract relevant information
        relevant_info = self.extract_relevant_info(query, relevant_chunks)
        
        # Combine relevant passages
        combined_text = "\n\n".join([p["text"] for p in relevant_info["relevant_passages"]])
        
        # Check if query is procedural
        is_procedural = self.is_procedural_query(query)
        
        # Get simplified explanation and key points
        simplified = self.summary_agent.simplify_text(combined_text)
        key_points = self.summary_agent.extract_key_points(combined_text)
        
        # Handle missing fields in responses
        response = {
            "simple_explanation": simplified.get("simplified_text", combined_text),
            "key_points": key_points.get("key_points", []),
            "important_terms": simplified.get("terms", []),
            "warnings_and_deadlines": simplified.get("warnings", []),
            "sources": [
                {
                    "text": p["text"],
                    "document": relevant_chunks[p["document_index"]].get("title", f"Document {p['document_index']}"),
                    "relevance": p["relevance"]
                }
                for p in relevant_info["relevant_passages"]
            ]
        }
        
        # Add step-by-step guide for procedural queries
        if is_procedural:
            guide = self.summary_agent.create_step_by_step_guide(combined_text)
            response["step_by_step_guide"] = guide.get("steps", [])
            
        return response 