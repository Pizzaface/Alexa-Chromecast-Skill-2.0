import os
import pychromecast
import subprocess
import requests

class Skill():

    def __init__(self, chromecast_name='Living Room'):
        chromecasts = pychromecast.get_chromecasts()
        if len(chromecasts) > 0:
            self.cast = next(cc for cc in chromecasts if cc.device.friendly_name == chromecast_name)
        else:
            print("No Chromecasts found")
            exit(1)


    def handle_command(self, command, data):
        try:
            self.cast.wait()
            mc = self.cast.media_controller
            getattr(self, command)(data, self.cast, mc)
        except Exception as err:
            print('No handler for {}. Data: {}. Error {}'.format(command, data, err))

    def resume(self, data, cast, mc):
        mc.play()
        print('Play command sent to Chromecast.')

    def pause(self, data, cast, mc):
        mc.pause()
        print('Pause command sent to Chromecast.')

    def stop(self, data, cast, mc):
        self.cast.quit_app()
        print('Stop command sent to Chromecast.')

    def set_volume(self, data, cast, mc):
        volume = data['level'] # volume as 0-10
        volume_normalized = float(volume) / 10.0 # volume as 0-1
        cast.set_volume(volume_normalized)
        print('Volume command sent to Chromecast. Set to {}.'.format(volume_normalized))

    def play_video(self, data, cast, mc):
        url = subprocess.check_output("youtube-dl -g --no-check-certificate -f best -- " + data['videoId'], shell=True)
        mc.play_media(url, 'video/mp4')
        print('video sent to chromecast: {}'.format(url))

    def power_off(self, data, cast, mc):
        self.stop(data, cast, mc)

        panasonic_viera_ip = os.getenv('PANASONIC_VIERA_IP', False)
        if panasonic_viera_ip:
            self.power_off_panasonic_viera(panasonic_viera_ip)

    def power_off_panasonic_viera(self, ip_address):

        URN = 'urn:panasonic-com:service:p00NetworkControl:1'
        key = 'NRC_POWER-ONOFF'
        soap_payload = "<?xml version='1.0' encoding='utf-8'?><s:Envelope xmlns:s='http://schemas.xmlsoap.org/soap/envelope/' s:encodingStyle='http://schemas.xmlsoap.org/soap/encoding/'><s:Body><u:X_SendKey xmlns:u='{}'><X_KeyEvent>{}</X_KeyEvent></u:X_SendKey></s:Body></s:Envelope>".format(URN, key)
        path = 'nrc/control_0'
        port = 55000

        headers = {
            'Connection': 'Close',
            'Content-Type': 'text/xml; charset="utf-8"',
            'SOAPACTION':  '"' + URN + '#X_SendKey"'
        }

        result = requests.post(
            'http://{}:{}/{}'.format(ip_address, port, path),
            data=soap_payload,
            headers=headers
        )
