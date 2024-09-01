from scripts.AE.figure_11.analysis import statistics, analyse
from scripts.AE.figure_11.data import sharing_main, single_main
from scripts.AE.utils import CONFIG

statistics("/root/Erms/data_hotel-reserv/validation/f11-final-firm/Search_Recommendation")
# analyse("data_social/validation/f11/HomeTimeline_UserTimeline")

# app = "social-network"
# slas_workload_configs = [
#     (
#         {"UserTimeline": a, "HomeTimeline": b},
#         {
#             "UserTimeline": {
#                 "clients": c,
#                 "thread": 2,
#                 "conn": 3,
#                 "throughput": 6,
#             },
#             "HomeTimeline": {
#                 "clients": d,
#                 "thread": 3,
#                 "conn": 5,
#                 "throughput": 10,
#             },
#         },
#     )
#     # for a in [200, 250, 300, 350, 400]
#     for a in [200]
#     # for b in [300, 400, 500, 600]
#     for b in [300]
#     for c in [20]
#     for d in [20]
# ]

# service = "UserTimeline"
# single_main(
#     CONFIG["interference"][1],
#     slas_workload_configs,
#     "data_social",
#     service,
#     CONFIG["nodes"],
#     CONFIG["namespace"][app],
#     CONFIG["pod_spec"],
#     CONFIG["yaml_repo"][app],
#     CONFIG["image"][app],
#     CONFIG["prometheus_host"],
#     CONFIG["scripts"][app][service],
#     CONFIG["host"][app],
#     CONFIG["operations"][app][service],
#     [0, 1, 2],
#     "validation/f11",
#     CONFIG["jaeger_host"][app],
#     CONFIG["entry_point"][app],
#     no_nginx=True,
#     # do_inf_deployment=True,
#     methods=["firm"],
#     init_containers={
#         "HomeTimeline": {"post-storage-service": 2},
#         "UserTimeline": {"post-storage-service": 3},
#     },
#     fixed_ms={"nginx-web-server": 20},
# )

# sharing_main(
#     CONFIG["interference"][1],
#     slas_workload_configs,
#     # CONFIG["data_path"][app],
#     "data_social",
#     ["HomeTimeline", "UserTimeline"],
#     CONFIG["nodes"],
#     CONFIG["namespace"][app],
#     CONFIG["pod_spec"],
#     CONFIG["yaml_repo"][app],
#     CONFIG["image"][app],
#     CONFIG["prometheus_host"],
#     CONFIG["scripts"][app],
#     CONFIG["host"][app],
#     CONFIG["operations"][app],
#     [0, 1, 2],
#     "validation/f11",
#     CONFIG["jaeger_host"][app],
#     CONFIG["entry_point"][app],
#     no_nginx=True,
#     # do_inf_deployment=True,
#     methods=["erms"],
# )

# app = "media-microsvc"

# single_main(
#     CONFIG["interference"][0],
#     {
#         "ComposeReview": [
#             ({"ComposeReview": x}, {"ComposeReview": y})
#             for x in [250, 500, 750]
#             for y in [40, 80, 120]
#         ]
#     },
#     CONFIG["data_path"][app],
#     ["ComposeReview"],
#     CONFIG["nodes"],
#     CONFIG["namespace"][app],
#     CONFIG["pod_spec"],
#     CONFIG["yaml_repo"][app],
#     CONFIG["image"][app],
#     CONFIG["prometheus_host"],
#     CONFIG["scripts"][app],
#     CONFIG["host"][app],
#     CONFIG["operations"][app],
#     [0, 1, 2],
#     "validation/f11/ComposeReview",
#     CONFIG["jaeger_host"][app],
#     CONFIG["entry_point"][app],
#     no_nginx=False,
# )

app = "hotel-reserv"

slas_workload_configs = [
    (
        {"Search": a, "Recommendation": b},
        {
            "Search": {
                "clients": c,
                "thread": 1,
                "conn": 2,
                "throughput": 3,
            },
            "Recommendation": {
                "clients": d,
                "thread": 2,
                "conn": 4,
                "throughput": 7,
            },
        },
    )
    for a in [150, 300]
    for b in [30, 60]
    for c in [40, 50, 60]
    for d in [60, 70]
]

sharing_main(
    CONFIG["interference"][0],
    slas_workload_configs,
    # CONFIG["data_path"][app],
    "data_hotel-reserv",
    ["Search", "Recommendation"],
    CONFIG["nodes"],
    CONFIG["namespace"][app],
    CONFIG["pod_spec"],
    CONFIG["yaml_repo"][app],
    CONFIG["image"][app],
    CONFIG["prometheus_host"],
    CONFIG["scripts"][app],
    CONFIG["host"][app],
    CONFIG["operations"][app],
    [0, 1, 2],
    "validation/f11-final-firm",
    CONFIG["jaeger_host"][app],
    CONFIG["entry_point"][app],
    no_frontend=True,
    methods=["firm"],
    # do_inf_deployment=True,
    init_containers={
        "Search": {"profile": 2},
        "Recommendation": {"profile": 2},
    },
    base_workload={"Search": 60, "Recommendation": 140},
    fixed_ms={"frontend": 15},
)
