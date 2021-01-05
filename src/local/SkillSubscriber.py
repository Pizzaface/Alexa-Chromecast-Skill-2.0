import os
import sys
import signal
import json
from http.server import HTTPServer, BaseHTTPRequestHandler
from requests import get
import miniupnpc
import boto3
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

"""
Generic Skill Subscription class to handle commands from an
Lambda Fucntion via SNS notifications.
"""
class Subscriber(BaseHTTPRequestHandler):

    def __init__(self, skills, ip, port, topic_arn=os.getenv('AWS_SNS_TOPIC_ARN')):
        self.token = ""
        if port:
            self.manual_port_forward = True
        else:
            self.manual_port_forward = False
            try:
                self.initialize_upnp()
            except Exception:
                logger.exception('Fallo al configurar UPnP. Por favor, configúralo manualmente e introduce la variable de entorno PORT.')
                sys.exit(1)

        self.sns_client = boto3.client('sns')
        self.skills = skills
        self.topic_arn = topic_arn
        instance = self

        class SNSRequestHandler(BaseHTTPRequestHandler):
            def do_POST(self):
                self.send_response(200)
                self.send_header('content-type', 'text/html')
                self.end_headers()
                raw_data = self.rfile.read(
                    int(self.headers['Content-Length']))
                data = json.loads(raw_data)
                topic_arn = self.headers.get('X-Amz-Sns-Topic-Arn')
                type = data['Type']
 
                if type == 'SubscriptionConfirmation':
                    logger.info('Confirmación de suscripción recibida...')
                    token = data['Token']
                    instance.confirm_subscription(topic_arn, token)
                    
                elif type == 'Notification':
                    logger.info('Mensaje recibido...')
                    if data['Message']:
                        instance.dispatch_notification(json.loads(data['Message']))

            def log_message(self, format, *args):
                pass

        self.server = HTTPServer(('', int(port) if port else 0), SNSRequestHandler)

        port = self.server.server_port
        if not ip:
          ip = self.get_external_ip() 
        self.endpoint_url = 'http://{}:{}'.format(ip, port)
        logger.info('Escuchando a {}'.format(self.endpoint_url))
        signal.signal(signal.SIGINT,
                      lambda signal, frame: self.unsubscribe())
        self.subscribe()
        self.server.serve_forever()

    def initialize_upnp(self):
        upnp = miniupnpc.UPnP()
        upnp.discoverdelay = 10
        upnp.discover()
        upnp.selectigd()
        self.upnp = upnp

    def get_external_ip(self):
        return get('https://api.ipify.org').text

    def subscribe(self):
        if not self.manual_port_forward:
            try:
                self.upnp.addportmapping(
                    self.server.server_port,
                    'TCP',
                    self.upnp.lanaddr,
                    self.server.server_port,
                    '',
                    ''
                )
            except:
                logger.error('No se pudo reenviar automáticamente el puerto.')
                logger.error('Por favor, establezca el puerto como una variable de entorno y envíelo manualmente.')
                sys.exit(1)

        try:
            logger.info("Suscribiéndose a los comandos de Alexa...")
            self.sns_client.subscribe(
                TopicArn=self.topic_arn,
                Protocol='http',
                Endpoint=self.endpoint_url
            )

        except Exception:
            logger.exception('El SNS Topic ({}) no es válido. Por favor, compruébalo en AWS.'.format(self.topic_arn))
            sys.exit(1)

    def confirm_subscription(self, topic_arn, token):
        
        try:
            self.sns_client.confirm_subscription(
                TopicArn=topic_arn,
                Token=token,
                AuthenticateOnUnsubscribe="false")
            logger.info('Suscrito.')
        
        except Exception:
            logger.exception('No se confirmó la suscripción. Por favor, compruébalo en AWS.')
            sys.exit(1)

    def unsubscribe(self):

        if not self.manual_port_forward:
            result = self.upnp.deleteportmapping(self.server.server_port, 'TCP')

            if result:
                logger.debug('Se eliminó el reenvío al puerto {}.'.format(self.server.server_port))
            else:
                raise RuntimeError(
                    'No se pudo eliminar el reenvío al puerto {}.'.format(self.server.server_port))

        subscription_arn = None
        response = self.sns_client.list_subscriptions_by_topic(TopicArn=self.topic_arn)
        for sub in response['Subscriptions']:
            if sub['TopicArn'] == self.topic_arn and sub['Endpoint'] == self.endpoint_url:
                subscription_arn = sub['SubscriptionArn']
                break

        if (subscription_arn is not None and
                subscription_arn[:12] == 'arn:aws:sns:'):
            self.sns_client.unsubscribe(
                SubscriptionArn=subscription_arn
            )

        sys.exit(0)

    def dispatch_notification(self, notification):
        try:
            skill = self.skills.get(notification['handler_name'])
            skill.handle_command(notification['room'], notification['command'], notification['data'])
        except Exception:
            logger.exception('Error inesperado gestionando mensaje')


