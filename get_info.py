import os
import logging
import subprocess
import itertools
import re

TOTAL_POWER_REGEX = r"^.*Total\sOn-Chip\sPower\s\(W\)\s*\|\s*(\d*\.?\d+)"
DYNAMIC_POWER_REGEX = r"^.*Dynamic\s*\(W\)\s*\|\s*(\d*\.?\d+)"
STATIC_POWER_REGEX = r"^.*Device\sStatic\s*\(W\)\s*\|\s*(\d*\.?\d+)"

TOTAL_UTIL_REGEX = r"^.*ProcessingPipeline\s*\|\s*\(top\)\s*\|\s*(\d+)\s*\|\s*\d+\s*\|\s*\d+\s*\|\s*\d+\s*\|\s*(\d+)\s*\|\s*\d+\s*\|\s*(\d+)\s*\|\s*(\d+)"
FFT_UTIL_REGEX = r"^.*peList_0\s*\|\s*FFTWrapper\s*\|\s*(\d+)\s*\|\s*\d+\s*\|\s*\d+\s*\|\s*\d+\s*\|\s*(\d+)\s*\|\s*\d+\s*\|\s*(\d+)\s*\|\s*(\d+)"
LMFE_UTIL_REGEX = r"^.*peList_1\s*\|\s*LMFEWrapper\s*\|\s*(\d+)\s*\|\s*\d+\s*\|\s*\d+\s*\|\s*\d+\s*\|\s*(\d+)\s*\|\s*\d+\s*\|\s*(\d+)\s*\|\s*(\d+)"

TIMING_REGEX = r"^\s*WNS\(ns\).*\n\s*.*\n\s*(\d*\.?\d+)"

def main():
    test_config = {
        "frame_length": (128, 256, 512, 1024),
        "num_frames": (8, 16, 32, 64),
        "num_mels": (10, 13, 15, 20)
    }
    script_file = os.path.abspath(__file__)
    script_dir = os.path.dirname(script_file)
    tests_dir = os.path.join(script_dir, "tests")
    for test_case in itertools.product(*test_config.values()):
        tcdict = dict(zip(test_config.keys(), test_case))
        frame_length = tcdict["frame_length"]
        num_frames = tcdict["num_frames"]
        num_mels = tcdict["num_mels"]
        test_case_dir = os.path.join(tests_dir, f"frame_length_{frame_length}_num_frames_{num_frames}_num_mels_{num_mels}")
        power_file = os.path.join(test_case_dir, "synth", "post_synth_power.rpt")
        util_file = os.path.join(test_case_dir, "synth", "post_synth_utilization.rpt")
        timing_file = os.path.join(test_case_dir, "synth", "post_synth_timing_summary.rpt")
        
        file = open(power_file, "r")
        power_rpt_string = ''.join(file.readlines())
        file.close()
        mtotal = re.findall(TOTAL_POWER_REGEX, power_rpt_string, re.MULTILINE)
        assert len(mtotal) == 1
        mdynamic = re.findall(DYNAMIC_POWER_REGEX, power_rpt_string, re.MULTILINE)
        assert len(mdynamic) == 1
        mstatic = re.findall(STATIC_POWER_REGEX, power_rpt_string, re.MULTILINE)
        assert len(mstatic) == 1

        file = open(util_file, "r")
        util_rpt_string = ''.join(file.readlines())
        file.close()
        mluts = re.findall(TOTAL_UTIL_REGEX, util_rpt_string, re.MULTILINE)
        assert len(mluts[0]) == 4
        mfftluts = re.findall(FFT_UTIL_REGEX, util_rpt_string, re.MULTILINE)
        assert len(mfftluts[0]) == 4
        mlmfeluts = re.findall(LMFE_UTIL_REGEX, util_rpt_string, re.MULTILINE)
        assert len(mlmfeluts[0]) == 4

        file = open(timing_file, "r")
        timing_rpt_string = ''.join(file.readlines())
        file.close()
        mtiming = re.findall(TIMING_REGEX, timing_rpt_string, re.MULTILINE)
        assert len(mtiming) == 1
        slack = mtiming[0]
        print(f"{frame_length:04d}/{num_frames:02d}/{num_mels:02d}: TOTAL:{mtotal[0]} W, DYNAMIC:{mdynamic[0]} W, STATIC:{mstatic[0]} W.\
TOTAL LUTs:{mluts[0][0]}, FFT/LMFE: {mfftluts[0][0]}/{mlmfeluts[0][0]}. FF:{mluts[0][1]}/{mfftluts[0][1]}/{mlmfeluts[0][1]}. \
RAMB18:{mluts[0][2]}/{mfftluts[0][2]}/{mlmfeluts[0][2]}, DSP:{mluts[0][3]}/{mfftluts[0][3]}/{mlmfeluts[0][3]}. SLACK MET: +{slack}")


if __name__ == "__main__":
    main()
