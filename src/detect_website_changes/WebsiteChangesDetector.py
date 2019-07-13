# -*- coding: utf-8 -*-

from __future__ import annotations

import json
import hashlib

from abc import *
from typing import Optional
from logging import Logger
from botocore.exceptions import ClientError
from WebDriverWrapper import WebDriverWrapper

from WebMonitor import DetectWebsiteChangesResult


class WebsiteRevisions(metaclass=ABCMeta):
    @abstractmethod
    def get(self, url: str, selector: str) -> Optional[str]:
        pass

    @abstractmethod
    def update(self, url: str, selector: str, selected_source: str):
        pass


class WebsiteRevisionsOnS3(WebsiteRevisions):
    def __init__(self, s3_bucket, logger: Logger):
        self._bucket = s3_bucket
        self._logger = logger

    @staticmethod
    def _object_key(url: str, selector: str):
        return hashlib.sha256(f'{url}::{selector}'.encode()).hexdigest()

    def get(self, url: str, selector: str) -> Optional[str]:
        try:
            res = self._bucket.Object(WebsiteRevisionsOnS3._object_key(url, selector)).get()
            return res['Body'].read().decode('utf-8')
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code != 'NoSuchKey':
                raise e
            return None

    def update(self, url: str, selector: str, selected_source: str):
        object_key = WebsiteRevisionsOnS3._object_key(url, selector)
        self._logger.info(json.dumps({
            'event': 'web-monitor:WebsiteRevisionsOnS3:update',
            'details': {
                'url': url,
                'selector': selector,
                'object_key': object_key,
            }
        }, ensure_ascii=False))
        self._bucket.Object(object_key).put(
            Body=selected_source.encode('utf-8'),
            ContentEncoding='utf-8',
            ContentType='text/plane'
        )


class WebsiteChangesDetector:
    def __init__(self, driver: WebDriverWrapper, revisions: WebsiteRevisions):
        self._driver = driver
        self._revisions = revisions

    def detect_changes(self, url: str, selector: str, title: Optional[str]) -> DetectWebsiteChangesResult:
        current = self._driver.find_element(url, selector)
        latest_revision = self._revisions.get(url, selector)
        has_changed = current.selected_text != latest_revision
        if has_changed:
            self._revisions.update(url, selector, current.selected_text)
        return DetectWebsiteChangesResult(
            url=current.url,
            selector=current.selector,
            title=title or current.title,
            has_changed=has_changed,
            text_previous=latest_revision,
            text_current=current.selected_text,
        )
