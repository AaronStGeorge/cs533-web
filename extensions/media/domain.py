"""
Sphinx extension to implement video support
"""

import re
from dataclasses import dataclass

from docutils import nodes
from sphinx.application import Sphinx
from sphinx.roles import XRefRole
from sphinx.domains import Domain, ObjType
from sphinx.util.nodes import make_id, make_refnode

from .module import ModuleDirective
from .video import VideoDirective


EMOJI_DEFS = {
    'module': '📅',
    'video': '🎥'
}

_vl_re = re.compile(r'(\d+)m(\d+)s')
_pfx_re = re.compile('^(\d+-\d+\s+-\s+)?(.*)')


@dataclass
class MediaObject:
    name: str
    title: str
    type: str
    docname: str
    anchor: str
    module: str = None

    def astuple(self):
        """
        Convert this object into a tuple suitable for get_objects().
        """
        return (self.name, self.display_title, self.type, self.docname, self.anchor, 1)

    @property
    def display_title(self):
        icon = EMOJI_DEFS.get(self.type, None)
        return f'{icon} {self.title}' if icon else self.title


@dataclass
class Video(MediaObject):
    length: str = None

    def vid_length(self):
        if self.length:
            m = _vl_re.match(self.length)
            mins = float(m.group(1))
            secs = float(m.group(2))
            return mins * 60 + secs


class CourseDomain(Domain):
    name = 'res'
    label = 'Course'

    object_types = {
        'video': ObjType('video', 'video'),
        'module': ObjType('module', 'module'),
    }
    directives = {
        'module': ModuleDirective,
        'video': VideoDirective,
    }
    roles = {
        'module': XRefRole(),
        'video': XRefRole()
    }

    def _dom_objects(self):
        return self.env.domaindata['res'].setdefault('objects', [])

    def note_module(self, key, title):
        docname = self.env.docname
        mod = MediaObject(key, title, 'module', docname, key)
        self._dom_objects().append(mod)

    def note_video(self, key, id, name, length):
        modname = self.env.ref_context.get('res:module')
        fullkey = f'{modname}:{key}' if modname else key
        docname = self.env.docname

        if name:
            trunc = _pfx_re.match(name).group(2)
        else:
            trunc = '<untitled video>'

        mod = Video(fullkey, trunc, 'video', docname, id, modname, length)
        mod.full_name = name

        self._dom_objects().append(mod)

    def resolve_xref(self, env, fromdocname, builder, type, target, node, contnode):
        objects = self._dom_objects()

        tgt = None
        for candidate in objects:
            if candidate.name == target:
                tgt = candidate
                break

        if not tgt:
            return None

        label = tgt.display_title
        content = nodes.inline('', label)

        return make_refnode(builder, fromdocname, tgt.docname, tgt.anchor, content, tgt.name)
