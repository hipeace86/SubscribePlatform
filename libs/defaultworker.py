#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Author: hipeace86<hipeace86@gmail.com>
# Created on __TIME__

from libs.baseworker import BaseWorker
from tornado.httpclient import HTTPClient
import logging

logger = logging.getLogger('fetcher')


class Worker(BaseWorker):

    def __init__(self):
        """
        `amqp` mq server connection string
        `exchange` which exchange to bind
        """
        super(Worker, self).__init__('__NAME__', **
                                     {"amqp": "amqp://guest:guest@localhost:5672/", 'exchange': "CiprunSubscribe"})

    def callback(self, ch, method, propertys, body):
        """
        consume main function
        If you are using HTTP for Api Server,you should note
        request method `GET` or `POST`

        If Api Server need auth or request header verification,
        you can modify `try` region code

        httpclient can be replaced by urllib or requests
        """
        super(Worker, self).callback(ch, method, propertys, body)
        try:
            httpClient = HTTPClient()
            httpClient.fetch(
                "__URL__", callback=self._on_result, method="POST", body={'msg': body})
            self.channel.basic_ack(delivery_tag=method.delivery_tag)
        except Exception as e:
            logger.error(str(e))

    def _on_result(self, response):
        """
        response.body: content of request to response
        response.code: http response code for the request returned
        """
        logger.info(response.body)
        self.saveresult()
        """
        Save `self.RecordDict` into database,if you don't need,
        please delete or comment above line

        You can custom the `self.RecordDict' dictionary
        keys `ProjectName` and `msg(current queue message)` already exists
        """
