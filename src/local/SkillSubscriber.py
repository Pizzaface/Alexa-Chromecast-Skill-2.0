import os
import sys
import signal
import json
from BaseHTTPServer import HTTPServer, BaseHTTPRequestHandler
from requests import get
import miniupnpc
import boto3

"""
Generic Skill Subscription class to handle commands from an
Lambda Fucntion via SNS notifications.
"""


class Subscriber():

    def __init__(self, skills, port_overide, topic_arn=os.getenv('AWS_SNS_TOPIC_ARN')):

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

        class SNSRequestHandler(BaseHTTPRequestHandler):

            def do_POST(request):
                request.send_response(200)
                request.send_header('content-type', 'text/html')
                request.end_headers()
                raw_data = request.rfile.read(
                    int(request.headers['Content-Length']))
                data = json.loads(raw_data)
                type = data['Type']

                if type == 'SubscriptionConfirmation':
                    self.confirm_subscription(data)
                elif type == 'Notification':
                    if data['Message']:
                        self.dispatch_notification(json.loads(data['Message']))
            def log_message(self, format, *args):
                pass

        self.server = HTTPServer(('', int(port_overide) if port_overide else 0), SNSRequestHandler)

        port = self.server.server_port
        endpoint_url = 'http://{}:{}'.format(self.get_external_ip(), port)

        self.subscribe(topic_arn, endpoint_url)
        print('Listening on {}'.format(endpoint_url))
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

    def subscribe(self, topic_arn, endpoint_url):
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
                TopicArn=topic_arn,
                Protocol='http',
                Endpoint=endpoint_url
            )
        except Exception as err:
            print('SNS Topic ({}) is invalid. Please check in AWS.'.format(topic_arn))
            print(err)
            sys.exit(1)

    def confirm_subscription(self, data):
        subscribe_url = data['SubscribeURL']
        response = get(subscribe_url, headers={'accept': 'application/json'})
        response_data = response.json()
        if response.status_code == 200:
            subscription_arn = response_data['ConfirmSubscriptionResponse'][
                'ConfirmSubscriptionResult']['SubscriptionArn']
            if subscription_arn:
                print('Subscription confirmed. ARN: {}'.format(subscription_arn))
                self.subscription_arn = subscription_arn
            else:
                print('Error confirming subscription.')
        else:
            return None

    def unsubscribe(self):

        if not self.manual_port_forward:
            result = self.upnp.deleteportmapping(self.server.server_port, 'TCP')

            if result:
                print('Removed forward for port {}.'.format(self.server.server_port))
            else:
                raise RuntimeError(
                    'Failed to remove port forward for {}.'.format(self.server.server_port))

        if hasattr(self, 'subscription_arn'):
            self.sns_client.unsubscribe(SubscriptionArn=self.subscription_arn)
            print('Removed SNS subscription. ({})'.format(self.subscription_arn))
        else:
            print('Failed to remove SNS subscription. (Possibly not subscribed initially.)')

        sys.exit(0)

    def dispatch_notification(self, notification):
        try:
            skill = self.skills.get(notification['handler_name'])
            skill.handle_command(notification['command'], notification['data'])
        except Exception as err:
            print(err)
