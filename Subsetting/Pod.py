from Node import Node

class Pod:
    def __init__(self, node: Node, ip_address: str = None) -> None:
        # the pod is placed on a node
        self.node = node
        self.optimal_workload = 0
        self.workload = 0
        
        self.rest_connections = 0
        self.connections = 0
        
        self.ip_address = ip_address
        
    def assign_workload(self, workload: float):
        self.workload = workload
    