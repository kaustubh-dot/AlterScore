import torch

def check_gpu():
    print(f"PyTorch version: {torch.__version__}")
    cuda_available = torch.cuda.is_available()
    print(f"CUDA Available: {cuda_available}")
    
    if cuda_available:
        print(f"Number of GPUs: {torch.cuda.device_count()}")
        print(f"Active GPU: {torch.cuda.get_device_name(0)}")
        print(f"Current device ID: {torch.cuda.current_device()}")
    else:
        print("No GPU detected. PyTorch will run on CPU.")

if __name__ == "__main__":
    check_gpu()
