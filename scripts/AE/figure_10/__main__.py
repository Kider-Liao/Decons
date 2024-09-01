from scripts.AE.figure_10.data import sharing_main, single_main
from scripts.AE.utils import CONFIG

infs = [
    {"cpu": x, "mem": y}
    for x in [0.25, 0.5, 0.75, 1, 1.25, 1.5]
    for y in [500, 1000, 1500, 2000, 2500, 3000]
]

# app = "media-microsvc"
# single_main(
#     CONFIG["data_path"][app],
#     "validation/f10/single",
#     infs,
#     {
#         "ComposeReview": [
#             ({"ComposeReview": x}, {"ComposeReview": y})
#             for x in [250, 375, 500]
#             for y in [40, 80, 120]
#         ]
#     },
#     ["ComposeReview"],
#     3
# )
app = "hotel-reserv"
sharing_main(
    # CONFIG["data_path"][app],
    "data_hotel-reserv",
    "validation/f10/sharing",
    infs,
    [
        ({"Search": a, "Recommendation": b}, {"Search": c, "Recommendation": d})
        for a in [100, 150, 200]
        for b in [20, 30, 40]
        for c in [60, 120, 180]
        for d in [140, 280, 420]
    ],
    ["Search", "Recommendation"],
    4,
    init_containers={
        "Search": {"profile": 2},
        "Recommendation": {"profile": 2},
    },
    # fixed_ms={"frontend": 15},
    base_workload={"Search": 60, "Recommendation": 140},
    # debug=True,
)
# app = "social-network"
# slas_workloads = [
#     (
#         {"UserTimeline": a, "HomeTimeline": b},
#         {"UserTimeline": c, "HomeTimeline": d},
#     )
#     # for a in [200, 250, 300, 350, 400]
#     for a in [200]
#     for b in [300]
#     for c in [120]
#     for d in [200]
# ]
# sharing_main(
#     # CONFIG["data_path"][app],
#     "data_social",
#     "validation/f10/sharing",
#     infs,
#     slas_workloads,
#     # ["HomeTimeline", "UserTimeline"],
#     ["HomeTimeline"],
#     4,
#     debug=True,
# )
# # import ipdb
# # ipdb.set_trace()

# # sharing_main(
# #     CONFIG["data_path"][app],
# #     "validation/f10/sharing",
# #     infs,
# #     [
# #         ({"ComposePost": a, "HomeTimeline": b}, {"ComposePost": c, "HomeTimeline": d})
# #         for a in [250, 500, 750]
# #         for b in [650, 1300, 1950]
# #         for c in [80, 160, 240]
# #         for d in [20, 40, 60]
# #     ],
# #     ["HomeTimeline", "ComposePost"],
# #     3,
# # )
# # app = "media-microsvc"
# # single_main(
# #     CONFIG["data_path"][app],
# #     "validation/f10",
# #     infs,
# #     {
# #         "ComposeReview": [
# #             ({"ComposeReview": x}, {"ComposeReview": y})
# #             for x in [250, 500, 750]
# #             for y in [40, 80, 120]
# #         ]
# #     },
# #     ["ComposeReview"],
# #     3,
# # )
