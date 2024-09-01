from dataCollector.OfflineProfilingDataCollector import OfflineProfilingDataCollector
from deployment.deployer import delete_by_yaml
from onlineScheduling.applyPriority import clear_vifs
from onlineScheduling.placementOptimization import ErmsScheduler
from scripts.AE.utils import (
    config_to_workload,
    container_computation,
    deploy_infs,
    get_inter,
    k8s_scheduling,
    generate_multiple_workloads,
)
from math import ceil


def sharing_main(
    cpu_inter,
    mem_inter,
    slas_workloads,
    data_path,
    services,
    nodes,
    namespace,
    pod_spec,
    yaml_repo,
    image,
    prometheus_host,
    scripts,
    host,
    operations,
    repeats,
    result_path,
    jaeger_host,
    entry_point,
    no_nginx=False,
):
    erms_scheduling = ErmsScheduler(data_path)
    collector = OfflineProfilingDataCollector(
        namespace, jaeger_host, entry_point, prometheus_host, nodes, data_path
    )
    methods = ["erms", "rhythm", "grandSLAm"]
    # Latency target computation
    print("Computing latency targets...")
    result = container_computation(
        data_path, slas_workloads, cpu_inter, mem_inter, services, methods
    )
    for var_index, (slas, workloads) in enumerate(slas_workloads):
        latency_targets_result = result[0]
        containers_result = result[1]
        for repeat in repeats:
            for method in methods:
                containers = containers_result.loc[
                    (containers_result["var_index"] == var_index)
                    & (containers_result["method"] == method)
                ]
                latency_targets = latency_targets_result.loc[
                    (latency_targets_result["var_index"] == var_index)
                    & (latency_targets_result["method"] == method)
                ]
                print(containers)
                # Containers deployment
                print("Deploying containers...")
                if method == "erms":
                    erms_scheduling.main(
                        pod_spec,
                        1,
                        nodes,
                        yaml_repo,
                        namespace,
                        prometheus_host,
                        image,
                        latency_target_df=latency_targets,
                        container_df=containers,
                    )
                elif method == "rhythm" or method == "grandSLAm":
                    k8s_scheduling(
                        containers, nodes, namespace, pod_spec, yaml_repo, image
                    )
                else:
                    continue
                print("Test starts...")
                # Workload generation
                start_time = generate_multiple_workloads(
                    services, 60, workloads, scripts, host
                )
                # Data collection
                kwargs = {f"{service}_sla": slas[service] for service in services}
                kwargs.update(
                    {f"{service}_workload": workloads[service] for service in services}
                )
                kwargs.update({"method": method, "var_index": var_index})
                for service in services:
                    collector.validation_collection_async(
                        f"validation_{service}",
                        start_time,
                        operations[service],
                        service,
                        repeat,
                        result_path,
                        no_nginx,
                        **kwargs,
                    )
                if method == "erms":
                    clear_vifs(data_path)
    print("Waiting for data collection...")
    collector.wait_until_done()
    delete_by_yaml("tmp/scheduledAPP")


