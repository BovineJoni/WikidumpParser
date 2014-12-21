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

"""WikidumpParser - article module
-----------------------------------------------------------

Note:
    Class for saving wikipedia articles. An article can
    have multiple entries of multiple authors.
-----------------------------------------------------------
"""
from __future__ import division

class article(object):
    def __init__(self, article_id, article_title):
        self.article_id = article_id
        self.article_title = article_title
        self.authors = 0
        self.entries = []
        self.lines = 0

    def append(self, entry):
        """Append new entry to article."""
        self.entries.append(entry)
        self.authors = len(set(map(lambda entry: entry.author_id, self.entries)))
        self.lines += entry.len

    def current_pos(self):
        """Return current length of the article."""
        if len(self.entries) != 0:
            return self.entries[-1].end
        return 0