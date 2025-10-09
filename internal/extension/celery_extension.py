from flask import Flask
from celery import Task, Celery


def init_app(app:Flask):
    """初始化celery"""
    class FlaskTask(Task):
        """保证celery在flask应用的的上下文可以访问到"""
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)


    # 创建celery应用并配置
    celery_app = Celery(app.name, task_cls=FlaskTask)
    celery_app.config_from_object(app.config["CELERY"])
    celery_app.set_default()

    # 挂载
    app.extensions["celery"] = celery_app