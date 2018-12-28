from .router import g_data_route, g_mqtt_data_route
import re

from user.parse_data import *

import logging


class MessageBroker(object):
    """
    消息使者
    """

    def __init__(self, mqtt_client, arduino_clients, config):

        self.mqtt_client = mqtt_client
        self.arduino_clients = arduino_clients
        self.config = config
        self._rg_cb()

        self._init_device_state()

        pd_init(self)

    def _rg_cb(self):
        # 注册MQTT消息接受事件
        self.mqtt_client.on_message = self.new_mqtt_msg

        # 注册Arduino 消息回调
        for item in self.arduino_clients:
            item.on_message = self.new_arduino_msg

    def new_arduino_msg(self, client, msg):
        """
        新arduino消息回调
        :param msg:
        :return:
        """
        for k in g_data_route:
            try:
                res = re.match(k, msg)
                # print(res.group())
            except Exception as e:
                print(e)
            else:
                if res is None:
                    continue
                # print(res.groups())
                if len(res.groups()) > 0:
                    g_data_route[k](client, self.mqtt_client, self.arduino_clients, msg, res.groups())
                else:
                    g_data_route[k](client, self.mqtt_client, self.arduino_clients, msg)
        return

    def new_mqtt_msg(self, client, userdata, msg):
        """
         新mqtt消息回调
         从服务器读取到数据，那么表示数据下发Arduino
         """

        for k in g_mqtt_data_route:
            try:
                res = re.match(k, msg.payload.decode())
                # print(res.group())
            except Exception as e:
                logging.error(e)
            else:
                if res is None:
                    continue
                if len(res.groups()) > 0:
                    g_mqtt_data_route[k](self.mqtt_client, self.arduino_clients, msg.payload.decode(), res.groups())
                else:
                    g_mqtt_data_route[k](self.mqtt_client, self.arduino_clients, msg.payload.decode())
        return

    def send_msg_to_all(self, data):
        for sock in self.arduino_clients:
            sock.send_msg(data)

    def _init_device_state(self):
        self.send_msg_to_all('query_relay_state')

    def flush_arduino_clients(self):
        for item in self.arduino_clients:
            item.on_message = self.new_arduino_msg
