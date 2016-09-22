import time
import logging
from libs import utils
from processor.project_module import ProjectManager


logger = logging.getLogger('scheduler')


class Scheduler(object):

    EXCEPTION_LIMIT = 3
    LOOP_INTERVAL = 0.1

    def __init__(self):
        self._quit = False
        self.projects = dict()

    def run_once(self):
        logger.info(time.time())

    def run(self):
        logger.info("loading projects")
        while not self._quit:
            try:
                time.sleep(self.LOOP_INTERVAL * 100)
                self.run_once()
                self._exceptions = 0
            except KeyboardInterrupt:
                break
            except Exception as e:
                print e
                self._exceptions += 1
                if self._exceptions > self.EXCEPTION_LIMIT:
                    break
                continue
        logger.info("scheduler exiting...")

    def quit(self):
        '''Set quit signal'''
        self._quit = True
        # stop xmlrpc server
        if hasattr(self, 'xmlrpc_server'):
            self.xmlrpc_ioloop.add_callback(self.xmlrpc_server.stop)
            self.xmlrpc_ioloop.add_callback(self.xmlrpc_ioloop.stop)

    def xmlrpc_run(self, port=23333, bind='127.0.0.1', logRequests=False):
        '''Start xmlrpc interface'''
        from libs.wsgi_xmlrpc import WSGIXMLRPCApplication

        application = WSGIXMLRPCApplication()

        application.register_function(self.quit, '_quit')

        # TODO:
        def new_project(objParams):
            try:
                ret = ProjectManager.build_module(objParams)
                project = {'worker': ret.get(
                    'instance'), 'process': utils.run_in_thread(ret.get('instance').run)}
                self.projects[objParams.get('ProjectName')] = project
                return True
            except Exception as e:
                logger.error(e)
            return False

        application.register_function(new_project, 'newproject')

        # TODO:
        def stop_project(projectName):
            try:
                project = self.projects.get(projectName)
                # project['worker'].pause()
                project['process'].terminate()
                logger.info('{0} stoped'.format(projectName))
                return True
            except Exception as e:
                logger.error(e)
            return False

        application.register_function(stop_project, 'stopproject')

        def start_project(objParams):
            try:
                if self.projects.get(objParams['ProjectName']):
                    project = self.projects.get(objParams['ProjectName'])
                    del project['worker']
                    project['process'].terminate()
                    project['process'].join(1)

                ret = ProjectManager.build_module(objParams)
                project = {'worker': ret.get(
                    'instance'), 'process': utils.run_in_subprocess(ret.get('instance').run)}
                self.projects[objParams.get('ProjectName')] = project
                return True
            except Exception as e:
                logger.error(e)
            return False

        application.register_function(start_project, 'startproject')

        import tornado.wsgi
        import tornado.httpserver

        container = tornado.wsgi.WSGIContainer(application)
        self.xmlrpc_ioloop = tornado.ioloop.IOLoop()
        self.xmlrpc_server = tornado.httpserver.HTTPServer(
            container, io_loop=self.xmlrpc_ioloop)
        self.xmlrpc_server.listen(port=port, address=bind)
        self.xmlrpc_ioloop.start()
