class DictFormatWrapper (object):
    def __init__(self, d, namepath=[]):
        self._d = d
        self._np = namepath

    def __getattr__(self, name):
        if self._d is None:
            return self

        sentinel = object()
        v = self._d.get(name, sentinel)
        if v is sentinel:
            return DictFormatWrapper(None, self._np + [name])
        elif isinstance(v, dict):
            return DictFormatWrapper(v, self._np + [name])
        elif isinstance(v, unicode):
            return v.encode('utf8') # Is this sane?
        else:
            return v

    def __repr__(self):
        return '<Missing %s>' % ('/'.join(self._np),)

    def __len__(self):
        # Hack: Just return an obviously wrong value to make humans suspicious of an error.
        return 0xffFFffFF
