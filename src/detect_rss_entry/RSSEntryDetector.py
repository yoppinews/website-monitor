# -*- coding: utf-8 -*-

from __future__ import annotations

import re
import json
import hashlib
import feedparser
import dataclasses

from abc import *
from typing import Optional, List
from logging import Logger
from botocore.exceptions import ClientError
from WebDriverWrapper import WebDriverWrapper


@dataclasses.dataclass(frozen=True)
class RSSEntry:
    url: str
    title: str


class RSSEntries(metaclass=ABCMeta):
    @abstractmethod
    def has_checked(self, feed_url: str, entry_url: Optional[str] = None) -> bool:
        pass

    @abstractmethod
    def check(self, feed_url: str, entry_url: Optional[str]):
        pass


class RSSEntriesOnS3(RSSEntries):
    def __init__(self, s3_bucket, logger: Logger):
        self._bucket = s3_bucket
        self._logger = logger

    @staticmethod
    def _object_key(feed_url: str, entry_url: Optional[str]):
        object_key = hashlib.sha256(feed_url.encode()).hexdigest()
        if entry_url:
            entry_url_hash = hashlib.sha256(entry_url.encode()).hexdigest()
            object_key = f'{object_key}/{entry_url_hash}'
        return object_key

    def has_checked(self, feed_url: str, entry_url: Optional[str] = None) -> bool:
        try:
            self._bucket.Object(RSSEntriesOnS3._object_key(feed_url, entry_url)).get()
            return True
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code != 'NoSuchKey':
                raise e
            return False

    def check(self, feed_url: str, entry_url: Optional[str]):
        object_key = RSSEntriesOnS3._object_key(feed_url, entry_url)
        self._logger.info(json.dumps({
            'event': 'web-monitor:WebsiteRevisionsOnS3:update',
            'details': {
                'feed_url': feed_url,
                'entry_url': entry_url,
                'object_key': object_key,
            }
        }, ensure_ascii=False))
        self._bucket.Object(object_key).put(
            Body='',
            ContentEncoding='utf-8',
            ContentType='text/plane'
        )


class RSSNewEntryDetector:
    def __init__(self, entries: RSSEntries):
        self._entries = entries

    def detect_new_entries(self, feed_url: str) -> List[RSSEntry]:
        entries = []
        is_new_feed = True
        res = feedparser.parse(feed_url)
        for entry in res.entries:
            if self._entries.has_checked(feed_url, entry.link):
                is_new_feed = False
                continue
            self._entries.check(feed_url, entry.link)
            entries.append(RSSEntry(entry.link, entry.title))
        return entries if not is_new_feed else []


class RelatedRSSEntryDetector:
    def __init__(self, driver: WebDriverWrapper):
        self._driver = driver

    def matched_keyword(self, entry: RSSEntry, selector: str, keywords: List[str]) -> Optional[str]:
        for k in keywords:
            if re.findall(k, entry.title):
                return k
        text = self._driver.find_element(entry.url, selector).selected_text
        for k in keywords:
            if re.findall(k, text):
                return k
        return None
