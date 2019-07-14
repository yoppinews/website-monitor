# -*- coding: utf-8 -*-

from __future__ import annotations

import os
import json
import boto3
import string
import logging
import dataclasses

from WebMonitorConfig import WebMonitorConfig
from WebMonitor import DetectWebsiteChangesResult, DetectRSSEntryResult

stage = os.environ['Stage']
config_bucket = os.environ['ConfigBucket']
config_key_name = os.environ['ConfigKeyName']
tweet_topic = os.environ['TweetTopic']


@dataclasses.dataclass(frozen=True)
class HandleEventsConfig:
    sns_client: any
    tweet_topic: str
    logger: logging.Logger


def lambda_handler(event, __) -> dict:
    logger = logging.getLogger(__name__)
    handler = logging.StreamHandler()
    log_level = getattr(logging, 'INFO', None)
    handler.setLevel(log_level)
    logger.setLevel(log_level)
    logger.handlers = [handler]
    logger.propagate = False

    sns_client = boto3.client('sns')
    handle_config = HandleEventsConfig(sns_client, tweet_topic, logger)
    monitor_config = WebMonitorConfig.initialize(config_bucket, config_key_name)

    try:
        record = event['Records'][0]
        sns = record['Sns']
        message_id = sns['MessageId']
        message = json.loads(sns['Message'])
        logger.info(json.dumps({
            'event': 'web-monitor:handle_events:lambda_handler',
            'details': {
                'message_id': message_id,
                'message': message,
            }
        }, ensure_ascii=False))

        t = message['type']
        if t == 'DetectWebsiteChangesResult':
            e = DetectWebsiteChangesResult(**message)
            return handle_website_changes(e, monitor_config, handle_config)
        if t == 'DetectRSSEntryResult':
            e = DetectRSSEntryResult(**message)
            return handle_rss_entry(e, monitor_config, handle_config)
        return {}
    except KeyError as e:
        logger.info(json.dumps({
            'event': 'web-monitor:handle_events:lambda_handler:error',
            'details': {
                'message': e.__str__(),
            }
        }, ensure_ascii=False))


def handle_website_changes(
    event: DetectWebsiteChangesResult,
    monitor_config: WebMonitorConfig,
    handle_config: HandleEventsConfig
) -> dict:
    if event.has_changed and event.text_previous is not None:
        dic = {
            'title': event.title,
            'url': event.url,
        }
        template = string.Template(monitor_config.site_template)
        status = template.substitute(dic).strip("\"")
        tweet_message = {'status': status}
        notify_message(
            handle_config.sns_client,
            handle_config.tweet_topic,
            tweet_message,
            handle_config.logger
        )
    return {}


def handle_rss_entry(
    event: DetectRSSEntryResult,
    monitor_config: WebMonitorConfig,
    handle_config: HandleEventsConfig
) -> dict:
    dic = {
        'title': event.title,
        'url': event.url,
        'feed_url': event.feed_url,
        'selector': event.selector,
        'matched_keyword': event.matched_keyword,
    }
    template = string.Template(monitor_config.rss_template)
    status = template.substitute(dic).strip("\"")
    tweet_message = {'status': status}
    notify_message(
        handle_config.sns_client,
        handle_config.tweet_topic,
        tweet_message,
        handle_config.logger
    )
    return {}


def notify_message(sns, topic: str, message: dict, logger: logging.Logger):
    j = json.dumps(message, ensure_ascii=False)
    res = sns.publish(
        TopicArn=topic,
        Message=j,
    )
    logger.info(json.dumps({
        'event': 'web_monitor:handle_events:notify_message:message_id',
        'details': {'message': message, 'return': res}
    }, ensure_ascii=False))
