import logging


class LogMixin (object):
    def _init_log(self):
        name = type(self).__name__
        self._log = logging.getLogger(name)
