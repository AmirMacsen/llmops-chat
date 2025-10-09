import logging
import time
from uuid import UUID
from flask import current_app

from celery import shared_task


@shared_task
def demo_task(id:UUID)->str:
    """测试异步任务"""
    logging.info("睡眠5s")
    time.sleep(5)
    logging.info(f"id: {id}")
    logging.info(current_app.config)
    return "success"

