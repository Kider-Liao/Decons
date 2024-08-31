from collections import defaultdict
import random
from typing import Dict, List, Tuple, Union

import numpy as np
from Microservice import Microservice
from Pod import Pod

def alternate_sort(sorted_list):
    start, end = 0, len(sorted_list) - 1
    alternated_list = []
    while start <= end:
        alternated_list.append(sorted_list[start])
        start += 1
        if start <= end:
            alternated_list.append(sorted_list[end])
            end -= 1
            
    return alternated_list

class Chain:
    def __init__(self, eta: float = 0.1) -> None:
        self.execution_chain: List[Tuple[Microservice, Microservice]] = []
        self.eta = eta # the learning rate
        self.latency = 0
        self.last_latency = 0
        self.total_connections = 0
        self.last_total_connections = 0
        self.minimal_connections = 0
        self.fully_connections = 0
        self.connections_distribution: Dict[int, int] = {}
        
    def scale(self, pods_distribution:Dict[str, int]):
        for upstream, downstream in self.execution_chain:
            downstream.scale(pods_distribution)
    
    def get_pods(self):
        num_pods = 0
        for upstream, downstream in self.execution_chain:
            num_pods += downstream.get_pods()
        return num_pods
    
    def get_connections(self):
        return self.total_connections
    
    def reset(self):
        for upstream, downstream in self.execution_chain:
            downstream.reset()
        
        self.latency = 0
        self.last_latency = 0
        self.total_connections = 0
        self.last_total_connections = 0
    
    def attain_latency(self):
        return self.latency
    
    def calculate_latency(self):
        chain_latency = 0
        for upstream, downstream in self.execution_chain:
            downstream.calculate_latency()
            chain_latency += downstream.attain_latency()
        self.last_latency = self.latency
        self.latency = chain_latency
    
    def attain_optimal_distribution(self, workloads: int):
        for _, downstream in self.execution_chain:
            downstream.attain_optimal_distribution(workloads)
    
    def attain_fully_connections(self, upstream: Microservice):
        for upstream, downstream in self.execution_chain:
            downstream.attain_fully_connections(upstream)
            self.fully_connections += downstream.fully_connections
            
    def attain_minimal_connections(self, upstream: Microservice):
        for upstream, downstream in self.execution_chain:
            downstream.attain_minimal_connections(upstream)
            self.minimal_connections += downstream.minimal_connections
            
    def calculate_gradient(self, discount: float = 1):
        if self.total_connections == self.last_total_connections:
            gradient = 0
        else:
            gradient = (self.latency - self.last_latency) / (self.total_connections - self.last_total_connections)
        
        return gradient * discount
    
    def assign_connections(self, upstream: Microservice, workloads: int):
        for i, (upstream, downstream) in enumerate(self.execution_chain):
            downstream.assign_connections(upstream, workloads)
    
    def set_connections(self, chain_total_connections: int, iteration_round: int):
        self.last_total_connections = self.total_connections
        self.total_connections = chain_total_connections
        
        if iteration_round == 0:
            for i, (upstream, downstream) in enumerate(self.execution_chain):
                self.connections_distribution[i] = downstream.minimal_connections   
        elif iteration_round == 1:
            total_connections = chain_total_connections
            fully_connections = sum([downstream.fully_connections for upstream, downstream in self.execution_chain])
            
            for i, (upstream, downstream) in enumerate(self.execution_chain):
                if i == len(self.execution_chain)-1:
                    ms_connections = total_connections
                else:
                    ms_connections = int(total_connections * downstream.fully_connections // fully_connections)
                self.connections_distribution[i] = ms_connections
                fully_connections -= downstream.fully_connections
                total_connections -= ms_connections
        else:
            microservice_gradient = {}
            for i, (upstream, downstream) in enumerate(self.execution_chain):
                microservice_gradient[i] = downstream.calculate_gradient()
            
            max_gradient: int = np.max([microservice_gradient[x] for x in microservice_gradient])
            for x in microservice_gradient:
                microservice_gradient[x] -= max_gradient
            mean_gradient: int = np.mean([microservice_gradient[x] for x in microservice_gradient])
            
            if mean_gradient != 0:
                for i, (upstream, downstream) in enumerate(self.execution_chain):
                    modification_rate = min(abs(self.eta * (mean_gradient - microservice_gradient[i]) / mean_gradient), 0.2)
                    if mean_gradient > microservice_gradient[i]:
                        new_connection_quota = self.connections_distribution[i] * (1 + modification_rate)
                    else:
                        new_connection_quota = self.connections_distribution[i] * (1 - modification_rate)
                    self.connections_distribution[i] = max(int(new_connection_quota), downstream.minimal_connections)
                
                updated_connections = sum(self.connections_distribution.values())
                total_connections = chain_total_connections
                self.connections_distribution = dict(sorted(self.connections_distribution.items(), key=lambda item: item[1]))
                for i, ms in enumerate(self.connections_distribution):
                    _, downstream = self.execution_chain[ms]
                    if i == len(self.connections_distribution)-1:
                        self.connections_distribution[ms] = total_connections
                    else:
                        new_connections = int(max(downstream.minimal_connections, self.connections_distribution[ms] * total_connections // updated_connections))
                        updated_connections -= self.connections_distribution[ms]
                        self.connections_distribution[ms] = new_connections
                        total_connections -= new_connections
        
        for i, (upstream, downstream) in enumerate(self.execution_chain):
            downstream.set_connections(self.connections_distribution[i], iteration_round)

class Compose:
    def __init__(self, call_type="parallel", call_probability=None) -> None:
        self.ms_name = "ComposeService"
        self.execution_chain: List[Chain] = []
        self.call_type: str = call_type
        self.call_probability: List[float] = call_probability
        self.latency = 0
        self.last_latency = 0
        self.total_connections = 0
        self.last_total_connections = 0
        self.connection_distribution: Dict[int, int] = {}
        
        self.minimal_connections = 0
        self.fully_connections = 0
        
        self.eta = 0.1
        
    def add_new_chain(self, chain: Chain, probability=None):
        self.execution_chain.append(chain)
        if self.call_type == "conditional":
            self.call_probability.append(probability)

    def scale(self, pods_distribution:Dict[str, int]):
        for chain in self.execution_chain:
            chain.scale(pods_distribution)
    
    def get_pods(self):
        num_pods = 0
        for chain in self.execution_chain:
            num_pods += chain.get_pods()
        return num_pods
    
    def get_connections(self):
        return self.total_connections

    def reset(self):
        for chain in self.execution_chain:
            chain.reset()
            
        self.last_latency = 0
        self.latency = 0
        self.total_connections = 0
        self.last_total_connections = 0

    def attain_latency(self):
        return self.latency
    
    def calculate_latency(self):
        
        for chain in self.execution_chain:
            chain.calculate_latency()
            
        latency = 0
        if self.call_type == "parallel":
            for chain in self.execution_chain:
                chain_latency = chain.attain_latency()
                latency = max(latency, chain_latency)
        else:
            for i, chain in enumerate(self.execution_chain):
                chain_latency = chain.attain_latency()
                latency += chain_latency * self.call_probability[i]
                
        self.last_latency = self.latency
        self.latency = latency
    
    def attain_optimal_distribution(self, workloads: int):
        if self.call_type == "parallel":
            for chain in self.execution_chain:
                chain.attain_optimal_distribution(workloads)
        else:
            for i, chain in enumerate(self.execution_chain):
                chain.attain_optimal_distribution(workloads * self.call_probability[i])

    def attain_fully_connections(self, upstream: Microservice):
        for chain in self.execution_chain:
            chain.attain_fully_connections(upstream)
            self.fully_connections += chain.fully_connections
    
    def attain_minimal_connections(self, upstream: Microservice):
        for chain in self.execution_chain:
            chain.attain_minimal_connections(upstream)
            self.fully_connections += chain.minimal_connections
    
    def assign_connections(self, upstream: Microservice, workloads: int):
        if self.call_type == "parallel":
            for chain in self.execution_chain:
                chain.assign_connections(upstream, workloads)
        else:
            for i, chain in enumerate(self.execution_chain):
                chain.assign_connections(upstream, workloads * self.call_probability[i])
    
    def calculate_gradient(self, discount: float = 1):
        if self.total_connections == self.last_total_connections:
            gradient = 0
        else:
            gradient = (self.latency - self.last_latency) / (self.total_connections - self.last_total_connections)
        
        return gradient * discount
    
    def set_connections(self, compose_total_connections: int, iteration_round: int):
        self.last_total_connections = self.total_connections
        self.total_connections = compose_total_connections
        
        if iteration_round == 0:
            for i, chain in enumerate(self.execution_chain):
                self.connections_distribution[i] = chain.minimal_connections   
        elif iteration_round == 1:
            total_connections = compose_total_connections
            fully_connections = sum([chain.fully_connections for chain in self.execution_chain])
            
            for i, chain in enumerate(self.execution_chain):
                if i == len(self.execution_chain)-1:
                    ms_connections = total_connections
                else:
                    ms_connections = int(total_connections * chain.fully_connections // fully_connections)
                self.connections_distribution[i] = ms_connections
                fully_connections -= chain.fully_connections
                total_connections -= ms_connections
        else:
            microservice_gradient = {}
            max_latency = max([chain.attain_latency() for chain in self.execution_chain])
            for i, chain in enumerate(self.execution_chain):
                microservice_gradient[i] = chain.calculate_gradient()
                if self.call_type != "parallel":
                    microservice_gradient[i] *= self.call_probability[i]
                else:
                    microservice_gradient[i] *= chain.latency / max_latency
            
            max_gradient: int = np.max([microservice_gradient[x] for x in microservice_gradient])
            for x in microservice_gradient:
                microservice_gradient[x] -= max_gradient
            mean_gradient: int = np.mean([microservice_gradient[x] for x in microservice_gradient])
            
            if mean_gradient != 0:
                for i, chain in enumerate(self.execution_chain):
                    modification_rate = min(abs(self.eta * (mean_gradient - microservice_gradient[i]) / mean_gradient), 0.2)
                    if mean_gradient > microservice_gradient[i]:
                        new_connection_quota = self.connections_distribution[i] * (1 + modification_rate)
                    else:
                        new_connection_quota = self.connections_distribution[i] * (1 - modification_rate)
                    self.connections_distribution[i] = max(int(new_connection_quota), chain.minimal_connections)
                
                updated_connections = sum(self.connections_distribution.values())
                total_connections = compose_total_connections
                self.connections_distribution = dict(sorted(self.connections_distribution.items(), key=lambda item: item[1]))
                for i, ms in enumerate(self.connections_distribution):
                    chain: Chain = self.execution_chain[ms]
                    if i == len(self.connections_distribution)-1:
                        self.connections_distribution[ms] = total_connections
                    else:
                        new_connections = int(max(chain.minimal_connections, self.connections_distribution[ms] * total_connections // updated_connections))
                        updated_connections -= self.connections_distribution[ms]
                        self.connections_distribution[ms] = new_connections
                        total_connections -= new_connections
        
        for i, chain in enumerate(self.execution_chain):
            chain.set_connections(self.connections_distribution[i], iteration_round)
        
        