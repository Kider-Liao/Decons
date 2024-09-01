import argparse
import os
from latencyAnalyzer.fitting import Fitting
import pandas as pd
import configs

parser = argparse.ArgumentParser(
    description=(
        "This script will perform model training with different amounts of data, "
        "and it will compare the accuracy of Erms, XGBoost and Neural Network. "
        "To generate the corresponding figure (Figure 10 in the paper), "
        "please run F10_figure.sh. "
        "Ususally, this script will consume 15 minutes for each application. "
    ),
    formatter_class=argparse.RawTextHelpFormatter,
)
parser.add_argument(
    "--app",
    "-a",
    dest="app",
    help="Application name. (`hotel-reserv`, `social-network`, `media-microsvc`)",
    default="hotel-reserv",
)
parser.add_argument(
    "--profiling-data",
    "-p",
    dest="profiling_data",
    help="Path to the profiling data (if AECs use their own profiling data)",
    default="AE",
)
parser.add_argument(
    "--dir",
    "-d",
    dest="directory",
    help="Directory to store data and figures",
    required=True,
)
args = parser.parse_args()
app = args.app
input_path = args.profiling_data
output_path = args.directory


app_data_path = {
    "hotel-reserv": "data_hotel-reserv",
    "media-microsvc": "data_media-microsvc",
    "social-network": "data_social-network",
}[app]
data_path = f"{input_path}/{app_data_path}"
os.system(f"mv {data_path}/fittingResult {data_path}/fittingResult_original")
os.system(f"mkdir -p {output_path}/figure_10")

accy_result = []
for portion in [0.5, 0.6, 0.7, 0.8, 0.9]:
    fitter = Fitting(
        data_path,
        portion,
        {
            x[0]: range(x[1].min, x[1].max, x[1].step)
            for x in configs.FITTING_CONFIG.cutoff_range.items()
        },
        f"{data_path}/figures",
        {"lower": 0.1, "higher": 0.9},
        0.6,
        0.3,
        configs.FITTING_CONFIG.throughput_classification_precision,
        configs.GLOBAL_CONFIG.replicas,
    )
    fitter.erms_main()
    fitter.xgboost_fitting()
    fitter.nn_fitting()
    os.system(
        f"mv {data_path}/fittingResult {output_path}/figure_10/{app}_fittingResult_{portion}"
    )
    erms_df = pd.read_csv(
        f"{output_path}/figure_10/{app}_fittingResult_{portion}/ermsFull.csv"
    )
    erms_df = erms_df.loc[erms_df["accy"] > 0.5]
    erms_mean = erms_df["accy"].mean()
    erms_median = erms_df["accy"].median()
    xgboost_df = pd.read_csv(
        f"{output_path}/figure_10/{app}_fittingResult_{portion}/xgboost.csv"
    )
    xgboost_df = xgboost_df.loc[xgboost_df["accy"] > 0.5]
    xgboost_mean = xgboost_df["accy"].mean()
    xgboost_median = xgboost_df["accy"].median()
    nn_df = pd.read_csv(f"{output_path}/figure_10/{app}_fittingResult_{portion}/nn.csv")
    nn_df = nn_df.loc[nn_df["accy"] > 0.5]
    nn_mean = nn_df["accy"].mean()
    nn_median = nn_df["accy"].median()
    accy_result.append(
        {
            "portion": portion,
            "erms_mean": erms_mean,
            "xgboost_mean": xgboost_mean,
            "nn_mean": nn_mean,
            "erms_median": erms_median,
            "xgboost_median": xgboost_median,
            "nn_median": nn_median,
        }
    )

os.system(f"mv {data_path}/fittingResult_original {data_path}/fittingResult")

pd.DataFrame(accy_result).to_csv(
    f"{output_path}/figure_10/{app}_result.csv", index=False
)
