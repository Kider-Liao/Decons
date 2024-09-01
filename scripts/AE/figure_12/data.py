from copy import deepcopy
from dataCollector.OfflineProfilingDataCollector import OfflineProfilingDataCollector
from onlineScheduling.placementOptimization import ErmsScheduler
from scripts.AE.utils import (
    config_to_workload,
    container_computation,
    deploy_infs,
    get_inter,
    k8s_scheduling,
)

from workloadGenerator.dynamicWorkload import DynamicWorkloadGenerator
from deployment.deployer import delete_by_yaml
from time import time


def main(
    interference,
    sla,
    workload_config,
    scale,
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
    methods=["erms", "rhythm", "grandSLAm", "firm"],
    no_nginx=False,
    no_frontend=False,
    do_inf_deployment=False,
    init_containers=None,
    fixed_ms=None,
    base_workload=None,
):
    collector = OfflineProfilingDataCollector(
        namespace, jaeger_host, entry_point, prometheus_host, nodes, data_path
    )
    generator = DynamicWorkloadGenerator("wrk2/wrk", script, host)
    scheduler = ErmsScheduler(data_path)
    # Deploy interference
    if do_inf_deployment:
        print("Deploying interference...")
        deploy_infs(interference, nodes)
    cpu_inter, mem_inter = get_inter(interference)
    # Generate dynamic workload estimation
    clients_list = generator.workload_sequence(scale)
    print(clients_list)
    slas_workload_configs = []
    for clients in clients_list:
        updated_workload_config = deepcopy(workload_config)
        updated_workload_config["clients"] = clients
        slas_workload_configs.append(
            ({service: sla}, {service: updated_workload_config})
        )
    slas_workloads = config_to_workload(slas_workload_configs)
    # Latency target computation
    print("Computing latency targets...")
    latency_targets, containers = container_computation(
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
    latency_targets = latency_targets.rename(columns={"var_index": "timestamp"})
    containers = containers.rename(columns={"var_index": "timestamp"})
    # Modify container numbers based on its previous/next timestamp
    # new_containers = []
    # for (ms, method), ms_containers in containers.groupby(["microservice", "method"]):
    #     ms_containers = pd.DataFrame(ms_containers)["container"].to_list()
    #     for index, curr in enumerate(ms_containers):
    #         next = 0 if index + 1 >= len(ms_containers) else ms_containers[index + 1]
    #         prev = 0 if index - 1 < 0 else ms_containers[index - 1]
    #         new_containers.append(
    #             {
    #                 "microservice": ms,
    #                 "method": method,
    #                 "container": max(next, prev, curr),
    #                 "timestamp": index,
    #             }
    #         )
    # containers = pd.DataFrame(new_containers)

    for repeat in repeats:
        for method in methods:
            method_containers = containers.loc[containers["method"] == method]
            # Init deployments
            # print("Initializing...")
            # scheduler.main(
            #     pod_spec,
            #     1,
            #     nodes,
            #     yaml_repo,
            #     namespace,
            #     prometheus_host,
            #     image,
            #     latency_target_df=latency_targets.loc[latency_targets["timestamp"] == 0],
            #     container_df=containers.loc[containers["timestamp"] == 0],
            # )
            gen_procs = generator.generate_workload(slas_workload_configs, service)
            for index, (_, grp) in enumerate(method_containers.groupby("timestamp")):
                print(grp)
                if method == "erms":
                    scheduler.main(
                        pod_spec,
                        1,
                        nodes,
                        yaml_repo,
                        namespace,
                        prometheus_host,
                        image,
                        latency_target_df=latency_targets.loc[
                            latency_targets["timestamp"] == index
                        ],
                        container_df=grp,
                    )
                else:
                    k8s_scheduling(
                        grp, nodes, namespace, pod_spec, yaml_repo, image, "tmp/dynamic"
                    )
                start_time = time()
                print(
                    f"Timestamp {index}, workload {slas_workloads[index][1][service]}, testing..."
                )
                gen_procs[index].start()
                gen_procs[index].join()
                collector.validation_collection_async(
                    f"dynamic_{index}",
                    start_time,
                    operation,
                    service,
                    repeat,
                    f"{result_path}/{service}",
                    no_nginx,
                    no_frontend,
                    method=method,
                    sla=sla,
                    workload=slas_workloads[index][1][service],
                    timestamp=index,
                    container=grp["container"].sum(),
                )
            collector.wait_until_done()
    delete_by_yaml("tmp/dynamic")
