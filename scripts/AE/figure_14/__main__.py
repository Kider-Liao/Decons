from scripts.AE.figure_14.analysis import analyse, statistics_b, statistics_a
from scripts.AE.figure_14.data import figure_a, single_main
from scripts.AE.utils import CONFIG

# statistics_a("/root/Erms/data_social/validation/f14/UserTimeline-a")
# statistics_b("data_hotel-reserv", "Search")
interference = [
    {
        "cpu": {
            "cpu_size": 0.25,
            "mem_size": "10Mi",
            "allocation": {
                "izj6c6vb9bfm8mxnvb4n47z": {"idle": 0, "busy": 8},
                "izj6c6vb9bfm8mxnvb4n46z": {"idle": 0, "busy": 8},
                "izj6c6vb9bfm8mxnvb4n45z": {"idle": 7, "busy": 0},
                "izj6c6vb9bfm8mxnvb4n44z": {"idle": 7, "busy": 0},
            },
        },
        "mem": {
            "cpu_size": 0.01,
            "mem_size": "500Mi",
            "allocation": {
                "izj6c6vb9bfm8mxnvb4n47z": {"idle": 0, "busy": 8},
                "izj6c6vb9bfm8mxnvb4n46z": {"idle": 0, "busy": 8},
                "izj6c6vb9bfm8mxnvb4n45z": {"idle": 7, "busy": 0},
                "izj6c6vb9bfm8mxnvb4n44z": {"idle": 7, "busy": 0},
            },
        },
    },
]

app = "social-network"
result_path = "validation/f14/UserTimeline-a"
repeats = [8]
figure_a(
    interference,
    [
        (
            {"UserTimeline": 35},
            {"UserTimeline": {"clients": 20, "thread": 2, "conn": 3, "throughput": 6}},
        ),
        (
            {"UserTimeline": 40},
            {"UserTimeline": {"clients": 20, "thread": 2, "conn": 3, "throughput": 6}},
        ),
    ],
    "data_social",
    "UserTimeline",
    CONFIG["nodes"],
    CONFIG["namespace"][app],
    CONFIG["pod_spec"],
    CONFIG["yaml_repo"][app],
    CONFIG["image"][app],
    CONFIG["prometheus_host"],
    CONFIG["scripts"][app],
    CONFIG["host"][app],
    CONFIG["operations"][app],
    repeats,
    result_path,
    CONFIG["jaeger_host"][app],
    CONFIG["entry_point"][app],
    [1, 1.2, 1.4, 1.6, 1.8, 2],
    no_nginx=True,
)