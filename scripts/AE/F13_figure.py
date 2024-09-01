import argparse
import os
import matplotlib.pyplot as plt
import pandas as pd
import matplotlib.gridspec as gridspec

blue = "#52A4A6"
orange = "#FF9300"
green = "#57AC45"
red = "#FF7F50"
deepred = "#D03A23"
purple = "#9D32A7"
deepBlue = "#4D839D"
lightBlue = "#4478C5"

brown = (0.5764705882352941, 0.47058823529411764, 0.3764705882352941)
pink = (0.8549019607843137, 0.5450980392156862, 0.7647058823529411)

parser = argparse.ArgumentParser(
    description="Figure 13 figure drawing",
    formatter_class=argparse.RawTextHelpFormatter,
)
parser.add_argument(
    "--dir",
    "-d",
    dest="directory",
    help="Directory to store data and figures",
    required=True,
)
args = parser.parse_args()
directory = args.directory

files = [x for x in os.listdir(f"{directory}/figure_13") if x[-4:] == ".csv"]
for file in files:
    service = file.split(".")[0]
    df = pd.read_csv(f"{directory}/figure_13/{file}")
    Erms = df[df.method == "erms"].sort_values(by="timestamp").reset_index()
    grandslam = df[df.method == "grandSLAm"].sort_values(by="timestamp").reset_index()
    rhythm = df[df.method == "rhythm"].sort_values(by="timestamp").reset_index()
    Firm = df[df.method == "firm"].sort_values(by="timestamp").reset_index()

    lw = 3
    marker = 6

    fig = plt.figure(figsize=(10, 8))
    gridspec.GridSpec(2, 1)
    plt.subplot2grid((2, 1), (0, 0), colspan=1, rowspan=1)
    ax1 = plt.gca()
    plt.plot(
        -10,
        100,
        markersize=marker,
        marker="X",
        linewidth=lw,
        linestyle=":",
        color=purple,
        label="Workload",
    )
    plt.plot(
        Erms["timestamp"],
        Erms["container"],
        markersize=marker,
        marker="X",
        linewidth=lw,
        linestyle="-",
        color=blue,
        label="Erms",
    )
    plt.plot(
        grandslam["timestamp"],
        grandslam["container"],
        markersize=marker,
        marker="o",
        linewidth=lw,
        linestyle="-",
        color=red,
        label="Rhythm",
    )
    plt.plot(
        rhythm["timestamp"],
        rhythm["container"],
        markersize=marker,
        marker="v",
        linewidth=lw,
        linestyle="-",
        color=green,
        label="GrandSLAm",
    )
    plt.plot(
        Firm["timestamp"],
        Firm["container"],
        markersize=marker,
        marker="v",
        linewidth=lw,
        linestyle="-",
        color=brown,
        label="Firm",
    )
    plt.grid(color="#C0C0C0", linestyle="-", linewidth=1, axis="y")
    ax1.set_ylabel("# of Containers", fontsize=21)
    ax1.set_xlabel("Time (min)", fontsize=21)
    plt.xlim([-1, 41])
    ax1.set_ylim(ymin=35, ymax=60)
    plt.xticks(fontsize=21)
    plt.yticks(fontsize=21)
    ax1.legend(fontsize=18, frameon=False, ncol=2, loc="upper left")

    # workload
    ax2 = ax1.twinx()
    line1 = plt.plot(
        Erms["timestamp"],
        Erms["workload"],
        markersize=marker,
        marker="X",
        linewidth=lw,
        linestyle=":",
        color=purple,
    )
    ax2.set_ylabel(r"Workload", fontsize=21, color=purple)
    # ax2.set_yticks([0, 126, 248, 371, 494, 617])
    # ax2.set_yticklabels(['0', '2', '4', '6', '8', '10'])
    ax2.tick_params(axis="y", colors=purple)
    ax2.spines["right"].set_color(purple)
    ax2.set_ylim(ymin=0, ymax=100)
    plt.xticks(fontsize=21)
    plt.yticks(fontsize=21)
    fig.tight_layout()
    # plt.savefig("figure/figure12.png")

    plt.subplot2grid((2, 1), (1, 0), colspan=1, rowspan=1)
    ax = plt.gca()
    # Erms = pd.read_csv('/root/Erms/AE/data_hotel-reserv/validation/dynamic_result.csv').reset_index()
    Erms["traceLatency"] = Erms["traceLatency"] / 1000
    rhythm["traceLatency"] = rhythm["traceLatency"] / 1000
    grandslam["traceLatency"] = grandslam["traceLatency"] / 1000
    Firm["traceLatency"] = Firm["traceLatency"] / 1000
    # rhythm = pd.read_csv('AE/data_hotel-reserv/validation/dynamic_result.csv')
    # grandslam = pd.read_csv('AE/data_hotel-reserv/validation/dynamic_result.csv')

    plt.plot(
        Erms["timestamp"],
        Erms["traceLatency"],
        markersize=marker,
        marker="X",
        linewidth=lw,
        linestyle="-",
        color=blue,
        label="Erms",
    )
    plt.plot(
        grandslam["timestamp"],
        grandslam["traceLatency"],
        markersize=marker,
        marker="o",
        linewidth=lw,
        linestyle="-",
        color=red,
        label="GrandSLAm",
    )
    plt.plot(
        rhythm["timestamp"],
        rhythm["traceLatency"],
        markersize=marker,
        marker="v",
        linewidth=lw,
        linestyle="-",
        color=green,
        label="Rhythm",
    )
    plt.plot(
        Firm["timestamp"],
        Firm["traceLatency"],
        markersize=marker,
        marker="v",
        linewidth=lw,
        linestyle="-",
        color=brown,
        label="Firm",
    )
    plt.grid(color="#C0C0C0", linestyle="-", linewidth=1, axis="y")
    ax.set_ylabel("Tail Latency (ms)", fontsize=22)
    ax.set_xlabel("Time (min)", fontsize=22)

    plt.xticks(fontsize=22)
    plt.yticks(fontsize=22)
    ax.legend(loc="upper left", ncol=2, fontsize=22, frameon=False)
    plt.axhline(y=200, linewidth=2, linestyle="--", color="red")
    # plt.ylim([5, 300])
    fig.tight_layout()
    plt.savefig(f"{directory}/figure_13/figure_13_{service}.png")
    print(f"Figure is saved in {directory}/figure_13/figure_13_{service}.png")
