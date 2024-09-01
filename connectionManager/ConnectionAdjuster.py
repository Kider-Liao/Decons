from decimal import Decimal
import os
import ipdb
import configs
from .RuleSet import *
from Test.TestConfig import *
from connectionManager.update_single_record import modify_prob, update_record, get_pod_ips

# Change working directory
os.chdir("/home/stluo/Decons")

app = os.environ["ERMS_APP"]

class ConnectionAdjuster:
    def __init__(self, slave_list, microservice_list) -> None:
        self.slave_list = slave_list
        self.microservice_list = microservice_list
        self.pod_connection = {}  # Connection scheme of each pod
        self.unassigned = []  # List of unassigned microservices

        for ms in microservice_list:
            self.pod_connection[ms] = {}

        self.rule_set = RuleSet()  # Initialize rule set
        self.up_stream = TestConfig["upstream_config"]

    def prob_assign(self, microservice, flag, path) -> None:
        ips = get_pod_ips(configs.GLOBAL_CONFIG.namespace, microservice)
        prob_combine = []

        try:
            for ip in ips.keys():
                prob_combine += [{"ip": x, "prob": 1} for x in ips[ip]]
        except Exception:
            ipdb.set_trace()

        modified_probs = modify_prob([Decimal(x["prob"]) for x in prob_combine])
        ips = [x["ip"] for x in prob_combine]
        update_record(path, ips, modified_probs, flag)

    def assign_connection(self, connection_scheme):
        self.pod_connection = connection_scheme

    def connection_scheme_apply(self):
        ms_dm = {ms: {} for ms in self.microservice_list}

        for ms in self.microservice_list:
            if ms not in self.up_stream:
                self.unassigned.append(ms)
                continue

            up_ms = self.up_stream[ms]
            for (up_pod_ip, up_node_ip) in self.pod_connection[(up_ms, ms)]:
                prob_list = []
                pod_list = self.pod_connection[(up_ms, ms)][(up_pod_ip, up_node_ip)]

                for (down_pod_ip, down_node_ip) in pod_list:
                    prob_list.append(DownstreamPod(down_pod_ip, 1, ms))

                if up_pod_ip not in ms_dm[up_ms]:
                    ms_dm[up_ms][up_pod_ip] = [DownstreamService(ms, prob_list)]
                else:
                    ms_dm[up_ms][up_pod_ip].append(DownstreamService(ms, prob_list))

        for ms in self.microservice_list:
            if ms_dm[ms]:
                for ip in ms_dm[ms]:
                    self.rule_set.add(Rule(ip, ms_dm[ms][ip], ms))

    def apply(self, path):
        password = TestConfig["password"]
        os.system(f"echo {password} | sudo -S iptables-save > {path}/iptable.rules")

        for ms in self.unassigned:
            self.prob_assign(ms, True, path)

        self.rule_set.write_to_iptables(f"{path}/iptable.rules", f"{path}/iptable.rules")

        user = "stluo"
        command = f"echo {password} | sudo -S iptables-restore {path}/iptable.rules -w"
        os.system(f"echo {password} | sudo -S iptables-restore ./iptable.rules -w")

        for node in self.slave_list:
            result = os.system(f"sshpass -p {password} scp {path}/iptable.rules {node}:/home/stluo/")
            if result != 0:
                print(f"Failed to copy iptable.rules to {node}")
                continue

            result = os.system(f"sshpass -p {password} ssh {user}@{node} {command}")
            if result != 0:
                print(f"Failed to execute command on {node}")
            else:
                print(f"Successfully executed command on {node}")
