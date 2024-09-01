from time import time
import requests

def fetch_prometheus(
    host: str,
    prometheus_query: str,
    query_type: str,
    step: str = None,
    start_time: int = None,
    end_time: int = None,
    time: int = None,
) -> requests.Response:
    request_data = {"query": prometheus_query}
    if query_type == "range":
        request_data.update({"step": step, "start": start_time, "end": end_time})
    elif query_type == "point":
        request_data["time"] = time

    url_suffix = {"range": "query_range", "point": "query"}[query_type]
    res = requests.get(f"{host}/api/v1/{url_suffix}", params=request_data)
    return res

def fetch_cpu_usage(
    host: str,
    namespace: str,
    deployments: list,
    start_time: int,
    end_time: int,
    step: str
) -> requests.Response:
    constraint = f'namespace="{namespace}", container!="POD", container!="", pod=~"{".*|".join(deployments)}.*"'
    prometheus_query = (
        f"sum(node_namespace_pod_container:container_cpu_usage_seconds_total:sum_irate{{{constraint}}}) by (container, pod)/"
        + f'sum(kube_pod_container_resource_limits{{{constraint}, resource="cpu"}}) by (container, pod) * 100'
    )
    return fetch_prometheus(
        host, prometheus_query, "range", step=step, start_time=start_time, end_time=end_time
    )

def fetch_mem_usage(
    host: str,
    namespace: str,
    deployments: list,
    start_time: int,
    end_time: int,
    step: str
) -> requests.Response:
    constraint = f'container!= "", container!="POD", namespace="{namespace}", pod=~"{".*|".join(deployments)}.*"'
    query = (
        f"sum(node_namespace_pod_container:container_memory_working_set_bytes{{{constraint}}}) by (pod) / "
        f'sum(kube_pod_container_resource_limits{{{constraint}, resource="memory"}}) by (pod) * 100'
    )
    return fetch_prometheus(
        host, query, "range", step=step, start_time=start_time, end_time=end_time
    )

def fetch_node_mem_usage(host: str, nodes: list) -> requests.Response:
    query = f'instance:node_memory_utilisation:ratio{{instance=~"{".*|".join(nodes)}.*"}}'
    return fetch_prometheus(host, query, "point", time=time())

def fetch_node_cpu_usage(host: str, nodes: list) -> requests.Response:
    query = f'instance:node_cpu_utilisation:rate1m{{instance=~"{".*|".join(nodes)}.*"}}'
    return fetch_prometheus(host, query, "point", time=time())

def fetch_node_cpu_aloc(host: str, nodes: list) -> requests.Response:
    query = f'sum(kube_pod_container_resource_limits_cpu_cores{{node=~"{"|".join(nodes)}"}}) by (node)'
    return fetch_prometheus(host, query, "point", time=time())

def fetch_node_mem_aloc(host: str, nodes: list) -> requests.Response:
    query = f'sum(kube_pod_container_resource_limits_memory_bytes{{node=~"{"|".join(nodes)}"}}) by (node) / 1024 / 1024'
    return fetch_prometheus(host, query, "point", time=time())
