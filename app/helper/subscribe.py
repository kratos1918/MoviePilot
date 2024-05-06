from threading import Thread
from typing import List

from cachetools import TTLCache, cached

from app.db.subscribe_oper import SubscribeOper
from app.db.systemconfig_oper import SystemConfigOper
from app.schemas.types import SystemConfigKey
from app.utils.http import RequestUtils
from app.utils.singleton import Singleton


class SubscribeHelper(metaclass=Singleton):
    """
    订阅数据统计
    """

    _sub_reg = "https://movie-pilot.org/subscribe/add"

    _sub_report = "https://movie-pilot.org/subscribe/report"

    _sub_statistic = "https://movie-pilot.org/subscribe/statistic"

    def __init__(self):
        self.systemconfig = SystemConfigOper()
        if not self.systemconfig.get(SystemConfigKey.SubscribeReport):
            if self.sub_report():
                self.systemconfig.set(SystemConfigKey.SubscribeReport, "1")

    @cached(cache=TTLCache(maxsize=10, ttl=1800))
    def get_statistic(self, stype: str, page: int = 1, count: int = 30) -> List[dict]:
        """
        获取订阅统计数据
        """
        res = RequestUtils(timeout=15).get_res(self._sub_statistic, params={
            "stype": stype,
            "page": page,
            "count": count
        })
        if res and res.status_code == 200:
            return res.json()
        return []

    def sub_reg(self, sub: dict) -> bool:
        """
        新增订阅统计
        """
        res = RequestUtils(timeout=5, headers={
            "Content-Type": "application/json"
        }).post_res(self._sub_reg, json=sub)
        if res and res.status_code == 200:
            return True
        return False

    def sub_reg_async(self, sub: dict) -> bool:
        """
        异步新增订阅统计
        """
        # 开新线程处理
        Thread(target=self.sub_reg, args=(sub,)).start()
        return True

    def sub_report(self) -> bool:
        """
        上报存量订阅统计
        """
        subscribes = SubscribeOper().list()
        if not subscribes:
            return True
        res = RequestUtils(content_type="application/json",
                           timeout=10).post(self._sub_report,
                                            json={
                                                "subscribes": [
                                                    {
                                                        "name": sub.name,
                                                        "year": sub.year,
                                                        "type": sub.type,
                                                        "tmdbid": sub.tmdbid,
                                                        "imdbid": sub.imdbid,
                                                        "tvdbid": sub.tvdbid,
                                                        "doubanid": sub.doubanid,
                                                        "bangumiid": sub.bangumiid,
                                                        "season": sub.season,
                                                        "poster": sub.poster,
                                                        "backdrop": sub.backdrop,
                                                        "vote": sub.vote,
                                                        "description": sub.description
                                                    } for sub in subscribes
                                                ]
                                            })
        return True if res else False
