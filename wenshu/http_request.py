import logging
logger = logging.getLogger()
import requests
import traceback
import threading


def get_ip():
    for i in range(3):
        try:
            mutex = threading.Lock()
            url = 'http://10.0.2.82/proxy/next/:wenshu.court.gov.cn'
            mutex.acquire()
            r = eval(requests.get(url=url).text)
            mutex.release()
            proxy = {'http': "http://" + str(r.get("ip")) + ":" + str(r.get("port"))}
            print(proxy)
            return proxy
            break
        except Exception:
            logger.info('获取动态代理异常')

header = {
          'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
          'Accept-Encoding': 'gzip, deflate',
          'Accept-Language': 'zh-Hans-CN, zh-Hans; q=0.5',
          'Connection': 'Keep-Alive',
          'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                        'Chrome/52.0.2743.116 Safari/537.36 Edge/15.15063'
        }


class Http():
    def __init__(self, wite_name):
        self.wite_name = wite_name
        self.charset = 'utf-8'
        self.session = requests.session()
        self.r = None
        self.content = None
        self.header = header

        logger.info('要抓取的网站:' + wite_name)

    def set_charset(self, charset):
        self.charshet = charset

    def http_request(self, method, url, **kwargs):
        try:
            logger.info(self.wite_name + '开始抓取链接' + url)
            self.r = self.session.request(method, url, timeout=60,  **kwargs)
        except Exception:
            m = traceback.format_exc()
            logger.error(self.wite_name +'抓取异常链接为' + url + '异常信息为:' + m)
            self.retry(method, url, **kwargs)

    def retry(self, method, url, **kwargs):
        suc =0
        for i in range(3):
            suc = 0
            logger.info(self.wite_name + '开始第' + str(i) + '次重新抓取链接' + url)
            try:
                self.r = self.session.request(method, url, timeout=40, **kwargs)
                if self.get_status_code == 200:
                    break
            except Exception:
                m = traceback.format_exc()
                if 'Caused by ProxyError' in m or 'Read timed out' in m:
                    suc = 1
                    break
                logger.error(self.wite_name + '链接抓取第' + str(i) + '次异常为' + url + '异常信息为:' + m)
                suc = 1
        return suc

    def parse_html(self):
        self.content = self.r.content.decode(self.charset, 'ignore').replace(u'\xa0', u'').replace('&nbsp;', '')\
            .replace(u'\xa9', u'')

    def parse_json(self):
        self.content = self.r.json()

    def get_cookie(self):
        return self.session.cookies

    def get_cookie_key(self, key):
        return self.session.cookies.get(key)

    def add_cookie(self,key, value):
        self.session.cookies.set(key, value)

    def get_status_code(self):
        return self.r.status_code
