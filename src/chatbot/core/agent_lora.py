"""
Agent LoRA Module
Implements the multi-agent orchestration for the LoRA chatbot using LangGraph.
"""

from typing import TypedDict, List, Literal, Dict, Any
from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langgraph.graph import StateGraph, END
from .storage.vector_store_manager import VectorStoreManager
from .lora_chain import LoRAChain

class LoRAState(TypedDict):
    """
    Represents the state of the agent LoRA.
    """
    question: str
    generation: str
    documents: List[Document]
    web_search_needed: bool


class AgentLoRA:
    """
    Manages the multi-agent LoRA workflow.
    """

    def __init__(self, vector_store_manager: VectorStoreManager, lora_chain: LoRAChain):
        """
        Initialize the agent LoRA.

        Args:
            vector_store_manager: Initialized VectorStoreManager
            lora_chain: Initialized LoRAChain (provides LLM)
        """
        self.vector_store_manager = vector_store_manager
        self.lora_chain = lora_chain
        self.llm = lora_chain.llm  # Reuse the LLM from LoRAChain
        self.app = self._build_graph()

    def _build_graph(self):
        """
        Build and compile the state graph.
        """
        workflow = StateGraph(LoRAState)

        # Define nodes
        workflow.add_node("retrieve", self.retrieve)
        workflow.add_node("grade_documents", self.grade_documents)
        workflow.add_node("generate", self.generate)
        workflow.add_node("rewrite_query", self.rewrite_query)

        # Define edges
        workflow.set_entry_point("retrieve")
        workflow.add_edge("retrieve", "grade_documents")
        
        # Conditional edge from grader
        workflow.add_conditional_edges(
            "grade_documents",
            self.decide_to_generate,
            {
                "generate": "generate",
                "rewrite_query": "rewrite_query",
            },
        )
        
        workflow.add_edge("rewrite_query", "retrieve")
        workflow.add_edge("generate", END)

        return workflow.compile()

    def retrieve(self, state: LoRAState) -> Dict[str, Any]:
        """
        Retrieve documents from vector store.
        """
        print("---RETRIEVE---")
        question = state["question"]
        
        # Retrieval
        documents = self.vector_store_manager.similarity_search(question, k=4)
        return {"documents": documents, "question": question}

    def grade_documents(self, state: LoRAState) -> Dict[str, Any]:
        """
        Determines whether the retrieved documents are relevant to the question.
        If any document is not relevant, we will set a flag to run web search (or rewrite query).
        """
        print("---CHECK DOCUMENT RELEVANCE---")
        question = state["question"]
        documents = state["documents"]
        
        # Score each doc
        filtered_docs = []
        web_search_needed = False
        
        # Simple grader prompt
        system = """You are a grader assessing relevance of a retrieved document to a user question. \n 
        If the document contains keyword(s) or semantic meaning related to the user question, grade it as relevant. \n
        Give a binary score 'yes' or 'no' score to indicate whether the document is relevant to the question."""
        
        grade_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", system),
                ("human", "Retrieved document: \n\n {document} \n\n User question: {question}"),
            ]
        )
        
        grader = grade_prompt | self.llm | StrOutputParser()
        
        for d in documents:
            score = grader.invoke({"question": question, "document": d.page_content})
            grade = score.lower().strip()
            if "yes" in grade:
                print("---GRADE: DOCUMENT RELEVANT---")
                filtered_docs.append(d)
            else:
                print("---GRADE: DOCUMENT NOT RELEVANT---")
                continue
                
        if not filtered_docs:
            web_search_needed = True
            print("---GRADE: NO RELEVANT DOCUMENTS FOUND, NEED REWRITE---")
            
        return {"documents": filtered_docs, "question": question, "web_search_needed": web_search_needed}

    def generate(self, state: LoRAState) -> Dict[str, Any]:
        """
        Generate answer.
        """
        print("---GENERATE---")
        question = state["question"]
        documents = state["documents"]
        
        # Reuse existing chain logic if possible or build ad-hoc
        # Using a simple chain for generation here using the LoRAChain's LLM
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", self.lora_chain.system_prompt),
            ("human", "Context: {context} \n\n Question: {question}")
        ])
        
        # Combine docs
        context = "\n\n".join([d.page_content for d in documents])
        
        chain = prompt | self.llm | StrOutputParser()
        generation = chain.invoke({"context": context, "question": question})
        
        return {"documents": documents, "question": question, "generation": generation}

    def rewrite_query(self, state: LoRAState) -> Dict[str, Any]:
        """
        Transform the query to produce a better question.
        """
        print("---TRANSFORM QUERY---")
        question = state["question"]
        
        msg = [
            ("system", "You area a helpful assistant that optimizes input questions for vector, semantic search."),
            ("human", f"Look at the input and try to reason about the underlying semantic intent / meaning. \n Here is the initial question: {question} \n Formulate an improved question: "),
        ]
        
        chain = ChatPromptTemplate.from_messages(msg) | self.llm | StrOutputParser()
        better_question = chain.invoke({})
        
        return {"question": better_question}

    def decide_to_generate(self, state: LoRAState) -> Literal["generate", "rewrite_query"]:
        """
        Determines whether to generate an answer, or re-generate a question.
        """
        print("---DECIDE TO GENERATE---")
        if state["web_search_needed"]:
            # In a full agent, we might go to web search here. 
            # For now, we rewrite query and try retrieving again.
            # To avoid infinite loops, we might check loop count usually, 
            # but for this MVP we'll just rewrite.
            print("---DECISION: REWRITE QUERY---")
            return "rewrite_query"
        else:
            print("---DECISION: GENERATE---")
            return "generate"

    def invoke(self, question: str) -> Dict[str, Any]:
        """
        Run the graph with a question.
        """
        inputs = {"question": question}
        return self.app.invoke(inputs)
