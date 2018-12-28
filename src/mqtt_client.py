import paho.mqtt.client as mqtt
import logging
import time

class MQTTClient():
    """
    MQTT协议封装
    """
    def __init__(self, auto_connect=True, auto_reconnect=10, **kwargs):
        self.client_id = kwargs.get('client_id')
        self.user_name = kwargs.get('user_name')
        self.user_pwd = kwargs.get('user_pwd')
        self.host = kwargs.get('server_host')
        self.port = kwargs.get('server_port')
        self.keepalive = kwargs.get('keepalive')
        self.subscribe_topic = kwargs.get('subscribe_topic')
        self.publish_topic = kwargs.get('publish_topic')
        self.client = mqtt.Client(self.client_id)  # 创建client
        self.client.on_connect = self.on_connect  # 连接回调
        self.client.on_disconnect = self.on_disconnect  # 断开连接回调
        self.client.username_pw_set(self.user_name, self.user_pwd)
        self.auto_reconnect = auto_reconnect
        if auto_connect:
            try:
                self.client.connect(self.host, self.port, self.keepalive)  # 连接
            except Exception as e:
                logging.error('MQTTClient: ', e)
                raise Exception('Connect mqtt server failed! Please check the network or configuration.')

    def connect(self):
        try:
            self.client.connect(self.host, self.port, self.keepalive)
        except Exception as e:
            raise e

    def on_connect(self, client, userdata, flags, rc):

        logging.info("连接成功, 订阅消息主题：{}， 发布消息主题: {}".format(self.subscribe_topic, self.publish_topic))
        client.subscribe(self.subscribe_topic)

    def on_disconnect(self, client, userdata, rc):
        logging.error("************************MQTT断开连接************************")
        if self.auto_reconnect <= 0:
            return
        if self.auto_reconnect < 10:
            self.auto_reconnect = 10

        IS_CONNECTED = False
        COUNT = 0
        while not IS_CONNECTED:
            time.sleep(self.auto_reconnect)
            try:
                self.connect()
            except Exception as e:
                logging.error('************************MQTT重接失败 No: {}************************'.format(COUNT))
                COUNT += 1
                logging.error(e)
            else:
                IS_CONNECTED = True
                import sys
                sys.exit(-1)  # 让进程管理器去重启


    @property
    def on_message(self):
        return self.client.on_message

    @on_message.setter
    def on_message(self, fun):
        self.client.on_message = fun

    @property
    def socket(self):
        return self.client.socket()

    def loop_read(self):
        self.client.loop_read()

    def loop_write(self):
        self.client.loop_write()

    def loop_misc(self):
        self.client.loop_misc()

    def publish_topic_msg(self, topic, msg):
        self.client.publish(topic=topic, payload=msg)

    def send_msg(self, msg):
        self.client.publish(topic=self.publish_topic, payload=msg)

    def want_write(self):
        return self.client.want_write()
