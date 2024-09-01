import os
import matplotlib.pyplot as plt
import argparse
import pandas as pd
import numpy as np

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
        "This script will generate the Figure 10 in the paper. To generate the figure, "
        "you need to generate data first. Please check the script F10_data.sh for more detail. "
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

files = [x for x in os.listdir(f"{directory}/figure_10") if x[-11:] == "_result.csv"]
all_data = []
for file in files:
    data = pd.read_csv(f"{directory}/figure_10/{file}")
    all_data.append(data.assign(app=file.split("_")[0]))
all_data = pd.concat(all_data)

fig = plt.figure(figsize=(10, 8))
plt.subplot2grid((2, 1), (0, 0), colspan=1, rowspan=1)
ax = plt.gca()
gap = 0.2
width = 0.15
category = np.array([1, 2, 3, 4])

Erms = all_data[["app", "erms_mean", "erms_median", "portion"]]
XGBoost = all_data[["app", "xgboost_mean", "xgboost_median", "portion"]]
NerualNetwork = all_data[["app", "nn_mean", "nn_median", "portion"]]

Erms = pd.concat(
    [
        Erms.loc[Erms["app"] == "social-network"],
        Erms.loc[Erms["app"] == "hotel-reserv"],
        Erms.loc[Erms["app"] == "media-microsvc"],
        Erms.loc[Erms["app"] == "ali"],
    ]
)
Erms = Erms.loc[Erms["portion"] == 0.9]["erms_mean"] * 100
XGBoost = pd.concat(
    [
        XGBoost.loc[XGBoost["app"] == "social-network"],
        XGBoost.loc[XGBoost["app"] == "hotel-reserv"],
        XGBoost.loc[XGBoost["app"] == "media-microsvc"],
        XGBoost.loc[XGBoost["app"] == "ali"],
    ]
)
XGBoost = XGBoost.loc[XGBoost["portion"] == 0.9]["xgboost_mean"] * 100
NerualNetwork = pd.concat(
    [
        NerualNetwork.loc[NerualNetwork["app"] == "social-network"],
        NerualNetwork.loc[NerualNetwork["app"] == "hotel-reserv"],
        NerualNetwork.loc[NerualNetwork["app"] == "media-microsvc"],
        NerualNetwork.loc[NerualNetwork["app"] == "ali"],
    ]
)
NerualNetwork = NerualNetwork.loc[NerualNetwork["portion"] == 0.9]["nn_mean"] * 100

ax.bar(x=category - gap, height=Erms, width=width, color=blue, label="Erms")
ax.bar(x=category, height=XGBoost, width=width, color=green, label="XGBoost")
ax.bar(x=category + gap, height=NerualNetwork, width=width, color=red, label="NN")
ax.set_ylabel("Accuracy (%)", fontsize=22)

ax.set_xticks(category)
ax.set_xticklabels(["Social\nNetwork", "Hotel\nReservation", "Media\nService", "Alibaba\nTrace"])
plt.xticks(fontsize=22)
plt.yticks(fontsize=22)
plt.ylim(0, 100)
plt.xlim(0.6, 4.6)
ax.legend(
    loc="upper center", fontsize=19, ncol=3, frameon=False, bbox_to_anchor=(0.5, 1.07)
)
plt.grid(color="#C0C0C0", linestyle="-", linewidth=1, axis="y")

plt.subplot2grid((2, 1), (1, 0), colspan=1, rowspan=1)
ax = plt.gca()
all_data["erms_mean"] = all_data["erms_mean"] * 100
all_data["xgboost_mean"] = all_data["xgboost_mean"] * 100
all_data["nn_mean"] = all_data["nn_mean"] * 100
all_data = all_data.groupby(["portion"]).mean().reset_index()

plt.plot(
    all_data["portion"],
    all_data["erms_mean"],
    linestyle="-",
    linewidth=3,
    marker="d",
    color=blue,
    label="Erms",
)
plt.plot(
    all_data["portion"],
    all_data["xgboost_mean"],
    linestyle="-",
    linewidth=3,
    marker="X",
    color=green,
    label="XGBoost",
)
plt.plot(
    all_data["portion"],
    all_data["nn_mean"],
    linestyle="-",
    linewidth=3,
    marker="o",
    color=red,
    label="NN",
)

ax.set_ylabel("Accuracy (%)", fontsize=22)
ax.set_xlabel("Portion of Training Data", fontsize=22)

ax.set_xticks([0.5, 0.6, 0.7, 0.8, 0.9])
ax.set_xticklabels(["0.5", "0.6", "0.7", "0.8", "0.9"])

plt.ylim([60, 90])

plt.xticks(fontsize=22)
plt.yticks(fontsize=22)
ax.legend(loc="upper center", fontsize=21, ncol=3, frameon=False)

plt.grid(color="#C0C0C0", linestyle="-", linewidth=1, axis="y")
plt.grid(color="#C0C0C0", linestyle="-", linewidth=1, axis="x")

fig.tight_layout()
plt.savefig(f"{directory}/figure_10/figure_10.png")
print(f"Figure is saved in {directory}/figure_10/figure_10.png")
