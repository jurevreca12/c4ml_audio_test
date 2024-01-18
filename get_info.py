import os
import logging
import subprocess
import itertools
import re

TOTAL_POWER_REGEX = r".*Total\sOn-Chip\sPower\s\(W\)\s*\|\s*(\d*\.?\d+)"
DYNAMIC_POWER_REGEX = r".*Dynamic\s*\(W\)\s*\|\s*(\d*\.?\d+)"
STATIC_POWER_REGEX = r".*Device\sStatic\s*\(W\)\s*\|\s*(\d*\.?\d+)"

TOTAL_LUT_REGEX = r".*ProcessingPipeline\s*\|\s*\(top\)\s*\|\s*(\d+)"
FFT_LUT_REGEX = r".*peList_0\s*\|\s*FFTWrapper\s*\|\s*(\d+)"
LMFE_LUT_REGEX = r".*peList_1\s*\|\s*LMFEWrapper\s*\|\s*(\d+)"


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
        
        file = open(power_file, "r")
        power_rpt_string = ''.join(file.readlines())
        file.close()
        mtotal = re.findall(TOTAL_POWER_REGEX, power_rpt_string)
        assert len(mtotal) == 1
        mdynamic = re.findall(DYNAMIC_POWER_REGEX, power_rpt_string)
        assert len(mdynamic) == 1
        mstatic = re.findall(STATIC_POWER_REGEX, power_rpt_string)
        assert len(mstatic) == 1

        file = open(util_file, "r")
        util_rpt_string = ''.join(file.readlines())
        file.close()
        mluts = re.findall(TOTAL_LUT_REGEX, util_rpt_string)
        assert len(mluts) == 1
        mfftluts = re.findall(FFT_LUT_REGEX, util_rpt_string)
        assert len(mfftluts) == 1
        mlmfeluts = re.findall(LMFE_LUT_REGEX, util_rpt_string)
        assert len(mlmfeluts) == 1
        print(f"{frame_length}/{num_frames}/{num_mels}: TOTAL:{mtotal[0]} W, DYNAMIC:{mdynamic[0]} W, STATIC:{mstatic[0]} W. TOTAL LUTs:{mluts[0]}, FFT/LMFE: {mfftluts[0]}/{mlmfeluts[0]}.")


if __name__ == "__main__":
    main()
