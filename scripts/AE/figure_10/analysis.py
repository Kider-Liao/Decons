from box import Box
import pandas as pd


def main(file_path):
    data = pd.read_csv(file_path)
    result = Box()
    for service, service_data in data.groupby("service"):
        service_workload_col = f"{service}_workload"
        service_sla_col = f"{service}_sla"
        service_data = pd.DataFrame(service_data)
        by_workload = (
            service_data.groupby(service_workload_col)[
                ["grandSLAm_ratio", "rhythm_ratio"]
            ]
            .mean()
            .reset_index()
        )

        by_sla = (
            service_data.groupby(service_sla_col)[["grandSLAm_ratio", "rhythm_ratio"]]
            .mean()
            .reset_index()
        )

        by_inter = (
            service_data.groupby(["cpu_inter", "mem_inter"])[
                ["grandSLAm_ratio", "rhythm_ratio"]
            ]
            .mean()
            .reset_index()
        )
        mean = service_data[["grandSLAm_ratio", "rhythm_ratio"]].mean()
        result[service] = Box(
            {
                "by_workload": by_workload,
                "by_sla": by_sla,
                "by_inter": by_inter,
                "mean": mean,
            }
        )
    import ipdb

    ipdb.set_trace()
