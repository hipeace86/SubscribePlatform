#! -*- coding:utf-8 -*-
import logging
import json
from celery import Celery
from webui.Entity.Record import Record
from webui.libs.Route import makesession
import os

db = makesession(os.environ.get('sqlalchemy'))


app = Celery('Record', broker=os.environ.get('RecordBroker'))
app.conf.update(
    CELERY_TASK_SERIALIZER='json',
    CELERY_ACCEPT_CONTENT=['json'],
    CELERY_RESULT_SERIALIZER='json',
)

logger = logging.getLogger('fetcher')


@app.task
def SaveRecord(RecordDict):
    # TODO: save record to db
    objRecord = Record()
    objRecord.ProjectName = RecordDict['ProjectName']
    objRecord.RecordJson = json.dumps(RecordDict)
    db.add(objRecord)
    db.commit()
    logger.info(RecordDict)


def runCeleryTask():
    app.worker_main(
        ['worker', '-A', 'tasks.RecordTasks', '-l', 'info', '-n', 'RecordTasks'])
