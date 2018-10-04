# -*- coding: utf-8 -*-

import os

from ..utils import get_page_layout, get_text_objects


class BaseParser(object):
    """Defines a base parser.
    """
    def _generate_layout(self, filename):
        self.filename = filename
        self.layout, self.dimensions = get_page_layout(
            self.filename,
            char_margin=self.char_margin,
            line_margin=self.line_margin,
            word_margin=self.word_margin)
        self.horizontal_text = get_text_objects(self.layout, ltype="lh")
        self.vertical_text = get_text_objects(self.layout, ltype="lv")
        self.pdf_width, self.pdf_height = self.dimensions
        self.rootname, __ = os.path.splitext(self.filename)
