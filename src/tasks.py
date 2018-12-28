import uuid
import time
import datetime

g_tasks = dict()
g_late_task = dict()


def late_task(time_offset):
    def func1(func):
        fun_id = 'func_late_task:' + str(uuid.uuid4())
        g_late_task[fun_id] = {'time': time.time()+time_offset, 'cb': func}

    return func1


def add_late_task(time_offset, cb):
    fun_id = 'func_late_task:' + str(uuid.uuid4())
    g_late_task[fun_id] = {'time': time.time() + time_offset, 'cb': cb}


def task(start_time, end_time, every_day=True):
    def func1(func):
        fun_id = 'func_task_'+str(uuid.uuid4())
        g_tasks[fun_id] = {'start_time': start_time, 'end_time': end_time, 'callback': func, 'every_day': every_day}

    return func1


@task('13:28', '13:35')
def test():
    print('test data')


def set_task(fun_id, start_time, end_time, cb, every_day=True):
    g_tasks[fun_id] = {'start_time': start_time, 'end_time': end_time, 'callback': cb, 'every_day': every_day}


if __name__ == '__main__':

    cur_time = '2018-12-10 12:00'

    for k in g_tasks:
        # if cur_time != k:
        #     continue
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
