import yaml
from deploy.deployer import Deployer, deploy_by_yaml
import os
import utils.deploymentEditor as editor
from utils.others import wait_deployment


AFFINITY_TEMPLATE = (
    "nodeAffinity:\n"
    "  requiredDuringSchedulingIgnoredDuringExecution:\n"
    "    nodeSelectorTerms:\n"
    "    - matchExpressions:\n"
    "      - key: kubernetes.io/hostname\n"
    "        operator: In\n"
    "        values: %%%\n"
)


class BusyInf:
    def __init__(
        self,
        nodes,
        interferenceType,
        duration,
        configs,
        namespace="interference",
    ):
        """Initialize a interference generator with certain type

        Args:
            nodes (list): Specify which nodes are going to be used to deploy pods
            interferenceType (str): "cpu" for CPU interference, "capaciry" for memory capaciry interference, "bandwidth" for memory bandwidth interference duration (int): Duration of interference pods
            namespace (str): Namespace used to deploy interference
        """
        self.resource_limits = {
            "requests": {"memory": configs["mem_size"], "cpu": configs["cpu_size"]},
            "limits": {"memory": configs["mem_size"], "cpu": configs["cpu_size"]},
        }
        self.interferenceType = interferenceType
        self.namespace = namespace
        self.nodes = nodes
        self.command = {
            "cpu": "/ibench/src/cpu",
            "capacity": "/ibench/src/memCap",
            "bandwidth": "/ibench/src/memBw",
            "network": "",
        }[self.interferenceType]

        if self.interferenceType == "cpu":
            self.args = [f"{duration}s"]
        elif self.interferenceType == "capacity":
            self.args = [f"{duration}s", "wired", "100000s"]
        elif self.interferenceType == "bandwidth":
            self.args = [f"{duration}s"]
        elif self.interferenceType == "network":
            self.args = [configs["throughput"], duration]

    def generateInterference(self, replicas, wait=False):
        """Create a set of pods with the same CPU size and memory size on target nodes

        Args:
            replicas (int): Number of replicas of this CPU interference deployment
        """
        if self.interferenceType == "network":
            self.generate_network_inf(replicas, False)
        else:
            for node in self.nodes:
                self.generate_single_interference(node, replicas, False)
        if wait:
            wait_deployment(self.namespace, 300)

    def generate_network_inf(self, replicas, wait=False):
        cm_name = "-".join(self.nodes) + "-launch-script"
        ds_name = "network-inf-" + "-".join(self.nodes)

        yamls = editor.read_yaml("yamlRepository/templates/net-inf.yaml")
        node_affinity = yaml.load(
            AFFINITY_TEMPLATE.replace("%%%", f"[{','.join(self.nodes)}]"),
            Loader=yaml.CLoader,
        )
        ds_pairs = [
            ("metadata.namespace", self.namespace),
            ("metadata.name", ds_name),
            ("spec.template.spec.affinity", node_affinity),
            ("spec.template.spec.containers[0].resources", self.resource_limits),
            ("spec.template.spec.containers[1].resources", self.resource_limits),
            ("spec.template.spec.containers[1].env[1].value", self.args[0]),
            ("spec.template.spec.containers[1].env[2].value", str(self.args[1])),
            ("spec.template.spec.containers[1].env[3].value", str(replicas)),
            ("spec.template.spec.volumes[0].configMap.name", cm_name),
        ]

        for pair in ds_pairs:
            yamls = editor.insert_to_python_objs(pair[0], pair[1], yamls, "DaemonSet")

        IP_MAP = {
            "slave1": "192.168.0.1",
            "slave2": "192.168.0.2",
            "slave3": "192.168.0.3",
            "slave4": "192.168.0.4",
            "slave5": "192.168.0.5",
            "slave6": "192.168.0.6",
            "slave7": "192.168.0.7",
            "slave8": "192.168.0.8",
            "slave9": "192.168.0.9",
            "slave10": "192.168.0.10",
            "slave11": "192.168.0.11",
            "slave12": "192.168.0.12",
            "slave13": "192.168.0.13",
            "slave14": "192.168.0.14",
            "slave15": "192.168.0.15",
            "slave16": "192.168.0.16",
            "slave17": "192.168.0.17",
            "slave18": "192.168.0.18",
            "slave19": "192.168.0.19",
            "slave20": "192.168.0.20",
            "slave21": "192.168.0.21",
            "slave22": "192.168.0.22",
            "slave23": "192.168.0.23",
            "slave24": "192.168.0.24",
        }

        cm_pairs = [
            ("metadata.namespace", self.namespace),
            ("metadata.name", cm_name),
            (
                "data.data",
                "\n".join([IP_MAP[x] for x in self.nodes] + [IP_MAP[self.nodes[0]]]),
            ),
        ]

        for pair in cm_pairs:
            yamls = editor.insert_to_python_objs(pair[0], pair[1], yamls, "ConfigMap")

        os.system("rm -rf tmp/interference")
        os.system("mkdir -p tmp/interference")
        editor.save_all_yaml("tmp/interference", yamls)
        deploy_by_yaml("tmp/interference", wait, self.namespace)

    def generate_single_interference(self, node, replicas, wait=False):
        """Create a set of pods with the same CPU size and memory size on a single node

        Args:
            node (str): Specify which node is going to use to deploy pods
            replicas (int): Number of replicas of this CPU interference deployment
        """
        name = f"{self.interferenceType}-busy-inf-{node}"
        with open("yamlRepository/templates/deploymentAffinity.yaml", "r") as file:
            node_affinity = yaml.load(
                file.read().replace("%%%", f"[{node}]"), yaml.CLoader
            )
        yaml_file = editor.read_yaml("yamlRepository/templates/interference.yaml")
        pairs = [
            ("metadata.name", name),
            ("metadata.namespace", self.namespace),
            ("spec.replicas", replicas),
            ("spec.template.spec.containers[0].resources", self.resource_limits),
            ("spec.template.spec.containers[0].command[0]", self.command),
            ("spec.template.spec.containers[0].args", self.args),
            ("spec.template.spec.affinity", node_affinity),
        ]
        for pair in pairs:
            yaml_file = editor.insert_to_python_objs(pair[0], pair[1], yaml_file)
        os.system("rm -rf tmp/interference")
        os.system("mkdir -p tmp/interference")
        editor.save_all_yaml("tmp/interference", yaml_file)
        deploy_by_yaml("tmp/interference", wait, self.namespace)

    def clearAllInterference(self):
        """Delete all interference pod generated by this generator"""
        if self.interferenceType == "network":
            cm_name = "-".join(self.nodes) + "-launch-script"
            ds_name = "network-inf-" + "-".join(self.nodes)
            os.system(f"kubectl delete cm -n {self.namespace} {cm_name}")
            os.system(f"kubectl delete ds -n {self.namespace} {ds_name}")
        for node in self.nodes:
            name = f"{self.interferenceType}-busy-inf-{node}"
            Deployer.deleteDeployByNameInNamespace(name, self.namespace)
