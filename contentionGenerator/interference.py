import sys
sys.path.append("/home/stluo/cones/contentionGenerator")
from infGenerator.busyInf import BusyInf
import os
os.chdir("/home/stluo/Decons")

def generate_interference(
    node_list, 
    interference_list, 
    type, 
    duration, 
    config, 
    wait=False,
    namespace="interference"
):
    for i in range(len(node_list)):
        busyinf = BusyInf([node_list[i]], type, duration, config, namespace)
        busyinf.clearAllInterference()
        busyinf.generateInterference(interference_list[i], wait)


def clear_interference(
    node_list, 
    interference,
    namespace="interference"
):
    config = {"cpu_size": 0, "mem_size": 0}
    busyinf = BusyInf(node_list, interference, 0, config, namespace)
    busyinf.clearAllInterference()
    

def clear_all_interference(
    node_list,
    namespace="interference"
):
    interference_list = {"cpu", "capacity", "bandwidth", "network"}
    for interference in interference_list:
        for node in node_list:
            config = {"cpu_size": 0, "mem_size": 0, "throughput": 0}
            busyinf = BusyInf([node], interference, 0, config, namespace)
            busyinf.clearAllInterference()
