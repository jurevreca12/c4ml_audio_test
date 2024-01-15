import itertools
import qkeras
import tensorflow as tf
import numpy as np
from chisel4ml import generate
from chisel4ml import optimize
from chisel4ml.lbir.lbir_pb2 import FFTConfig
from chisel4ml.lbir.lbir_pb2 import LMFEConfig
from chisel4ml.preprocess.fft_layer import FFTLayer
from chisel4ml.preprocess.lmfe_layer import LMFELayer


def train_and_generate_models():
    test_config = {
        "frame_length": (64, 128, 256, 512, 1024),
        "num_frames": (8, 16, 32, 64),
        "num_mels": (10, 13, 15, 20, 26)
    }

if __name__ == "__main__":
    train_and_generate_models()
