import logging
import time
import unittest

from local.controllers.stan_controller import StanController
from tests.integration.helpers import TestChromecast


class TestStan(TestChromecast):

    def test_stan(self):
        cc = self.chromecast_controller.get_chromecast(self.cc_name)
        try:
            stan_cc = StanController()
            stan_cc.logger.setLevel(logging.DEBUG)

            cc.cast.register_handler(stan_cc)
            cc.media_controller.register_status_listener(stan_cc)
            cc.cast.register_status_listener(stan_cc)

            stan_cc.launch()
            time.sleep(20)
            stan_cc.play_media()
            time.sleep(20)
            print(cc.media_controller.status)
        finally:
            self._stop()


if __name__ == '__main__':
    unittest.main()
