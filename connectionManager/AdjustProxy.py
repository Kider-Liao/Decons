import subprocess
import time
import os
import re
from kubernetes import client, config
from Test.TestConfig import *

# Change working directory
os.chdir("/home/stluo/Decons")

def disable_adjustment(slave_list):
    config.load_kube_config()
    v1 = client.CoreV1Api()

    # Adjust kube-proxy configmap
    configmap = v1.read_namespaced_config_map('kube-proxy', 'kube-system')
    configmap.data['config.conf'] = re.sub(r"minSyncPeriod: \d+", "minSyncPeriod: 1k", configmap.data['config.conf'])
    configmap.data['config.conf'] = re.sub(r"syncPeriod: \d+", "syncPeriod: 1k", configmap.data['config.conf'])
    v1.replace_namespaced_config_map('kube-proxy', 'kube-system', configmap)
    time.sleep(5)

    # Reset all corresponding pods
    pods = v1.list_namespaced_pod('kube-system')
    for pod in pods.items:
        try:
            node_name = pod.spec.node_name
            pod_name = pod.metadata.name
            if 'kube-proxy' in pod_name and node_name in slave_list:
                v1.delete_namespaced_pod(pod_name, 'kube-system')
        except Exception as e:
            print(f"Error deleting pod {pod_name}: {e}")
            continue
    time.sleep(10)

def enable_adjustment(slave_list):
    config.load_kube_config()
    v1 = client.CoreV1Api()

    # Adjust kube-proxy configmap
    configmap = v1.read_namespaced_config_map('kube-proxy', 'kube-system')
    configmap.data['config.conf'] = re.sub(r"minSyncPeriod: \d+", "minSyncPeriod: 0s", configmap.data['config.conf'])
    configmap.data['config.conf'] = re.sub(r"syncPeriod: \d+", "syncPeriod: 1s", configmap.data['config.conf'])
    v1.replace_namespaced_config_map('kube-proxy', 'kube-system', configmap)
    time.sleep(5)

    # Reset all corresponding pods
    pods = v1.list_namespaced_pod('kube-system')
    for pod in pods.items:
        try:
            node_name = pod.spec.node_name
            pod_name = pod.metadata.name
            if 'kube-proxy' in pod_name and node_name in slave_list:
                v1.delete_namespaced_pod(pod_name, 'kube-system')
        except Exception as e:
            print(f"Error deleting pod {pod_name}: {e}")
            continue
    time.sleep(5)

def adjust_node_time(slave_list):
    print("Adjusting node time...")
    password = TestConfig["password"]
    user = "stluo"
    command = f"echo {password} | sudo -S ntpdate ntp.aliyun.com"
    i = 0
    finished = []
    while len(finished) != len(slave_list):
        try:
            if i not in finished:
                slave = slave_list[i]
                match = 100
                while abs(match) > 0.0005:
                    workload = f"sshpass -p {password} ssh {user}@{slave} {command}"
                    proc = subprocess.Popen(workload, stdout=subprocess.PIPE, shell=True)
                    out, _ = proc.communicate()
                    match_search = re.search(r"(\d+)\.(\d+)\ssec", out.decode("utf-8"))
                    if match_search:
                        match = float(match_search.group(1) + "." + match_search.group(2))
                    print(match)
                finished.append(i)
            else:
                i = (i + 1) % len(slave_list)
        except Exception as e:
            print(f"Error adjusting time on slave {slave}: {e}")
            time.sleep(30)
            i = (i + 1) % len(slave_list)

    print("Adjust finished...")

# Adjust node time for enabled slaves
adjust_node_time(GlobalConfig["enabled_slave"])
