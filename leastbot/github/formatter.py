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
        '{e.pusher.name!r} pushed {COMMITCOUNT} commits to {e.ref!r} of {e.repository.url}',
        'Push diff: {DIFFURL}',
        ]).format(
        e           = einfo,
        COMMITCOUNT = len(einfo.commits),
        DIFFURL     = einfo.compare.replace('^', '%5E'),
        )


@_formatters.register
def _format_issues(_eid, _etype, einfo):
    return '\n'.join([
        '{e.sender.login!r} {e.action} issue {e.issue.number}: {e.issue.title!r}',
        'Issue: {e.issue.html_url}',
        ]).format(
        e = einfo,
        )


@_formatters.register
def _format_issue_comment(_eid, _etype, einfo):
    body = einfo.comment.body.strip()
    trunctext = ''

    if len(body) > 120:
        body = body[:120]
        trunctext = u'\u2026 (truncated)'

    return u'\n'.join([
        '{e.sender.login!r} {e.action} issue {e.issue.number} comment {e.comment.id}: {BODY!r}{TRUNCTEXT}',
        'Comment: {e.comment.html_url}',
        ]).format(
        e         = einfo,
        BODY      = body,
        TRUNCTEXT = trunctext,
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