def figure_a(
    inters,
    slas_workload_configs,
    data_path,
    service,
    nodes,
    namespace,
    pod_spec,
    yaml_repo,
    image,
    prometheus_host,
    scripts,
    host,
    operations,
    repeats,
    result_path,
    jaeger_host,
    entry_point,
    ratios,
    no_nginx=False,
    no_frontend=False,
):
    collector = OfflineProfilingDataCollector(
        namespace, jaeger_host, entry_point, prometheus_host, nodes, data_path
    )
    # Latency target computation
    for inter in inters:
        cpu_inter, mem_inter = get_inter(inter)
        print("Deploying interference...")
        deploy_infs(inter, nodes)
        print("Computing latency targets...")
        slas_workloads = config_to_workload(slas_workload_configs)
        latency_targets_result, containers_result = container_computation(
            data_path, slas_workloads, cpu_inter, mem_inter, [service], ["erms"]
        )
        for var_index, (sla, workload_config) in enumerate(slas_workload_configs):
            for repeat in repeats:
                for ratio in ratios:
                    containers = containers_result.loc[
                        containers_result["var_index"] == var_index
                    ]
                    containers.loc[containers["microservice"] == "nginx-web-server", "container"] = 20
                    original_containers = containers["container"].sum() - 20
                    containers = containers.assign(
                        container=(containers["container"] * ratio).apply(ceil)
                    )
                    containers.loc[containers["microservice"] == "nginx-web-server", "container"] = 20
                    print(f"Ratio: {(containers['container'].sum() - 20) / original_containers}")
                    print(containers)
                    # Containers deployment
                    print("Deploying containers...")
                    k8s_scheduling(
                        containers, nodes, namespace, pod_spec, yaml_repo, image
                    )
                    print("Test starts...")
                    # Workload generation
                    start_time = generate_multiple_workloads(
                        [service], 60, workload_config, scripts, host
                    )
                    # Data collection
                    kwargs = {
                        f"{service}_sla": sla[service] * 1000,
                        f"{service}_workload": slas_workloads[var_index][1][service],
                        "container": containers["container"].sum(),
                        "original_container": original_containers,
                        "var_index": var_index,
                        "cpu_inter": cpu_inter,
                        "mem_inter": mem_inter,
                    }
                    collector.validation_collection_async(
                        f"validation_{service}",
                        start_time,
                        operations[service],
                        service,
                        repeat,
                        result_path,
                        no_nginx,
                        no_frontend,
                        **kwargs,
                    )
    print("Waiting for data collection...")
    collector.wait_until_done()
    delete_by_yaml("tmp/scheduledAPP")


def single_main(
    inters,
    slas_workload_configs,
    data_path,
    service,
    nodes,
    namespace,
    pod_spec,
    yaml_repo,
    image,
    prometheus_host,
    scripts,
    host,
    operations,
    repeats,
    result_path,
    jaeger_host,
    entry_point,
    no_nginx=False,
    no_frontend=False,
):
    erms_scheduling = ErmsScheduler(data_path)
    collector = OfflineProfilingDataCollector(
        namespace, jaeger_host, entry_point, prometheus_host, nodes, data_path
    )
    # Latency target computation
    for inter in inters:
        cpu_inter, mem_inter = get_inter(inter)
        print("Deploying interference...")
        deploy_infs(inter, nodes)
        print("Computing latency targets...")
        slas_workloads = config_to_workload(slas_workload_configs)
        latency_targets_result, containers_result = container_computation(
            data_path, slas_workloads, cpu_inter, mem_inter, [service], ["erms"]
        )
        for var_index, (sla, workload_config) in enumerate(slas_workload_configs):
            for repeat in repeats:
                for scheduler in ["k8s"]:
                    containers = containers_result.loc[
                        containers_result["var_index"] == var_index
                    ]
                    latency_targets = latency_targets_result.loc[latency_targets_result["var_index"] == var_index]
                    print(containers)
                    # Containers deployment
                    print("Deploying containers...")
                    if scheduler == "erms":
                        erms_scheduling.main(
                            pod_spec,
                            1,
                            nodes,
                            yaml_repo,
                            namespace,
                            prometheus_host,
                            image,
                            latency_target_df=latency_targets,
                            container_df=containers,
                        )
                    elif scheduler == "k8s":
                        k8s_scheduling(
                            containers, nodes, namespace, pod_spec, yaml_repo, image
                        )
                    else:
                        continue
                    print("Test starts...")
                    # Workload generation
                    start_time = generate_multiple_workloads(
                        [service], 60, workload_config, scripts, host
                    )
                    # Data collection
                    kwargs = {
                        f"{service}_sla": sla[service] * 1000,
                        f"{service}_workload": slas_workloads[var_index][1][service],
                        "scheduler": scheduler,
                        "var_index": var_index,
                        "cpu_inter": cpu_inter,
                        "mem_inter": mem_inter,
                    }
                    collector.validation_collection_async(
                        f"validation_{service}",
                        start_time,
                        operations[service],
                        service,
                        repeat,
                        result_path,
                        no_nginx,
                        no_frontend,
                        **kwargs,
                    )
                    if scheduler == "erms":
                        clear_vifs(data_path)
    print("Waiting for data collection...")
    collector.wait_until_done()
    delete_by_yaml("tmp/scheduledAPP")
