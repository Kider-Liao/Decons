import os
import re
from decimal import Decimal
from typing import List, Dict
from kubernetes import client, config
from Test.TestConfig import *

def backup_old_table():
    pass

def update_record(path: str, ips: List[str], probs: List[float], flag: bool) -> bool:
    password = TestConfig["password"]
    if not flag:
        os.system(f"echo {password} | sudo -S iptables-save > {path}/iptable.rules")
    
    probs = [Decimal(prob).quantize(Decimal("0.00000000000")) for prob in probs]
    
    # Read existing rules
    with open(f"{path}/iptable.rules", "r") as file:
        rules = file.readlines()

    ip_to_chain = {}
    for rule in rules:
        for ip in ips:
            pattern = f"-j DNAT --to-destination {ip}:"
            if pattern in rule:
                ip_to_chain[ip] = rule.split(" ")[1]
                break

    updated_rules = []
    start_idx = len(rules)
    for ip, prob in zip(ips, probs):
        chain_name = ip_to_chain.get(ip)
        if not chain_name:
            continue
        
        pattern = f"-j {chain_name}"
        for idx, rule in enumerate(rules):
            if pattern not in rule:
                continue
            
            if idx < start_idx:
                start_idx = idx
            
            if "--probability" in rule:
                updated_rules.append(
                    re.sub(r"--probability 0\.\d+", f"--probability {prob}", rule)
                )
            else:
                updated_rules.append(
                    re.sub(
                        r"-j",
                        f"-m statistic --mode random --probability {prob} -j",
                        rule,
                    )
                )
    
    rules[start_idx:start_idx + len(updated_rules)] = updated_rules
    
    # Write updated rules to file
    with open(f"{path}/iptable.rules", "w") as file:
        file.writelines(rules)
    
    return True

def update_single_record(path: str, ip: str, prob: float) -> bool:
    prob = Decimal(prob).quantize(Decimal("0.00000000000"))

    with open(f"{path}/iptable.rules", "r") as file:
        rules = file.readlines()

    pattern = f"-j DNAT --to-destination {ip}"
    rule_chain_name = None
    for rule in rules:
        if pattern in rule:
            rule_chain_name = rule.split(" ")[1]
            break
    
    if not rule_chain_name:
        print("Cannot find target rule, exiting.")
        return False

    # Update probability in the rule
    pattern = f"-j {rule_chain_name}"
    success = False
    for idx, rule in enumerate(rules):
        if pattern in rule and "--probability" in rule:
            rules[idx] = re.sub(
                r"--probability 0\.\d+", f"--probability {prob}", rule
            )
            success = True
            break
    
    if not success:
        print("Cannot find probability control rule, exiting.")
        return False

    # Write updated rules to file and apply changes
    with open(f"{path}/iptable.rules", "w") as file:
        file.writelines(rules)
    
    os.system(f"echo 'lijt' | sudo -S iptables-restore {path}/iptable.rules")
    
    return True

def get_pod_ips(namespace: str, deploy_name: str) -> Dict[str, List[str]]:
    config.load_kube_config()
    v1 = client.CoreV1Api()
    pods = v1.list_namespaced_pod(namespace=namespace)
    pod_ips = {}
    
    for pod in pods.items:
        if pod.metadata.name.startswith(deploy_name):
            host_ip = pod.status.host_ip
            pod_ip = pod.status.pod_ip
            if host_ip not in pod_ips:
                pod_ips[host_ip] = []
            pod_ips[host_ip].append(pod_ip)
    
    return pod_ips

def modify_prob(prob_list: List[float]) -> List[float]:
    modified_probs = []
    total_prob = sum(prob_list)
    
    for i, prob in enumerate(prob_list):
        remaining_prob = total_prob - sum(prob_list[:i])
        modified_probs.append(prob / remaining_prob if remaining_prob > 0 else 0)
    
    return modified_probs
