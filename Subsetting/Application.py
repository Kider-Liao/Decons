from typing import Dict, List, Tuple, Union
import numpy as np
from Microservice import Microservice
from Compose import Compose, Chain

class Application:
    def __init__(self, app_name="default") -> None:
        self.execution_chain: List[Tuple[Union[Compose, Microservice], Union[Compose, Microservice]]] = []
        self.app_name = app_name
        self.eta = 0.1
    
    def add_new_execution(self, upsteam: Union[Compose, Microservice], downstream: Union[Compose, Microservice]):
        self.execution_chain.append((upsteam, downstream))
    
    def get_pods(self):
        num_pods = []
        for _, downstream in self.execution_chain:
            num_pods.append(downstream.get_pods())
        return num_pods
    
    def application_scaling(self, pods_distribution: Dict[str, int]):
        for _, downstream in self.execution_chain:
            downstream.scale(pods_distribution)

    def app_connection_assignment_process(self, app_total_connections: int, workloads: int):
        connections_distribution: Dict[int, int] = {}
        
        for i, (upstream, downstream) in enumerate(self.execution_chain):
            downstream.attain_optimal_distribution(workloads)
            
        for i, (upstream, downstream) in enumerate(self.execution_chain):
            downstream.attain_fully_connections(upstream)
            downstream.attain_minimal_connections(upstream)

        num_iterations = 10
        best_latency = 100000001
        best_distribution = {}
        for iteration_round in range(num_iterations):
            if iteration_round == 0:
                for i, (upstream, downstream) in enumerate(self.execution_chain):
                    connections_distribution[i] = downstream.minimal_connections
            if iteration_round == 0:
                total_connections = app_total_connections
                fully_connections = sum([downstream.fully_connections for upstream, downstream in self.execution_chain])
                
                for i, (upstream, downstream) in enumerate(self.execution_chain):
                    if i == len(self.execution_chain)-1:
                        ms_connections = total_connections
                    else:
                        ms_connections = int(total_connections * downstream.fully_connections // fully_connections)
                    connections_distribution[i] = ms_connections
                    fully_connections -= downstream.fully_connections
                    total_connections -= ms_connections
            microservice_gradient = {}
            for i, (upstream, downstream) in enumerate(self.execution_chain):
                downstream.set_connections(connections_distribution[i], workloads)
                downstream.assign_connections(upstream, workloads)
                downstream.calculate_latency()
                microservice_gradient[i] = downstream.calculate_gradient()
            E2E_latency = self.attain_E2E_latency()
            if E2E_latency < best_latency:
                best_latency = E2E_latency
                best_distribution = connections_distribution.copy()
            max_gradient: int = np.max([microservice_gradient[x] for x in microservice_gradient])
            for x in microservice_gradient:
                microservice_gradient[x] -= max_gradient
            mean_gradient: int = np.mean([microservice_gradient[x] for x in microservice_gradient])
            
            if mean_gradient == 0:
                break
            for i, (upstream, downstream) in enumerate(self.execution_chain):
                modification_rate = min(abs(self.eta * (mean_gradient - microservice_gradient[i]) / mean_gradient), 0.2)
                if mean_gradient > microservice_gradient[i]:
                    new_connection_quota = connections_distribution[i] * (1 + modification_rate)
                else:
                    new_connection_quota = connections_distribution[i] * (1 - modification_rate)
                connections_distribution[i] = max(int(new_connection_quota), downstream.minimal_connections)
            
            updated_connections = sum(connections_distribution.values())
            total_connections = app_total_connections
            connections_distribution = dict(sorted(connections_distribution.items(), key=lambda item: item[1]))
            for i, ms in enumerate(connections_distribution):
                _, downstream = self.execution_chain[ms]
                if i == len(connections_distribution)-1:
                    connections_distribution[ms] = total_connections
                else:
                    new_connections = int(max(downstream.minimal_connections, connections_distribution[ms] * total_connections // updated_connections))
                    updated_connections -= connections_distribution[ms]
                    connections_distribution[ms] = new_connections
                    total_connections -= new_connections
        return best_latency
                
    def attain_E2E_latency(self) -> float:
        latency = 0
        for _, downstream in self.execution_chain:
            latency += downstream.attain_latency()
        return latency