from src.tasks import task, set_task, late_task, add_late_task
from .status import STATUS
from .tools import send_msg_by_name

import datetime
import logging

"""
{
    'water_ctl_time': {'start_time': '23:00', 'end_time': '34:00', 'operator': '开', 'status': True}, 
    'water_ctl_tmp: {'threshold': '34', 'operator': None, 'status': True}, 
    'water_ctl_hum': {'threshold': '99', 'operator': '关', 'status': True},
    'light_ctl_light': {'threshold': '99', 'operator': '关', 'status': True},
    'light_ctl_mq': {'threshold': '99', 'operator': '关', 'status': True},
}
"""

broker = None


def foo():
    send_msg_by_name(broker.arduino_clients, 'query_relay_state', 'arduino02_relay')
    send_msg_by_name(broker.arduino_clients, 'query_relay_state', 'arduino03_nodemcu')


def sc_init(b):
    global broker
    broker = b
    logging.debug('broker = {}'.format(broker))


def on_status_update():
    water_ctl_time = STATUS['cur_auto_ctl'].get('water_ctl_time', None)
    if water_ctl_time is None:
        logging.error('water_ctl_time is None')
        return
    s_time = water_ctl_time.get('start_time', 'NODATA')
    e_time = water_ctl_time.get('end_time', 'NODATA')
    try:
        datetime.datetime.strptime(s_time, '%H:%M')
        datetime.datetime.strptime(e_time, '%H:%M')
    except Exception as e:
        logging.error(e)
        return

    set_task('water_ctl_time', s_time, e_time, ctl_relay)


def ctl_relay():
    logging.error('达到时间段，控制继电器')
    water_ctl_time = STATUS['cur_auto_ctl'].get('water_ctl_time', None)
    if water_ctl_time is None:
        logging.error('water_ctl_time is None')
        return

    status = water_ctl_time.get('status', False)
    if status is False:
        return

    operator = water_ctl_time.get('operator', None)
    if operator is None:
        return

    # 发送数据给arduino
    if STATUS['cur_relay_state'].get('02', 'NODATA') == '1' and operator == '关':
        send_msg_by_name(broker.esp_clients, 'close:2', 'arduino03_nodemcu')
    elif STATUS['cur_relay_state'].get('02', 'NODATA') == '0' and operator == '开':
        send_msg_by_name(broker.esp_clients, 'open:2', 'arduino03_nodemcu')



