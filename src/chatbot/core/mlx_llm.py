
from typing import Any, List, Optional, Dict
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import BaseMessage, AIMessage, HumanMessage, SystemMessage
from langchain_core.outputs import ChatResult, ChatGeneration
from langchain_core.callbacks.manager import CallbackManagerForLLMRun
import mlx_lm
import glob
import os

class MLXChatModel(BaseChatModel):
    """
    A custom LangChain ChatModel that uses mlx_lm for inference.
    """
    model_path: str
    adapter_path: Optional[str] = None
    model: Any = None
    tokenizer: Any = None
    temperature: float = 0.7
    max_tokens: int = 500

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._load_model()

    def _load_model(self):
        """Loads the model and adapter."""
        if self.model is not None:
             return

        print(f"Loading MLX model from {self.model_path}...")
        if self.adapter_path:
             print(f"Loading adapters from {self.adapter_path}...")
             
        self.model, self.tokenizer = mlx_lm.load(
            self.model_path,
            adapter_path=self.adapter_path,
            tokenizer_config={"trust_remote_code": True}
        )

    def _generate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> ChatResult:
        
        # Convert messages to format expected by tokenizer apply_chat_template
        # or simple string concatenation if template not available.
        # Mistral usually supports chat template.
        
        formatted_messages = []
        for msg in messages:
            role = "user"
            if isinstance(msg, AIMessage):
                role = "assistant"
            elif isinstance(msg, SystemMessage):
                role = "system"
            elif isinstance(msg, HumanMessage):
                role = "user"
            
            formatted_messages.append({"role": role, "content": msg.content})

        prompt = self.tokenizer.apply_chat_template(
            formatted_messages, 
            tokenize=False, 
            add_generation_prompt=True
        )

        response_text = mlx_lm.generate(
            self.model,
            self.tokenizer,
            prompt=prompt,
            max_tokens=self.max_tokens,
            temp=self.temperature,
            verbose=False
        )

        generation = ChatGeneration(message=AIMessage(content=response_text))
        return ChatResult(generations=[generation])

    @property
    def _llm_type(self) -> str:
        return "mlx-chat"
