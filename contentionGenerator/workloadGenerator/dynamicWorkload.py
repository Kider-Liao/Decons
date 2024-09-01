from math import ceil
import multiprocessing
from typing import List
import pandas as pd
from workloadGenerator.staticWorkload import StaticWorkloadGenerator

class DynamicWorkloadGenerator:
    """
    A class to generate dynamic workloads for testing purposes. 
    This generator uses a predefined CSV file to create a workload sequence 
    and spawns multiple processes to simulate the workload.

    Attributes:
        wrk_path (str): The path to the `wrk` binary.
        script_path (str): The path to the Lua script for `wrk`.
        url (str): The target URL for the workload generation.
        processes (list): A list to hold the processes used for workload generation.
    """
    
    def __init__(self, wrk_path: str, script_path: str, url: str):
        """
        Initializes the DynamicWorkloadGenerator with the necessary paths and URL.

        Args:
            wrk_path (str): Path to the `wrk` binary.
            script_path (str): Path to the Lua script for `wrk`.
            url (str): Target URL for workload generation.
        """
        self.wrk_path = wrk_path
        self.script_path = script_path
        self.url = url
        self.processes = []

    @staticmethod
    def workload_sequence(scale: float) -> List[int]:
        """
        Generates a workload sequence by scaling the transactions per second (TPS) 
        data from a CSV file.

        Args:
            scale (float): A scaling factor to apply to the TPS data.

        Returns:
            List[int]: A list of TPS values after applying the scaling factor and ceiling function.
        """
        cpm = pd.read_csv("workloadGenerator/dynamicWorkload.csv")
        return (cpm["tps_truth"] * scale).apply(ceil).tolist()

    def generate_workload(self, slas_workload_configs: List[dict], service: str, test_duration: int = 60) -> List[multiprocessing.Process]:
        """
        Generates and returns a list of processes that simulate the workload based on 
        the provided SLAs and workload configurations.

        Args:
            slas_workload_configs (List[dict]): A list of workload configurations for each SLA.
            service (str): The service name for which to generate the workload.
            test_duration (int, optional): The duration for which each test should run. Defaults to 60 seconds.

        Returns:
            List[multiprocessing.Process]: A list of multiprocessing.Process objects ready to be started.
        """
        processes: List[multiprocessing.Process] = []
        
        for index, (_, workload_config) in enumerate(slas_workload_configs):
            static_generator = StaticWorkloadGenerator(
                workload_config[service]["thread"],
                workload_config[service]["conn"],
                test_duration,
                workload_config[service]["throughput"],
                self.wrk_path,
                self.script_path,
                self.url,
            )
            process = multiprocessing.Process(
                target=static_generator.generateWorkload,
                args=(f"dynamic_{index}", workload_config[service]["clients"]),
            )
            processes.append(process)
        
        return processes
