import os
import sys
import signal
import json
from http.server import HTTPServer, BaseHTTPRequestHandler
from requests import get
import miniupnpc
import boto3

"""
Generic Skill Subscription class to handle commands from an
Lambda Fucntion via SNS notifications.
"""
class Subscriber(BaseHTTPRequestHandler):

    def __init__(self, skills, port_overide, topic_arn=os.getenv('AWS_SNS_TOPIC_ARN')):
        self.token = ""
        if port_overide:
            self.manual_port_forward = True
        else:
            self.manual_port_forward = False
            try:
                self.initialize_upnp()
            except Exception as err:
                print('Failed to configure UPnP. Please map port manually and pass PORT environment variable.')
                print(err)
                sys.exit(1)

        self.sns_client = boto3.client('sns')
        self.skills = skills
        self.topic_arn = topic_arn
        instance = self

        class SNSRequestHandler(BaseHTTPRequestHandler):
            def do_POST(self):
                print('Received POST request...')
                self.send_response(200)
                self.send_header('content-type', 'text/html')
                self.end_headers()
                raw_data = self.rfile.read(
                    int(self.headers['Content-Length']))
                data = json.loads(raw_data)
                topic_arn = self.headers.get('X-Amz-Sns-Topic-Arn')
                type = data['Type']
 
                if type == 'SubscriptionConfirmation':
                    token = data['Token']
                    instance.confirm_subscription(topic_arn, token)
                elif type == 'Notification':
                    if data['Message']:
                        instance.dispatch_notification(json.loads(data['Message']))

            def log_message(self, format, *args):
                pass

        self.server = HTTPServer(('', int(port_overide) if port_overide else 0), SNSRequestHandler)

        port = self.server.server_port
        self.endpoint_url = 'http://{}:{}'.format(self.get_external_ip(), port)
        self.subscribe()
        print('Listening on {}'.format(self.endpoint_url))
        signal.signal(signal.SIGINT,
                      lambda signal, frame: self.unsubscribe())
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
                print(
                    '''
                    Failed to automatically forward port.
                    Please set port as an environment variable and forward manually.
                    '''
                )
                sys.exit(1)

        try:
            self.sns_client.subscribe(
                TopicArn=self.topic_arn,
                Protocol='http',
                Endpoint=self.endpoint_url
            )

        except Exception as err:
            print('SNS Topic ({}) is invalid. Please check in AWS.'.format(self.topic_arn))
            print(err)
            sys.exit(1)

    def confirm_subscription(self, topic_arn, token):
        
        try:
            self.sns_client.confirm_subscription(
                TopicArn=topic_arn,
                Token=token,
                AuthenticateOnUnsubscribe="false")
            
        except Exception as err:
            print('Failed to confirm subscription. Please check in AWS.')
            print(err)
            sys.exit(1)

    def unsubscribe(self):

        if not self.manual_port_forward:
            result = self.upnp.deleteportmapping(self.server.server_port, 'TCP')

            if result:
                print('Removed forward for port {}.'.format(self.server.server_port))
            else:
                raise RuntimeError(
                    'Failed to remove port forward for {}.'.format(self.server.server_port))

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
        except Exception as err:
            print(err)

