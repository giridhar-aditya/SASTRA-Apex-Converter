#This file contains all the hyper parameters of the transformer model
from pathlib import Path

def get_config():
    return {
        "batch_size": 16,
        "num_epochs": 20,
        "lr": 10**-4,
        "seq_len": 64,
        "d_model": 1024,
    }

