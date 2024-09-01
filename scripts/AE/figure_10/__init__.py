from scripts.AE.figure_10.data import single_main as generation
from scripts.AE.figure_10.analysis import main as analyse

# Recommendation: 170ms, 140
# Search: 1700ms, 60
# Login: 100ms, 160

# HomeTimeline: 1300ms, 40
# UserTimeline: 48ms, 40
# ComposePost: 580ms, 160

# ComposeReview: 495ms, 80
max_processes = 3

# SLA and workloads, SLA units in `ms`
slas = {
    "hotel-reserv": {
        "Recommendation": [150, 160, 170, 180, 190],
        "Search": [1500, 1600, 1700, 1800, 1900],
        "Login": [40, 60, 80, 100],
    },
    "social-network": {
        "HomeTimeline": [800, 900, 1000, 1100, 1200],
        "UserTimeline": [32, 40, 48, 56, 64],
        "ComposePost": [480, 530, 580, 630, 680],
    },
    "media-microsvc": {"ComposeReview": [250, 300, 350, 400, 450]},
}
workloads = {
    "hotel-reserv": {
        "Search": [60, 120, 180, 240, 300],
        "Recommendation": [140, 280, 420, 560, 600],
        "Login": [160, 180, 200, 220, 240],
    },
    "social-network": {
        "HomeTimeline": [40, 60, 80, 100, 120],
        "UserTimeline": [40, 80, 120, 160, 200],
        "ComposePost": [80, 160, 320, 480],
    },
    "media-microsvc": {"ComposeReview": [20, 40, 60, 80, 100]},
}

# Services
services = {
    "hotel-reserv": ["Login"],
    "social-network": ["ComposePost"],
    "media-microsvc": ["ComposeReview"],
}

# Interference
cpu_infs = [0.4, 0.8, 1.2, 1.6, 2.0, 2.4]
# cpu_infs=[1.5]
mem_infs = [500, 1000, 1500, 2000, 2500, 3000]
# mem_infs=[1500]

# File path
data_path = {
    "hotel-reserv": "AE/data_hotel-reserv",
    "social-network": "AE/data_social-network",
    "media-microsvc": "AE/data_media-microsvc",
}
result_path = {
    "hotel-reserv": "AE/data_hotel-reserv/validation/f10/hoelResult.csv",
    "social-network": "AE/data_social-network/validation/f10/socialResult.csv",
    "media-microsvc": "AE/data_media-microsvc/validation/f10/mediaResult.csv",
}


def generate_single_service_data(
    app,
    debug=False,
    workload=None,
    sla=None,
    cpu_inter=None,
    mem_inter=None,
    service=None,
):
    if debug:
        generation(
            [service],
            {service: [float(sla)]},
            {service: [float(workload)]},
            [float(cpu_inter)],
            [float(mem_inter)],
            data_path[app],
            result_path[app],
            max_processes,
            True,
        )
    else:
        generation(
            services[app],
            slas[app],
            workloads[app],
            cpu_infs,
            mem_infs,
            data_path[app],
            result_path[app],
            max_processes,
            False,
        )


def analyse_data(app):
    analyse(result_path[app])
