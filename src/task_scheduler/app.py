# -*- coding: utf-8 -*-

from __future__ import annotations

import os
import json
import boto3
import logging
import dataclasses

from WebMonitorConfig import WebMonitorConfig
from WebMonitor import DetectWebsiteChangesEvent, DetectRSSEntryEvent

stage = os.environ['Stage']
config_bucket = os.environ['ConfigBucket']
config_key_name = os.environ['ConfigKeyName']
detect_website_changes_topic = os.environ['DetectWebsiteChangesTopic']
detect_rss_entry_topic = os.environ['DetectRSSEntryTopic']


@dataclasses.dataclass(frozen=True)
class TaskSchedulerConfig:
    sns_client: any
    detect_website_changes_topic: str
    detect_rss_entry_topic: str
    logger: logging.Logger


def lambda_handler(_, __) -> dict:
    logger = logging.getLogger(__name__)
    handler = logging.StreamHandler()
    log_level = getattr(logging, 'INFO', None)
    handler.setLevel(log_level)
    logger.setLevel(log_level)
    logger.handlers = [handler]
    logger.propagate = False

    monitor_config = WebMonitorConfig.initialize(config_bucket, config_key_name)

    sns = boto3.client('sns')
    task_config = TaskSchedulerConfig(sns, detect_website_changes_topic, detect_rss_entry_topic, logger)

    return handle(monitor_config, task_config)


def handle(monitor_config: WebMonitorConfig, task_config: TaskSchedulerConfig) -> dict:
    for site in monitor_config.site_targets:
        e = DetectWebsiteChangesEvent(site.url, site.selector, site.title)
        notify_message(
            task_config.sns_client,
            task_config.detect_website_changes_topic,
            dataclasses.asdict(e),
            task_config.logger
        )
    for rss in monitor_config.rss_targets:
        keywords = monitor_config.keywords.copy()
        keywords.extend(rss.keywords)
        e = DetectRSSEntryEvent(rss.url, rss.selector, keywords)
        notify_message(
            task_config.sns_client,
            task_config.detect_rss_entry_topic,
            dataclasses.asdict(e),
            task_config.logger
        )
    return {}


def notify_message(sns, topic: str, message: dict, logger: logging.Logger):
    j = json.dumps(message, ensure_ascii=False)
    res = sns.publish(
        TopicArn=topic,
        Message=j,
    )
    logger.info(json.dumps({
        'event': 'web_monitor:notify_message:message_id',
        'details': {'message': message, 'return': res}
    }, ensure_ascii=False))
