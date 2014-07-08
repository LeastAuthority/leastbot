from functable import FunctionTable


def format_event(eventid, eventtype, eventinfo):
    f = _formatters.get(eventtype)
    if f is None:
        return None
    else:
        alw = _AttrLookupWrapper(eventinfo)
        result = f(eventid, eventtype, alw)

        if result is None:
            return result
        else:
            return result.encode('utf8') # BUG: Is this acceptable for IRC?


# Event formatting - innards:
_formatters = FunctionTable('_format_')


@_formatters.register
def _format_ping(_eid, _etype, _einfo):
    return None


@_formatters.register
def _format_push(_eid, _etype, einfo):
    return '\n'.join([
        '%(PUSHER)r pushed %(COMMITCOUNT)r commits to %(REF)r of %(REPOURL)s',
        'Push diff: %(DIFFURL)s',
        ]) % dict(
        PUSHER      = einfo.pusher.name,
        COMMITCOUNT = len(einfo.commits),
        REF         = einfo.ref,
        REPOURL     = einfo.repository.url,
        DIFFURL     = einfo.compare.replace('^', '%5E'),
        )


@_formatters.register
def _format_issues(_eid, _etype, einfo):
    return '\n'.join([
        '%(SENDER)r %(ACTION)s issue %(NUMBER)r: %(TITLE)r',
        'Issue: %(URL)s',
        ]) % dict(
        SENDER = einfo.sender.login,
        ACTION = einfo.action,
        NUMBER = einfo.issue.number,
        TITLE  = einfo.issue.title,
        URL    = einfo.issue.html_url,
        )


@_formatters.register
def _format_issue_comment(_eid, _etype, einfo):
    body = einfo.comment.body.strip()
    trunctext = ''

    if len(body) > 120:
        body = body[:120]
        trunctext = u'\u2026 (truncated)'

    return '\n'.join([
        '%(SENDER)r %(ACTION)s issue %(ISSUENUMBER)r comment %(COMMENTID)r: %(BODY)r%(TRUNCTEXT)s',
        'Comment: %(URL)s',
        ]) % dict(
        SENDER      = einfo.sender.login,
        ACTION      = einfo.action,
        ISSUENUMBER = einfo.issue.number,
        COMMENTID   = einfo.comment.id,
        BODY        = body,
        TRUNCTEXT   = trunctext,
        URL         = einfo.comment.html_url,
        )



class _AttrLookupWrapper (object):
    def __init__(self, d, namepath=[]):
        self._d = d
        self._np = namepath

    def __getattr__(self, name):
        if self._d is None:
            return self

        sentinel = object()
        v = self._d.get(name, sentinel)
        if v is sentinel:
            return _AttrLookupWrapper(None, self._np + [name])
        elif isinstance(v, dict):
            return _AttrLookupWrapper(v, self._np + [name])
        elif isinstance(v, unicode):
            return v.encode('utf8') # Is this sane?
        else:
            return v

    def __repr__(self):
        return '<Missing %s>' % ('/'.join(self._np),)

    def __len__(self):
        # Hack: Just return an obviously wrong value to make humans suspicious of an error.
        return 0xffFFffFF
