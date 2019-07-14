# -*- coding: utf-8 -*-

from __future__ import annotations

import yaml
import boto3
import datetime
import dataclasses
from typing import Optional, List


class WebMonitorConfig:
    def __init__(self, dic: dict):
        self._dic = dic

    @staticmethod
    def initialize(config_bucket: str, config_key_name: str) -> WebMonitorConfig:
        bucket = boto3.resource('s3').Bucket(config_bucket)
        timestamp = datetime.datetime.utcnow().timestamp()
        config_path = '/tmp/config.' + str(timestamp)
        bucket.download_file(config_key_name, config_path)
        f = open(config_path, "r")
        dic = yaml.load(f, Loader=yaml.SafeLoader)
        f.close()
        return WebMonitorConfig(dic)

    @property
    def site_template(self) -> str:
        return self._dic.get('message_format', {}).get('site_template')

    @property
    def rss_template(self) -> str:
        return self._dic.get('message_format', {}).get('rss_template')

    @property
    def site_targets(self) -> List[TargetWebsite]:
        targets = []
        items = self._dic.get('site_targets', [])
        for i in items:
            try:
                url = i['url']
                selector = i['selector']
                title = i.get('title', None)
                targets.append(TargetWebsite(url, selector, title))
            except KeyError:
                continue
        return targets

    @property
    def rss_targets(self) -> List[TargetRSS]:
        targets = []
        items = self._dic.get('rss_targets', [])
        for i in items:
            try:
                url = i['url']
                selector = i['selector']
                keywords = i.get('keywords', [])
                targets.append(TargetRSS(url, selector, keywords))
            except KeyError:
                continue
        return targets

    @property
    def keywords(self) -> List[str]:
        return self._dic.get('keywords', [])


@dataclasses.dataclass(frozen=True)
class TargetWebsite:
    url: str
    selector: Optional[str]
    title: Optional[str]


@dataclasses.dataclass(frozen=True)
class TargetRSS:
    url: str
    selector: Optional[str]
    keywords: List[str]
