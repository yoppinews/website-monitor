# -*- coding: utf-8 -*-

from typing import List


class SiteConfig:
    def __init__(self, url: str, selector: str, title: str):
        self._url = url
        self._selector = selector
        self._title = title

    @property
    def url(self) -> str:
        return self._url

    @property
    def selector(self) -> str:
        return self._selector

    @property
    def title(self) -> str:
        return self._title


class RSSConfig:
    def __init__(self, url: str, selector: str, keywords: [str]):
        self._url = url
        self._selector = selector
        self._keywords = keywords

    @property
    def url(self) -> str:
        return self._url

    @property
    def selector(self) -> str:
        return self._selector

    @property
    def title(self) -> str:
        return self._keywords


class WebsiteMonitorConfig:
    @property
    def rss_targets(self) -> List[RSSConfig]:
        return []

    @property
    def website_targets(self) -> List[SiteConfig]:
        return []
