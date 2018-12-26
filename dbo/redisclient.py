# --*-- coding:utf-8 --*--
import redis
import logging

logger = logging.getLogger("log")


class RedisClient(object):

    def __init__(self, **kwargs):
        """
        Args:
            host: str, Redis ip/hostname
            port, int, Redis port
            db: int, Redis default database
            password: int(optional)
        """
        if kwargs:
            self.pool = redis.ConnectionPool(**kwargs)
        else:
            raise Exception("redis 初始化参数不能为空")
        self.client = redis.Redis(connection_pool=self.pool, socket_timeout=1.0, socket_connect_timeout=1.0)

    def get_client(self):
        return self.client

    def get_list_lpop(self, list_name):
        """
        获取所有的list 队列里取出第一个
        :param list_name:
        :return:
        """
        succ = False
        item = None
        try:
            item = self.client.lpop(list_name)
            if item:
                item = item.decode("utf-8")
            succ = True
        except Exception as e:
            logger.exception(str(e))
        return succ, item

    def add_list_data(self, list_name, data):
        suc = False
        try:

            self.client.rpush(list_name, data)
            suc = True
        except Exception as e:
            logger.exception(str(e))
        return suc

    def get_list_len(self, list_name):
        data = None
        try:
            data = self.client.llen(list_name)
        except Exception as e:
            logger.exception(str(e))
        return data

    def del_list_data(self, list_name):
        data = None
        try:
            data = self.client.delete(list_name)
        except Exception as e:
            logger.exception(str(e))
        return data


redis_client = None


def init_redis_client(**param):
    """初始化redis"""
    global redis_client
    redis_client = RedisClient(**param)


# redis_global = RedisClient()
# redis_tiger_local = RedisClient(**redis_config_tiger_local)
# redis_tiger_remote = RedisClient(**redis_config_tiger_remote)
# redis_local = RedisClient(**redis_config_loacl)


