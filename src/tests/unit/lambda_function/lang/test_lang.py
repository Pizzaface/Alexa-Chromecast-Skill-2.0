import unittest

from lambda_function.lang.language import Language


class TestLanguage(unittest.TestCase):

    def test_en_au(self):
        language = Language('en-AU')
        self.assertEqual('Ok', language.get('Ok'))
        self.assertEqual('en-AU', language.locale)

    def test_en_unknown(self):
        # Defaults to en-AU
        language = Language('UNKNOWN')
        self.assertEqual('Ok', language.get('Ok'))
        self.assertEqual('UNKNOWN', language.locale)


if __name__ == '__main__':
    unittest.main()
