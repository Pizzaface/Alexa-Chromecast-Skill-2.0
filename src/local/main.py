#!/usr/bin/env python3

"""
Required Environment Variables:

AWS_ACCESS_KEY_ID - AWS User Access Key (IAM)
AWS_SECRET_ACCESS_KEY - AWS Secret Access Key (IAM)
AWS_DEFAULT_REGION - AWS Lambda and SNS Region (e.g. eu-west-1)
AWS_SNS_TOPIC_ARN - AWS SNS Topic ARN (e.g. arn:aws:sns:eu-west-1:236205202378:Alexa-Chromecast) 
PORT - Hardcode external port.
CHROMECAST_NAME - name of the Chromecast to send commands to

"""

import os
import sys
import signal
import logging
from local.skill_subscriber import Subscriber
from local.controllers.chromecast_controller import ChromecastController

cwd = os.getcwd()

# Setup root logger to log to stdout and a file
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(formatter)
root_logger = logging.getLogger()
root_logger.setLevel(logging.INFO)
root_logger.addHandler(handler)

handler = logging.handlers.TimedRotatingFileHandler(cwd + os.path.sep + 'alexa-chromecast.log', when='D', interval=1,
                                                    backupCount=5)
handler.setFormatter(formatter)
root_logger.addHandler(handler)

PORT = os.getenv('EXTERNAL_PORT')
IP = os.getenv('EXTERNAL_IP')


class Main(object):

    def __init__(self):
        # Exit gracefully on docker/command-line stop
        signal.signal(signal.SIGINT, self.shutdown)
        signal.signal(signal.SIGTERM, self.shutdown)
        self.chromecast_controller = ChromecastController()
        self.subscriber = Subscriber({'chromecast': self.chromecast_controller}, IP, PORT)
        self.subscriber.serve_forever()

    def shutdown(self, signum, frame):
        root_logger.info('Shutdown in progress...')
        self.chromecast_controller.shutdown(signum, frame)
        self.subscriber.shutdown(signum, frame)


if __name__ == "__main__":
    root_logger.info("Starting Alexa Chromecast listener...")
    main = Main()
