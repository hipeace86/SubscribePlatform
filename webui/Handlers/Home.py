# -*- coding: utf-8 -*-
__author__ = 'Hipeace86'

from webui.libs.BaseHandler import BaseHandler
from webui.libs.urlmap import urlmap
from webui.Entity.Project import Project
from libs import defaultworker
import time
import inspect


@urlmap(r'/')
class HomeHandler(BaseHandler):

    def get(self):
        projects = self.db.query(Project).all()
        self.render('home.html', **{'projects': projects})

    def post(self):
        try:
            url = self.get_argument('notifyUrl', '')
            note = self.get_argument('note', '')
            project = self.get_argument('project', '')
            default_script = inspect.getsource(defaultworker)
            default_script = default_script.replace(
                "__TIME__", time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())).\
                replace('__URL__', url).replace(
                    '__NAME__', project)

            objProject = Project()
            objProject.ProjectName = project
            objProject.Desc = note
            objProject.Script = default_script
            objProject.Url = url
            objProject.Status = 2
            objProject.LastUpdate = int(time.time())
            self.db.add(objProject)
            self.db.commit()
            self.redirect('/project/{0}'.format(project))
        except Exception as e:
            self.db.rollback()
            print e
            self.redirect('/')
