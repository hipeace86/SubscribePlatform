#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Author: hipeace86<hipeace86@gmail.com>
# Created on 2016-08-19 15:50:30

import pika
import logging
import json
from libs.utils import md5string

logger = logging.getLogger('fetcher')


class BaseWorker(object):

    def __init__(self, projectName, **kwargs):
        if not kwargs.get('amqp'):
            raise BaseException("amqp backend not given")
        if not kwargs.get('exchange'):
            raise BaseException("exchange name not given")
        parameters = pika.URLParameters(kwargs.get('amqp'))
        self.connection = pika.BlockingConnection(parameters)
        self.channel = self.connection.channel()
        self._queue = md5string(projectName)
        self.channel.queue_declare(queue=self._queue)
        try:
            self.channel.exchange_declare(
                kwargs.get('exchange'), exchange_type='fanout', durable=True)
        except Exception as e:
            logger.warn(e)
        self.channel.queue_bind(exchange=kwargs.get('exchange'),
                                queue=self._queue)

        self.channel.basic_consume(self.callback, queue=self._queue)
        self._running = False
        self.active = True
        self.RecordDict = {'ProjectName': projectName}

    def callback(self, ch, method, propertys, body):
        self.RecordDict['msg'] = json.dumps(body)

    def run(self):
        if not self._running and self.active:
            try:
                self._running = True
                logger.info('{0} start consuming'.format(self._queue))
                self.channel.start_consuming()
            except KeyboardInterrupt as e:
                logger.warn('{0} exit with {1}'.format(self._queue, str(e)))

    def _on_result(self):
        pass

    def saveresult(self):
        try:
            from tasks.RecordTasks import SaveRecord
            SaveRecord.delay(self.RecordDict)
        except Exception as e:
            print e

    def updateWorker(self, project):
        pass

    def active(self):
        self.active = True

    def pause(self):
        try:
            self._running = False
            self.active = False
            # self.channel.stop_consuming()
            self.channel.cancel()
            self.channel.close()
            self.connection.close()
            logger.info('stop consuming:{0}'.format(self._queue))
        except Exception as e:
            logger.warn(e)
