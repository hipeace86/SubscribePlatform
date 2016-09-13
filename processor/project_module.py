import six
import imp
import logging
import inspect
import linecache
import time
from libs.log import SaveLogHandler, LogFormatter

logger = logging.getLogger("processor")


class ProjectManager(object):

    @staticmethod
    def build_module(objProject, env={}):
        '''Build project script as module'''
        from libs import baseworker
        # assert 'name' in project, 'need name of project'
        # assert 'script' in project, 'need script of project'

        env = dict(env)
        env.update({
            'debug': objProject.get('Status','DEBUG') == 'DEBUG',
        })

        loader = ProjectLoader(objProject)
        module = loader.load_module(objProject.get('ProjectName'))

        # logger inject
        module.log_buffer = []
        module.logging = module.logger = logging.Logger(objProject.get('ProjectName'))
        if env.get('enable_stdout_capture', True):
            handler = SaveLogHandler(module.log_buffer)
            handler.setFormatter(LogFormatter(color=False))
        else:
            handler = logging.StreamHandler()
            handler.setFormatter(LogFormatter(color=True))
        module.logger.addHandler(handler)

        if '__handler_cls__' not in module.__dict__:
            BaseWorker = module.__dict__.get(
                'BaseWorker', baseworker.BaseWorker)
            for each in list(six.itervalues(module.__dict__)):
                if inspect.isclass(each) and each is not BaseWorker \
                        and issubclass(each, BaseWorker):
                    module.__dict__['__handler_cls__'] = each
        _class = module.__dict__.get('__handler_cls__')
        assert _class is not None, "need BaseWorker in project module"

        instance = _class()
        instance.__env__ = env
        instance.project_name = objProject.get('ProjectName')
        instance.project = objProject

        return {
            'loader': loader,
            'module': module,
            'class': _class,
            'instance': instance,
            'exception': None,
            'exception_log': '',
            'info': objProject,
            'load_time': time.time(),
        }


class ProjectLoader(object):
    '''ProjectLoader class for sys.meta_path'''

    def __init__(self, project, mod=None):
        self.project = project
        self.name = project['ProjectName']
        self.mod = mod

    def load_module(self, fullname):
        if self.mod is None:
            self.mod = mod = imp.new_module(fullname)
        else:
            mod = self.mod
        mod.__file__ = '<%s>' % self.name
        mod.__loader__ = self
        mod.__project__ = self.project
        mod.__package__ = ''
        code = self.get_code(fullname)
        six.exec_(code, mod.__dict__)
        linecache.clearcache()
        return mod

    def is_package(self, fullname):
        return False

    def get_code(self, fullname):
        return compile(self.get_source(fullname), '<%s>' % self.name, 'exec')

    def get_source(self, fullname):
        script = self.project['Script']
        if isinstance(script, six.text_type):
            return script.encode('utf8')
        return script
