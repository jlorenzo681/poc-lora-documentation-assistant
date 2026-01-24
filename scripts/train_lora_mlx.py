
import argparse
import sys
import subprocess
from pathlib import Path

def train_lora(model_path, data_dir, adapter_path, batch_size=2, lorap_layers=16, iters=1000, learning_rate=2e-5):
    """
    Wrapper to run mlx_lm.lora.
    """
    # mlx_lm.lora is a command line tool, but we can also import it if we want deeper integration.
    # For simplicity and stability, we'll invoke the CLI using subprocess which ensures we run in the right env context if called from shell.
    
    cmd = [
        sys.executable, "-m", "mlx_lm", "lora",
        "--model", model_path,
        "--train",
        "--data", data_dir,
        "--adapter-path", adapter_path,
        "--batch-size", str(batch_size),
        "--num-layers", str(lorap_layers),
        "--iters", str(iters),
        "--learning-rate", str(learning_rate),
        "--save-every", "100",
        "--steps-per-eval", "100"
    ]
    
    print(f"Running command: {' '.join(cmd)}")
    try:
        subprocess.run(cmd, check=True)
        print(f"Training completed. Adapters saved to {adapter_path}")
    except subprocess.CalledProcessError as e:
        print(f"Training failed: {e}")
        exit(1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run LoRA training with MLX")
    parser.add_argument("--model", type=str, default="mlx-community/Mistral-7B-Instruct-v0.3-4bit", help="Hugging Face model ID or path")
    parser.add_argument("--data", type=str, default="data/mlx_data", help="Directory containing train.jsonl and valid.jsonl")
    parser.add_argument("--adapter-path", type=str, default="data/adapters", help="Path to save adapters")
    parser.add_argument("--batch-size", type=int, default=2, help="Batch size (lower for less memory)")
    parser.add_argument("--iters", type=int, default=1000, help="Number of training iterations")
    parser.add_argument("--learning-rate", type=float, default=2e-5, help="Learning rate")
    
    args = parser.parse_args()
    
    # Resolve paths
    base_path = Path(__file__).resolve().parent.parent
    data_dir = str(base_path / args.data)
    adapter_path = str(base_path / args.adapter_path)
    
    train_lora(args.model, data_dir, adapter_path, args.batch_size, 16, args.iters, args.learning_rate)
