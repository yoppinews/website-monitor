# -*- coding: utf-8 -*-

from __future__ import annotations

import os
import json
import boto3
import logging
import dataclasses
from typing import Optional

from WebMonitor import DetectWebsiteChangesEvent
from WebsiteChangesDetector import WebsiteRevisionsOnS3
from WebsiteChangesDetector import WebsiteChangesDetector, DetectWebsiteChangesResult
from WebDriverWrapper import WebDriverWrapper

stage = os.environ['Stage']
bucket_name = os.environ['WebMonitorBucket']
next_topic = os.environ['NextTopic']
bucket = boto3.resource('s3').Bucket(bucket_name)
detector: Optional[WebsiteChangesDetector] = None


@dataclasses.dataclass(frozen=True)
class DetectWebsiteChangesConfig:
    sns_client: any
    next_topic: str
    logger: logging.Logger


def lambda_handler(event, _) -> dict:
    logger = logging.getLogger(__name__)
    handler = logging.StreamHandler()
    log_level = getattr(logging, 'INFO', None)
    handler.setLevel(log_level)
    logger.setLevel(log_level)
    logger.handlers = [handler]
    logger.propagate = False

    try:
        record = event['Records'][0]
        sns = record['Sns']
        message_id = sns['MessageId']
        message = json.loads(sns['Message'])
        logger.info(json.dumps({
            'event': 'web-monitor:detect_website_changes:lambda_handler',
            'details': {
                'message_id': message_id,
                'message': message,
            }
        }, ensure_ascii=False))
        e = DetectWebsiteChangesEvent.from_message(message)
        global detector
        if detector is None:
            driver = WebDriverWrapper()
            revisions = WebsiteRevisionsOnS3(bucket, logger)
            detector = WebsiteChangesDetector(driver, revisions)
        sns_client = boto3.client('sns')
        config = DetectWebsiteChangesConfig(sns_client, next_topic, logger)
        result = dataclasses.asdict(handle(e, detector, config))
        logger.info(json.dumps({
            'event': 'web-monitor:detect_website_changes:lambda_handler:result',
            'details': {
                'result': result,
            }
        }, ensure_ascii=False))
        return result
    except KeyError as e:
        logger.info(json.dumps({
            'event': 'web-monitor:detect_website_changes:lambda_handler:error',
            'details': {
                'message': e.__str__(),
            }
        }, ensure_ascii=False))


def handle(
    event: DetectWebsiteChangesEvent,
    changes_detector: WebsiteChangesDetector,
    config: DetectWebsiteChangesConfig
) -> DetectWebsiteChangesResult:
    result = changes_detector.detect_changes(event.url, event.selector, event.title)
    if result.has_changed and result.text_previous is not None:
        notify_message(config.sns_client, config.next_topic, dataclasses.asdict(result), config.logger)
    return result


def notify_message(sns, topic: str, message: dict, logger: logging.Logger):
    j = json.dumps(message, ensure_ascii=False)
    res = sns.publish(
        TopicArn=topic,
        Message=j,
    )
    logger.info(json.dumps({
        'event': 'web-monitor:detect_website_changes:notify_message:message_id',
        'details': {'message': message, 'return': res}
    }, ensure_ascii=False))
