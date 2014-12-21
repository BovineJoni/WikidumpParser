# -*- coding: utf-8 -*-

# WikidumpParser, Copyright 2014 Daniel Schneider.
# schneider.dnl(at)gmail.com

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""WikidumpParser - entry module
-----------------------------------------------------------

Note:
    Class for saving article entries. An entry has an author,
    a starting and ending line number and the corresponding
    text.
-----------------------------------------------------------
"""
from __future__ import division

class entry(object):

    def __init__(self, author_id, text, start, end=None):
        self.author_id = author_id
        self.start = start
        self.len = len(filter(lambda t: t != "", text))
        if end is None:
            self.end = start + self.len
        else:
            self.end = end
        self.text = '\n'.join(text)

    def __repr__(self):
        return "author {} // {} - {} text:\n{}".format(self.author_id, self.start, self.end, self.text)

    def __str__(self):
        return "author {} // {} - {} text:\n{}".format(self.author_id, self.start, self.end, self.text)