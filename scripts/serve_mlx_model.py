
import argparse
import sys
import subprocess
from pathlib import Path

def serve_model(model_path, adapter_path, host, port):
    """
    Starts an OpenAI-compatible API server using mlx_lm.server.
    """
    cmd = [
        sys.executable, "-m", "mlx_lm.server",
        "--model", model_path,
        "--host", host,
        "--port", str(port)
    ]
    
    if adapter_path:
        cmd.extend(["--adapter-path", adapter_path])

    print(f"🚀 Starting MLX Server on {host}:{port}...")
    print(f"   Model: {model_path}")
    if adapter_path:
        print(f"   Adapters: {adapter_path}")
    print("\nPress Ctrl+C to stop.")
    
    try:
        subprocess.run(cmd, check=True)
    except KeyboardInterrupt:
        print("\n🛑 Server stopped.")
    except subprocess.CalledProcessError as e:
        print(f"❌ Server failed: {e}")
        exit(1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Serve LoRA model via OpenAI-compatible API")
    parser.add_argument("--model", type=str, default="mlx-community/Mistral-7B-Instruct-v0.3-4bit", help="Base model path")
    parser.add_argument("--adapter-path", type=str, default="data/adapters", help="Path to trained adapters")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8080, help="Port to bind to")
    
    args = parser.parse_args()
    
    serve_model(args.model, args.adapter_path, args.host, args.port)
