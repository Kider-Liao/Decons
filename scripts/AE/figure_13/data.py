import multiprocessing
import os
from scripts.AE.utils import container_computation
from utils.files import append_data
import pandas as pd


def sharing_main(
    data_path,
    result_path,
    infs,
    slas_workloads,
    services,
    max_processes,
    debug=False,
):
    os.system(f"mkdir -p {data_path}/{result_path}")
    result_file = f"{data_path}/{result_path}/{'_'.join(services)}.csv"
    if debug:
        test_infs(
            data_path,
            result_file,
            slas_workloads,
            infs,
            services,
            debug,
        )
        return
    print(f"Data will be saved into {result_file}")
    pool = multiprocessing.Pool(max_processes)
    inf_part_len = int(len(infs) / max_processes)
    for i in range(max_processes):
        if i + 1 == max_processes:
            part_infs = infs[i * inf_part_len :]
        else:
            part_infs = infs[i * inf_part_len : (i + 1) * inf_part_len]
        pool.apply_async(
            test_infs,
            (
                data_path,
                result_file,
                slas_workloads,
                part_infs,
                services,
                debug,
            ),
        )
    pool.close()
    pool.join()


def test_infs(
    data_path,
    result_file,
    slas_workloads,
    infs,
    services,
    debug=False,
):
    pid = os.getpid()
    total = len(infs)
    counter = 0
    for inf in infs:
        print(f"Process {pid}: {format(counter / total * 100, '.2f')}%")
        latency_target_data, container_data = container_computation(
            data_path,
            slas_workloads,
            inf["cpu"],
            inf["mem"],
            services,
            ["erms", "rhythm", "grandSLAm"],
            debug=debug,
            prio=True,
        )
        container_result = statistics(container_data, latency_target_data, True)
        if not debug:
            append_data(container_result, result_file)
        latency_target_data, container_data = container_computation(
            data_path,
            slas_workloads,
            inf["cpu"],
            inf["mem"],
            services,
            ["erms", "rhythm", "grandSLAm"],
            debug=debug,
            prio=False,
        )
        container_result = statistics(container_data, latency_target_data, False)
        counter += 1
        if not debug:
            append_data(container_result, result_file)
    print(f"Process {pid} done.")


def statistics(container_data: pd.DataFrame, latency_target_data: pd.DataFrame, prio):
    container_data = container_data.loc[
        container_data["microservice"] != "nginx-web-server"
    ]
    columns = ["service", "cpu_inter", "mem_inter", "var_index", "method"]
    data = (
        latency_target_data.groupby(columns + ["microservice"])["container"]
        .max()
        .groupby(columns)
        .sum()
        .reset_index()
    )
    services = latency_target_data["service"].unique().tolist()
    service_1 = services[0]
    latency_target_1 = (
        data.loc[data["service"] == service_1]
        .merge(
            latency_target_data[
                ["service", "var_index", f"{service_1}_sla", f"{service_1}_workload"]
            ].drop_duplicates(),
            on=["service", "var_index"],
        )
        .rename(
            columns={f"{service_1}_sla": "sla_1", f"{service_1}_workload": "workload_1"}
        )
    )
    if len(services) > 1:
        service_2 = services[1]
        latency_target_2 = (
            data.loc[data["service"] == service_2]
            .merge(
                latency_target_data[
                    [
                        "service",
                        "var_index",
                        f"{service_2}_sla",
                        f"{service_2}_workload",
                    ]
                ].drop_duplicates(),
                on=["service", "var_index"],
            )
            .rename(
                columns={
                    f"{service_2}_sla": "sla_2",
                    f"{service_2}_workload": "workload_2",
                }
            )
        )
        container_merge = (
            container_data.groupby(["cpu_inter", "mem_inter", "method", "var_index"])[
                "container"
            ]
            .sum()
            .reset_index()
            .rename(columns={"container": "container_merge"})
        )
        result = latency_target_1.merge(
            latency_target_2,
            on=["cpu_inter", "mem_inter", "var_index", "method"],
            suffixes=("_1", "_2"),
        ).merge(container_merge, on=["cpu_inter", "mem_inter", "var_index", "method"])
    else:
        result = latency_target_1.assign(
            service_2=None,
            container_2=None,
            sla_2=None,
            workload_2=None,
            container_merge=latency_target_1["container"],
        ).rename(columns={"container": "container_1", "service": "service_1"})
    result = result.assign(use_prio=prio, latency_1=None, latency_2=None).rename(
        columns={"cpu_inter": "cpu_inf", "mem_inter": "mem_inf"}
    )
    result = result[
        [
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
    return result
