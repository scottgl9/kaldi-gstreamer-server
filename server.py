#!/usr/bin/python

from gi.repository import GObject
import yaml
import logging
import tornado.ioloop
import tornado.options
import tornado.web
import tornado.websocket
import tornado.gen
import tornado.concurrent
import time
import thread
from subprocess import Popen, PIPE
import sys

from kaldigstserver.worker import ServerWebsocket
from kaldigstserver.decoder import DecoderPipeline
from kaldigstserver.decoder2 import DecoderPipeline2
from kaldigstserver.master_server import Application
import kaldigstserver.common

logger = logging.getLogger(__name__)

CONNECT_TIMEOUT = 5
SILENCE_TIMEOUT = 5
USE_NNET2 = False

def worker_thread():
    uri = "ws://localhost:8888/worker/ws/speech"
    with open("tedlium_english_nnet2.yaml") as f:
        conf = yaml.safe_load(f)
    global USE_NNET2
    USE_NNET2 = conf.get("use-nnet2", False)

    global SILENCE_TIMEOUT
    SILENCE_TIMEOUT = conf.get("silence-timeout", 5)

    post_processor = None
    if "post-processor" in conf:
        post_processor = Popen(conf["post-processor"], shell=True, stdin=PIPE, stdout=PIPE)

    full_post_processor = None
    if "full-post-processor" in conf:
        full_post_processor = Popen(conf["full-post-processor"], shell=True, stdin=PIPE, stdout=PIPE)

    USE_NNET2 = conf.get("use-nnet2", False)
    global USE_NNET2

    SILENCE_TIMEOUT = conf.get("silence-timeout", 5)
    global SILENCE_TIMEOUT

    if USE_NNET2:
        decoder_pipeline = DecoderPipeline2(conf)
    else:
        decoder_pipeline = DecoderPipeline(conf)

    loop = GObject.MainLoop()
    thread.start_new_thread(loop.run, ())
    while True:
        ws = ServerWebsocket(uri, decoder_pipeline, post_processor, full_post_processor=None) #full_post_processor)
        try:
            logger.info("Opening websocket connection to master server")
            ws.connect()
            ws.run_forever()
        except Exception:
            logger.error("Couldn't connect to server, exiting")
            exit(0)
        # fixes a race condition
        time.sleep(1)

def main():
    logging.basicConfig(level=logging.DEBUG, format="%(levelname)8s %(asctime)s %(message)s ")
    logging.debug('Starting up server')
    from tornado.options import define, options
    define("certfile", default="", help="certificate file for secured SSL connection")
    define("keyfile", default="", help="key file for secured SSL connection")

    tornado.options.parse_command_line()
    app = Application()
    if options.certfile and options.keyfile:
        ssl_options = {
          "certfile": options.certfile,
          "keyfile": options.keyfile,
        }
        logging.info("Using SSL for serving requests")
        app.listen(options.port, ssl_options=ssl_options)
    else:
        app.listen(options.port)
    #tornado.ioloop.IOLoop.instance().start()

    #GObject.threads_init()
    #thread.start_new_thread(worker_thread, ())
    thread.start_new_thread(tornado.ioloop.IOLoop.instance().start, ())
    worker_thread()

if __name__ == "__main__":
    main()
