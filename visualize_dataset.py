import os
import re
import logging
import tensorflow as tf
import qkeras
import numpy as np
from chisel4ml import generate
from chisel4ml import optimize
from chisel4ml.lbir.lbir_pb2 import FFTConfig
from chisel4ml.lbir.lbir_pb2 import LMFEConfig
from chisel4ml.preprocess.fft_layer import FFTLayer
from chisel4ml.preprocess.lmfe_layer import LMFELayer
from chisel4ml.chisel4ml_server import connect_to_server
import matplotlib.image
import tensorflow_datasets as tfds

def main():

    frame_length = 512
    num_frames = 32
    num_mels = 20
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

    c4ml_dir = f"/tmp/.chisel4ml0"
    c4ml_port = 50000
    server = connect_to_server() #(c4ml_dir, c4ml_port)
    preproc_circuit = generate.circuit(
        opt_model=preproc_model,
        use_verilator=True,
        server=server
    )

    
    def pad_signal(signal):
        frame_length = 512
        num_frames = 32
        act_len = num_frames * frame_length # 16384
        signal = np.pad(signal, (0, act_len-len(signal))) # pad after	
    	# we model a 12-bit signed input
        signal = np.round(signal.astype(np.float32) * (2**11 / 2**16))
        frames = signal.reshape([1, num_frames, frame_length])
        return frames 

    test_ds, info = tfds.load('speech_commands', split='test', with_info=True)
    label_names = info.features['label'].names
    spec_ex = {}
    for ex in test_ds:
        if ex['label'].numpy() not in spec_ex.keys():
            spec_ex[ex['label'].numpy()] = pad_signal(ex['audio'])
        if len(spec_ex) == len(label_names):
            break

    script_file = os.path.abspath(__file__)
    script_dir = os.path.dirname(script_file)
    tests_dir = os.path.join(script_dir, "tests_vis")
    test_case_dir = os.path.join(tests_dir, f"frame_length_{frame_length}_num_frames_{num_frames}_num_mels_{num_mels}")
    os.makedirs(test_case_dir)
    for key in spec_ex:
        sw_res = preproc_model(spec_ex[key])
        hw_res = preproc_circuit(spec_ex[key], sim_timeout_sec=600)
        assert np.allclose(
            sw_res.numpy().flatten(),
            hw_res.flatten(),
            atol=1,
            rtol=0.05
        )
        matplotlib.image.imsave(os.path.join(test_case_dir, f"sw_res_{label_names[key]}.png"), sw_res.numpy().reshape(num_frames, num_mels).T)
        matplotlib.image.imsave(os.path.join(test_case_dir, f"hw_res_{label_names[key]}.png"), hw_res.reshape(num_frames, num_mels).T)
    

if __name__ == "__main__":
    main()
