import pandas as pd


def statistics_b(data_path, service):
    data = pd.read_csv(f"{data_path}/validation/f14/{service}-b/trace_latency.csv")
    columns = ["service", "var_index", "cpu_inter", "mem_inter", "scheduler"]
    data = data.groupby(columns + ["repeat"]).quantile(0.95)
    import ipdb

    ipdb.set_trace()


def statistics_a(file_path):
    data = pd.read_csv(f"{file_path}/trace_latency.csv")
    columns = ["service", "var_index", "cpu_inter", "mem_inter", "container"]
    data = (
        data.groupby(columns + ["repeat"])
        .quantile(0.95)
        .groupby(columns)
        .mean()
        .reset_index()
    )
    import ipdb

    ipdb.set_trace()


def analyse(data_path):
    data = pd.read_csv(f"{data_path}/validation/f14/trace_latency.csv")
    import ipdb

    ipdb.set_trace()
    data = (
        data.groupby(
            ["var_index", "cpu_inter", "mem_inter", "scheduler", "repeat", "service"]
        )
        .quantile(0.95)
        .groupby(["var_index", "cpu_inter", "mem_inter", "scheduler", "service"])
        .mean()
        .reset_index()
    )
    data = data.assign(
        ratio=data.apply(lambda x: x["traceLatency"] / x[f"{x['service']}_sla"], axis=1)
    )
    import ipdb

    ipdb.set_trace()
