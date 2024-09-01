import sys
sys.path.append("/home/stluo/Decons")
import traceback 
import ipdb
from contentionGenerator.interference import *
from connectionManager.CustomizeScheduler import *
from connectionManager.AdjustProxy import *
from contentionMonitor.prometheusFetcher import *
from deploy.AppDeployment import *
from Test.TestConfig import *
import random
from Test.MinuteRun import *
from latencyAnalyzer.latencyModelFitting import *

import os
os.chdir("/home/stluo/Decons")

def init_environment(containers, round_val, inf_type):
    print("Initializing application...")
    enable_adjustment(enabled_node + ["lijt-master"])
    clear_all_interference(GlobalConfig["enabled_slave"])
    DEPLOYER.delete_app(True)
    
    port = TestConfig["port"] if app in ["social", "media"] else None  
    DEPLOYER.full_init(app, configs.GLOBAL_CONFIG.nodes_for_infra, port, containers)
    DEPLOYER.deploy_app(containers, GlobalConfig["scheduler"], False)
    
    if GlobalConfig["scheduler"]:
        CustomizeScheduler.average_scale(containers, microservice_list)
        
    time.sleep(2 * TestConfig["sleep_time"])
    
    # Apply interference
    interference_list = InterenceConfig[f"{inf_type}_interference"][round_val]
    resource = InterenceConfig["resource"]
    duration = InterenceConfig["duration"]
    interfere_config = InterenceConfig["interference_config"]
    
    for i in range(len(interference_list)):
        interference = interference_list[i]
        resource_type = resource[i]
        config_val = interfere_config[i]
        generate_interference(enabled_node, interference, resource_type, duration, config_val)
    
    time.sleep(60)
    print("Interference applied successfully.")
    
    print("Pre-warming application...")
    prewarm_app(WorkloadConfig["client"], TestConfig["prewarm_duration"])
    print("Application initialization complete.")

def ms_latency_collect():
    print("Generating workload and collecting data...")
    enable_adjustment(adjust_node + ["lijt-master"])

    try:
        repeat_list = []
        while len(repeat_list) < 1:
            try:
                end_to_end_latency_list, microservice_latency = connection_minute_run(TestConfig["repeat"], WorkloadConfig["client"], TestConfig["detail_path"])
                p95_latency = np.percentile(end_to_end_latency_list, 50)
                repeat_list.append(p95_latency)
            except:
                print("Failed to execute latency collection.")
                traceback.print_exc()
                ipdb.set_trace()
                time.sleep(30)
                continue
                
        p95_latency = np.median(repeat_list)
        print(f"Repeat list for this round: {repeat_list}")
        print(f"P95 latency for this round: {p95_latency}")
    except:
        traceback.print_exc()

def connection_adjust(adjuster: ConnectionAdjuster):
    connection_scheme = temp_choice()
    adjuster.assign_connection(connection_scheme)
    adjuster.connection_scheme_apply()
    adjuster.apply('/home/stluo/cones')
    print("Connections adjusted successfully.")

def temp_choice():
    temp_connection = {}
    up_ms_list = TestConfig["upstream_config"]
    
    for ms in microservice_list:
        if ms not in up_ms_list:
            continue
        up_ms = up_ms_list[ms]
        temp_connection[(up_ms, ms)] = {}
        ips = get_pod_ips(configs.GLOBAL_CONFIG.namespace, up_ms)
        
        try:
            for ip in ips.keys():
                for x in ips[ip]:
                    down_ips = get_pod_ips(configs.GLOBAL_CONFIG.namespace, ms)
                    if not down_ips:
                        continue
                    down_node_ip = random.choice(list(down_ips.keys()))
                    down_pod_ip = random.choice(down_ips[down_node_ip])
                    temp_connection[(up_ms, ms)][(x, ip)] = [(down_pod_ip, down_node_ip)]
        except:
            ipdb.set_trace()
            
    return temp_connection

def prometheus():
    prometheus_fetcher = PrometheusFetcher(host=TestConfig["prometheus_host"], namespace="monitoring", duration=300, monitor_interval=15)
    pod_latency = pd.read_csv(f'{data_path}/{save_path}/{TestConfig["detail_path"]}/pod_latency.csv')
    deployments = (
                pod_latency["pod"]
                .apply(lambda x: "-".join(str(x).split("-")[:-2]))
                .unique()
                .tolist()
            )
    start_time = int(time.time()) - 3600 

    cpu_usage_df = prometheus_fetcher.collect_cpu_usage(deployments, start_time)
    mem_usage_df = prometheus_fetcher.collect_mem_usage(deployments, start_time)
    network_usage_df = prometheus_fetcher.collect_network_usage(deployments, start_time)
    return cpu_usage_df, mem_usage_df, network_usage_df

def fit_latency_model():
    file_path = f'{data_path}/{save_path}/{TestConfig["detail_path"]}/ms_latency.csv'
    cut_off_points = 3

    workload, memory_bandwidth, network_utilization, cpu_utilization, latency = load_data(file_path)
    models, cut_points = fit_latency_models(workload, memory_bandwidth, network_utilization, cpu_utilization, latency,
                                            cut_off_points)
    return models, cut_points
    
print("Starting testing...")
try:
    process_round = 0
    init_environment(containers, process_round, TestConfig["inf_type"])
    ms_latency_collect()
    fit_latency_model()
    prometheus()
    adjuster = ConnectionAdjuster(enabled_node, microservice_list)
    connection_adjust(adjuster)
    
except:
    traceback.print_exc()

