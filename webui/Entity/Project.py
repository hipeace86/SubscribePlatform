# -*- coding: utf-8 -*-
"""
Project
@author: Hipeace86
"""
from sqlalchemy import Column, Integer, String, Text
from webui.libs.Route import Basebase, BaseModel


class Project(Basebase, BaseModel):
    """
    项目订阅
    """
    __tablename__ = 'subscribe_project'

    ProjectId = Column('fi_project_id', Integer, primary_key=True)
    ProjectName = Column('fs_name', String(50), unique=True)
    Script = Column('fs_script', Text)
    Status = Column('fi_status', Integer)
    LastUpdate = Column('fi_last_update', Integer)
    Url = Column('fs_url', String(255))
    Desc = Column('fs_desc', String(255))

    def to_dict(self):
        return {'ProjectName': self.ProjectName, 'Script': self.Script, 'Status': self.Status, 'Url': self.Url}
