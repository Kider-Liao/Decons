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
        "This script will generate the Figure 12 in the paper. To generate the figure, "
        "you need to generate data first. Please check the script F12_data.sh for more detail. "
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

files = [x for x in os.listdir(f"{directory}/figure_12") if x[-4:] == ".csv"]
df = []
for file in files:
    df.append(pd.read_csv(f"{directory}/figure_12/{file}"))
df = pd.concat(df)

df["sla_1"] = df["sla_1"] * 1000
df["sla_2"] = df["sla_2"] * 1000
df["ratio1"] = df["latency_1"] / df["sla_1"]
df["ratio2"] = df["latency_2"] / df["sla_2"]
df["violation_1"] = 0
df["violation_2"] = 0
df.loc[df["latency_1"] > df["sla_1"], "violation_1"] = 1
df.loc[df["latency_2"] > df["sla_2"], "violation_2"] = 1

dfThreshold = pd.concat(
    [
        df.loc[df["service_1"] != "ComposeReview"]
        .groupby(["service_1", "service_2"])[
            ["sla_1", "sla_2", "workload_1", "workload_2"]
        ]
        .mean()
        .reset_index()
        .rename(
            columns={
                "sla_1": "slaThreshold_1",
                "sla_2": "slaThreshold_2",
                "workload_1": "workloadThreshold_1",
                "workload_2": "workloadThreshold_2",
            }
        ),
        df.loc[df["service_1"] == "ComposeReview"]
        .groupby(["service_1"])[["sla_1", "sla_2", "workload_1", "workload_2"]]
        .mean()
        .reset_index()
        .rename(
            columns={
                "sla_1": "slaThreshold_1",
                "sla_2": "slaThreshold_2",
                "workload_1": "workloadThreshold_1",
                "workload_2": "workloadThreshold_2",
            }
        ),
    ]
)


df = pd.merge(df, dfThreshold, on=["service_1", "service_2"])

# the average of SLA violation
dfMeanCount = pd.concat(
    [
        df.loc[df["service_1"] != "ComposeReview"]
        .groupby(["service_1", "service_2", "method"])[["violation_1"]]
        .count()
        .reset_index()
        .rename(columns={"violation_1": "num"}),
        df.loc[df["service_1"] == "ComposeReview"]
        .groupby(["service_1", "method"])[["violation_1"]]
        .count()
        .reset_index()
        .rename(columns={"violation_1": "num"}),
    ]
)
dfMean = pd.concat(
    [
        df.loc[df["service_1"] != "ComposeReview"]
        .groupby(["service_1", "service_2", "method"])[["violation_1", "violation_2"]]
        .sum()
        .reset_index()
        .rename(columns={"violation_1": "count_1", "violation_2": "count_2"}),
        df.loc[df["service_1"] == "ComposeReview"]
        .groupby(["service_1", "method"])[["violation_1", "violation_2"]]
        .sum()
        .reset_index()
        .rename(columns={"violation_1": "count_1", "violation_2": "count_2"}),
    ]
)
dfMean["flag"] = "mean"
dfMeanMerge = pd.merge(dfMeanCount, dfMean, on=["service_1", "service_2", "method"])
dfMeanMerge["percentage_1"] = dfMeanMerge["count_1"] / dfMeanMerge["num"]
dfMeanMerge["percentage_2"] = dfMeanMerge["count_2"] / dfMeanMerge["num"]
dfService1Mean = dfMeanMerge[["method", "percentage_1"]].rename(
    columns={"percentage_1": "percentage"}
)
dfService2Mean = dfMeanMerge[["method", "percentage_2"]].rename(
    columns={"percentage_2": "percentage"}
)
dfMean = pd.concat([dfService1Mean, dfService2Mean])
dfMean = dfMean.groupby(["method"])[["percentage"]].mean().reset_index()

df["workloadFlag1"] = "low"
df["workloadFlag2"] = "low"
df["slaFlag1"] = "low"
df["slaFlag2"] = "low"
df.loc[df["sla_1"] > df["slaThreshold_1"], "slaFlag1"] = "high"
df.loc[df["sla_2"] > df["slaThreshold_2"], "slaFlag2"] = "high"
df.loc[df["workload_1"] > df["workloadThreshold_1"], "workloadFlag1"] = "high"
df.loc[df["workload_2"] > df["workloadThreshold_2"], "workloadFlag2"] = "high"

