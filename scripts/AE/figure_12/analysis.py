import pandas as pd


def statistics(result_path, service):
    file = f"{result_path}/{service}/trace_latency.csv"
    data = pd.read_csv(file)
    data = data.loc[data["service"] == service]
    columns = ["service", "method", "timestamp"]
    data = (
        data.groupby(columns + ["repeat"])
        .quantile(0.95)
        .groupby(columns)
        .mean()
        .reset_index()
    )
    data = data.assign(sla=data["sla"] * 1000)
    data.to_csv(f"{result_path}/{service}.csv")


def analyse(result_path: str):
    file = f"{result_path}/trace_latency.csv"
    data = pd.read_csv(file)
    data = data.assign(ratio=data["traceLatency"] / data["sla"])
    p95_ratio = (
        data.groupby(["index", "method", "repeat"], sort=False)[
            ["ratio", "traceLatency"]
        ]
        .quantile(0.95)
        .reset_index()
        .groupby(["method", "index"], sort=False)[["traceLatency", "ratio"]]
        .mean()
        .reset_index()
        .sort_values("index")
    )
    import ipdb

    ipdb.set_trace()
