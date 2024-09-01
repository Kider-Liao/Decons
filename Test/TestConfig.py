import os
app = os.environ["ERMS_APP"]

SocialConfig = {
    "test_service": "ComposePost",
    "microservice_list": ["nginx-thrift", "home-timeline-service", "compose-post-service", "text-service", "user-timeline-service", "url-shorten-service"],
    "container_num": {"home-timeline-service": 4, "unique-id-service": 4, "media-service": 4, "user-service": 4, "nginx-thrift": 4, "compose-post-service": 16, "text-service": 8, "social-graph-service": 4, "url-shorten-service": 4, "user-mention-service": 4, "user-timeline-service": 4, "post-storage-service": 4},
    "upstream_config": {"compose-post-service": "nginx-thrift", "text-service": "compose-post-service", "url-shorten-service": "text-service", "user-timeline-service": "compose-post-service", "home-timeline-service": "compose-post-service"},
    "prewarm_time": 0,
    "prewarm_duration": 600,
    "init_round": 5,
    "sleep_time": 120,
    "inf_type": "low",
    "port" : 30928,
    "prometheus_host": "http://localhost:30091",
    "repeat": 1,
    "detail_path": "initial_test",
    "password": "lijt",
}

# modify this to your machine name
GlobalConfig = {
    "scheduler": True,
    "enabled_slave": ["node2", "node3"],
    "adjust_slave": ["node2", "node3"],
    "slave_addr": ["192.168.3.23", "192.168.3.178"],
    "repeat_round": 1,
    "method": "Random",
}

InterenceConfig = {
    "high_interference": [[[15, 30], [15, 35]]],
    "low_interference": [[[1, 1], [1, 10]]],
    "resource": ["cpu", "bandwidth"],
    "interference_config": [{"cpu_size": 1, "mem_size": "20Mi"}, {"cpu_size": 1, "mem_size": "200Mi"}],
    "duration": 72000,
}

WorkloadConfig = {
    "client": 10,
    "duration": 60, 
    "thread": 2,
    "connection": 4, 
    "rate": 8, 
}

DataConfig = {
    "data_path": "journal/test_data",
    "save_path": "latencyResult",
}

TestConfig = SocialConfig