import os
import time
import yaml
from kubernetes import utils, config, client
import utils.deploymentEditor as editor
from utils.others import wait_deletion, wait_deployment

class Deployer:
    def __init__(self, namespace, cpuSize, memorySize, nodes, yamlRepo, app_img):
        self.namespace = namespace
        self.pod_spec = {"mem_size": memorySize, "cpu_size": cpuSize}
        self.nodes = nodes
        self.yamlRepo = yamlRepo
        self.tmpYamlRepo = f"tmp/testing-{namespace}"
        self.application_img = app_img
        self.createNamespace()

    def full_init(self, app, infra_nodes, port, containers=None):
        non_test_yamls = editor.read_all_yaml(f"{self.yamlRepo}/non-test")
        with open("yamlRepository/templates/deploymentAffinity.yaml", "r") as file:
            non_test_node_affinity = yaml.load(
                file.read().replace("%%%", f'[{", ".join(infra_nodes)}]'),
                yaml.CLoader,
            )
        
        non_test_yamls = editor.insert_to_python_objs("metadata.namespace", self.namespace, non_test_yamls, None)
        non_test_yamls = editor.insert_to_python_objs("spec.template.spec.affinity", non_test_node_affinity, non_test_yamls)
        non_test_yamls = editor.insert_to_python_objs("spec.template.spec.containers[0].imagePullPolicy", "IfNotPresent", non_test_yamls)

        tmp_infra_path = f"tmp/infra-{self.namespace}"
        os.system(f"rm -rf {tmp_infra_path}")
        os.system(f"mkdir {tmp_infra_path}")
        editor.save_all_yaml(tmp_infra_path, non_test_yamls)

        delete_by_yaml(tmp_infra_path)
        deploy_by_yaml(tmp_infra_path, True, self.namespace)

        self.redeploy_app(containers)

        time.sleep(30)

        if app == "social":
            from scripts.socialNetwork.init import main
            main(port=port)
        elif app == "media":
            from scripts.mediaMicroservice.write_movie_info import main
            main(server_address=f"http://localhost:{port}")
            from scripts.mediaMicroservice.register_movies_and_users import main
            main(server_address=f"http://localhost:{port}")

    def redeploy_app(self, containers=None, schedulerFlag=None, wait=True):
        self.delete_app()
        self.deploy_app(containers, schedulerFlag, wait)

    def deploy_app(self, containers=None, schedulerFlag=None, wait=True):
        containers = containers if containers is not None else {}
        os.system(f"rm -rf {self.tmpYamlRepo}")
        os.system(f"mkdir -p {self.tmpYamlRepo}")

        yaml_list = editor.read_all_yaml(f"{self.yamlRepo}/test")
        yaml_list = editor.base_yaml_preparation(yaml_list, self.namespace, self.application_img, self.pod_spec)
        yaml_list = editor.assign_affinity(yaml_list, self.nodes)
        yaml_list = editor.assign_containers(yaml_list, containers)
        yaml_list = editor.insert_to_python_objs("spec.template.spec.containers[0].imagePullPolicy", "IfNotPresent", yaml_list)

        if schedulerFlag:
            path = "spec.template.spec.schedulerName"
            microserviceList = list(containers.keys())
            value = dict(zip(microserviceList, ["erms-scheduler"] * len(microserviceList)))
            if "nginx-web-server" in value:
                value["nginx-thrift"] = value["nginx-web-server"]
            if "nginx" in value:
                value["nginx-web-server"] = value["nginx"]
            key_path = "metadata.name"
            yaml_list = editor.insert_to_python_objs(path, value, yaml_list, key_path=key_path)

        # Save to temporary folder and deploy
        editor.save_all_yaml(self.tmpYamlRepo, yaml_list)
        delete_by_yaml(self.tmpYamlRepo, wait=True, namespace=self.namespace)
        deploy_by_yaml(self.tmpYamlRepo, wait, self.namespace)
    
    def delete_app(self, wait=False):
        delete_by_yaml(self.tmpYamlRepo, wait, self.namespace)

    def deployFromYaml(yamlPath, namespace):
        config.load_kube_config()
        apiClient = client.ApiClient()
        utils.create_from_yaml(apiClient, yamlPath, namespace=namespace)

    def deleteDeployByNameInNamespace(name, namespace):
        try:
            config.load_kube_config()
            v1Client = client.AppsV1Api()
            v1Client.delete_namespaced_deployment(name, namespace)
        except:
            pass  # Ignore errors if deployment doesn't exist

    def createNamespace(self):
        config.load_kube_config()
        coreV1Client = client.CoreV1Api()
        metadata = client.V1ObjectMeta(name=self.namespace)
        body = client.V1Namespace(api_version="v1", kind="Namespace", metadata=metadata)
        try:
            coreV1Client.create_namespace(body=body)
        except:
            pass

config.load_kube_config()

def deploy_by_yaml(folder, wait=False, namespace=None, timeout=300):
    api_client = client.ApiClient()
    for file in [x for x in os.listdir(folder) if x.endswith(".yaml") or x.endswith(".yml")]:
        utils.create_from_yaml(api_client, f"{folder}/{file}")
    if wait:
        if namespace is None:
            raise Exception("No namespace specified")
        (namespace, timeout)

def delete_by_yaml(folder, wait=False, namespace=None, timeout=300, display=False):
    command = f"kubectl delete -Rf {folder}"
    if not display:
        command += " >/dev/null"
    os.system(command)
    if wait:
        if namespace is None:
            raise Exception("No namespace specified")
        wait_deletion(namespace, timeout)

def apply_by_yaml(folder, wait=False, namespace=None, timeout=300, display=False):
    command = f"kubectl apply -Rf {folder}"
    if not display:
        command += " >/dev/null"
    os.system(command)
    if wait:
        if namespace is None:
            raise Exception("No namespace specified")
        wait_deployment(namespace, timeout)
