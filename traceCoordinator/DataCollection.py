# import time
from .OfflineProfilingDataCollector import OfflineProfilingDataCollector
from contentionGenerator.Workload import *
from Test.TestConfig import *
from kubernetes import config, client

import os
os.chdir("/home/stluo/Decons")
import configs
import pandas as pd
import numpy as np

dataCollector = OfflineProfilingDataCollector(
    configs.GLOBAL_CONFIG.namespace,
    configs.TESTING_CONFIG.collector_config.jaeger_host,
    configs.TESTING_CONFIG.collector_config.entry_point,
    configs.GLOBAL_CONFIG.prometheus_host,
    configs.GLOBAL_CONFIG.nodes_for_test,
    DataConfig["data_path"],
    max_traces=configs.TESTING_CONFIG.collector_config.max_traces,
    mointorInterval=configs.TESTING_CONFIG.collector_config.monitor_interval,
    duration=WorkloadConfig["duration"],
    max_processes=20,
)

def node_percentile(data_path, save_path, detail_path, microservice, node_list, repeat, mode="latency", data_file="pod_latency"):
    if microservice == "nginx-thrift":
        microservice = "nginx-web-server"
    elif microservice == "nginx-web-server":
        microservice = "nginx"

    config.load_kube_config()
    v1 = client.CoreV1Api()

    mean_latency = {}
    pod_latency = {node: [] for node in node_list}

    pod_data = pd.read_csv(f'{data_path}/{save_path}/{detail_path}/{data_file}.csv')
    pod_data = pod_data[(pod_data["repeat"] == repeat) & (pod_data["microservice"] == microservice)][["microservice", "pod", mode]]

    for _, row in pod_data.iterrows():
        pod_name = row["pod"]
        latency = row[mode]
        node_name = v1.read_namespaced_pod(pod_name, configs.GLOBAL_CONFIG.namespace).spec.node_name
        pod_latency[node_name].append(latency)

    latency_sum = 0
    count = 0
    for node in node_list:
        if pod_latency[node]:
            mean_latency[node] = np.mean(pod_latency[node])
            latency_sum += mean_latency[node]
            count += 1
        else:
            mean_latency[node] = 0

    if count == 0:
        print(microservice)
        for node in node_list:
            mean_latency[node] = 1
    else:
        for node in node_list:
            if mean_latency[node] == 0:
                mean_latency[node] = latency_sum / count
    
    return mean_latency

def trace_latency_collection(data_path, save_path, detail_path, percentile, repeat=None):
    trace_data = pd.read_csv(f'{data_path}/{save_path}/{detail_path}/trace_latency.csv')
    if repeat is not None:
        trace_data = trace_data[trace_data["repeat"] == repeat]
    return float(format(trace_data['traceLatency'].quantile(percentile) / 1000, '.2f'))

def microservice_latency_collection(data_path, save_path, detail_path, percentile, microservice, repeat=None):
    trace_data = pd.read_csv(f'{data_path}/{save_path}/{detail_path}/ms_trace.csv')
    trace_data = trace_data[trace_data["microservice"] == microservice]
    if repeat is not None:
        trace_data = trace_data[trace_data["repeat"] == repeat]
    return float(format(trace_data['duration'].quantile(percentile) / 1000, '.2f'))

def throughput_collection(data_path, save_path):
    trace_data = pd.read_csv(f'{data_path}/{save_path}/trace_latency.csv')
    return float(format(trace_data['throughput'].quantile(0.95), '.2f'))


testName = "Compose"
