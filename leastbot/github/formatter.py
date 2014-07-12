from functable import FunctionTable

from leastbot.formatutil import DictFormatWrapper, dedent


def format_event(eventid, eventtype, eventinfo):
    f = _formatters.get(eventtype)
    if f is None:
        return None
    else:
        alw = DictFormatWrapper(eventinfo)
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
    return dedent('''
        {e.pusher.name!r} pushed {COMMITCOUNT} commits to {e.ref!r} of {e.repository.url}
        Push diff: {DIFFURL}
        ''').format(
        e           = einfo,
        COMMITCOUNT = len(einfo.commits),
        DIFFURL     = einfo.compare.replace('^', '%5E'),
        )


@_formatters.register
def _format_issues(_eid, _etype, einfo):
    return dedent('''
        {e.sender.login!r} {e.action} issue {e.issue.number}: {e.issue.title!r}
        Issue: {e.issue.html_url}
        ''').format(
        e = einfo,
        )


@_formatters.register
def _format_issue_comment(_eid, _etype, einfo):
    body = einfo.comment.body.strip()
    trunctext = ''

    if len(body) > 120:
        body = body[:120]
        trunctext = u'\u2026 (truncated)'

    return dedent(u'''
        {e.sender.login!r} {e.action} issue {e.issue.number} comment {e.comment.id}: {BODY!r}{TRUNCTEXT}
        Comment: {e.comment.html_url}
        ''').format(
        e         = einfo,
        BODY      = body,
        TRUNCTEXT = trunctext,
        )


@_formatters.register
def _format_gollum(_eid, _etype, einfo):
    return dedent('''
        {e.sender.login!r} edited wiki pages: {PAGE_LIST}
        {PAGE_URLS}
        ''').format(
        e = einfo,
        PAGE_LIST = ', '.join( '{title}'.format(**d) for d in einfo.pages ),
        PAGE_URLS = '\n'.join( 'Page: {html_url}'.format(**d) for d in einfo.pages ),
        )


