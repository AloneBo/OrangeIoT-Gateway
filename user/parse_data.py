from src.router import reroute, mqtt_reroute
from user.db import DB
from .status import STATUS
from .scheduler import on_status_update, sc_init
from .tools import send_msg_by_name
import logging
import json
import datetime
from .tools import send_mail


db_sqlite = DB()

STATUS['cur_auto_ctl'] = db_sqlite.query_auto_ctl()

STATUS['email'] = db_sqlite.query_email()

logging.info("STATUS['cur_auto_ctl'] = {}".format(STATUS['cur_auto_ctl']))

on_status_update()

broker = None


logging.error(STATUS)


def pd_init(b):
    global broker
    broker = b
    sc_init(broker)


@reroute(r'^.{2}_(.{1,2})_10_(\d*)')
def upload_data(client, mqtt_client, esp_clients, data, groups):
    logging.debug('new data start' + '*' *20)
    logging.debug(groups)
    logging.debug('new data end' + '*' * 20)
    mqtt_client.send_msg(groups[0]+'_'+groups[1])


@reroute(r'^01_(0.{1})_10_(\d*)')
def relay_value(client, mqtt_client, esp_clients, data, groups):
    logging.info('relay_value ')
    STATUS['cur_relay_state'][groups[0]] = groups[1]


@reroute(r'^01_(1.{1})_10_(\d*)')
def temperature_value(client, mqtt_client, esp_clients, data, groups):
    """
    01_10_10_18.00 [温]度
    :param client:
    :param data:
    :param groups:
    :return:
    """
    # logging.info()(groups)
    logging.info('[温]度传感器:{}, id:{}, value:{}'.format(data, groups[0], groups[1]))
    water_ctl_tmp = STATUS['cur_auto_ctl'].get('water_ctl_tmp', {})
    threshold = water_ctl_tmp.get('threshold', None)
    operator = water_ctl_tmp.get('operator', None)
    if water_ctl_tmp.get('status') == True and operator:
        prefix_threshold = threshold[0] if len(threshold) > 2 else None
        value_threshold = threshold[1:] if len(threshold) > 2 else None
        logging.info('调用自动控制-温度')
        if prefix_threshold == '>':
            if float(groups[1]) > float(value_threshold):
                # 发送数据给esp
                if STATUS['cur_relay_state'].get('00', 'NODATA') == '1' and operator == '关':
                    send_msg_by_name(esp_clients, 'close:0', 'esp02_relay')
                elif STATUS['cur_relay_state'].get('00', 'NODATA') == '0' and operator == '开':
                    send_msg_by_name(esp_clients, 'open:0', 'esp02_relay')

        elif prefix_threshold == '<':
            if float(groups[1]) < float(value_threshold):
                # 发送数据给esp
                if STATUS['cur_relay_state'].get('00', 'NODATA') == '1' and operator == '关':
                    send_msg_by_name(esp_clients, 'close:0', 'esp02_relay')
                elif STATUS['cur_relay_state'].get('00', 'NODATA') == '0' and operator == '开':
                    send_msg_by_name(esp_clients, 'open:0', 'esp02_relay')
    logging.info(STATUS['last_time_data'])
    l_tmp_value = STATUS['last_time_data'].get('l_tmp_value', 0)

    offset = float(groups[1]) - float(l_tmp_value)
    if abs(offset) <= 2:
        logging.info('【温】度值相差不大于2, 不保存, l_tmp_value={}, 现在的数据={}'.format(l_tmp_value, groups[1]))
    else:
        # 保存
        db_sqlite.save_data(groups[0], groups[1])
        STATUS['last_time_data']['l_tmp_value'] = groups[1]


@reroute(r'^01_(2.{1})_10_(\d*)')
def humidity_value(client, mqtt_client, esp_clients, data, groups):
    """
    01_20_10_54.00 湿度
    :param client:
    :param data:
    :param groups:
    :return:
    """
    logging.info('湿度传感器:{}, id:{}, value:{}'.format(data, groups[0], groups[1]))
    water_ctl_hum = STATUS['cur_auto_ctl'].get('water_ctl_hum', {})
    threshold = water_ctl_hum.get('threshold', None)
    operator = water_ctl_hum.get('operator', None)
    if water_ctl_hum.get('status') == True and operator:
        prefix_threshold = threshold[0] if len(threshold) > 2 else None
        value_threshold = threshold[1:] if len(threshold) > 2 else None
        if prefix_threshold == '>':
            if float(groups[1]) > float(value_threshold):
                # 发送数据给esp
                if STATUS['cur_relay_state'].get('01', 'NODATA') == '1' and operator == '关':
                    send_msg_by_name(esp_clients, 'close:1', 'esp02_relay')
                elif STATUS['cur_relay_state'].get('01', 'NODATA') == '0' and operator == '开':
                    send_msg_by_name(esp_clients, 'open:1', 'esp02_relay')

        elif prefix_threshold == '<':
            if float(groups[1]) < float(value_threshold):
                # 发送数据给esp
                if STATUS['cur_relay_state'].get('01', 'NODATA') == '1' and operator == '关':
                    send_msg_by_name(esp_clients, 'close:1', 'esp02_relay')
                elif STATUS['cur_relay_state'].get('01', 'NODATA') == '0' and operator == '开':
                    send_msg_by_name(esp_clients, 'open:1', 'esp02_relay')

    l_hum_value = STATUS['last_time_data'].get('l_hum_value', 0)

    offset = float(groups[1]) - float(l_hum_value)
    if abs(offset) <= 10:
        logging.info('湿度值相差不大于10, 不保存, l_hum_value={}, 当前数据={}'.format(l_hum_value, groups[1]))
    else:
        # 保存
        db_sqlite.save_data(groups[0], groups[1])
        STATUS['last_time_data']['l_hum_value'] = groups[1]


