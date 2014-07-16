from functable import FunctionTable

from leastbot.formatutil import wrap_template_param, dedent


def format_event(eventid, eventtype, eventinfo):
    f = _formatters.get(eventtype, _format_generic)

    result = f(
        wrap_template_param(eventid, [], 'eventid'),
        wrap_template_param(eventtype, [], 'eventtype'),
        wrap_template_param(eventinfo, [], 'event'),
        )

    if result is None:
        return result
    else:
        return result.encode('utf8') # BUG: Is this acceptable for IRC?


# Event formatting - innards:
def _format_generic(_eid, etype, einfo):
    return dedent(u'''
        github {eventname} event sent by {e.sender.login} in {e.repository.url.urlencoding}
        ''').format(
        e         = einfo,
        eventname = etype
        )


_formatters = FunctionTable('_format_')



@_formatters.register
def _format_ping(_eid, _etype, _einfo):
    return None


@_formatters.register
def _format_push(_eid, _etype, einfo):
    return dedent(u'''
        {e.pusher.name} pushed {e.commits.len} commits to {e.ref} of {e.repository.url.urlencoding}
        Push diff: {e.compare.urlencoding}
        ''').format(
        e       = einfo,
        DIFFURL = einfo.compare._v.replace('^', '%5E'),
        )


@_formatters.register
def _format_issues(_eid, _etype, einfo):
    return dedent(u'''
        {e.sender.login} {e.action.bare} issue {e.issue.number}: {e.issue.title}
        Issue: {e.issue.html_url.urlencoding}
        ''').format(
        e = einfo,
        )


@_formatters.register
def _format_issue_comment(_eid, _etype, einfo):
    return dedent(u'''
        {e.sender.login} {e.action.bare} issue {e.issue.number} comment {e.comment.id}: {e.comment.body}
        Comment: {e.comment.html_url.urlencoding}
        ''').format(
        e = einfo,
        )


@_formatters.register
def _format_gollum(_eid, _etype, einfo):
    return dedent(u'''
        {e.sender.login} edited wiki pages: {e.pages[*.title.bare].comma_separated}
        {e.pages[*.html_url.urlencoding].newline_separated}
        ''').format(
        e = einfo,
        )


