from scripts.AE.figure_13 import HOME_USER_INFS, HOME_USER_SLAS_WORKLOADS
from scripts.AE.figure_13.data import sharing_main

import pandas as pd

# data = pd.read_csv(
#     "/root/Erms/data_social/validation/f13/HomeTimeline_UserTimeline.csv"
# )
# columns = [
#     "service_1",
#     "service_2",
#     "cpu_inf",
#     "mem_inf",
#     "sla_1",
#     "sla_2",
#     "workload_1",
#     "workload_2",
# ]
# use_prio = data.loc[data["use_prio"]].rename(columns={"container_merge": "prio"})
# non_prio = data.loc[~data["use_prio"]].rename(columns={"container_merge": "non"})
# merged = use_prio.merge(non_prio, on=columns + ["method"])[
#     columns + ["method", "prio", "non"]
# ]
# merged = merged.assign(ratio=merged["non"] / merged["prio"])
# erms = merged.loc[merged["method"] == "erms"].rename(columns={"ratio": "erms_ratio"})
# rhythm = merged.loc[merged["method"] == "rhythm"].rename(
#     columns={"ratio": "rhythm_ratio"}
# )
# grandSLAm = merged.loc[merged["method"] == "grandSLAm"].rename(
#     columns={"ratio": "grandSLAm_ratio"}
# )
# result = erms.merge(rhythm, on=columns).merge(grandSLAm, on=columns)[
#     columns + ["erms_ratio", "rhythm_ratio", "grandSLAm_ratio"]
# ]
# result = result.assign(
#     r2e=result["rhythm_ratio"] / result["erms_ratio"],
#     g2e=result["grandSLAm_ratio"] / result["erms_ratio"],
# )
# w1 = result.groupby("workload_1").mean()
# w2 = result.groupby("workload_2").mean()
# s1 = result.groupby("sla_1").mean()
# s2 = result.groupby("sla_2").mean()
# import ipdb

# ipdb.set_trace()

# infs = [{"cpu": x, "mem": y} for x in [0.25, 0.5, 1, 1.25, 1.5] for y in [500, 1000, 1500, 2000, 2500, 3000]]
# infs = [{"cpu": x, "mem": y} for x in [0.25, 1.5] for y in [500, 3000]]
infs = [{"cpu": 0.25, "mem": 500}]
# app = "hotel-reserv"
# sharing_main(
#     # CONFIG["data_path"][app],
#     "data_hotel-reserv",
#     "validation/f13",
#     infs,
#     [
#         ({"Search": a, "Recommendation": b}, {"Search": c, "Recommendation": d})
#         for a in [300, 350]
#         for b in [50, 60]
#         for c in [240]
#         for d in [560]
#     ],
#     ["Search", "Recommendation"],
#     4,
# )
app = "social-network"
# sharing_main(
#     "data_social",
#     "validation/f13",
#     infs,
#     [
#         ({"HomeTimeline": a, "UserTimeline": b}, {"HomeTimeline": c, "UserTimeline": d})
#         # for a in [200, 300, 400, 500, 600]
#         # for b in [150, 200, 250, 300, 350, 400, 450]
#         # for c in [10, 30, 50, 70, 140, 210, 280, 350, 420]
#         # for d in [10, 20, 30, 40, 80, 120, 160, 200, 240]
#         for a in [200]
#         for b in [150]
#         for c in [10]
#         for d in [240]
#     ],
#     # HOME_USER_INFS,
#     # HOME_USER_SLAS_WORKLOADS,
#     ["HomeTimeline", "UserTimeline"],
#     1,
#     # True
# )
sharing_main(
    "data_social",
    "validation/f13",
    infs,
    [
        ({"ComposePost": a, "UserTimeline": b}, {"ComposePost": c, "UserTimeline": d})
        for a in [100, 200, 300, 400, 500, 600]
        # for a in [300]
        for b in [100, 200, 300, 400, 500, 600]
        # for b in [500]
        for c in [20, 40, 80, 160, 320, 480]
        # for c in [360]
        for d in [30, 60, 90, 120, 240, 360]
        # for d in [160]
    ],
    ["ComposePost", "UserTimeline"],
    1,
    # True
)
