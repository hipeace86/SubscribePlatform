# -*- coding: utf-8 -*-

__author__ = 'Hipeace86'
import inspect
from webui.libs.BaseHandler import BaseHandler
from webui.libs.urlmap import urlmap
from webui.Entity.Project import Project
from libs import defaultworker
from tornado.web import HTTPError
from tornado.web import asynchronous
import json
import time


@urlmap(r'/project/(.*)')
class ProjectHandler(BaseHandler):

    def get(self, projectName):
        try:
            objProject = self.db.query(Project).filter(
                Project.ProjectName == projectName).first()
            if not objProject:
                raise HTTPError(404)
            default_script = inspect.getsource(defaultworker)
            default_script = default_script.replace(
                "__TIME__", time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())).\
                replace('__URL__', objProject.Url).replace(
                    '__NAME__', objProject.ProjectName)
            default_script = objProject.Script if len(
                objProject.Script) > 100 else default_script

            self.render('project.html', **
                        {'defaultWorker': json.dumps(default_script), 'project': projectName, 'status': objProject.Status})
        except Exception as e:
            print str(e)


@urlmap(r'/ajax/(.*)/save')
class ProjectSaveHandler(BaseHandler):

    @asynchronous
    def post(self, project):
        objProject = self.db.query(Project).filter(
            Project.ProjectName == project).first()
        objProject.Script = self.get_argument('script', '')
        self.db.add(objProject)
        self.db.commit()
        self.finish({"status": 200, "msg": "ok"})


@urlmap(r'/ajax/(.*)/run')
class ProjectRunHandler(BaseHandler):

    @asynchronous
    def get(self, project):
        objProject = self.db.query(Project).filter(
            Project.ProjectName == project).first()
        objProject.Status = 1
        self.db.add(objProject)
        self.db.commit()
        try:
            self.rpc.startproject(objProject.to_dict())
            self.finish({'status': 200, "msg": "running"})
        except Exception as e:
            self.finish({'status': 500, "msg": str(e)})


@urlmap(r'/ajax/(.*)/stop')
class ProjectStopHandler(BaseHandler):

    @asynchronous
    def get(self, project):
        try:
            objProject = self.db.query(Project).filter(
                Project.ProjectName == project).first()
            objProject.Status = 2
            self.db.add(objProject)
            self.db.commit()

            self.rpc.stopproject(project)
            self.finish({'status': 200, "msg": "Stoped"})
        except Exception as e:
            self.finish({'status': 500, "msg": str(e)})
