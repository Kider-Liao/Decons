from scripts.AE.figure_12.analysis import statistics
from scripts.AE.figure_12.data import main
from scripts.AE.utils import CONFIG

statistics("data_hotel-reserv/validation/f12", "Search")
import ipdb

ipdb.set_trace()

# sla = 200
# scale = 1
# app = "hotel-reserv"
# service = "Search"
# repeats = [0, 1, 2]
# methods = ["erms", "firm", "rhythm", "grandSLAm"]
# # methods = ["erms"]
# main(
#     CONFIG["interference"][0],
#     sla,
#     {
#         "thread": 1,
#         "conn": 2,
#         "throughput": 3,
#     },
#     scale,
#     # CONFIG["data_path"][app],
#     "data_hotel-reserv",
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
#     repeats,
#     "validation/f12",
#     CONFIG["jaeger_host"][app],
#     CONFIG["entry_point"][app],
#     methods,
#     # no_frontend=True,
#     init_containers={
#         "Search": {"frontend": 2, "profile": 2},
#         # "Recommendation": {"profile": 2},
#         # "HomeTimeline": {"post-storage-service": 2},
#         # "UserTimeline": {"post-storage-service": 3},
#     },
#     base_workload={
#         "Search": 60,
#         # "Recommendation": 140,
#     },
#     # do_inf_deployment=True,
# )

sla = 200
scale = 0.25
app = "social-network"
service = "ComposePost"
repeats = [0, 1, 2]
methods = ["erms", "firm"]
# methods = ["erms"]
main(
    CONFIG["interference"][0],
    sla,
    {
        "thread": 2,
        "conn": 4,
        "throughput": 8,
    },
    scale,
    CONFIG["data_path"][app],
    service,
    CONFIG["nodes"],
    CONFIG["namespace"][app],
    CONFIG["pod_spec"],
    CONFIG["yaml_repo"][app],
    CONFIG["image"][app],
    CONFIG["prometheus_host"],
    CONFIG["scripts"][app][service],
    CONFIG["host"][app],
    CONFIG["operations"][app][service],
    repeats,
    "validation/f12",
    CONFIG["jaeger_host"][app],
    CONFIG["entry_point"][app],
    methods,
    no_nginx=True,
    init_containers={
        "ComposePost": {"compose-post-service": 4, "text-service": 2},
        # "Recommendation": {"profile": 2},
        # "HomeTimeline": {"post-storage-service": 2},
        # "UserTimeline": {"post-storage-service": 3},
    },
    base_workload={
        "ComposePost": 160,
        # "Recommendation": 140,
    },
    fixed_ms={"nginx-web-server": 30}
    # do_inf_deployment=True,
)
