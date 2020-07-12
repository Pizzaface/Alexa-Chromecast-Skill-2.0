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
import logging
from local.SkillSubscriber import Subscriber
from local.ChromecastSkill import Skill

cwd = os.getcwd()

#Setup root logger to log to stdout and a file
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(formatter)
root_logger = logging.getLogger()
root_logger.setLevel(logging.INFO)
root_logger.addHandler(handler)

handler = logging.handlers.TimedRotatingFileHandler(cwd+os.path.sep+'alexa-chromecast.log', when='D', interval=1, backupCount=5)
handler.setFormatter(formatter)
root_logger.addHandler(handler)

PORT = os.getenv('EXTERNAL_PORT')
IP = os.getenv('EXTERNAL_IP')

if __name__ == "__main__":
    root_logger.info("Starting Alexa Chromecast listener...")
    chromecast_skill = Skill()
    Subscriber({'chromecast': chromecast_skill}, IP, PORT)
