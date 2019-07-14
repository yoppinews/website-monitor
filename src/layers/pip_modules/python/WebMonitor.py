# -*- coding: utf-8 -*-

from __future__ import annotations

import dataclasses
from typing import Optional, List


@dataclasses.dataclass(frozen=True)
class DetectWebsiteChangesEvent:
    url: str
    selector: Optional[str]
    title: Optional[str]

    @staticmethod
    def from_message(message: dict) -> Optional[DetectWebsiteChangesEvent]:
        try:
            return DetectWebsiteChangesEvent(
                url=message['url'],
                selector=message.get('selector', 'body'),
                title=message.get('title', None)
            )
        except KeyError:
            return None


@dataclasses.dataclass(frozen=True)
class DetectRSSEntryEvent:
    feed_url: str
    selector: str
    keywords: List[str]

    @staticmethod
    def from_message(message: dict) -> Optional[DetectRSSEntryEvent]:
        try:
            return DetectRSSEntryEvent(
                feed_url=message['feed_url'],
                selector=message.get('selector', 'body'),
                keywords=message['keywords']
            )
        except KeyError:
            return None


@dataclasses.dataclass(frozen=True)
class DetectWebsiteChangesResult:
    url: str
    selector: Optional[str]
    title: Optional[str]
    has_changed: bool = False
    text_previous: Optional[str] = None
    text_current: Optional[str] = None
    type: str = 'DetectWebsiteChangesResult'


@dataclasses.dataclass(frozen=True)
class DetectRSSEntryResult:
    url: str
    feed_url: str
    selector: Optional[str]
    title: str
    matched_keyword: str
    type: str = 'DetectRSSEntryResult'
