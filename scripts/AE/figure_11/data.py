from onlineScheduling.applyPriority import clear_vifs
from onlineScheduling.placementOptimization import ErmsScheduler

from scripts.AE.utils import config_to_workload, deploy_infs, get_inter
from deployment.deployer import delete_by_yaml

from dataCollector.OfflineProfilingDataCollector import OfflineProfilingDataCollector
from scripts.AE.utils import (
    container_computation,
    k8s_scheduling,
    generate_multiple_workloads,
)


def sharing_main(
    interference,
    slas_workload_configs,
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
    init_containers=None,
    base_workload=None,
    fixed_ms=None,
    no_nginx=False,
    no_frontend=False,
    do_inf_deployment=False,
    methods=["erms", "rhythm", "grandSLAm", "firm"],
):
    erms_scheduling = ErmsScheduler(data_path)
    collector = OfflineProfilingDataCollector(
        namespace, jaeger_host, entry_point, prometheus_host, nodes, data_path
    )
    # Deploy interference
    if do_inf_deployment:
        print("Deploying interference...")
        deploy_infs(interference, nodes)
    cpu_inter, mem_inter = get_inter(interference)
    # Process workload configs
    slas_workloads = config_to_workload(slas_workload_configs)
    # Latency target computation
    print("Computing latency targets...")
    latency_targets_result, containers_result = container_computation(
        data_path,
        slas_workloads,
        cpu_inter,
        mem_inter,
        services,
        methods,
        init_containers=init_containers,
        base_workload=base_workload,
        fixed_ms=fixed_ms,
    )
    for repeat in repeats:
        for var_index, (sla, workload_config) in enumerate(slas_workload_configs):
            for method in methods:
                containers = containers_result.loc[
                    (containers_result["var_index"] == var_index)
                    & (containers_result["method"] == method)
                ]
                latency_targets = latency_targets_result.loc[
                    (latency_targets_result["var_index"] == var_index)
                    & (latency_targets_result["method"] == method)
                ]
                print(latency_targets[["service", "microservice", "latency_target", "container", "workload"]])
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
                elif method in ["rhythm", "grandSLAm", "firm"]:
                    k8s_scheduling(
                        containers, nodes, namespace, pod_spec, yaml_repo, image
                    )
                else:
                    continue
                print("Test starts...")
                # Workload generation
                start_time = generate_multiple_workloads(
                    services, 60, workload_config, scripts, host
                )
                # Data collection
                kwargs = {f"{service}_sla": sla[service] for service in services}
                kwargs.update(
                    {
                        f"{service}_workload": slas_workloads[var_index][1][service]
                        for service in services
                    }
                )
                kwargs.update(
                    {
                        "method": method,
                        "var_index": var_index,
                        "container": containers["container"].sum(),
                        "cpu_inf": cpu_inter,
                        "mem_inf": mem_inter,
                    }
                )
                for service in services:
                    kwargs.update(
                        {
                            "service_container": latency_targets.loc[
                                latency_targets["service"] == service
                            ]
                            .groupby("microservice")["container"]
                            .max()
                            .sum()
                        }
                    )
                    collector.validation_collection_async(
                        f"validation_{service}",
                        start_time,
                        operations[service],
                        service,
                        repeat,
                        f"{result_path}/{'_'.join(services)}",
                        no_nginx,
                        no_frontend,
                        **kwargs,
                    )
                if method == "erms":
                    clear_vifs(data_path)
    print("Waiting for data collection...")
    collector.wait_until_done()
    delete_by_yaml("tmp/scheduledAPP")


def single_main(
    interference,
    slas_workload_configs,
    data_path,
    service,
    nodes,
    namespace,
    pod_spec,
    yaml_repo,
    image,
    prometheus_host,
    script,
    host,
    operation,
    repeats,
    result_path,
    jaeger_host,
    entry_point,
    no_nginx=False,
    no_frontend=False,
    do_inf_deployment=False,
    methods=["erms", "rhythm", "grandSLAm", "firm"],
    init_containers=None,
    base_workload=None,
    fixed_ms=None,
):
    erms_scheduling = ErmsScheduler(data_path)
    collector = OfflineProfilingDataCollector(
        namespace, jaeger_host, entry_point, prometheus_host, nodes, data_path
    )
    # Process workloads
    slas_workloads = config_to_workload(slas_workload_configs)
    # Deployment interference
    if do_inf_deployment:
        print("Deploying interference...")
        deploy_infs(interference, nodes)
    cpu_inter, mem_inter = get_inter(interference)
    # Latency target computation
    print("Computing latency targets...")
    latency_targets_result, containers_result = container_computation(
        data_path,
        slas_workloads,
        cpu_inter,
        mem_inter,
        [service],
        methods,
        init_containers=init_containers,
        base_workload=base_workload,
        fixed_ms=fixed_ms,
    )
    for var_index, (sla, workload_config) in enumerate(slas_workload_configs):
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
                print("Deploying containers...")
                print(containers)
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
                else:
                    k8s_scheduling(
                        containers, nodes, namespace, pod_spec, yaml_repo, image
                    )
                print("Test starts...")
                start_time = generate_multiple_workloads(
                    [service], 60, workload_config, {service: script}, host
                )
                # Data collection
                kwargs = {f"{service}_sla": sla[service]}
                kwargs.update(
                    {f"{service}_workload": slas_workloads[var_index][1][service]}
                )
                kwargs.update({"method": method, "var_index": var_index})
                collector.validation_collection_async(
                    f"validation_{service}",
                    start_time,
                    operation,
                    service,
                    repeat,
                    f"{result_path}/{service}",
                    no_nginx,
                    no_frontend,
                    **kwargs,
                )
                if method == "erms":
                    clear_vifs(data_path)
            collector.wait_until_done()
        delete_by_yaml("tmp/scheduledAPP")
