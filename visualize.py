import pandas as pd
import os

def get_main_table(results):
    latex_str = "\\hline\n"
    latex_str += "Parameterization & LUT & FF & DSP & CYCLES & Throughput [Msamples/s] & Dynamic Power [W] \\\\\n"
    latex_str += "\\hline\n"
    clr = "\\clr" 
    for _, row in results.iterrows():
        latex_str += f"({int(row['frame_length'])}, {int(row['num_frames'])}, {int(row['num_mels'])}){clr} & \
 {int(row['total_luts'])}{clr} & \
 {int(row['total_ff'])}{clr} & \
 {int(row['total_dsp'])}{clr} & \
 {int(row['consumed_cycles'])}{clr} & \
 {row['max_throughput_msamples_sec']:.02f}{clr}& \
 {row['dynamic_power']:.03f}{clr}\\\\\n" 
        if clr == "\\clr":
            clr = ""
        else:
            clr = "\\clr"
    latex_str += "\\hline\n"
    return latex_str

def visualize():
    results = pd.read_csv('results.csv')
    script_file = os.path.abspath(__file__)
    script_dir = os.path.dirname(script_file)
    vis_dir = os.path.join(script_dir, "vis")
    os.makedirs(vis_dir)
    main_table_file = os.path.join(vis_dir, "main_table.tex")
    main_table_str = get_main_table(results)
    with open(main_table_file, 'w') as f:
        f.write(main_table_str)

if __name__ == '__main__':
    visualize()
