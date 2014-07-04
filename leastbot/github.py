import json
import hmac
import hashlib

from twisted.web import resource
from twisted.web.server import NOT_DONE_YET

from functable import FunctionTable

from leastbot.log import LogMixin



class WebhookResource (LogMixin, resource.Resource):
    isLeaf = True

    def __init__(self, sharedsecret, handle_event):
        resource.Resource.__init__(self)
        self._init_log()
        self._verify_signature = SignatureVerifier(sharedsecret)
        self._handle_event = handle_event

    def render_GET(self, request):
        request.setResponseCode(403, 'FORBIDDEN')
        request.finish()
        return NOT_DONE_YET

    def render_POST(self, request):
        allegedsig = request.getHeader('X-Hub-Signature')
        body = request.content.getvalue()

        if self._verify_signature(allegedsig, body):
            self._handle_signed_message(request, body)
        else:
            self._log.warn(
                'render_POST signature mismatch 403 - allegedsig %r; body %r...',
                allegedsig,
                body)
            request.setResponseCode(403, 'FORBIDDEN')
        request.finish()
        return NOT_DONE_YET

    def _handle_signed_message(self, request, body):
        eventname = request.getHeader('X-Github-Event')
        eventid = request.getHeader('X-Github-Delivery')
        try:
            message = json.loads(body)
        except ValueError:
            request.setResponseCode(400, 'MALFORMED')
        else:
            self._handle_event(eventid, eventname, message)
            request.setResponseCode(200, 'OK')


class SignatureVerifier (object):
    def __init__(self, sharedsecret):
        self._sharedsecret = sharedsecret

    def __call__(self, allegedsig, message):
        expectedsig = 'sha1=' + self._calculate_hmacsha1(message)
        return constant_time_compare(allegedsig, expectedsig)

    def _calculate_hmacsha1(self, body):
        m = hmac.HMAC(key=self._sharedsecret, msg=body, digestmod=hashlib.sha1)
        return m.hexdigest()


def constant_time_compare(a, b):
    # Use Nate Lawson's constant time compare:
    # http://rdist.root.org/2010/01/07/timing-independent-array-comparison/

    if len(a) != len(b):
        return False

    result = 0
    for (x, y) in zip(a, b):
        result |= ord(x) ^ ord(y)
    return result == 0


# Event formatting - public api:
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
        '%(PUSHER)r pushed %(COMMITCOUNT)r commits to %(REF)r of %(REPOURL)r',
        'Push diff: %(DIFFURL)s',
        ]) % dict(
        PUSHER      = einfo.pusher.email,
        COMMITCOUNT = len(einfo.commits),
        REF         = einfo.ref,
        REPOURL     = einfo.repository.url,
        DIFFURL     = einfo.compare,
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
