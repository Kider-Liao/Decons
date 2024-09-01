from Test.TestConfig import *
from connectionManager.AdjustProxy import *
from deploy.AppDeployment import *
from traceCoordinator.DataCollection import *
from connectionManager.ConnectionAdjuster import *
import traceback

enabled_node = GlobalConfig["enabled_slave"]
adjust_node = GlobalConfig["adjust_slave"]
slave_addr = GlobalConfig["slave_addr"]
slave_num = len(slave_addr)
test_service = TestConfig["test_service"]
microservice_list = TestConfig["microservice_list"]
method = GlobalConfig["method"]
data_path = DataConfig["data_path"]
save_path = DataConfig["save_path"]
repeat_round = GlobalConfig["repeat_round"]

def connection_minute_run(process_round, client_num, detail_path):
    t = 0
    os.system(f"rm -r {data_path}/{save_path}/{detail_path}")
    enable_adjustment(adjust_node + ["lijt-master"])
    
    end_to_end_latency_list = []
    microservice_latency = {ms: [] for ms in microservice_list}

    while t < process_round:
        t += 1
        try:
            test_name = f"[Gaussian]round{t}r{client_num}"
            startTime = int(time.time())
            workloadGenerator.generateWorkload(test_name, client_num)
            print("workload generation finished...")
            time.sleep(30)

            dataCollector.validation_collection(
                test_name,
                startTime,
                None,
                test_service,
                t,
                save_path,
                detail_path,
                client=client_num,
                no_nginx=True if app == "social" else False,
            )
            print("finish collection...")

            end_to_end_latency_list.append(
                trace_latency_collection(data_path, save_path, detail_path, 0.95, t)
            )
            for ms in microservice_list:
                if ms == "nginx-thrift":
                    new_ms = "nginx-web-server"
                elif ms == "nginx-web-server":
                    new_ms = "nginx"
                else:
                    new_ms = ms
                microservice_latency[ms].append(
                    microservice_latency_collection(
                        data_path, save_path, detail_path, 0.95, new_ms, t
                    )
                )
        except:
            traceback.print_exc()
            time.sleep(60)
            t -= 1
            continue

    for ms in microservice_list:
        microservice_latency[ms] = np.percentile(microservice_latency[ms], 50)

    return end_to_end_latency_list, microservice_latency
