import socket
import logging


class EspClientSocket(object):
    """
    ESP8266通信客户端
    """
    def __init__(self, *, host="127.0.0.1", port=9000, name=''):
        self.host = host
        self.port = port
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        self.client.connect((host, port))

        self.client.setblocking(False)  # 设置不阻塞
        self.client.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # 端口复用
        self.on_message = None
        self.name = name

    @property
    def socket(self):
        return self.client

    def send_msg(self, msg):
        if type(msg) == str:
            msg = msg.encode()
        self.client.send(msg)
        logging.info('发送给{}-> {}'.format(self.name, msg))
