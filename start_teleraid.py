#!/usr/bin/python
# -*- coding: utf-8 -*-

import json
import Queue
import logging

from gevent import monkey
from gevent import wsgi
from flask import Flask, request

# Custom files and packages
from config.config import config
from teleraid.Teleraid import TeleRaid
from telepot import Bot as TelegramBot
from teleraid.core import RaidUpdater, Session, MessageUpdater

from threading import Event

monkey.patch_all()
logging.basicConfig(
    format='%(asctime)s [%(threadName)14s][%(module)14s][%(levelname)8s] ' +
    '%(message)s')
log = logging.getLogger()
if config.get('debug', False):
    log.setLevel(logging.DEBUG)
else:
    log.setLevel(logging.INFO)

app = Flask(__name__)
data_queue = Queue.Queue()


@app.route('/', methods=['POST'])
def accept_webhook():
    try:
        data = json.loads(request.data)
        data_queue.put(data)
    except Exception as e:
        log.exception("Encountered error while receiving webhook ({}: {})".format(type(e).__name__, e))
        pass
    return "OK"


t_client = TelegramBot(config['bot_token'])
session = Session(name="Shared Session", telegram_client=t_client)
t1_stopEvent = Event()
t2_stopEvent = Event()
t3_stopEvent = Event()

log.info('Starting Bot')
try:
    t = TeleRaid(queue=data_queue, session=session, event=t1_stopEvent)
    t.daemon = True
    t.start()

    log.debug('Starting thread: RaidUpdater...')
    t2 = RaidUpdater(session=session, logger=log, event=t2_stopEvent, name='RaidUpdater')
    t2.daemon = True
    t2.start()
    log.debug('RaidUpdater started.')

    log.debug('Starting thread: MessageUpdater...')
    t3 = MessageUpdater(session=session, logger=log, event=t3_stopEvent, name='MessageUpdater')
    t3.daemon = True
    t3.start()
    log.debug('MessageUpdater started.')

    log.debug('Starting wsgi server for Webhook and server forever ;)')
    server = wsgi.WSGIServer((config['host'], config['port']), app)
    server.serve_forever()

    t.join()
    t2.join()
    t3.join()
except KeyboardInterrupt:
    pass
log.info("TeleRaid ended.")
