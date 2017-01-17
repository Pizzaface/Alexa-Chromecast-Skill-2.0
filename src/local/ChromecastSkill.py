import pychromecast
import subprocess

class Skill():

    def __init__(self, chromecast_name='Living Room'):
        chromecasts = pychromecast.get_chromecasts()
        self.cast = next(cc for cc in chromecasts if cc.device.friendly_name == chromecast_name)

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
        url = subprocess.check_output("youtube-dl -g -- " + data['videoId'], shell=True)
        mc.play_media(url, 'video/mp4')
        print('video sent to chromecast: {}'.format(url))
