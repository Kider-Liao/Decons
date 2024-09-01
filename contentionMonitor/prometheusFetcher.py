import time
import requests
import pandas as pd

class PrometheusFetcher:
    def __init__(self, host, namespace, duration, monitor_interval):
        self.prometheus_host = host
        self.namespace = namespace
        self.duration = duration
        self.monitor_interval = monitor_interval

    def fetch_prometheus(self, prometheus_query, query_type, step=None, start_time=None, end_time=None, time=None):
        request_data = {"query": prometheus_query}
        if query_type == "range":
            request_data.update({"step": step, "start": start_time, "end": end_time})
        elif query_type == "point":
            request_data["time"] = time

        url_suffix = {"range": "query_range", "point": "query"}[query_type]
        res = requests.get(f"{self.prometheus_host}/api/v1/{url_suffix}", params=request_data)
        return res

    def _generate_query(self, metric, constraints, by, resource=None):
        query = f"sum({metric}{{{constraints}}}) by ({by})"
        if resource:
            query += f" / sum(kube_pod_container_resource_limits{{{constraints}, resource='{resource}'}}) by ({by}) * 100"
        return query

    def fetch_cpu_usage(self, deployments, start_time, end_time, step):
        constraints = f'namespace="{self.namespace}", container!="POD", container!="", pod=~"{".*|".join(deployments)}.*"'
        prometheus_query = self._generate_query(
            'node_namespace_pod_container:container_cpu_usage_seconds_total:sum_irate',
            constraints,
            'container, pod',
            resource='cpu'
        )
        return self.fetch_prometheus(prometheus_query, "range", step, start_time, end_time)

    def fetch_mem_usage(self, deployments, start_time, end_time, step):
        constraints = f'container!= "", container!="POD", namespace="{self.namespace}", pod=~"{".*|".join(deployments)}.*"'
        prometheus_query = self._generate_query(
            'node_namespace_pod_container:container_memory_working_set_bytes',
            constraints,
            'pod',
            resource='memory'
        )
        return self.fetch_prometheus(prometheus_query, "range", step, start_time, end_time)
    
    def fetch_network_usage(self, deployments, start_time, end_time, step):
        constraints = f'namespace="{self.namespace}", container!="POD", container!="", pod=~"{".*|".join(deployments)}.*"'
        prometheus_query = (
            f"sum(rate(container_network_transmit_bytes_total{{{constraints}}}[5m])) by (pod) / "
            f"sum(rate(container_network_receive_bytes_total{{{constraints}}}[5m])) by (pod) * 100"
        )
        return self.fetch_prometheus(prometheus_query, "range", step, start_time, end_time)


    def collect_usage(self, fetch_function, deployments, start_time):
        time.sleep(1)
        response = fetch_function(deployments, start_time, start_time + self.duration, self.monitor_interval)
        usage = response.json()
        result = pd.DataFrame(columns=["deployment", "pod", "usage"])
        if usage["data"] and usage["data"]["result"]:
            result = pd.DataFrame(data=usage["data"]["result"])
            result["pod"] = result["metric"].apply(lambda x: x["pod"])
            result["deployment"] = result["pod"].apply(lambda x: "-".join(x.split("-")[:-2]))
            result["usage"] = result["values"].apply(lambda x: max([float(v[1]) for v in x]))
            result = result[["deployment", "pod", "usage"]]
        return result

    def collect_cpu_usage(self, deployments, start_time):
        return self.collect_usage(self.fetch_cpu_usage, deployments, start_time)

    def collect_mem_usage(self, deployments, start_time):
        return self.collect_usage(self.fetch_mem_usage, deployments, start_time)
    
    def collect_network_usage(self, deployments, start_time):
        return self.collect_usage(self.fetch_network_usage, deployments, start_time)
