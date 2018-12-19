# -*- coding: utf-8 -*-

import os

from ..utils import get_page_layout, get_text_objects


class BaseParser(object):
    """Defines a base parser.
    """
    def _generate_layout(self, filename, layout_kwargs):
        self.filename = filename
        self.layout_kwargs = layout_kwargs
        self.layout, self.dimensions = get_page_layout(
            filename, **layout_kwargs)
        self.horizontal_text = get_text_objects(self.layout, ltype="lh")
        self.vertical_text = get_text_objects(self.layout, ltype="lv")
        self.pdf_width, self.pdf_height = self.dimensions
        self.rootname, __ = os.path.splitext(self.filename)
