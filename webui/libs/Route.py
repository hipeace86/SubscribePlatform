# -*- coding: utf-8 -*-
__author__ = 'Hipeace86'
__datetime__ = '2016-0822'

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

BaseModel = declarative_base()


class Basebase(object):
    __table_args__ = {
        'mysql_engine': 'innodb',
        'mysql_charset': 'utf8'
    }


def makesession(sqlalchemy):
    engine = create_engine(sqlalchemy, echo=True)
    Session = sessionmaker(bind=engine, autocommit=False)
    return Session()


def createAll(sqlalchemy):
    engine = create_engine(sqlalchemy)
    from webui.Entity.Project import Project
    from webui.Entity.Record import Record

    BaseModel.metadata.create_all(engine)
