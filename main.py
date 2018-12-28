import logging
from src.mqtt_client import MQTTClient
from src.arduino_client import ArduinoClientSocket
from src.message_broker import MessageBroker
from src.tasks import g_tasks, g_late_task
import select
import signal
import orangepi_config
import threading
import sys
import time
import datetime
import logging.handlers


LOG_LEVEL = getattr(orangepi_config, 'LOG_LEVEL', logging.WARNING)

SOCKET_READ_BUFFER = getattr(orangepi_config, 'SOCKET_READ_BUFFER', 1024)  # bytes; once recv data max size;

SELECT_TIME_OUT = getattr(orangepi_config, 'SELECT_TIME_OUT', 10) * 2  # seconds must be > 10


class Main(object):
    """
    主类 事件循环
    """
    def __init__(self):

        # 创建arduino MessageBroker MQTTClient客户端
        try:
            self.mqtt_client = MQTTClient(**orangepi_config.MQTT_CONFIG)
        except Exception as e:
            logging.error(e)
            sys.exit(-1)

        self.mqtt_socket = self.mqtt_client.socket

        self.arduino_clients = []

        for k in orangepi_config.ARDUINO_CLIENTS:
            item = orangepi_config.ARDUINO_CLIENTS[k]
            ip = item.get('ip', '127.0.0.1')
            port = item.get('port', 9000)
            self.arduino_clients.append(ArduinoClientSocket(host=ip, port=port, name=k))

        self.arduino_sockets = [client.socket for client in self.arduino_clients]

        # 创建消息中间人
        self.broker = MessageBroker(self.mqtt_client, self.arduino_clients, orangepi_config.MQTT_CONFIG)

    def loop(self):
        s_time = time.time()
        while True:
            #
            logging.debug('select running, timeout:{}s'.format(SELECT_TIME_OUT))
            logging.debug('.')
            try:
                r, w, e = select.select(
                    [self.mqtt_socket, *self.arduino_sockets],  # 监听读事件的 套接字 Arduino Client
                    [self.mqtt_socket] if self.mqtt_client.want_write() else [],  # 监听写事件
                    [],
                    SELECT_TIME_OUT  # timeout
                )
            except Exception as e:
                logging.error(e)
                time.sleep(10)
                # try:
                #     self.mqtt_client = MQTTClient(**orangepi_config.MQTT_CONFIG)
                # except Exception as e:
                #     logging.error(e)
                # continue

            if self.mqtt_socket in r:
                self.mqtt_client.loop_read()

            if self.mqtt_socket in w:
                self.mqtt_client.loop_write()

            self.mqtt_client.loop_misc()

            # check if need to read.
            for i, sock in enumerate(self.arduino_sockets):
                if sock not in r:
                    continue
                try:
                    data = sock.recv(SOCKET_READ_BUFFER)  # 接收数据
                    arduino_client = self.arduino_clients[i]
                    try:
                        arduino_client.on_message(arduino_client, data.decode())
                    except Exception as e:
                        logging.error(e)
                    # set last data update time
                    k = self.arduino_clients[i].name
                    v = orangepi_config.ARDUINO_CLIENTS.get(k, None)
                    if v:
                        v['last_update_time'] = time.time()
                        logging.info("update last time: {}".format(k))
                    else:
                        logging.warning('main.py [loop]: v is None')
                except Exception as e:
                    logging.error('main.py[loop]: read socket data error!')
                    logging.error(e)
                    sys.exit(0)

            for t in g_late_task:
                if time.time() > g_late_task[t]['time']:
                    g_late_task[t]['cb']()

            if time.time() - s_time >= SELECT_TIME_OUT:

                self.check_time_out()

                self.check_tasks()

                s_time = time.time()

    def check_tasks(self):
        # 判断当前时间是否大于
        logging.error('检查执行tasks')

        for k in g_tasks:

            # 判断当前时间是否处在这个时间段
            now_h = datetime.datetime.now().hour
            now_m = datetime.datetime.now().minute
            start_h = datetime.datetime.strptime(g_tasks[k]['start_time'], '%H:%M').hour
            start_m = datetime.datetime.strptime(g_tasks[k]['start_time'], '%H:%M').minute
            end_h = datetime.datetime.strptime(g_tasks[k]['end_time'], '%H:%M').hour
            end_m = datetime.datetime.strptime(g_tasks[k]['end_time'], '%H:%M').minute

            if now_h < start_h:
                continue

            if now_h > end_h:
                continue

            if now_h == start_h:
                if now_m < start_m:
                    continue

            if now_h == end_h:
                if now_m > end_m:
                    continue

            g_tasks[k]['callback']()

    def check_time_out(self):
        logging.info('开始检查超时元素')
        logging.info(orangepi_config.ARDUINO_CLIENTS)  # ok

        flag = False

        for k in orangepi_config.ARDUINO_CLIENTS:
            item = orangepi_config.ARDUINO_CLIENTS[k]
            last_time = item.get('last_update_time', time.time())
            if (time.time() - last_time) >= SELECT_TIME_OUT:
                logging.warning('{} 检查到数据超时， 相差{}秒 上次数据时间{}, 现在时间{}'.format(k, int(time.time()-last_time), int(last_time), int(time.time())))
                item['is_timeout'] = True
                flag = True

        if flag is False:
            logging.info('此次检查没有发现新的异常Arduino Client')

        for i, k in enumerate(orangepi_config.ARDUINO_CLIENTS):
            item = orangepi_config.ARDUINO_CLIENTS[k]
            if not item.get('is_timeout', False):
                continue

            ip = item.get('ip', '127.0.0.1')
            port = item.get('port', 9000)
            if not item.get('is_reconnecting', False):
                logging.warning('创建新线程')
                logging.warning('重连第{}个Arduino socket'.format(i))
                t = threading.Thread(target=self.connect, args=(ip, port, k, i))
                t.setDaemon(True)
                t.start()
            else:
                logging.warning('不创建新线程，在连接中')

    def connect(self, host, port, name, ii):
        logging.warning('name = {}'.format(name))
        orangepi_config.ARDUINO_CLIENTS[name]['is_connecting'] = True
        logging.warning(orangepi_config.ARDUINO_CLIENTS[name])
        try:
            arduino = ArduinoClientSocket(host=host, port=port, name=name)
        except Exception as e:
            logging.error('main.py [loop-sub-thread]: reconnect failure!, name: {}'.format(name))
            # print(e)
        else:  #
            logging.info('重连成功pop(ii) = {}'.format(ii))

            self.arduino_clients[ii] = arduino
            orangepi_config.ARDUINO_CLIENTS[name]['is_timeout'] = False
            orangepi_config.ARDUINO_CLIENTS[name]['last_update_time'] = time.time()
            logging.info('reconnect success [loop-sub-thread]!, name: {}'.format(name))
            # Flush
            self.arduino_sockets = [client.socket for client in self.arduino_clients]
            self.broker.flush_arduino_clients()
            logging.info('flush')
        finally:
            orangepi_config.ARDUINO_CLIENTS[name]['is_connecting'] = False


if __name__ == '__main__':
    from importlib import reload
    reload(logging)
    handler = logging.handlers.RotatingFileHandler('./log/log.txt',
                                                   maxBytes=1024 * 1024 * 5,
                                                   backupCount=5,
                                                   )
    s = logging.StreamHandler()
    logging.basicConfig(level=LOG_LEVEL,
                        format='%(asctime)s-[%(filename)s %(lineno)d]-%(levelname)s->  %(message)s',
                        datefmt='%Y-%m-%d %H:%M',
                        handlers=[handler, s],
)
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    main_app = Main()
    main_app.loop()
