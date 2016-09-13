# -*- coding: utf-8 -*-
__author__ = 'Hipeace86'

import os
import tornado.web
from libs.urlmap import urlmap
import webui.Handlers
from webui.libs.Jinja import JinjaLoader


class Application(tornado.web.Application):

    def __init__(self):
        settings = dict(
            static_path=os.path.join(os.path.dirname(__file__), "static"),
            template_path=os.path.join(os.path.dirname(__file__), "templates"),
            template_loader=JinjaLoader(os.path.join(
                os.path.dirname(__file__), 'templates/'))
        )
        super(Application, self).__init__(
            tuple(urlmap.handlers), **settings)
        tornado.ioloop.PeriodicCallback(self._ping_db, 4 * 3600 * 1000).start()

    def _ping_db(self):
        self.db.execute('show variables')
        self.db.close_all()


def make_app():
    return Application()

if __name__ == "__main__":
    import tornado.ioloop
    app = make_app()
    app.listen(8888)
    tornado.ioloop.IOLoop.current().start()
