# -*- coding: utf-8 -*-
"""
Record
@author: Hipeace86
"""
from sqlalchemy import Column, Integer, String, Text
from webui.libs.Route import Basebase, BaseModel


class Record(Basebase, BaseModel):
    """
    项目订阅
    """
    __tablename__ = 'subscribe_record'

    RecordId = Column('fi_record_id', Integer, primary_key=True)
    ProjectName = Column('fs_name', String(50))
    RecordJson = Column('fs_json', Text)

    def to_dict(self):
        return {'ProjectName': self.ProjectName, 'RecordJson': self.RecordJson}
