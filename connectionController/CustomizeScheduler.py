from kubernetes import config, client, watch
from Test.TestConfig import *
from random import choice
import numpy as np
import os

# Change working directory
os.chdir("/home/stluo/Decons")
import configs

class CustomizeScheduler:
    def __init__(self, namespace) -> None:
        self.namespace = namespace

    def average_scale(self, containers, microservice_list):
        container_num = np.sum([val for val in containers.values()])
        config.load_kube_config()
        api = client.CoreV1Api()
        watcher = watch.Watch()
        node_choice = {ms: 0 for ms in containers.keys()}
        ready_pods = []
        node_list = GlobalConfig["enabled_slave"]
        namespace = configs.GLOBAL_CONFIG.namespace
        
        for event in watcher.stream(api.list_namespaced_pod, namespace):
            if (event["object"].status.phase == "Pending"
                and event["object"].spec.scheduler_name == "erms-scheduler"
                and event["object"].metadata.name not in ready_pods):
                
                pod_name = str(event["object"].metadata.name)
                microservice = "-".join(pod_name.split("-")[:-2])
                
                try:
                    target = client.V1ObjectReference(
                        kind="Node",
                        api_version="v1",
                        name=node_list[node_choice[microservice]]
                    )

                    node_choice[microservice] = (node_choice[microservice] + 1) % len(node_list)

                    body = client.V1Binding(
                        target=target,
                        metadata=client.V1ObjectMeta(name=pod_name)
                    )

                    api.create_namespaced_binding(namespace, body, _preload_content=False)

                    ready_pods.append(pod_name)
                    print(len(ready_pods), container_num)

                    if len(ready_pods) == container_num:
                        watcher.stop()
                        return True
                        
                except Exception as e:
                    import ipdb
                    ipdb.set_trace()
                    watcher.stop()
                    print(f"Failed to allocate: {pod_name}")
                    continue
