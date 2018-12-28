import sqlite3
import orangepi_config
import json
import datetime
import logging


class DB(object):
    def __init__(self):
        self._conn = sqlite3.connect(orangepi_config.DB_NAME)
        logging.info('open {} db success.'.format(orangepi_config.DB_NAME))
        self._init_sqlite()

    @property
    def conn(self):
        return self._conn

    def _init_sqlite(self):
        c = self._conn.cursor()
        c.execute(
            """create table if not exists tb_autoctl(id integer AUTO_INCREMENT, key text not null, value text not null, PRIMARY KEY(key));""")
        c.execute(
            """create table if not exists tb_historydata(id integer AUTO_INCREMENT, sensorid text not null, value text not null, time text not null, PRIMARY KEY(id));""")
        # c.execute("""create table if not exists tb_email(id integer auto_increment, email text not null, primary key(email));""")

        self._conn.commit()

    def query_auto_ctl(self):
        c = self._conn.cursor()
        c.execute("""select value from tb_autoctl where key=?""", ("autoctl",))
        res = c.fetchall()
        self._conn.commit()
        if len(res) == 1:
            cur_auto_ctl = json.loads(res[0][0])
            logging.info('auto_ctl: ', cur_auto_ctl)
            return cur_auto_ctl
        return {}

    def query_email(self):
        c = self._conn.cursor()
        c.execute("""select value from tb_autoctl where key=?""", ("email",))
        res = c.fetchall()
        self._conn.commit()
        if len(res) == 1:
            email = json.loads(res[0][0])
            logging.info('email: ', email)
            return email
        return {}

    def save_email(self, value):
        c = self._conn.cursor()
        try:
            c.execute('replace into tb_autoctl(key, value) values ("email", ?)', (value,))
            self._conn.commit()
        except Exception as e:
            logging.error(e)
            return False
        else:
            return True
        finally:
            c.close()

    def save_auto_ctl(self, value):
        c = self._conn.cursor()
        try:
            c.execute('replace into tb_autoctl(key, value) values ("autoctl", ?)', (value,))
            self._conn.commit()
        except Exception as e:
            logging.error(e)
            return False
        else:
            return True
        finally:
            c.close()

    def save_data(self, sensor_id, value, time=datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')):
        try:
            c = self._conn.cursor()
            time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            c.execute("""insert into tb_historydata(sensorid,value,time) values (?, ?,?)""", (sensor_id, value, time))

        except Exception as e:
            logging.error(e)
        else:
            logging.info('保存到数据库: {}, {}'.format(sensor_id, value))
            self._conn.commit()

    def query_history_data(self, page, size, date)->(int, []):
        if type(page) == str:
            page = int(page)
        if type(size) == str:
            size = int(size)
        # query begin 1
        page = page - 1
        c = self._conn.cursor()
        try:
            c.execute("""select count(*) from tb_historydata where time like ?;""", (date+'%',))
        except Exception as e:
            logging.error(e)
            return 0, []
        count = c.fetchone()

        count = count[0]

        # 计算分页
        if count == 0:
            return 0, []

        # page_count =  count / size  # 100/10 = 10

        offset_start = page * size

        c.execute("""select sensorid,value,time from tb_historydata where time like ? limit ?,?;""", (date+'%',offset_start, offset_start+size,))
        data = c.fetchall()
        return count, data
