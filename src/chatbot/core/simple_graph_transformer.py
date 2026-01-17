from typing import List, Optional
from langchain_core.documents import Document
from langchain_community.graphs.graph_document import GraphDocument, Node, Relationship
from langchain_core.language_models import BaseChatModel
from langchain_core.prompts import ChatPromptTemplate
import json_repair

class SimpleGraphTransformer:
    """
    A robust graph transformer designed for smaller local LLMs (like Llama 3).
    Uses json_repair to handle malformed outputs and enforces schema safety.
    """
    def __init__(self, llm: BaseChatModel):
        self.llm = llm
        self.prompt = ChatPromptTemplate.from_messages([
            ("user", """You are a data extraction expert. Extract entities and relationships from the text.
            
            Return ONLY a JSON object with this format:
            {{
                "relationships": [
                    {{
                        "head": "Entity1",
                        "head_type": "Type1",
                        "relation": "RELATION_TYPE",
                        "tail": "Entity2",
                        "tail_type": "Type2"
                    }}
                ]
            }}
            
            Rules:
            1. Use common types: Person, Organization, Location, Concept, Event, etc.
            2. specific types are better (e.g. "Python Library" instead of "Concept").
            3. Relation types should be UPPER_CASE (e.g. WORKS_AT, LOCATED_IN, USES).
            4. If no relationships found, return {{"relationships": []}}.
            5. Do not add any explanation or preamble. Only JSON.
            
            Text to process:
            {input}""")
        ])
        self.chain = self.prompt | llm

    def convert_to_graph_documents(self, documents: List[Document]) -> List[GraphDocument]:
        results = []
        for doc in documents:
            graph_doc = self._process_document(doc)
            if graph_doc:
                results.append(graph_doc)
        return results

    def _process_document(self, document: Document) -> Optional[GraphDocument]:
        try:
            # Invoke LLM
            response = self.chain.invoke({"input": document.page_content})
            content = response.content
            
            # Parse JSON with repair
            data = json_repair.loads(content)
            
            # Extract relationships safely
            rels = data.get("relationships", [])
            if not isinstance(rels, list):
                # Try to find list if it's nested or malformed
                if isinstance(data, list):
                    rels = data
                else:
                    return None

            nodes_dict = {} # Map id -> Node
            relationships = []

            for r in rels:
                # robust check for keys
                if not isinstance(r, dict):
                    continue
                
                head_id = r.get("head")
                tail_id = r.get("tail")
                
                if not head_id or not tail_id:
                    continue
                    
                head_type = r.get("head_type", "Concept")
                tail_type = r.get("tail_type", "Concept")
                rel_type = r.get("relation", "RELATED_TO")
                
                # Create/Get Nodes
                if head_id not in nodes_dict:
                    nodes_dict[head_id] = Node(id=head_id, type=head_type)
                if tail_id not in nodes_dict:
                    nodes_dict[tail_id] = Node(id=tail_id, type=tail_type)
                
                # Create Relationship
                relationships.append(Relationship(
                    source=nodes_dict[head_id],
                    target=nodes_dict[tail_id],
                    type=rel_type.replace(" ", "_").upper()
                ))

            if not nodes_dict and not relationships:
                return None

            return GraphDocument(
                nodes=list(nodes_dict.values()),
                relationships=relationships,
                source=document
            )

        except Exception as e:
            print(f"SimpleGraphTransformer Error: {e}")
            return None
