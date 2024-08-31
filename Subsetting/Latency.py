class Latency:
    def __init__(self, workload, latency) -> None:
        self.step_size = workload[1] - workload[0]
        self.workload = workload
        self.latency = latency
    
    def query_latency(self, workload):
        start = int(workload // self.step_size)
        end = int(workload // self.step_size + 1)
        
        if end >= len(self.workload):
            start = len(self.workload) - 2
            end = len(self.workload) - 1
        slope = (self.latency[end] - self.latency[start]) / (self.workload[end] - self.workload[start])
        return slope * (workload - self.workload[start]) + self.latency[start]