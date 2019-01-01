import uuid
import logging

LOG_LEVEL = logging.INFO

DB_NAME = 'data.db'

MQTT_CONFIG = {
    'client_id': 'orangepi_' + str(uuid.uuid4()),
    'user_name': 'alonebo',
    'user_pwd': '976447044',
    'server_host': 'iot.alonebo.top',
    'server_port': 1883,
    'keepalive': 60,
    'publish_topic': "arduino/01",  # 发布消息主题 01版本号
    'subscribe_topic': "arduino_server/01"  # 订阅消息主题
}

ESP_CLIENTS = {
    'arduino01_sensors': {'ip': '192.168.0.102', 'port': 9000},
    'arduino02_relay': {'ip': '192.168.0.103', 'port': 9000},
    'arduino03_nodemcu': {'ip': '192.168.0.101', 'port': 9000},
}


if __name__ == '__main__':
    for i, k in enumerate(ESP_CLIENTS):
        print(ESP_CLIENTS[k], i)
    print(MQTT_CONFIG)
    print(list(ESP_CLIENTS))
