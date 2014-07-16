from leastbot.formatutil import wrap_template_param, dedent


def format_event(eventid, eventtype, eventinfo):
    template = dedent(_templates.get(eventtype, _generic_template))

    result = template.format(
        event_id = wrap_template_param(eventid, [], 'eventid'),
        event_type = wrap_template_param(eventtype, [], 'eventtype'),
        event = wrap_template_param(eventinfo, [], 'event'),
        )

    return result.encode('utf8') # BUG: Is this acceptable for IRC?


# Event formatting - innards:
_generic_template = u'''
    github {event_type} event sent by {event.sender.login} in {event.repository.url.urlencoding}
'''


_templates = {
    'ping': u'''
        Ping! {event.zen}
        ''',

    'push': u'''
        {event.pusher.name} pushed {event.commits.len} commits to {event.ref} of {event.repository.url.urlencoding}
        Push diff: {event.compare.urlencoding}
        ''',

    'issues': u'''
        {event.sender.login} {event.action.bare} issue {event.issue.number}: {event.issue.title}
        Issue: {event.issue.html_url.urlencoding}
        ''',

    'issue_comment': u'''
        {event.sender.login} {event.action.bare} issue {event.issue.number} comment {event.comment.id}: {event.comment.body}
        Comment: {event.comment.html_url.urlencoding}
        ''',

    'gollum': u'''
        {event.sender.login} edited wiki pages: {event.pages[*.title.bare].comma_separated}
        {event.pages[*.html_url.urlencoding].newline_separated}
        ''',
    }

