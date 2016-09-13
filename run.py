#!/usr/bin/env python
# -*- coding: utf-8 -*-

from scheduler.scheduler import Scheduler
from libs import utils
import os
import sys
import logging
import logging.config
import time
import six
import click


def read_config(ctx, param, value):
    if not value:
        return {}
    import json

    def underline_dict(d):
        if not isinstance(d, dict):
            return d
        return dict((k.replace('-', '_'), underline_dict(v)) for k, v in six.iteritems(d))

    config = underline_dict(json.load(value))
    ctx.default_map = config
    return config


def connect_rpc(ctx, param, value):
    if not value:
        return
    try:
        from six.moves import xmlrpc_client
    except ImportError:
        import xmlrpclib as xmlrpc_client
    return xmlrpc_client.ServerProxy(value, allow_none=True)


@click.group(invoke_without_command=True)
@click.option('--logging-config', default=os.path.join(os.path.dirname(__file__), "logging.conf"),
              help="logging config file for built-in python logging module", show_default=True)
@click.option('--debug', envvar='DEBUG', default=False, is_flag=True, help='debug mode')
@click.option('-c', '--config', callback=read_config, type=click.File('r'),
              help='a json file with default values for subcommands. {"webui": {"port":5001}}')
@click.option('--add-sys-path/--not-add-sys-path', default=True, is_flag=True,
              help='add current working directory to python lib search path')
@click.pass_context
def cli(ctx, **kwargs):
    if kwargs['add_sys_path']:
        sys.path.append(os.getcwd())

    logging.config.fileConfig(kwargs['logging_config'])
    ctx.obj = utils.ObjectDict(ctx.obj or {})
    ctx.obj['instances'] = []
    ctx.obj.update(kwargs)
    record_config = ctx.obj.config.get('record', {})
    os.environ['RecordBroker'] = record_config['amqp']
    os.environ['sqlalchemy'] = record_config['sqlalchemy']
    if ctx.invoked_subcommand is None and not ctx.obj.get('testing_mode'):
        ctx.invoke(all)
    return ctx


@cli.command()
@click.option('--host', default='0.0.0.0', envvar='WEBUI_HOST',
              help='webui bind to host')
@click.option('--port', default=5000, envvar='WEBUI_PORT',
              help='webui bind to host')
@click.option('--scheduler-rpc', help='xmlrpc path of scheduler')
@click.option('--sqlalchemy', default="mysql://root:111222@localhost/zcloud?charset=utf8")
@click.pass_context
def webui(ctx, host, port, scheduler_rpc, sqlalchemy):
    from webui.app import make_app
    import tornado
    app = make_app()
    from webui.libs.Route import makesession
    app.db = makesession(sqlalchemy)
    from webui.libs.Route import createAll
    createAll(sqlalchemy)

    if isinstance(scheduler_rpc, six.string_types):
        scheduler_rpc = connect_rpc(ctx, None, scheduler_rpc)
    if scheduler_rpc is None and os.environ.get('SCHEDULER_NAME'):
        app.scheduler_rpc = connect_rpc(ctx, None, 'http://%s/' % (
            os.environ['SCHEDULER_PORT_23333_TCP'][len('tcp://'):]))
    elif scheduler_rpc is None:
        app.scheduler_rpc = connect_rpc(ctx, None, 'http://127.0.0.1:23333/')

    g = ctx.obj
    if g.debug:
        from tornado import autoreload
        autoreload.start()
    app.listen(port, address=host)
    # webui_ioloop = tornado.ioloop.IOLoop()
    # g.webui_ioloop = webui_ioloo
    tornado.ioloop.IOLoop.instance().start()


@cli.command()
@click.option('--xmlrpc/--no-xmlrpc', default=True)
@click.option('--xmlrpc-host', default='0.0.0.0')
@click.option('--xmlrpc-port', envvar='SCHEDULER_XMLRPC_PORT', default=23333)
@click.pass_context
def scheduler(ctx, xmlrpc, xmlrpc_host, xmlrpc_port):
    g = ctx.obj
    scheduler = Scheduler()
    g.instances.append(scheduler)
    if g.get('testing_mode'):
        return scheduler

    if xmlrpc:
        utils.run_in_thread(scheduler.xmlrpc_run,
                            port=xmlrpc_port, bind=xmlrpc_host)
    scheduler.run()


@cli.command()
@click.option('--sqlalchemy', default="mysql://root:111222@localhost/zcloud?charset=utf8")
@click.option('--amqp', default="amqp://guest@localhost//")
@click.pass_context
def CeleryTasks(ctx, sqlalchemy, amqp):
    os.environ['RecordBroker'] = amqp
    import importlib
    for root, dir, files in os.walk('tasks'):
        for file in files:
            if file[-8:] == 'Tasks.py':
                try:
                    load_module = importlib.import_module(
                        'tasks.{0}'.format(file[:-3]))
                    if hasattr(load_module, 'runCeleryTask'):
                        # utils.run_in_thread(load_module.runCeleryTask)
                        load_module.runCeleryTask()
                        # TODO: multi task run in thread or process
                except Exception as e:
                    print e


@cli.command()
@click.option('--run_in', default="subprocess", help="sub programe run method")
@click.pass_context
def all(ctx, run_in):
    ctx.obj['debug'] = False
    g = ctx.obj
    if run_in == 'subprocess' and os.name != 'nt':
        run_in = utils.run_in_subprocess
    else:
        run_in = utils.run_in_thread

    threads = []
    try:
        # scheduler
        scheduler_config = g.config.get('scheduler', {})
        scheduler_config.setdefault('xmlrpc_host', '127.0.0.1')
        threads.append(utils.run_in_process(
            ctx.invoke, scheduler, **scheduler_config))
        # record
        record_config = g.config.get('record', {})
        threads.append(run_in(ctx.invoke, CeleryTasks, **record_config))
        # webui
        webui_config = g.config.get('webui', {})
        ctx.invoke(webui, **webui_config)
    finally:
        # exit components run in threading
        for each in g.instances:
            each.quit()

        # exit components run in subprocess
        for each in threads:
            if not each.is_alive():
                continue
            if hasattr(each, 'terminate'):
                each.terminate()
            each.join()
        import tornado
        tornado.ioloop.IOLoop.instance().stop()

if __name__ == "__main__":
    cli()
