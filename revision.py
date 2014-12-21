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

"""WikidumpParser - revision module
-----------------------------------------------------------

Note:
    Revision class for saving revisions of an article. A revision has
    a contributor (author), the wiki-text, the corresponding
    parsed text and an md5-hash value.
    a starting and ending line number and the corresponding
    text.

    Contributor class for saving the contributor of a revision.
    A valid contributor has an id and a name (an ip adress is
    not enough).
-----------------------------------------------------------
"""
import re

class Revision(object):
    def __init__(self, values, contributor):
        """init"""
        if values['text'] is None:
            values['text'] = u''
        self.rev_id, self.timestamp = values['id'], values['timestamp']
        self.contributor = contributor
        self.is_malformed = False
        self.wiki_text, self.parsed_text, self.size = values['text'], None, len(values['text'].encode('UTF-8'))
        self.md5, self.model, self.format = values['sha1'], values['model'], values['format']


    def __repr__(self):
        return 'Revision({},"{}",{},"{}","{}","{}", "{}")'.format(self.rev_id, 
            self.timestamp, self.contributor, self.wiki_text, 
            self.md5, self.model, self.format)

    @property
    def model(self):
        return self._model

    @model.setter
    def model(self, model):
        if model != 'wikitext':
            raise ValueError('Bad model: ' + model)
        self._model = model

    @property
    def format(self):
        return self._format

    @format.setter
    def format(self, format):
        if format != 'text/x-wiki':
            raise ValueError('bad format')
        self._format = format


class Contributor(object):
    def __init__(self, con_id=None, name=None, ip=None):
        if con_id is None and name is None and ip is None:
            self.con_id, self.name, self.ip = con_id, name, ip    
            raise ValueError('Bad Contributor attributes'+str(con_id)+' '+str(name)+' '+str(ip))
        self.con_id, self.name, self.ip = con_id, name, ip
        if name is not None:
            self.name = re.sub(r'[/?*:;{}\\]+', '_', name)

    def __repr__(self):
        return 'Contributor({},"{}","{}")'.format(
            self.con_id, self.name, self.ip)

    def get_idName(self):
        """Return string combination of id and name.""" 
        return self.con_id + '_' + self.name