#coding=utf-8

"""
带有数据库连接池的数据
"""

from sqlalchemy import create_engine
import logging


logger = logging.getLogger("log")


class Dbpool(object):
    """
    数据库的链接
    """

    def __init__(self, **config):
        """
        :param config: 
        """
        if not config:
            raise Exception("初始化mysql时参数不能为空")

        host = config.get("host", "127.0.0.1")
        user = config.get("user", "root")
        passwd = config.get("passwd", "root")
        db = config.get("db", "fashion")
        charset = config.get("charset", "utf8")
        port = config.get("port", "3306")
        print("链接数据库:", config)
        self.engine = create_engine(
            "mysql+pymysql://" + user + ":" + passwd + "@" + host + ":" + port + "/" + db + "?charset=" + charset,
            pool_size=30, echo=False, pool_recycle=3600, encoding="utf-8")
        print("链接数据库: suc:", config)

    def get_conn(self):
        """
        获取 mysql 的链接
        :return: 
        """
        conn = None
        try:
            conn = self.engine.connect()
        except Exception as e:
            raise e
        return conn

    def execute_data(self, sql, *param):
        """
        执行sql 
        :param sql: mysql 语句 可以带%s
        :param param: tuple 
        :return: 
        """
        conn = None
        result = {}
        suc = False
        data = None
        error = None
        try:
            conn = self.get_conn()
            cur = None
            if param:
                cur = conn.execute(sql, param)
            else:
                cur = conn.execute(sql)
            if cur.returns_rows:
                data = cur.fetchall()
            suc = True
        except Exception as e:
            logger.error(sql+":"+str(param))
            error = str(e)
            logger.exception(str(e))
        finally:
            if conn:
                conn.close()
        result["suc"] = suc
        result["data"] = data
        result["error"] = error
        return result

    def select_execute(self, sql, *param):
        suc = False
        try:
            conn = self.get_conn()
            if param:
                cur = conn.execute(sql, param)
            else:
                cur = conn.execute(sql)
            if cur.returns_rows:
                data = cur.fetchall()
            suc = True
        except Exception as e:
            logger.error(sql+":"+str(param))
        finally:
            if conn:
                conn.close()
        return suc, data

    def delete_execute(self, sql, *param):
        suc = False
        try:
            conn = self.get_conn()
            if param:
                cur = conn.execute(sql, param)
            else:
                cur = conn.execute(sql)
            if cur.returns_rows:
                data = cur.fetchall()
            suc = True
        except Exception as e:
            logger.error(sql+":"+str(param))
        finally:
            if conn:
                conn.close()
        return suc


# db__al = Dbpool(**al_db_setting)
# db__tiger = Dbpool(**db_tiger_setting)
# db__tiger_local = Dbpool(**db_tiger_local_setting)
# db__tiger_remote = Dbpool(**db_tiger_remote_setting)

mysql_db_client = None


def init_mysql_db_client(**param):
    global mysql_db_client
    mysql_db_client = Dbpool(**param)


