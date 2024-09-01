import pandas as pd


def analyse(result_path):
    data = statistics(result_path)
    data = data.assign(
        ratio_1=data["latency_1"] / data["sla_1"] / 1000,
        ratio_2=data["latency_2"] / data["sla_2"] / 1000,
    )
    erms = data.loc[data["method"] == "erms"].rename(
        columns={"ratio_1": "erms_1", "ratio_2": "erms_2"}
    )[["sla_1", "sla_2", "workload_1", "workload_2", "erms_1", "erms_2"]]
    grandSLAm = data.loc[data["method"] == "grandSLAm"].rename(
        columns={"ratio_1": "grandSLAm_1", "ratio_2": "grandSLAm_2"}
    )[["sla_1", "sla_2", "workload_1", "workload_2", "grandSLAm_1", "grandSLAm_2"]]
    rhythm = data.loc[data["method"] == "rhythm"].rename(
        columns={"ratio_1": "rhythm_1", "ratio_2": "rhythm_2"}
    )[["sla_1", "sla_2", "workload_1", "workload_2", "rhythm_1", "rhythm_2"]]

    result = erms.merge(
        grandSLAm, on=["sla_1", "sla_2", "workload_1", "workload_2"]
    ).merge(rhythm, on=["sla_1", "sla_2", "workload_1", "workload_2"])
    result = result.assign(
        erms_mean=(result["erms_1"] + result["erms_2"]) / 2,
        rhythm_mean=(result["rhythm_1"] + result["rhythm_2"]) / 2,
        grandSLAm_mean=(result["grandSLAm_1"] + result["grandSLAm_2"]) / 2,
    )
    import ipdb

    ipdb.set_trace()


def statistics(result_path):
    data = pd.read_csv(f"{result_path}/trace_latency.csv")
    data = (
        data.groupby(["service", "var_index", "method", "repeat"])
        .quantile(0.95)
        .reset_index()
    )
    services = data["service"].unique().tolist()
    service_1 = services[0]
    result_1 = data.loc[data["service"] == service_1][
        [
            "service",
            "var_index",
            "method",
            "traceLatency",
            "throughput",
            f"{service_1}_sla",
            f"{service_1}_workload",
            "container",
            "cpu_inf",
            "mem_inf",
            "service_container",
            "repeat",
        ]
    ].rename(
        columns={
            "service": "service_1",
            f"{service_1}_sla": "sla_1",
            f"{service_1}_workload": "workload_1",
            "container": "container_merge",
            "traceLatency": "latency_1",
            "service_container": "container_1",
        }
    )
    if len(services) > 1:
        service_2 = services[1]
        result_2 = data.loc[data["service"] == service_2][
            [
                "service",
                "var_index",
                "method",
                "traceLatency",
                "throughput",
                f"{service_2}_sla",
                f"{service_2}_workload",
                "service_container",
                "repeat",
            ]
        ].rename(
            columns={
                "service": "service_2",
                f"{service_2}_sla": "sla_2",
                f"{service_2}_workload": "workload_2",
                "traceLatency": "latency_2",
                "service_container": "container_2",
            }
        )
        result = result_1.merge(result_2, on=["var_index", "method", "repeat"]).assign(
            use_prio=True,
        )
    else:
        result = result_1.assign(
            service_2=None,
            sla_2=None,
            workload_2=None,
            latency_2=None,
            container_2=None,
        )
    result = result[
        [
            "repeat",
            "service_1",
            "service_2",
            "method",
            "use_prio",
            "cpu_inf",
            "mem_inf",
            "sla_1",
            "sla_2",
            "workload_1",
            "workload_2",
            "container_1",
            "container_2",
            "container_merge",
            "latency_1",
            "latency_2",
        ]
    ]
    import ipdb

    ipdb.set_trace()
    return result
