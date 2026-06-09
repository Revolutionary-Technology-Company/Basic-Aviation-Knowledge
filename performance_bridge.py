import os
import psutil
import torch # If utilizing CUDA for matrix math
import numba
def crank_performance():
    """Forces CPU affinity and GPU max-clock settings."""
    proc = psutil.Process()
    proc.cpu_affinity(list(range(psutil.cpu_count())))
    os.system("nvidia-smi -pm 1") 
    os.system("nvidia-smi -lgc 1500,1800") # Lock core clock range
    numba.set_num_threads(psutil.cpu_count())
if __name__ == "__main__":
    crank_performance()