@reroute(r'01_(3.{1})_10_(\d*)')
def mq2_value(client, mqtt_client, esp_clients, data, groups):
    """
    01_30_10_120 MQ2
    :param client:
    :param data:
    :param groups:
    :return:
    """
    logging.info('MQ2传感器:{}, id:{}, value:{}'.format(data, groups[0], groups[1]))
    l_mq2 = STATUS['last_time_data'].get('mq2_value', 0)
    # 上次不危险这次危险才需要发送
    if STATUS['email'].get('is_open', False):
        if int(l_mq2) < 200:
            if int(groups[1]) > 200:
                content = """您好，在{} 的时候，检测到可燃气体异常，异常值为{}，请尽快检查问题，如果您知道这个警告发生的原因，请忽略。""".\
                    format(datetime.datetime.now().strftime('%Y年%m月%d日 %H时%M分'), groups[1])
                for i in STATUS['email'].get('data', []):
                    if i.strip() == '': continue
                    logging.error('发送邮件给{}'.format(i))
                    send_mail(i, "MQ2可燃气体警告", content=content)

    STATUS['last_time_data']['mq2_value'] = groups[1]


@reroute(r'01_(4.{1})_10_(\d*)')
def light_value(client, mqtt_client, esp_clients, data, groups):
    """
    01_40_10_54.00 光照
    :param client:
    :param data:
    :param groups:
    :return:
    """
    logging.info('光照值:{}, id:{}, value:{}'.format(data, groups[0], groups[1]))



@mqtt_reroute(r'open:\d*')
def open_msg(mqtt_client, esp_clients, data):
    logging.info('open_msg->', data)
    for i in esp_clients:
        i.send_msg(data)


@mqtt_reroute(r'close:\d*')
def close_msg(mqtt_client, esp_clients, data):
    logging.info('close_msg->', data)
    for i in esp_clients:
        i.send_msg(data)


@mqtt_reroute(r'query_auto_ctl_cfg')
def query_autoctl_msg(mqtt_client, esp_clients, data):
    logging.info('autoctl_msg: query_auto_ctl_cfg}')
    try:
        d = json.dumps(STATUS['cur_auto_ctl'])
    except Exception as e:
        logging.error(e)
    else:
        mqtt_client.send_msg('autoctl:'+d)


@mqtt_reroute('autoctl:(.*)')
def autoctl_upload(mqtt_client, esp_clients, data, groups):
    logging.info('autoctl_upload: {}'.format( groups[0]))
    try:
        o = json.loads(groups[0])
    except Exception as e:
        logging.warning(e)
    else:
        STATUS['cur_auto_ctl'] = o
        db_sqlite.save_auto_ctl(groups[0])
        on_status_update()


@mqtt_reroute(r'query_relay_state')
def query_relay_state(mqtt_client, esp_clients, data):
    logging.info('relay_state: query_relay_state')
    for i in esp_clients:
        i.send_msg('query_relay_state')


@mqtt_reroute(r'query_history_data:(.*)')
def query_history_data(mqtt_client, esp_clients, data, groups):
    logging.info('query_history_data: ', groups[0])
    try:
        o = json.loads(groups[0])
    except Exception as e:
        logging.warning(e)
        return
    today = datetime.datetime.now().strftime('%Y-%m-%d')
    count, history_data = db_sqlite.query_history_data(o.get('page', 1), o.get('size', 10),
                                                       o.get('date', today))

    send_data = {"count": count, "history_data": history_data}
    try:
        send_data = json.dumps(send_data)
    except Exception as e:
        send_data = '{}'
        logging.warning(e)
    send_data = 'query_history_data:' + send_data
    mqtt_client.send_msg(send_data)


@mqtt_reroute(r'query_email')
def query_email(mqtt_client, esp_clients, data):
    logging.info('query_email')
    try:
        d = json.dumps(STATUS['email'])
    except Exception as e:
        logging.error(e)
    else:
        mqtt_client.send_msg('email:'+d)


@mqtt_reroute(r'email:(.*)')
def upload_email(mqtt_client, esp_clients, data, groups):
    logging.info('upload_email')
    try:
        d = json.loads(groups[0])
    except Exception as e:
        logging.warning(e)
    else:
        if type(d.get('data', None)) != list:
            logging.warning('上传的邮件不是list格式')
            return
        STATUS['email'] = d
        db_sqlite.save_email(groups[0])


