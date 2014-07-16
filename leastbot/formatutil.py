# -*- coding: utf-8 -*-


def dedent(s):
    inlines = s.split('\n')
    count = None
    indent = None
    outlines = []
    for l in inlines:
        if indent is None:
            if l.strip() != '':
                count = len(l) - len(l.lstrip(' '))
                indent = l[:count]
                outlines.append(l[count:])
                continue
            else:
                continue
        elif l.strip() == '':
            outlines.append('')
            continue
        elif l[:count] == indent:
            outlines.append(l[count:])
            continue
        else:
            raise AssertionError('Subsequent lines must be indented at least as much as the first:\n%s' % (s,))

    return '\n'.join(outlines)


def wrap_template_param(value, basepath, pathitem):
    path = basepath + [pathitem]

    if value is MissingParam:
        return MissingParam(path)
    elif isinstance(value, dict):
        return AttrDictTemplateParam(value, path)
    elif isinstance(value, list):
        return ListTemplateParam(value, path)
    elif isinstance(value, unicode) or isinstance(value, bytes):
        if isinstance(value, unicode):
            value = value.encode('utf8')
        return UnicodeTemplateParam(value, path)
    else:
        return value


class TemplatePathBase (object):
    def __init__(self, namepath):
        self._np = namepath

    @property
    def namepath(self):
        return '.'.join(self._np)


class MissingParam (TemplatePathBase):
    def __repr__(self):
        return '<Missing {0}>'.format(self.namepath)

    def __getattr__(self, name):
        return self


class TemplateParamBase (TemplatePathBase):
    def __init__(self, value, namepath):
        self._v = value
        TemplatePathBase.__init__(self, namepath)

    def __repr__(self):
        return '<{0} {1!r}>'.format(type(self).__name__, self._v)

    @property
    def len(self):
        return len(self._v)


class AttrDictTemplateParam (TemplateParamBase):
    def __getattr__(self, name):
        item = self._v.get(name, MissingParam)
        return wrap_template_param(item, self._np, name)


class ListTemplateParam (TemplateParamBase):
    def __init__(self, value, namepath, wrapped=False):
        if not wrapped:
            value = [
                wrap_template_param(x, namepath, '[{0}]'.format(i))
                for (i, x) in enumerate(value)
                ]
        TemplateParamBase.__init__(self, value, namepath)

    def __getitem__(self, ix):
        if isinstance(ix, int):
            return self._get_index(ix)
        else:
            return self._star_lookup(ix)

    def _get_index(self, ix):
        try:
            return self._v[ix]
        except IndexError:
            return wrap_template_param(MissingParam, self._np, '[{0}]'.format(ix))

    def _star_lookup(self, ix):
        assert ix.startswith('*.'), `ix`
        namepath = ix[2:].split('.')
        result = self._v
        for name in namepath:
            result = [ getattr(x, name) for x in result ]
        return ListTemplateParam( result, self._np + [ix], wrapped=True )

    @property
    def comma_separated(self):
        return self._join_with(u', ')

    @property
    def newline_separated(self):
        return self._join_with(u'\n')

    def _join_with(self, separator):
        return separator.join( unicode(self[i]) for i in range(self.len) )


class UnicodeTemplateParam (TemplateParamBase):
    def __unicode__(self):
        r = repr(self._v.strip())

        if len(r) > 121:
            return u'{0}{1}… (truncated)'.format(r[:121], r[0])
        else:
            return r

    @property
    def bare(self):
        return self._v

    @property
    def urlencoding(self):
        return self._v.replace('^', '%5E')