#  SLA violation in high or low workload
dfService1WorkloadCount = (
    df.groupby(["method", "workloadFlag1"])[["violation_1"]]
    .count()
    .reset_index()
    .rename(columns={"violation_1": "num"})
)
dfService1WorkloadSum = (
    df.groupby(["method", "workloadFlag1"])[["violation_1"]]
    .sum()
    .reset_index()
    .rename(columns={"violation_1": "count_1"})
)
dfService1Workload = pd.merge(
    dfService1WorkloadSum, dfService1WorkloadCount, on=["method", "workloadFlag1"]
)
dfService1Workload["percentage"] = (
    dfService1Workload["count_1"] / dfService1Workload["num"]
)

dfService2WorkloadCount = (
    df.groupby(["method", "workloadFlag2"])[["violation_2"]]
    .count()
    .reset_index()
    .rename(columns={"violation_2": "num"})
)
dfService2WorkloadSum = (
    df.groupby(["method", "workloadFlag2"])[["violation_2"]]
    .sum()
    .reset_index()
    .rename(columns={"violation_2": "count_2"})
)
dfService2Workload = pd.merge(
    dfService2WorkloadSum, dfService2WorkloadCount, on=["method", "workloadFlag2"]
)
dfService2Workload["percentage"] = (
    dfService2Workload["count_2"] / dfService2Workload["num"]
)

dfService1Workload = dfService1Workload.rename(
    columns={"workloadFlag1": "workloadFlag", "percentage_1": "percentage"}
)
dfService2Workload = dfService2Workload.rename(
    columns={"workloadFlag2": "workloadFlag", "percentage_2": "percentage"}
)
dfWorkload = pd.concat([dfService1Workload, dfService2Workload])
dfWorkload = (
    dfWorkload.groupby(["method", "workloadFlag"])[["percentage"]].mean().reset_index()
)
dfWorkload = dfWorkload.sort_values("workloadFlag", ascending=False)

# SLA violation in high or low sla
dfService1SlaCount = (
    df.groupby(["method", "slaFlag1"])[["violation_1"]]
    .count()
    .reset_index()
    .rename(columns={"violation_1": "num"})
)
dfService1SlaSum = (
    df.groupby(["method", "slaFlag1"])[["violation_1"]]
    .sum()
    .reset_index()
    .rename(columns={"violation_1": "count_1"})
)
dfService1Sla = pd.merge(
    dfService1SlaSum, dfService1SlaCount, on=["method", "slaFlag1"]
)
dfService1Sla["percentage"] = dfService1Sla["count_1"] / dfService1Sla["num"]

dfService2SlaCount = (
    df.groupby(["method", "slaFlag2"])[["violation_2"]]
    .count()
    .reset_index()
    .rename(columns={"violation_2": "num"})
)
dfService2SlaSum = (
    df.groupby(["method", "slaFlag2"])[["violation_2"]]
    .sum()
    .reset_index()
    .rename(columns={"violation_2": "count_2"})
)
dfService2Sla = pd.merge(
    dfService2SlaSum, dfService2SlaCount, on=["method", "slaFlag2"]
)
dfService2Sla["percentage"] = dfService2Sla["count_2"] / dfService2Sla["num"]

dfService1Sla = dfService1Sla.rename(
    columns={"slaFlag1": "slaFlag", "percentage_1": "percentage"}
)
dfService2Sla = dfService2Sla.rename(
    columns={"slaFlag2": "slaFlag", "percentage_2": "percentage"}
)
dfSla = pd.concat([dfService2Sla, dfService1Sla])
dfSla = dfSla.groupby(["method", "slaFlag"])[["percentage"]].mean().reset_index()
dfSla = dfSla.sort_values("slaFlag", ascending=False)

dfResult = pd.concat([dfMean, dfWorkload, dfSla])

category = np.array([1, 2, 3, 4, 5])
Erms = dfResult[dfResult.method == "erms"]
Grandslam = dfResult[dfResult.method == "grandSLAm"]
Rhythm = dfResult[dfResult.method == "rhythm"]
Firm = dfResult[dfResult.method == "firm"]

fig = plt.figure(figsize=(10, 8))
gridspec.GridSpec(2, 1)
plt.subplot2grid((2, 1), (0, 0), colspan=1, rowspan=1)
ax = plt.gca()
gap = 0.2
width = 0.15
# 'low SLA, low MCR'
ax.bar(x=category, height=Erms["percentage"], width=width, color=blue, label="Erms")
ax.bar(
    x=category + gap,
    height=Grandslam["percentage"],
    width=width,
    color=red,
    label="GrandSLAm",
)
ax.bar(
    x=category + 2 * gap,
    height=Rhythm["percentage"],
    width=width,
    color=green,
    label="Rhythm",
)
ax.bar(
    x=category + 3 * gap,
    height=Firm["percentage"],
    width=width,
    color=brown,
    label="Firm",
)
ax.set_ylabel("Probability of SLA Violation", fontsize=19)
ax.set_xticks(category + 1.5 * gap)
ax.set_xticklabels(["Avg", "low WL", "high WL", "low SLA", "high SLA"])
plt.xticks(fontsize=21)
plt.yticks(fontsize=21)
# plt.ylim(0, 26)
plt.xlim(0.8, 5.8)
plt.grid(color="#C0C0C0", linestyle="-", linewidth=1, axis="y")
ax.legend(loc="upper center", fontsize=19, ncol=4, frameon=False)
fig.tight_layout()


