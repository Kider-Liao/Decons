from typing import Dict, List, Set, Union
import pandas as pd

def exact_parent_duration(data: pd.DataFrame, method: str) -> pd.DataFrame:
    if method == "merge":
        return _cal_exact_merge(data)
    elif method == "max":
        return _cal_exact_max(data)


def _cal_exact_merge(data: pd.DataFrame) -> pd.DataFrame:
    def groupByParentLevel(potential_conf_grp: pd.DataFrame) -> pd.DataFrame:
        steps: List[Dict[str, Union[List[str], int]]] = []
        step: Dict[str, Union[List[str], int]] = {
            "start_time": -1,
            "end_time": -1,
            "members": [],
        }
        for _, record in potential_conf_grp.iterrows():
            if record["startTime"] <= step["end_time"]:
                step["members"].append(record["childId"])
                step["end_time"] = max(record["endTime"], step["end_time"])
            else:
                if step["start_time"] != -1:
                    steps.append(step)
                step = {
                    "start_time": record["startTime"],
                    "end_time": record["endEnd"],
                    "members": [record["childId"]],
                }
        steps.append(step)
        steps_df = pd.DataFrame([
            {
                "mergedChildDuration": v["end_time"] - v["start_time"],
                "step": i,
                "childId": m,
            }
            for i, v in enumerate(steps)
            for m in v["members"]
        ])
        potential_conf_grp = potential_conf_grp.merge(steps_df, on="childId")
        potential_conf_grp = potential_conf_grp.assign(
            exactParentDuration=potential_conf_grp["parentDuration"]
            - potential_conf_grp[["parentId", "step", "mergedChildDuration"]].drop_duplicates()["mergedChildDuration"].sum()
        )
        return potential_conf_grp

    data = data.sort_values("startTime")
    data = data.groupby(["traceId", "parentId"]).apply(groupByParentLevel)
    data = (
        data.drop(columns=["traceId", "parentId"]).reset_index().drop(columns="level_2")
    )
    data = data.astype({"exactParentDuration": float, "childDuration": float})
    return data


def _cal_exact_max(data: pd.DataFrame) -> pd.DataFrame:
    data = data.groupby("traceId").apply(
        lambda x: x.groupby("parentId").apply(
            lambda y: y.assign(
                exactParentDuration=y["parentDuration"] - y["childDuration"].max()
            )
        )
    )
    return (
        data.drop(columns=["traceId", "parentId"]).reset_index().drop(columns="level_2")
    )


def decouple_parent_and_child(data: pd.DataFrame, percentile: float = 0.95) -> pd.DataFrame:
    parent_perspective = (
        data.groupby(["parentMS", "parentPod", "traceId"])["exactParentDuration"]
        .mean()
        .groupby(["parentMS", "parentPod"])
        .quantile(percentile)
    )
    parent_perspective.index.names = ["microservice", "pod"]
    child_perspective = (
        data.groupby(["childMS", "childPod", "traceId"])["childDuration"]
        .mean()
        .groupby(["childMS", "childPod"])
        .quantile(percentile)
    )
    child_perspective.index.names = ["microservice", "pod"]
    quantiled = pd.concat([parent_perspective, child_perspective])
    quantiled = quantiled[~quantiled.index.duplicated(keep="first")]
    data = quantiled.to_frame(name="latency").reset_index()
    return data


def construct_relationship(data: pd.DataFrame, max_edges: int) -> Union[pd.DataFrame, bool]:
    result = pd.DataFrame()

    def graph_for_trace(x: pd.DataFrame):
        nonlocal max_edges
        if len(x) <= max_edges:
            return
        max_edges = len(x)
        root = x.loc[~x["parentId"].isin(x["childId"].unique().tolist())]

        nonlocal result
        result = pd.DataFrame()

        def dfs(parent, parent_tag):
            nonlocal result
            children = x.loc[x["parentId"] == parent["childId"]]
            for index, (_, child) in enumerate(children.iterrows()):
                child_tag = f"{parent_tag}.{index+1}"
                result = pd.concat(
                    [result, pd.DataFrame(child).transpose().assign(tag=child_tag)]
                )
                dfs(child, child_tag)

        for index, (_, first_lvl) in enumerate(root.iterrows()):
            first_lvl["tag"] = index + 1
            result = pd.concat([result, pd.DataFrame(first_lvl).transpose()])
            dfs(first_lvl, index + 1)

    data.groupby(["traceId", "traceTime"]).apply(graph_for_trace)
    if len(result) != 0:
        return (
            result[
                [
                    "parentMS",
                    "childMS",
                    "parentOperation",
                    "childOperation",
                    "tag",
                    "service",
                    "step",
                ]
            ],
            max_edges,
        )
    else:
        return False


def remove_repetition(data: pd.DataFrame) -> pd.DataFrame:
    roots = data.loc[
        (~data["parentId"].isin(data["childId"]))
        & (data["parentMS"] == data["childMS"])
    ]

    def remove_prev_level_child(prev_level):
        nonlocal data
        repeat_children = data.loc[
            (data["parentId"] == prev_level["childId"])
            & (data["parentMS"] == data["childMS"])
        ]
        other_children = data.loc[
            (data["parentId"] == prev_level["childId"])
            & ~(data["parentMS"] == data["childMS"])
        ]
        if len(repeat_children) != 0:
            for _, child in repeat_children.iterrows():
                next_level_children = remove_prev_level_child(child)
                other_children = pd.concat([other_children, next_level_children])
        other_children["parentId"] = prev_level["parentId"]
        other_children["parentDuration"] = prev_level["parentDuration"]
        other_children["parentOperation"] = prev_level["parentOperation"]
        data = data.loc[~(data["childId"] == prev_level["childId"])]
        data = data.loc[~data["childId"].isin(other_children["childId"])]
        data = pd.concat([data, other_children])
        return other_children

    for _, root in roots.iterrows():
        remove_prev_level_child(root)
    return data


def no_entrance_trace_duration(spans_data: pd.DataFrame, entrance_name: str) -> pd.DataFrame:
    roots = spans_data[
        (spans_data["parentMS"].str.contains(entrance_name))
        & (~spans_data["childMS"].str.contains(entrance_name))
    ]
    roots = roots.assign(endTime=roots["startTime"] + roots["childDuration"])
    start_time = roots.groupby(["traceTime", "traceId"], sort=False)["startTime"].min()
    end_time = roots.groupby(["traceTime", "traceId"], sort=False)["endTime"].max()
    return (
        roots.drop_duplicates("traceId")
        .assign(traceDuration=(end_time - start_time).values)[
            ["traceId", "traceTime", "traceDuration"]
        ]
        .rename(columns={"traceDuration": "traceLatency"})
    )
