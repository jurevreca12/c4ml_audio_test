import os
import logging
import subprocess
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
import matplotlib.image


def main():
    test_config = {
        "frame_length": (128, 256, 512, 1024),
        "num_frames": (8, 16, 32, 64),
        "num_mels": (10, 13, 15, 20)
    }
    script_file = os.path.abspath(__file__)
    script_dir = os.path.dirname(script_file)
    tests_dir = os.path.join(script_dir, "tests")
    os.makedirs(tests_dir)
    for test_case in itertools.product(*test_config.values()):
        tcdict = dict(zip(test_config.keys(), test_case))
        frame_length = tcdict["frame_length"]
        num_frames = tcdict["num_frames"]
        num_mels = tcdict["num_mels"]
        logging.info(f"\n \
______________________________________________________________________________________\n \
TEST CASE: frame_length:{frame_length}, num_frames:{num_frames}, num_mels:{num_mels}\n \
______________________________________________________________________________________\n")
        preproc_model = tf.keras.Sequential()
        preproc_model.add(tf.keras.layers.Input(num_frames, frame_length))
        preproc_model.add(
            qkeras.QActivation(
                qkeras.quantized_bits(12, 11, keep_negative=True, alpha=1)
            )
        )
        preproc_model.add(
            FFTLayer(
                FFTConfig(
                    fft_size=frame_length,
                    num_frames=num_frames,
                    win_fn=np.hamming(frame_length),
                )
            )
        )
        preproc_model.add(
            LMFELayer(
                LMFEConfig(
                    fft_size=frame_length,
                    num_frames=num_frames,
                    num_mels=num_mels,
                )
            )
        )
        preproc_circuit = generate.circuit(
            opt_model=preproc_model,
            use_verilator=True
        )

        # we model a 12-bit signed input
        amplitude = 0.6
        time = np.linspace(0, 1, num_frames * frame_length)
        wave = np.sin(2 * np.pi * 60 * time).reshape(num_frames, frame_length)
        frames = np.round(wave * 2047 * amplitude)
        
        sw_res = preproc_model(frames.reshape(1, num_frames, frame_length))
        hw_res = preproc_circuit(frames, sim_timeout_sec=600)
        assert np.allclose(
            sw_res.numpy().flatten(),
            hw_res.flatten(),
            atol=10,
            rtol=0.05
        )
        test_case_dir = os.path.join(tests_dir, f"frame_length_{frame_length}_num_frames_{num_frames}_num_mels_{num_mels}")
        os.makedirs(test_case_dir)
        matplotlib.image.imsave(os.path.join(test_case_dir, "sw_res.png"), sw_res.numpy().reshape(num_frames, num_mels))
        matplotlib.image.imsave(os.path.join(test_case_dir, "hw_res.png"), hw_res.reshape(num_frames, num_mels))
        preproc_circuit.package(directory=test_case_dir)
        subprocess.run(["vivado", "-mode", "batch", "-source", "synth.tcl", "-tclargs", test_case_dir], capture_output=True) 

if __name__ == "__main__":
    main()
