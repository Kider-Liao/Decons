import argparse
import os
import matplotlib.pyplot as plt
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
        "This script will generate the Figure 11 in the paper. To generate the figure, "
        "you need to generate data first. Please check the script F11_data.sh for more detail. "
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
output_path = args.directory

files = [x for x in os.listdir(f"{output_path}/figure_11") if x[-4:] == ".csv"]
dfSharing = []
for file in files:
    dfSharing.append(pd.read_csv(f"{output_path}/figure_11/{file}"))

dfSharing = pd.concat(dfSharing)

lw = 3
dfSharing = pd.concat(
    [
        dfSharing[
            [
                "service_1",
                "method",
                "cpu_inf",
                "mem_inf",
                "sla_1",
                "workload_1",
                "container_1",
            ]
        ].rename(
            columns={
                "service_1": "service",
                "sla_1": "sla",
                "workload_1": "workload",
                "container_1": "container",
            }
        ),
        dfSharing[
            [
                "service_2",
                "method",
                "cpu_inf",
                "mem_inf",
                "sla_2",
                "workload_2",
                "container_2",
            ]
        ].rename(
            columns={
                "service_2": "service",
                "sla_2": "sla",
                "workload_2": "workload",
                "container_2": "container",
            }
        ),
    ]
)
dfSharing["sla"] = dfSharing["sla"] * 1000
dfThreshold = (
    dfSharing.groupby("service")[["sla", "workload"]]
    .mean()
    .reset_index()
    .rename(columns={"sla": "s_threshold", "workload": "w_threshold"})
)
dfSharing = dfSharing.merge(dfThreshold, on="service")

Erms = dfSharing[dfSharing["method"] == "erms"].rename(columns={"container": "erms"})
grandSLAm = dfSharing[dfSharing["method"] == "grandSLAm"].rename(
    columns={"container": "grandSLAm"}
)
rhythm = dfSharing[dfSharing["method"] == "rhythm"].rename(
    columns={"container": "rhythm"}
)
firm = dfSharing[dfSharing["method"] == "firm"].rename(columns={"container": "firm"})
columns = [
    "service",
    "cpu_inf",
    "mem_inf",
    "sla",
    "workload",
    "w_threshold",
    "s_threshold",
]

df = (
    Erms.merge(grandSLAm, on=columns)
    .merge(rhythm, on=columns)
    .merge(firm, on=columns)[columns + ["erms", "grandSLAm", "rhythm", "firm"]]
)

fig = plt.figure(figsize=(10, 8))
gridspec.GridSpec(2, 1)

plt.subplot2grid((2, 1), (0, 0), colspan=1, rowspan=1)
ax = plt.gca()
bins = 200
raw, bins = np.histogram(Erms["erms"], bins, density=True)
cdf = np.cumsum(raw)
plt.plot(bins[1:], cdf / cdf[-1], linestyle="-", lw=lw, color=blue, label="Erms")

bins = 200
raw, bins = np.histogram(grandSLAm["grandSLAm"], bins, density=True)
cdf = np.cumsum(raw)
plt.plot(bins[1:], cdf / cdf[-1], linestyle="-.", lw=lw, color=red, label="GrandSLAm")

bins = 200
raw, bins = np.histogram(rhythm["rhythm"], bins, density=True)
cdf = np.cumsum(raw)
plt.plot(bins[1:], cdf / cdf[-1], linestyle=":", lw=3, color=green, label="Rhythm")

bins = 200
raw, bins = np.histogram(firm["firm"], bins, density=True)
cdf = np.cumsum(raw)
plt.plot(bins[1:], cdf / cdf[-1], linestyle=":", lw=3, color=brown, label="Firm")

plt.grid(color="#C0C0C0", linestyle="-", linewidth=1, axis="x")
plt.grid(color="#C0C0C0", linestyle="-", linewidth=1, axis="y")

ax.set_ylabel("CDF", fontsize=22)
ax.set_xlabel("# of Containers", fontsize=22)
plt.xticks(fontsize=22)
plt.yticks(fontsize=22)
ax.legend(fontsize=22, frameon=False)
plt.ylim([0, 1])

plt.subplot2grid((2, 1), (1, 0), colspan=1, rowspan=1)
ax = plt.gca()
gap = 0.2
width = 0.15

methods = ["erms", "grandSLAm", "rhythm", "firm"]
dfMean = df[methods].mean()
dfMean["flag"] = "mean"
dfLowWL = df[df["workload"] < df["w_threshold"]][methods].mean()
dfLowWL["flag"] = "LowWL"
dfHighWL = df[df["workload"] >= df["w_threshold"]][methods].mean()
dfHighWL["flag"] = "HighWL"
dfLowSla = df[df["sla"] <= df["s_threshold"]][methods].mean()
dfLowSla["flag"] = "LowSla"
dfHighSla = df[df["sla"] > df["s_threshold"]][methods].mean()
dfHighSla["flag"] = "HighSla"
df = pd.concat([dfMean, dfLowWL, dfHighWL, dfLowSla, dfHighSla])
category = np.array([1, 2, 3, 4, 5])

ax.bar(x=category, height=df["erms"], width=width, color=blue, label="Erms")
ax.bar(
    x=category + gap, height=df["grandSLAm"], width=width, color=red, label="GrandSLAm"
)
ax.bar(
    x=category + 2 * gap, height=df["rhythm"], width=width, color=green, label="Rhythm"
)
ax.bar(x=category + 3 * gap, height=df["firm"], width=width, color=brown, label="Firm")
ax.set_ylabel("# of Containers", fontsize=21)

ax.set_xticks([1.3, 2.3, 3.3, 4.3, 5.3])
ax.set_xticklabels(["Avg", "low WL", "high WL", "low SLA", "high SLA"])
plt.xticks(fontsize=21)
plt.yticks(fontsize=21)
plt.xlim(0.8, 5.8)

ax.legend(loc="upper center", fontsize=19, ncol=4, frameon=False)
plt.grid(color="#C0C0C0", linestyle="-", linewidth=1, axis="y")
fig.tight_layout()
plt.savefig(f"{output_path}/figure_11/figure_11.png")
print(f"Figure is saved in {output_path}/figure_11/figure_11.png")