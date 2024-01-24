import os
import re
import logging
import subprocess
import itertools
import qkeras
import tensorflow as tf
import numpy as np
import pandas as pd
from chisel4ml import generate
from chisel4ml import optimize
from chisel4ml.lbir.lbir_pb2 import FFTConfig
from chisel4ml.lbir.lbir_pb2 import LMFEConfig
from chisel4ml.preprocess.fft_layer import FFTLayer
from chisel4ml.preprocess.lmfe_layer import LMFELayer
import matplotlib.image

TOTAL_POWER_REGEX = r"^.*Total\sOn-Chip\sPower\s\(W\)\s*\|\s*(\d*\.?\d+)"
DYNAMIC_POWER_REGEX = r"^.*Dynamic\s*\(W\)\s*\|\s*(\d*\.?\d+)"
STATIC_POWER_REGEX = r"^.*Device\sStatic\s*\(W\)\s*\|\s*(\d*\.?\d+)"

TOTAL_UTIL_REGEX = r"^.*ProcessingPipeline\s*\|\s*\(top\)\s*\|\s*(\d+)\s*\|\s*\d+\s*\|\s*\d+\s*\|\s*\d+\s*\|\s*(\d+)\s*\|\s*(\d+)\s*\|\s*(\d+)\s*\|\s*(\d+)"
FFT_UTIL_REGEX = r"^.*peList_0\s*\|\s*FFTWrapper\s*\|\s*(\d+)\s*\|\s*\d+\s*\|\s*\d+\s*\|\s*\d+\s*\|\s*(\d+)\s*\|\s*(\d+)\s*\|\s*(\d+)\s*\|\s*(\d+)"
LMFE_UTIL_REGEX = r"^.*peList_1\s*\|\s*LMFEWrapper\s*\|\s*(\d+)\s*\|\s*\d+\s*\|\s*\d+\s*\|\s*\d+\s*\|\s*(\d+)\s*\|\s*(\d+)\s*\|\s*(\d+)\s*\|\s*(\d+)"

TIMING_REGEX = r"^\s*WNS\(ns\).*\n\s*.*\n\s*(\d*\.?\d+)"

def main():
    test_config = {
        "frame_length": (128, 256, 512, 1024),
        "num_frames":  (8, 16, 32, 64),
        "num_mels": (10, 13, 15, 20)
    }
    results_df = pd.DataFrame(columns=['frame_length', 'num_frames', 'num_mels', 'total_power', 'dynamic_power', 'static_power', \
                                       'total_luts', 'fft_luts', 'lmfe_luts', 'total_ff', 'fft_ff', 'lmfe_ff', 'total_ramb18', \
                                       'fft_ramb18', 'lmfe_ramb18', 'total_dsp', 'fft_dsp', 'lmfe_dsp', 'max_clock_ns', \
                                       'consumed_cycles', 'max_freq_mhz', 'max_throughput_msamples_sec'])
    script_file = os.path.abspath(__file__)
    script_dir = os.path.dirname(script_file)
    tests_dir = os.path.join(script_dir, "tests")
    os.makedirs(tests_dir)
    for test_case in itertools.product(*test_config.values()):
        tcdict = dict(zip(test_config.keys(), test_case))
        frame_length = int(tcdict["frame_length"])
        num_frames = int(tcdict["num_frames"])
        num_mels = int(tcdict["num_mels"])
        test_results = {'frame_length': frame_length, 'num_frames': num_frames, 'num_mels':num_mels}
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
        test_results['consumed_cycles'] = preproc_circuit.consumed_cycles
        test_case_dir = os.path.join(tests_dir, f"frame_length_{frame_length}_num_frames_{num_frames}_num_mels_{num_mels}")
        os.makedirs(test_case_dir)
        matplotlib.image.imsave(os.path.join(test_case_dir, "sw_res.png"), sw_res.numpy().reshape(num_frames, num_mels))
        matplotlib.image.imsave(os.path.join(test_case_dir, "hw_res.png"), hw_res.reshape(num_frames, num_mels))
        preproc_circuit.package(directory=test_case_dir)
        subprocess.run(["vivado", "-mode", "batch", "-source", "synth.tcl", "-tclargs", test_case_dir]) 
        power_file = os.path.join(test_case_dir, "synth", "post_synth_power.rpt")
        util_file = os.path.join(test_case_dir, "synth", "post_synth_utilization.rpt")
        timing_file = os.path.join(test_case_dir, "synth", "post_synth_timing_summary.rpt") 
    
        with open(power_file, "r") as file:
            power_rpt_string = ''.join(file.readlines())
            test_results['total_power'] = float(re.findall(TOTAL_POWER_REGEX, power_rpt_string, re.MULTILINE)[0])
            test_results['dynamic_power'] = float(re.findall(DYNAMIC_POWER_REGEX, power_rpt_string, re.MULTILINE)[0])
            test_results['static_power'] = float(re.findall(STATIC_POWER_REGEX, power_rpt_string, re.MULTILINE)[0])
        with open(util_file, "r") as file:
            util_rpt_string = ''.join(file.readlines())
            matches = re.findall(TOTAL_UTIL_REGEX, util_rpt_string, re.MULTILINE)
            test_results['total_luts'] = int(matches[0][0])
            test_results['total_ff'] = int(matches[0][1])
            test_results['total_ramb18'] = int(matches[0][3]) + 2 * int(matches[0][2])
            test_results['total_dsp'] = int(matches[0][4])
            matches = re.findall(FFT_UTIL_REGEX, util_rpt_string, re.MULTILINE)
            test_results['fft_luts'] = int(matches[0][0])
            test_results['fft_ff'] = int(matches[0][1])
            test_results['fft_ramb18'] = int(matches[0][3]) + 2 * int(matches[0][2])
            test_results['fft_dsp'] = int(matches[0][4])
            matches = re.findall(LMFE_UTIL_REGEX, util_rpt_string, re.MULTILINE)
            test_results['lmfe_luts'] = int(matches[0][0])
            test_results['lmfe_ff'] = int(matches[0][1])
            test_results['lmfe_ramb18'] = int(matches[0][3]) + 2 * int(matches[0][2])
            test_results['lmfe_dsp'] = int(matches[0][4])
        with open(timing_file, "r") as file:
            timing_rpt_string = ''.join(file.readlines())
            slack = re.findall(TIMING_REGEX, timing_rpt_string, re.MULTILINE)[0]
            max_clock_ns = 16.0 - float(slack)
            max_freq_mhz = (10**3) / max_clock_ns
            test_results['max_clock_ns'] = max_clock_ns
            test_results['max_freq_mhz'] = max_freq_mhz
            num_samples = num_frames * frame_length
            qtensor_proc_time = test_results['consumed_cycles'] * (max_clock_ns * 10**-9)
            average_sample_proc_time = qtensor_proc_time / num_samples
            test_results['max_throughput_msamples_sec'] = 1. / (average_sample_proc_time * 10.**6)
        results_df.loc[results_df.index.size] = test_results

    results_df.to_csv("results.csv")
if __name__ == "__main__":
    main()
