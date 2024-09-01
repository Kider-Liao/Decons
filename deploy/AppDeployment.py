from deploy.deployer import Deployer
from contentionGenerator.Workload import *
from Test.TestConfig import *

import os
os.chdir("/home/stluo/Decons")
import configs

DEPLOYER = Deployer(
    configs.GLOBAL_CONFIG.namespace,
    configs.GLOBAL_CONFIG.pod_spec.cpu_size,
    configs.GLOBAL_CONFIG.pod_spec.mem_size,
    GlobalConfig["enabled_slave"],
    configs.GLOBAL_CONFIG.yaml_repo_path,
    configs.GLOBAL_CONFIG.app_img,
)

# Number of containers for the test
containers: dict = TestConfig["container_num"]

def prewarm_app(client_num, duration):
    workload = StaticWorkloadGenerator(
        WorkloadConfig["thread"],
        WorkloadConfig["connection"],
        duration,
        WorkloadConfig["rate"],
        configs.TESTING_CONFIG.workload_config.wrk_path,
        currentWorkloadConfig.script_path,
        currentWorkloadConfig.url
    )
    workload.generateWorkload("prewarm", client_num)  # Start the prewarming workload