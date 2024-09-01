import copy
import os
from typing import Dict, Union
import pandas as pd
import yaml
from kditor import search_path, mapping_edit, edit


def read_yaml(path):
    with open(path, "r") as file:
        return [x for x in yaml.load_all(file, Loader=yaml.CLoader) if x is not None]


def read_all_yaml(folder):
    yaml_files = [
        x for x in os.listdir(folder) if x[-5:] == ".yaml" or x[-4:] == ".yml"
    ]
    yaml_list = []
    for file_name in yaml_files:
        with open(f"{folder}/{file_name}", "r") as file:
            yaml_objs = yaml.load_all(file, Loader=yaml.CLoader)
            yaml_list.extend([x for x in yaml_objs if x is not None])
    return yaml_list


def insert_to_python_objs(
    path: str, value, yaml_list, target_kind="Deployment", key_path: str = None
):
    edited_yaml = []
    for yaml_obj in yaml_list:
        if target_kind is not None:
            target_success, target, _ = search_path(yaml_obj, "kind")
            if target != target_kind or not target_success:
                edited_yaml.append(yaml_obj)
                continue
        if key_path is not None:
            edited_yaml.append(mapping_edit(yaml_obj, path, value, key_path))
        else:
            edited_yaml.append(edit(yaml_obj, path, value))
    return edited_yaml


def save_all_yaml(folder, yaml_list):
    os.system(f"rm -rf {folder}")
    os.system(f"mkdir -p {folder}")
    yaml.Dumper.ignore_aliases = lambda *args : True
    for yaml_obj in yaml_list:
        file_name = f'{yaml_obj["metadata"]["name"]}_{yaml_obj["kind"]}.yaml'
        with open(f"{folder}/{file_name}", "w") as file:
            yaml.dump(yaml_obj, file, default_flow_style=False)


def base_yaml_preparation(yaml_list, namespace, app_img, pod_spec):
    path = "metadata.namespace"
    value = namespace
    yaml_list = insert_to_python_objs(path, value, yaml_list, None)

    path = "spec.template.spec.containers[0].image"
    value = {"APP_IMG": app_img}
    yaml_list = insert_to_python_objs(path, value, yaml_list, key_path=path)

    resource_limits = {
        "requests": {
            "memory": pod_spec["mem_size"],
            "cpu": pod_spec["cpu_size"],
        },
        "limits": {
            "memory": pod_spec["mem_size"],
            "cpu": pod_spec["cpu_size"],
        },
    }
    path = "spec.template.spec.containers[0].resources"
    value = resource_limits
    yaml_list = insert_to_python_objs(path, value, yaml_list)
    for i in range(len(yaml_list)):
        yaml_obj = yaml_list[i]
        if yaml_obj['metadata']['name'] == 'nginx-thrift' and yaml_obj['kind'] == 'Deployment':
            containers = copy.deepcopy(yaml_list[i]['spec']['template']['spec']['containers'])
            containers[0]['resources']['requests']['memory'] = '600Mi'
            containers[0]['resources']['limits']['memory'] = '600Mi'
            yaml_list[i]['spec']['template']['spec']['containers'] = containers
    return yaml_list

def assign_containers(yaml_list, containers: Union[pd.DataFrame, Dict]):
    path = "spec.replicas"
    if isinstance(containers, Dict):
        value = containers
    else:
        value = dict(zip(containers["microservice"], containers["container"]))
    if "nginx-web-server" in value:
        value["nginx-thrift"] = value["nginx-web-server"]
    if "nginx" in value:
        value["nginx-web-server"] = value["nginx"]
    key_path = "metadata.name"
    yaml_list = insert_to_python_objs(path, value, yaml_list, key_path=key_path)

    return yaml_list

def assign_affinity(yaml_list, nodes):
    with open("yamlRepository/templates/deploymentAffinity.yaml", "r") as file:
        node_affinity = yaml.load(
            file.read().replace("%%%", f'[{", ".join(nodes)}]'),
            yaml.CLoader,
        )
    path = "spec.template.spec.affinity"
    value = node_affinity
    yaml_list = insert_to_python_objs(path, value, yaml_list)
    return yaml_list
