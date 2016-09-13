# -*- coding: utf-8 -*-
__author__ = 'Hipeace86'

import tornado


class BaseHandler(tornado.web.RequestHandler):

    @property
    def db(self):
        return self.application.db

    @property
    def rpc(self):
        return self.application.scheduler_rpc