# the average of SLA ratio
dfMeanRatio = pd.concat(
    [
        df.loc[df["service_1"] != "ComposeReview"]
        .groupby(["service_1", "service_2", "method"])[["ratio1", "ratio2"]]
        .mean()
        .reset_index(),
        df.loc[df["service_1"] == "ComposeReview"]
        .groupby(["service_1", "method"])[["ratio1", "ratio2"]]
        .mean()
        .reset_index(),
    ]
)
dfService1MeanRatio = dfMeanRatio[["method", "ratio1"]].rename(
    columns={"ratio1": "ratio"}
)
dfService2MeanRatio = dfMeanRatio[["method", "ratio2"]].rename(
    columns={"ratio2": "ratio"}
)
dfMeanRatio = pd.concat([dfService1MeanRatio, dfService2MeanRatio])
dfMeanRatio = dfMeanRatio.groupby(["method"])[["ratio"]].mean().reset_index()

#  SLA ratio in high or low workload
dfService1WorkloadMean = (
    df.groupby(["method", "workloadFlag1"])[["ratio1"]]
    .mean()
    .reset_index()
    .rename(columns={"workloadFlag1": "workloadFlag", "ratio1": "ratio"})
)
dfService2WorkloadMean = (
    df.groupby(["method", "workloadFlag1"])[["ratio2"]]
    .mean()
    .reset_index()
    .rename(columns={"workloadFlag1": "workloadFlag", "ratio1": "ratio"})
)

dfWorkload = pd.concat([dfService1WorkloadMean, dfService2WorkloadMean])
dfWorkload = (
    dfWorkload.groupby(["method", "workloadFlag"])[["ratio"]].mean().reset_index()
)
dfWorkload = dfWorkload.sort_values("workloadFlag", ascending=False)

# SLA violation in high or low sla
dfService1SlaMean = (
    df.groupby(["method", "slaFlag1"])[["ratio1"]]
    .mean()
    .reset_index()
    .rename(columns={"slaFlag1": "slaFlag", "ratio1": "ratio"})
)
dfService2SlaMean = (
    df.groupby(["method", "slaFlag2"])[["ratio2"]]
    .mean()
    .reset_index()
    .rename(columns={"slaFlag2": "slaFlag", "ratio2": "ratio"})
)
dfSla = pd.concat([dfService2SlaMean, dfService1SlaMean])
dfSla = dfSla.groupby(["method", "slaFlag"])[["ratio"]].mean().reset_index()
dfSla = dfSla.sort_values("slaFlag", ascending=False)

dfResult = pd.concat([dfMeanRatio, dfWorkload, dfSla])

plt.subplot2grid((2, 1), (1, 0), colspan=1, rowspan=1)
ax = plt.gca()
category = np.array([1, 2, 3, 4, 5])
gap = 0.2
width = 0.15

Erms = dfResult[dfResult.method == "erms"]
Grandslam = dfResult[dfResult.method == "grandSLAm"]
Rhythm = dfResult[dfResult.method == "rhythm"]
Firm = dfResult[dfResult.method == "firm"]
ax.bar(x=category, height=Erms["ratio"], width=width, color=blue, label="Erms")
ax.bar(
    x=category + gap,
    height=Grandslam["ratio"],
    width=width,
    color=red,
    label="GrandSLAm",
)
ax.bar(
    x=category + 2 * gap,
    height=Rhythm["ratio"],
    width=width,
    color=green,
    label="Rhythm",
)
ax.bar(
    x=category + 3 * gap, height=Firm["ratio"], width=width, color=brown, label="Firm"
)
ax.set_ylabel("Tail Latency / SLA", fontsize=20)
ax.set_xticks(category + 1.5 * gap)
ax.set_xticklabels(["Avg", "low WL", "high WL", "low SLA", " high SLA"])
plt.xticks(fontsize=20)
plt.yticks(fontsize=20)
# plt.ylim(0, 1.68)
plt.xlim(0.8, 5.8)
ax.legend(loc="upper center", fontsize=19, ncol=4, frameon=False)
plt.grid(color="#C0C0C0", linestyle="-", linewidth=1, axis="y")

fig.tight_layout()
plt.savefig(f"{directory}/figure_12/figure_12.png")
print(f"Figure is saved in {directory}/figure_12/figure_12.png")
