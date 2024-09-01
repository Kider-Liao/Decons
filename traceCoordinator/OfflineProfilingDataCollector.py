from datetime import datetime
import multiprocessing
import os
from time import sleep
import traceback
from typing import Dict, List, Set
import json
import re
import pandas as pd
import requests
import utils.traceProcessor as t_processor
from utils.files import append_data
import contentionMonitor.prometheus as prometheus_fetcher

pd.options.mode.chained_assignment = None


class OfflineProfilingDataCollector:
    def __init__(
            self,
            namespace,
            jaegerHost,
            entryPoint,
            prometheusHost,
            nodes,
            dataPath,
            duration=60,
            max_traces=1000,
            mointorInterval=1,
            max_processes=3
    ):
        self.namespace = namespace
        self.duration = duration
        self.jaegerHost = jaegerHost
        self.entryPoint = entryPoint
        self.prometheusHost = prometheusHost
        self.monitorInterval = mointorInterval
        self.nodes = nodes
        self.max_traces = max_traces
        self.data_path = dataPath
        self.resultPath = f"{dataPath}/offlineTestResult"
        os.system(f"mkdir -p {self.resultPath}")
        manager = multiprocessing.Manager()
        self.relationDF = manager.dict()
        self.max_edges = manager.dict()
        self.max_processes = max_processes
        self.pool = multiprocessing.Pool(max_processes)

    def validation_collection(self, test_name, start_time, operation, service, repeat, data_path, detail_path,
                              no_nginx=False, no_frontend=False, **kwargs):
        os.system(f"mkdir -p {self.data_path}/{data_path}")
        self.log_file = f"log/{service}_validation.log"

        log_directory = "log"
        if not os.path.exists(log_directory):
            os.makedirs(log_directory)

        log_filename = f"{service}_validation.log"
        log_file_path = os.path.join(log_directory, log_filename)
        open(log_file_path, 'a').close()

        output_dir = f"{self.data_path}/{data_path}/{detail_path}"
        os.makedirs(output_dir, exist_ok=True)

        try:
            # Collect throughput data
            req_counter = self.collect_wrk_data(test_name)
        except Exception:
            self.write_log("Collect wrk data failed!", "error")
            traceback.print_exc()
            return
        try:
            throughput = req_counter / self.duration
            _, span_data, trace_data = self.collect_trace_data(self.max_traces, start_time, operation, no_nginx,
                                                               no_frontend)
            ms_trace, full_duration, pod_latency, _, _ = self.process_span_data(span_data)
            ms_trace = ms_trace.assign(repeat=repeat)
            append_data(ms_trace, f"{self.data_path}/{data_path}/{detail_path}/ms_trace.csv")
            ms_latency = pod_latency.groupby("microservice").mean(True).reset_index()
            deployments = (
                pod_latency["pod"]
                .apply(lambda x: "-".join(str(x).split("-")[:-2]))
                .unique()
                .tolist()
            )
        except Exception:
            self.write_log("Collect trace data failed!", "error")
            traceback.print_exc()
            return
        try:
            pod_cpu_usage = self.collect_cpu_usage(
                list(filter(lambda x: x, deployments)),
                start_time
            ).rename(columns={
                "usage": "cpuUsage",
                "deployment": "microservice"
            })
            ms_cpu_usage = (
                pod_cpu_usage
                .groupby("microservice")
                .mean(True)
                .reset_index()
            )
        except Exception:
            self.write_log("Fetch CPU usage data failed!", "error")
            traceback.print_exc()
            return
        try:
            pod_latency = pod_latency.assign(
                service=service,
                repeat=repeat,
                throughput=throughput,
                **kwargs
            )
            ms_latency = ms_latency.assign(
                service=service,
                repeat=repeat,
                throughput=throughput,
                **kwargs
            )
            ms_latency = ms_latency.merge(ms_cpu_usage, on="microservice", how="left")
            pod_latency = pod_latency.merge(pod_cpu_usage, on=["microservice", "pod"], how="left")
            append_data(ms_latency, f"{self.data_path}/{data_path}/{detail_path}/ms_latency.csv")
            append_data(pod_latency, f"{self.data_path}/{data_path}/{detail_path}/pod_latency.csv")
            trace_latency = trace_data[["traceId", "traceLatency"]].assign(
                service=service, repeat=repeat, throughput=throughput, **kwargs
            )
            append_data(trace_latency, f"{self.data_path}/{data_path}/{detail_path}/trace_latency.csv")
            print(
                f"P95: {format(trace_latency['traceLatency'].quantile(0.95) / 1000, '.2f')}ms\n"
                f"P50: {format(trace_latency['traceLatency'].quantile(0.5) / 1000, '.2f')}ms\n"
                f"throughput: {format(throughput, '.2f')}, "
                f"service: {service}, "
                f"repeat: {repeat}\n"
                f"data: {kwargs}"
            )
        except Exception:
            self.write_log("Merge all data failed!", "error")
            traceback.print_exc()

    def collect_wrk_data(self, file_name):
        with open(f"tmp/wrkResult/{file_name}", "r") as file:
            lines = file.readlines()
            counter = 0
            for line in lines:
                counter += int(line)
            return counter

    def collect_trace_data(self, limit, start_time, operation=None, no_nginx=False, no_frontend=False):
        request_data = {
            "start": int(start_time * 1000000),
            "end": int((start_time + self.duration) * 1000000),
            "limit": limit,
            "service": self.entryPoint,
            "tags": '{"http.status_code":"200"}',
        }
        if operation is not None:
            request_data["operation"] = operation
        req = requests.get(f"{self.jaegerHost}/api/traces", params=request_data)
        self.write_log(f"Fetch latency data from: {req.url}")
        res = json.loads(req.content)["data"]
        if len(res) == 0:
            self.write_log(f"No traces are fetched!", "error")
            return False, None, None
        else:
            self.write_log(f"Number of traces: {len(res)}")
        service_id_mapping = (
            pd.json_normalize(res)
            .filter(regex="serviceName|traceID|tags")
            .rename(
                columns=lambda x: re.sub(
                    r"processes\.(.*)\.serviceName|processes\.(.*)\.tags",
                    lambda match_obj: match_obj.group(1)
                    if match_obj.group(1)
                    else f"{match_obj.group(2)}Pod",
                    x,
                )
            )
            .rename(columns={"traceID": "traceId"})
        )
        service_id_mapping = (
            service_id_mapping.filter(regex=".*Pod")
            .applymap(
                lambda x: [v["value"] for v in x if v["key"] == "hostname"][0]
                if isinstance(x, list)
                else ""
            )
            .combine_first(service_id_mapping)
        )
        spans_data = pd.json_normalize(res, record_path="spans")[
            [
                "traceID",
                "spanID",
                "operationName",
                "duration",
                "processID",
                "references",
                "startTime",
            ]
        ]
        spans_with_parent = spans_data[~(spans_data["references"].astype(str) == "[]")]
        root_spans = spans_data[(spans_data["references"].astype(str) == "[]")]
        root_spans = root_spans.rename(
            columns={
                "traceID": "traceId",
                "startTime": "traceTime",
                "duration": "traceLatency"
            }
        )[["traceId", "traceTime", "traceLatency"]]
        spans_with_parent.loc[:, "parentId"] = spans_with_parent["references"].map(
            lambda x: x[0]["spanID"]
        )
        temp_parent_spans = spans_data[
            ["traceID", "spanID", "operationName", "duration", "processID"]
        ].rename(
            columns={
                "spanID": "parentId",
                "processID": "parentProcessId",
                "operationName": "parentOperation",
                "duration": "parentDuration",
                "traceID": "traceId",
            }
        )
        temp_children_spans = spans_with_parent[
            [
                "operationName",
                "duration",
                "parentId",
                "traceID",
                "spanID",
                "processID",
                "startTime",
            ]
        ].rename(
            columns={
                "spanID": "childId",
                "processID": "childProcessId",
                "operationName": "childOperation",
                "duration": "childDuration",
                "traceID": "traceId",
            }
        )
        merged_df = pd.merge(
            temp_parent_spans, temp_children_spans, on=["parentId", "traceId"]
        )
        merged_df = merged_df[
            [
                "traceId",
                "childOperation",
                "childDuration",
                "parentOperation",
                "parentDuration",
                "parentId",
                "childId",
                "parentProcessId",
                "childProcessId",
                "startTime",
            ]
        ]
        merged_df = merged_df.merge(service_id_mapping, on="traceId")
        merged_df = merged_df.merge(root_spans, on="traceId")
        merged_df = merged_df.assign(
            childMS=merged_df.apply(lambda x: x[x["childProcessId"]], axis=1),
            childPod=merged_df.apply(lambda x: x[f"{str(x['childProcessId'])}Pod"], axis=1),
            parentMS=merged_df.apply(lambda x: x[x["parentProcessId"]], axis=1),
            parentPod=merged_df.apply(
                lambda x: x[f"{str(x['parentProcessId'])}Pod"], axis=1
            ),
            endTime=merged_df["startTime"] + merged_df["childDuration"],
        )
        merged_df = merged_df[
            [
                "traceId",
                "traceTime",
                "startTime",
                "endTime",
                "parentId",
                "childId",
                "childOperation",
                "parentOperation",
                "childMS",
                "childPod",
                "parentMS",
                "parentPod",
                "parentDuration",
                "childDuration",
            ]
        ]
        if no_nginx:
            return True, merged_df, t_processor.no_entrance_trace_duration(merged_df, "nginx")
        elif no_frontend:
            return True, merged_df, t_processor.no_entrance_trace_duration(merged_df, "frontend")
        else:
            return True, merged_df, root_spans

    def construct_relationship(self, span_data: pd.DataFrame, max_edges: Dict, relation_df: Dict, service):
        if service not in max_edges:
            max_edges[service] = 0
        relation_result = t_processor.construct_relationship(
            span_data.assign(service=service), max_edges[service]
        )
        if relation_result:
            relation_df[service], max_edges[service] = relation_result
        pd.concat(relation_df.values()).to_csv(
            f"{self.resultPath}/spanRelationships.csv", index=False
        )

    def full_ms_duration(self, data: pd.DataFrame) -> pd.DataFrame:
        percentile = 0.95
        parent_perspective = (
            data.groupby(["parentMS", "traceId"])["exactParentDuration"]
            .mean()
            .groupby(["parentMS"])
            .quantile(percentile)
        )
        parent_perspective.index.names = ["microservice"]
        child_perspective = (
            data.groupby(["childMS", "traceId"])["childDuration"]
            .mean()
            .groupby(["childMS"])
            .quantile(percentile)
        )
        child_perspective.index.names = ["microservice"]
        quantiled = pd.concat([parent_perspective, child_perspective])
        quantiled = quantiled[~quantiled.index.duplicated(keep="first")]
        return quantiled.reset_index(name="duration")

    def process_span_data(self, span_data: pd.DataFrame, filter_db=False) -> tuple:
        db_data = pd.DataFrame()
        if filter_db:
            for key_word in ["Mongo", "Redis", "Mmc", "Mem"]:
                dbs = span_data["childOperation"].str.contains(key_word)
                db_layer = span_data.loc[dbs]
                db_layer["childMS"] = key_word
                db_layer["childPod"] = key_word
                span_data = pd.concat([span_data.loc[~dbs], db_layer])
                db_data = pd.concat([
                    db_data,
                    db_layer[[
                        "parentMS", "parentOperation", "childMS", "childOperation", "childDuration"
                    ]]
                ])
        span_data = t_processor.exact_parent_duration(span_data, "merge")
        ms_trace = self.full_ms_duration(span_data)
        p95_df = t_processor.decouple_parent_and_child(span_data, 0.95)
        p50_df = t_processor.decouple_parent_and_child(span_data, 0.5)
        return ms_trace, pd.DataFrame([]), p50_df.rename(columns={"latency": "median"}).merge(p95_df, on=["microservice", "pod"]), db_data, span_data

    def collect_cpu_usage(self, deployments: list, start_time: int) -> pd.DataFrame:
        sleep(1)
        response = prometheus_fetcher.fetch_cpu_usage(
            self.prometheusHost, self.namespace, deployments, start_time, start_time + self.duration, self.monitorInterval
        )
        self.write_log(f"Fetch CPU usage from: {response.url}")
        usage = response.json()
        cpu_result = pd.DataFrame(columns=["microservice", "pod", "usage"])
        if usage["data"] and usage["data"]["result"]:
            cpu_result = pd.DataFrame(data=usage["data"]["result"])
            cpu_result["pod"] = cpu_result["metric"].apply(lambda x: x["pod"])
            cpu_result["deployment"] = cpu_result["pod"].apply(lambda x: "-".join(x.split("-")[:-2]))
            cpu_result["usage"] = cpu_result["values"].apply(lambda x: max(float(v[1]) for v in x))
            cpu_result = cpu_result[["deployment", "pod", "usage"]]
        return cpu_result

    def write_log(self, content: str, type: str = "info"):
        with open(self.log_file, "a+") as file:
            current_time = datetime.now().strftime("%Y/%m/%d %H:%M:%S")
            file.write(f"<{type}> <{current_time}> {content}\n")

