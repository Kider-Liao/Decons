import os

from box import Box
from onlineScaling.erms import ErmsBased
import matplotlib.pyplot as plt
import argparse
import numpy as np
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
    description=(
        "This script will generate the Figure 14 in the paper. To generate the figure, "
        "you need to generate data first. Please check the script F14_data.sh for more detail. "
    ),
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

files = [x for x in os.listdir(f"{directory}/figure_14") if x[-4:] == ".csv"]
df = []
for file in files:
    df.append(pd.read_csv(f"{directory}/figure_14/{file}"))
df = pd.concat(df)

prio = df.loc[df["use_prio"]].rename(columns={"container_merge": "prio"})
non_prio = df.loc[~df["use_prio"]].rename(columns={"container_merge": "non-prio"})
df = prio.merge(
    non_prio,
    on=[
        "service_1",
        "service_2",
        "method",
        "cpu_inf",
        "mem_inf",
        "workload_1",
        "workload_2",
    ],
)
Erms = df[df.method == "erms"]
grandslam = df[df.method == "grandSLAm"]
rhythm = df[df.method == "rhythm"]
fig = plt.figure(figsize=(10, 8))
gridspec.GridSpec(2, 1)
plt.subplot2grid((2, 1), (0, 0), colspan=1, rowspan=1)
ax = plt.gca()
bins = 200
raw, bins = np.histogram(Erms["non-prio"], bins, density=True)
cdf = np.cumsum(raw)
plt.plot(bins[1:], cdf / cdf[-1], linestyle="-", lw=3, color=blue, label="Erms")

bins = 200
raw, bins = np.histogram(grandslam["non-prio"], bins, density=True)
cdf = np.cumsum(raw)
plt.plot(bins[1:], cdf / cdf[-1], linestyle="-.", lw=3, color=red, label="GrandSLAm")

bins = 200
raw, bins = np.histogram(rhythm["non-prio"], bins, density=True)
cdf = np.cumsum(raw)
plt.plot(bins[1:], cdf / cdf[-1], linestyle=":", lw=3, color=green, label="Rhythm")

plt.grid(color="#C0C0C0", linestyle="-", linewidth=1, axis="y")
plt.grid(color="#C0C0C0", linestyle="-", linewidth=1, axis="x")

ax.set_ylabel("CDF", fontsize=22)
ax.set_xlabel("# of Containers", fontsize=22)
plt.ylim([0, 1])
# plt.xlim([0, 6.8])
# plt.axhline(y=1, color=red)
plt.xticks(fontsize=22)
plt.yticks(fontsize=22)
ax.legend(fontsize=22, frameon=False)

plt.subplot2grid((2, 1), (1, 0), colspan=1, rowspan=1)
ax = plt.gca()
dfAvg = df.groupby("method")[["prio", "non-prio"]].mean().reset_index()

category = np.array([1, 2, 3])
gap = 0.25
width = 0.15
# 'low SLA, low MCR'
ax.bar(
    x=category - gap / 2,
    height=dfAvg["prio"],
    width=width,
    color=red,
    label="Scheduling",
)
ax.bar(
    x=category + gap / 2,
    height=dfAvg["non-prio"],
    width=width,
    color=blue,
    label="No Scheduling",
)

ax.set_ylabel("Containers", fontsize=22)
# plt.axhline(y=1, color=red)
ax.set_xticks([1, 2, 3])
ax.set_xticklabels(["Erms", "GrandSLAm", "Rhythm"])
plt.xticks(fontsize=22)
plt.yticks(fontsize=22)
ax.legend(fontsize=22, loc="upper center", ncol=2, frameon=False)
# plt.ylim([0, 2.7])
plt.grid(color="#C0C0C0", linestyle="-", linewidth=1, axis="y")
# ax.legend(fontsize=20, ncol=3, frameon=False, bbox_to_anchor=(1, 1.03))
fig.tight_layout()
plt.savefig(f"{directory}/figure_14/figure_14.png")
print(f"Figure is saved in {directory}/figure_14/figure_14.png")
