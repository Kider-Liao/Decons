import re
from typing import List, Tuple

class DownstreamPod:
    """Represents a downstream pod and its associated request probability."""
    def __init__(self, ip: str, prob: float, name: str = None) -> None:
        self.ip: str = ip
        self.chain: str = None
        self.prob: float = prob
        self.name: str = name


class DownstreamService:
    """Encapsulates a collection of downstream pods for a given service."""
    def __init__(self, name: str, pods: List[DownstreamPod]) -> None:
        self.name: str = name
        self.chain: str = None
        self.pods: List[DownstreamPod] = pods


class Rule:
    """Defines routing rules for an upstream pod to its downstream services."""
    def __init__(
        self,
        upstream_ip: str,
        downstream_services: List[DownstreamService],
        upstream_name: str = None,
    ) -> None:
        self.upstream_pod_ip: str = upstream_ip
        self.upstream_pod_name: str = upstream_name
        self.downstream_services: List[DownstreamService] = downstream_services


class RuleSet:
    """Manages a collection of routing rules and updates iptables configurations."""
    def __init__(self) -> None:
        self.rules: dict[str, Rule] = {}

    def add(self, value: Rule) -> None:
        """Adds a rule to the rule set."""
        self.rules[value.upstream_pod_ip] = value

    def get(self, key: str) -> Rule:
        """Retrieves a rule by its upstream pod IP."""
        return self.rules[key]

    def clear(self):
        """Clears all rules."""
        self.rules.clear()
    
    def __getitem__(self, key: str) -> Rule:
        """Accesses a rule using bracket notation."""
        return self.get(key)

    def write_to_iptables(
        self, iptables_file_path: str, new_file_path: str = ""
    ) -> None:
        """Writes the rules to an iptables configuration file.

        :param iptables_file_path: Path to the existing iptables file.
        :param new_file_path: Path to save the updated iptables file. If empty, overwrites the original file.
        """
        with open(iptables_file_path, "r") as file:
            rules: List[str] = file.readlines()

        def find_chain(pod_ip: str) -> str:
            """Finds the iptables chain for a given pod IP."""
            pattern = f"-A (KUBE-SEP-[A-Z0-9]{{16}}) .* -j DNAT --to-destination {pod_ip}:"
            for rule in rules:
                result = re.search(pattern, rule)
                if result:
                    return result.groups()[0]

        
        def insert_before(contents: List[Tuple[str, DownstreamPod]], rules: List[str]): 
            """Inserts new rules before a specific chain in the iptables configuration.

            :param contents: List of rules to be inserted, with associated DownstreamPod objects.
            :param rules: Existing iptables rules.
            :return: Updated list of iptables rules.
            """
            pattern = "-A (KUBE-SVC-[A-Z0-9]{16}) .* -j "
            for rule in rules:
                for _, pod in contents:
                    result = re.search(pattern + pod.chain, rule)
                    if result:
                        service_chain = result.groups()[0]
                        break
            pattern = f"-A {service_chain} "
            for line, rule in enumerate(rules):
                if pattern in rule:
                    break

            return rules[:line] + [pattern + x[0] for x in contents] + rules[line:]

        for rule in self.rules.values():
            for downstream_service in rule.downstream_services:
                contents: List[Tuple[str, DownstreamPod]] = []
                cumulative_prob = 0
                sum_prob = sum(pod.prob for pod in downstream_service.pods)
                
                for downstream_pod in downstream_service.pods:
                    downstream_pod.chain = find_chain(downstream_pod.ip)
                    prob = downstream_pod.prob / (sum_prob - cumulative_prob)
                    cumulative_prob += downstream_pod.prob
                    contents.append(
                        (
                            f"-m comment --comment "
                            f'"{rule.upstream_pod_ip} -> '
                            f"{downstream_service.name} "
                            f"-({downstream_pod.prob * 100}%)-> "
                            f'{downstream_pod.ip}" '
                            f"-s {rule.upstream_pod_ip}/32 "
                            f"-m statistic --mode random "
                            f"--probability {min(prob, 1)} "
                            f"-j {downstream_pod.chain}\n",
                            downstream_pod,
                        )
                    )
                rules = insert_before(contents, rules)

            with open(
                iptables_file_path if not new_file_path else new_file_path,
                "w",
            ) as file:
                file.writelines(rules)
