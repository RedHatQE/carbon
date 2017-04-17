import carbon


class TestLogging(object):

    def test_logger_cache(self):
        cbn = carbon.Carbon(__name__)
        logger1 = cbn.logger
        assert cbn.logger is logger1
        assert cbn.name == __name__
        cbn.logger_name = __name__ + '/test_logger_cache'
        assert cbn.logger is not logger1
