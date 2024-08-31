# define the cpu and memory utilization of a node
class Node():
    def __init__(self, cpu_util: int, memory_util: int) -> None:
        self.cpu_util = cpu_util
        self.memory_util = memory_util
        
    def set_utilization(self, cpu_util: int, memory_util: int):
        self.cpu_util = cpu_util
        self.memory_util = memory_util