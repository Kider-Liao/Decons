from workloadGenerator.staticWorkload import StaticWorkloadGenerator
from Test.TestConfig import *

import os
import configs

os.chdir("/home/stluo/Decons")

currentWorkloadConfig = configs.TESTING_CONFIG.workload_config.services[TestConfig["test_service"]]

workloadGenerator = StaticWorkloadGenerator(
    WorkloadConfig["thread"],
    WorkloadConfig["connection"],
    WorkloadConfig["duration"],
    WorkloadConfig["rate"],
    configs.TESTING_CONFIG.workload_config.wrk_path,
    currentWorkloadConfig.script_path,
    currentWorkloadConfig.url,
)