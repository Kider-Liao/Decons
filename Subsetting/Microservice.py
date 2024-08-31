from __future__ import annotations
import itertools
from typing import Dict, List
import numpy as np
import pandas as pd
from Pod import Pod
from Node import Node
from Latency import Latency
from GlobalConfig import *
import random

class Microservice:
    def __init__(self, ms_name: str, local_eta: float = 0.2) -> None:
        self.ms_name = ms_name
        self.num_pods = 0
        
        if ms_name != "User":
            latency_data = pd.read_csv(f"ms_latency/{ms_name}.csv")
            self.latency_dict: Dict[int, Latency] = {}
            utilization_data = latency_data["utilization"].unique()
            for utilization in utilization_data:
                workload = list(latency_data[latency_data["utilization"]==utilization]["workload"])
                latency = list(latency_data[latency_data["utilization"]==utilization]["latency"])
                self.latency_dict[utilization] = Latency(workload, latency)

        self.pod_list: List[Pod] = []
        
        self.local_eta = local_eta # the learning rate of attaining optimal workloads
        self.eta = 0.1

        self.latency = 0
        self.last_latency = 0

        self.total_connections = 0
        self.last_total_connections = 0
        
        self.minimal_connections = 0

        self.fully_connections = 0
        
        self.subsets = []

    def scale(self, pods_distribution:Dict[str, int]):
        scaled_pods = pods_distribution[self.ms_name]
        if scaled_pods >= self.num_pods:
            for _ in range(self.num_pods, scaled_pods):
                new_pod = Pod(random.choice(node_list))
                self.pod_list.append(new_pod)
        else:
            random.shuffle(self.pod_list)
            self.pod_list = self.pod_list[:scaled_pods]
        self.num_pods = scaled_pods
    
    def get_pods(self):
        return self.num_pods
    
    def get_connections(self):
        return self.total_connections

    def set_connections(self, total_connections: int, workloads: int):
        self.last_total_connections = self.total_connections
        self.total_connections = total_connections

    def reset(self):
        self.latency = 0
        self.last_latency = 0
        self.total_connections = 0
        self.last_total_connections = 0
  
    def attain_latency(self):
        return self.latency

    def calculate_latency(self):
        latency = 0
        total_workload = 0
        for pod in self.pod_list:
            utilization = pod.node.cpu_util
            workload = pod.workload
            latency += self.latency_dict[utilization].query_latency(workload) * workload
            total_workload += workload
        latency /= total_workload
        
        self.last_latency = self.latency
        self.latency = latency

    def attain_optimal_distribution(self, workloads: int):
        last_latency_list = [0 for _ in range(self.num_pods)]
        latency_list = [0 for _ in range(self.num_pods)]
        
        last_workload_list = [0 for _ in range(self.num_pods)]
        workload_list = [0 for _ in range(self.num_pods)]
        
        initial_workload = workloads / self.num_pods
        for i, pod in enumerate(self.pod_list):
            utilization = pod.node.cpu_util
            workload_list[i] = initial_workload
            latency_list[i] = self.latency_dict[utilization].query_latency(workload_list[i])
            
        for i, pod in enumerate(self.pod_list):
            pod.optimal_workload = workload_list[i]
        self.pod_list = sorted(self.pod_list, key=lambda item: item.node.cpu_util)
    
    def attain_fully_connections(self, upstream: Microservice):
        self.fully_connections = self.num_pods * upstream.num_pods
    
    def attain_minimal_connections(self, upstream: Microservice):
        self.minimal_connections = max(self.num_pods, upstream.num_pods)
    
    def assign_connections(self, upstream: Microservice, workloads: int):
        
        upstream_pod_list: List[Pod] = [pod for pod in upstream.pod_list]
        downstream_pod_list: List[Pod] = [pod for pod in self.pod_list]

        rest_connections = self.total_connections
        total_workload = 0
        for i, pod in enumerate(upstream.pod_list):
            pod.connections = int(np.ceil(self.total_connections * pod.workload / workloads))
            rest_connections -= pod.connections
            total_workload += pod.workload
        while rest_connections < 0:
            for pod in reversed(upstream.pod_list):
                pod.connections -= 1
                rest_connections += 1
                if rest_connections == 0:
                    break
        for pod in upstream.pod_list:
            pod.rest_connections = pod.connections
        
        rest_connections = self.total_connections
        total_workload = 0 
        for i, pod in enumerate(self.pod_list):
            pod.connections = int(np.ceil(self.total_connections / self.num_pods))
            rest_connections -= pod.connections
            total_workload += pod.workload
        while rest_connections < 0:
            for pod in self.pod_list:
                pod.connections -= 1
                rest_connections += 1
                if rest_connections == 0:
                    break
        for pod in self.pod_list:
            pod.rest_connections = pod.connections
            pod.workload = 0

        for upstream_pod in upstream_pod_list:
            while upstream_pod.rest_connections > 0:
                downstream_pod = downstream_pod_list[0]
                downstream_pod_list.pop(0)
                downstream_pod.workload += upstream_pod.workload / upstream_pod.connections
                upstream_pod.rest_connections -= 1
                downstream_pod.rest_connections -= 1
                if downstream_pod.rest_connections > 0:
                    downstream_pod_list.append(downstream_pod)
    
    def calculate_gradient(self, discount: float = 1):
        if self.total_connections == self.last_total_connections:
            gradient = 0
        else:
            gradient = (self.latency - self.last_latency) / (self.total_connections - self.last_total_connections)
        
        return gradient * discount
        