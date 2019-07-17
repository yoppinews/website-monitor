# -*- coding: utf-8 -*-

from __future__ import annotations

import os
import json
import boto3
import logging
import dataclasses
from typing import List

from WebMonitor import DetectRSSEntryEvent, DetectRSSEntryResult
from RSSEntryDetector import RSSNewEntryDetector, RelatedRSSEntryDetector, RSSEntriesOnS3
from WebDriverWrapper import WebDriverWrapper

stage = os.environ['Stage']
bucket_name = os.environ['WebMonitorBucket']
next_topic = os.environ['NextTopic']
bucket = boto3.resource('s3').Bucket(bucket_name)
detector = None


@dataclasses.dataclass(frozen=True)
class DetectRSSEntryConfig:
    sns_client: any
    next_topic: str
    logger: logging.Logger


def lambda_handler(event, _) -> object:
    logger = logging.getLogger(__name__)
    handler = logging.StreamHandler()
    log_level = getattr(logging, 'INFO', None)
    handler.setLevel(log_level)
    logger.setLevel(log_level)
    logger.handlers = [handler]
    logger.propagate = False

    record = event['Records'][0]
    sns = record['Sns']
    message_id = sns['MessageId']
    message = json.loads(sns['Message'])
    logger.info(json.dumps({
        'event': 'web-monitor:detect_rss_entry:lambda_handler',
        'details': {
            'message_id': message_id,
            'message': message,
        }
    }, ensure_ascii=False))
    e = DetectRSSEntryEvent.from_message(message)

    global detector
    related_entry_detector = detector
    if related_entry_detector is None:
        driver = WebDriverWrapper()
        related_entry_detector = RelatedRSSEntryDetector(driver)

    cache = RSSEntriesOnS3(bucket, logger)
    new_entry_detector = RSSNewEntryDetector(cache)

    sns_client = boto3.client('sns')
    config = DetectRSSEntryConfig(sns_client, next_topic, logger)
    result = handle(e, new_entry_detector, related_entry_detector, config)
    result_dic = [dataclasses.asdict(r) for r in result]
    logger.info(json.dumps({
        'event': 'web-monitor:detect_rss_entry:lambda_handler:result',
        'details': {
            'result': result_dic,
        }
    }, ensure_ascii=False))
    return result_dic


def handle(
    event: DetectRSSEntryEvent,
    new_entry_detector: RSSNewEntryDetector,
    related_entry_detector: RelatedRSSEntryDetector,
    config: DetectRSSEntryConfig
) -> List[DetectRSSEntryResult]:
    matched_entries = []
    entries = new_entry_detector.detect_new_entries(event.feed_url)
    entries_dic = [dataclasses.asdict(e) for e in entries]
    config.logger.info(json.dumps({
            'event': 'web-monitor:detect_rss_entry:handle:new_entries',
            'details': {
                'entries': entries_dic
            }
        }, ensure_ascii=False))
    for e in entries:
        matched_keyword = related_entry_detector.matched_keyword(e, event.selector, event.keywords)
        if matched_keyword:
            res = DetectRSSEntryResult(e.url, event.feed_url, event.selector, e.title, matched_keyword)
            matched_entries.append(res)
            notify_message(config.sns_client, config.next_topic, dataclasses.asdict(res), config.logger)
    return matched_entries


def notify_message(sns, topic: str, message: dict, logger: logging.Logger):
    j = json.dumps(message, ensure_ascii=False)
    res = sns.publish(
        TopicArn=topic,
        Message=j,
    )
    logger.info(json.dumps({
        'event': 'web-monitor:detect_rss_entry:notify_message:message_id',
        'details': {'message': message, 'return': res}
    }, ensure_ascii=False))
