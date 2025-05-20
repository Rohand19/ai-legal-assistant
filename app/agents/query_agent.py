from typing import List, Dict, Any
import google.generativeai as genai
from pathlib import Path
import PyPDF2
import sys
import __main__
import site
import sqlite3
import os

# Check SQLite version
print(f"SQLite Version: {sqlite3.sqlite_version}")

# For macOS, we'll use the system SQLite
if sys.platform == "darwin":  # macOS
    print("Running on macOS, using system SQLite")
else:
    # On other systems, try to use pysqlite3 if available
    try:
        import pysqlite3
        sys.modules['sqlite3'] = pysqlite3
    except ImportError:
        print("pysqlite3 not found, using system sqlite3")
        if sqlite3.sqlite_version_info < (3, 35, 0):
            print("Warning: Your system's SQLite version might be too old for ChromaDB")
            print("Required version: 3.35.0 or higher")

import chromadb
from chromadb.utils import embedding_functions
import json
from .summary_agent import SummaryAgent

class QueryAgent:
    def __init__(self, api_key: str):
        """Initialize the Query Agent with Google API key."""
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-2.0-flash')
        
        # Initialize ChromaDB with persistent storage
        try:
            # Create persistent directory if it doesn't exist
            persist_dir = Path("chroma_db")
            persist_dir.mkdir(exist_ok=True)
            
            self.embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
                model_name="all-MiniLM-L6-v2"
            )
            self.client = chromadb.PersistentClient(path=str(persist_dir))
            
            # Try to get existing collection or create a new one
            try:
                self.collection = self.client.get_collection(
                    name="legal_docs",
                    embedding_function=self.embedding_function
                )
                print("Found existing collection 'legal_docs'")
            except ValueError:  # Collection doesn't exist
                print("Creating new collection 'legal_docs'")
                self.collection = self.client.create_collection(
                    name="legal_docs",
                    embedding_function=self.embedding_function
                )
                self._initialize_documents()
        except Exception as e:
            print(f"Warning: ChromaDB initialization failed: {str(e)}")
            self.collection = None
        
    def search_legal_documents(self, query: str) -> Dict[str, Any]:
        """Search through legal documents to find relevant information."""
        # First check if it's a non-legal query using LLM
        query_type_prompt = f"""Analyze if this query is related to legal matters or not:

Query: "{query}"

Consider:
1. Is this a general greeting (hi, hello, etc.)?
2. Is this expressing gratitude (thanks, thank you, etc.)?
3. Is this about non-legal topics (weather, food, entertainment, etc.)?
4. Is this a casual conversation starter?

Return a JSON response in this format:
{{
    "is_legal_query": boolean,
    "response": "If not a legal query, provide a polite response directing user to ask legal questions. If legal query, leave empty."
}}"""

        try:
            query_type_response = self.model.generate_content(query_type_prompt)
            query_analysis = self._parse_json_response(query_type_response.text)
            
            if not query_analysis.get("is_legal_query", True):
                return {
                    "simple_explanation": query_analysis.get("response", "I'm specifically designed to help with legal questions. Could you please ask me a legal-related question?"),
                    "key_points": [],
                    "important_terms": [],
                    "warnings_and_deadlines": [],
                    "step_by_step_guide": [],
                    "sources": []
                }
        except Exception as e:
            print(f"Warning: Query type analysis failed: {str(e)}")
        
        # If it's a legal query or analysis failed, proceed with normal processing
        if self.collection is not None:
            try:
                relevant_chunks = self.query(query)
                if relevant_chunks:
                    return self._process_chromadb_results(query, relevant_chunks)
            except Exception as e:
                print(f"Warning: ChromaDB search failed: {str(e)}")
        
        # Fallback to direct Gemini query
        prompt = f"""You are a specialized legal document search agent. Your task is to find and extract relevant information 
        from Indian legal documents for the following query:
        
        Query: {query}
        
        Search through these sources:
        1. Guide to Litigation in India
        2. Legal Compliance & Corporate Laws by ICAI
        
        Return a JSON object with the following structure:
        {{
            "relevant_sections": [
                {{
                    "source": "document name",
                    "section": "section name/number",
                    "content": "relevant text",
                    "relevance_score": float (0-1)
                }}
            ],
            "legal_context": "brief explanation of how these sections relate to the query",
            "applicable_laws": ["list of relevant laws and regulations"],
            "sources": [
                {{
                    "title": "document title",
                    "description": "clear description of what this source contributes"
                }}
            ]
        }}"""

        try:
            response = self.model.generate_content(prompt)
            return self._parse_json_response(response.text)
        except Exception as e:
            return {
                "simple_explanation": f"Error searching documents: {str(e)}",
                "key_points": [],
                "important_terms": [],
                "warnings_and_deadlines": [],
                "step_by_step_guide": [],
                "sources": []
            }
    
    def _process_chromadb_results(self, query: str, chunks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Process ChromaDB search results into the expected format."""
        relevant_sections = []
        for chunk in chunks:
            # Format the source information more readably
            source_doc = chunk.get("metadata", {}).get("source", "Unknown")
            section_id = chunk.get("metadata", {}).get("section", "Unknown")
            
            # Clean up source name
            source_name = source_doc.replace("_", " ").title()
            
            # Format the section identifier
            if section_id.startswith("chunk_"):
                section_num = section_id.split("_")[1]
                section_desc = f"Section {section_num}"
            else:
                section_desc = section_id.replace("_", " ").title()
            
            relevant_sections.append({
                "source": source_name,
                "section": section_desc,
                "content": chunk.get("document", ""),
                "relevance_score": chunk.get("distance", 1.0)
            })
        
        # Use Gemini to analyze the context and applicable laws
        context_prompt = f"""Based on these document sections and the query:
        Query: {query}
        
        Sections:
        {json.dumps(relevant_sections, indent=2)}
        
        Provide:
        1. A brief explanation of how these sections relate to the query
        2. A list of applicable laws and regulations
        3. A summary of each source's contribution
        
        Return as JSON:
        {{
            "legal_context": "explanation",
            "applicable_laws": ["law1", "law2", ...],
            "sources": [
                {{
                    "title": "document title",
                    "description": "clear description of what this source contributes"
                }}
            ]
        }}"""
        
        try:
            response = self.model.generate_content(context_prompt)
            context_result = self._parse_json_response(response.text)
            return {
                "relevant_sections": relevant_sections,
                "legal_context": context_result.get("legal_context", ""),
                "applicable_laws": context_result.get("applicable_laws", []),
                "sources": context_result.get("sources", [
                    {
                        "title": section["source"],
                        "description": f"From {section['section']}: {section['content'][:200]}..."
                    }
                    for section in relevant_sections
                ])
            }
        except Exception as e:
            return {
                "relevant_sections": relevant_sections,
                "legal_context": "Error analyzing context",
                "applicable_laws": [],
                "sources": [
                    {
                        "title": section["source"],
                        "description": f"From {section['section']}: {section['content'][:200]}..."
                    }
                    for section in relevant_sections
                ]
            }
    
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

    def _initialize_documents(self):
        """Load and index legal documents."""
        try:
            # Try multiple possible paths for the docs directory
            possible_paths = [
                Path("data/legal_docs"),  # Local development path
                Path(__file__).parent.parent.parent / "data" / "legal_docs",  # Relative to this file
                Path("/mount/src/demo/data/legal_docs"),  # Streamlit Cloud path
                Path.home() / "data/legal_docs"  # Home directory
            ]
            
            # Print current working directory and all possible paths
            print(f"Current working directory: {os.getcwd()}")
            print("Searching for documents in:")
            for path in possible_paths:
                print(f"- {path} (exists: {path.exists()})")
            
            docs_path = None
            for path in possible_paths:
                if path.exists():
                    docs_path = path
                    print(f"Found documents directory at: {path}")
                    # List all files in the directory
                    print("Directory contents:")
                    for item in path.iterdir():
                        print(f"  - {item.name} ({item.stat().st_size} bytes)")
                    break
            
            if not docs_path:
                print(f"Warning: Document directory not found in any of these locations: {[str(p) for p in possible_paths]}")
                return
            
            pdf_files = list(docs_path.glob("*.pdf"))
            if not pdf_files:
                print(f"Warning: No PDF files found in {docs_path}")
                return
                
            print(f"Found {len(pdf_files)} PDF files")
            for pdf_file in pdf_files:
                try:
                    print(f"\nProcessing file: {pdf_file}")
                    print(f"File size: {pdf_file.stat().st_size} bytes")
                    print(f"File exists: {pdf_file.exists()}")
                    print(f"File is readable: {os.access(pdf_file, os.R_OK)}")
                    
                    with open(pdf_file, 'rb') as file:
                        pdf_reader = PyPDF2.PdfReader(file)
                        print(f"Number of pages: {len(pdf_reader.pages)}")
                        text = ""
                        for i, page in enumerate(pdf_reader.pages):
                            page_text = page.extract_text()
                            text += page_text
                            if i == 0:  # Print first page sample
                                print(f"Sample text from first page: {page_text[:200]}...")
                        
                        # Split text into chunks
                        chunks = self._split_text(text)
                        print(f"Created {len(chunks)} chunks")
                        print(f"Average chunk size: {sum(len(c) for c in chunks) / len(chunks) if chunks else 0:.2f} characters")
                        
                        # Add chunks to the collection
                        self.collection.add(
                            documents=chunks,
                            ids=[f"{pdf_file.stem}_chunk_{i}" for i in range(len(chunks))],
                            metadatas=[{
                                "source": pdf_file.stem,
                                "section": f"chunk_{i}"
                            } for i in range(len(chunks))]
                        )
                        print(f"Successfully indexed {pdf_file.name}")
                        
                        # Verify chunks were added
                        result = self.collection.query(
                            query_texts=["test query"],
                            n_results=1
                        )
                        print(f"Verification query returned {len(result['documents'][0])} results")
                        
                except Exception as e:
                    print(f"Warning: Failed to process {pdf_file}: {str(e)}")
                    import traceback
                    print(f"Traceback: {traceback.format_exc()}")
        except Exception as e:
            print(f"Warning: Document initialization failed: {str(e)}")
            import traceback
            print(f"Traceback: {traceback.format_exc()}")

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
        if self.collection is None:
            return []
            
        results = self.collection.query(
            query_texts=[query],
            n_results=n_results
        )
        
        # Format results
        return [
            {
                'document': doc,
                'metadata': results.get('metadatas', [[{}]])[0][i],
                'distance': results.get('distances', [[0]])[0][i] if 'distances' in results else None
            }
            for i, doc in enumerate(results['documents'][0])
        ]

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