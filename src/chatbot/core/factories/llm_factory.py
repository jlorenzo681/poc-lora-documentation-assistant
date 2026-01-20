"""
LLM Factory Module
Centralizes the creation of LLM instances for easy reuse across the application.
"""

from typing import Optional, Literal, Any
import config.settings as settings

class LLMFactory:
    """
    Factory class to create LLM instances based on configuration.
    """

    @staticmethod
    def create_llm(
        provider: Literal["mlx", "lmstudio"] = "mlx",
        model_name: str = "local-model",
        temperature: float = 0.3,
        max_tokens: int = 500,
        mlx_model_path: Optional[str] = None,
        mlx_adapter_path: Optional[str] = None,
        lmstudio_base_url: str = "http://localhost:1234/v1"
    ) -> Any:
        """
        Create and return an LLM instance.
        """
        if provider == "mlx":
            try:
                # Try to load local MLX
                from .mlx_llm import MLXChatModel
                
                # Use provided paths or fall back to settings
                final_model_path = mlx_model_path or getattr(settings, "MLX_MODEL_PATH", None)
                final_adapter_path = mlx_adapter_path or getattr(settings, "MLX_ADAPTER_PATH", None)
                
                if not final_model_path:
                    # If strictly local MLX is required but path missing, we might log warning
                    # But if we want fallback to client, we proceed to except block if import works but path fails? 
                    # Actually MLXChatModel needs path.
                    pass

                # If local MLX import works and we have a path (or want to try default), go ahead
                llm = MLXChatModel(
                    model_path=final_model_path,
                    adapter_path=final_adapter_path,
                    temperature=temperature,
                    max_tokens=max_tokens
                )
                print(f"⚡ LLM Factory: Initialized MLX LoRA LLM (Local)")
                return llm

            except (ImportError, Exception) as e:
                # Fallback to MLX Client mode (Docker)
                print(f"⚠ LLM Factory: Local MLX init failed ({e}). Attempting Docker/Client mode.")
                
                from langchain_openai import ChatOpenAI
                mlx_base_url = getattr(settings, "MLX_SERVER_BASE_URL", "http://host.docker.internal:8080/v1")
                
                llm = ChatOpenAI(
                    base_url=mlx_base_url,
                    api_key="mlx",
                    model=model_name,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    timeout=300.0,
                )
                print(f"📡 LLM Factory: Initialized MLX Client for Server: {mlx_base_url}")
                return llm

        elif provider == "lmstudio":
            from langchain_openai import ChatOpenAI
            llm = ChatOpenAI(
                base_url=lmstudio_base_url,
                api_key="lm-studio",
                model=model_name,
                temperature=temperature,
                max_tokens=max_tokens,
                timeout=300.0,
            )
            print(f"🤖 LLM Factory: Initialized LM Studio LLM: {model_name}")
            return llm

        else:
            raise ValueError(f"Unsupported LLM provider: {provider}")
