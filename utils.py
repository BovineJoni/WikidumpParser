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

"""WikidumpParser - utils module
-----------------------------------------------------------

Note:
    utilities: dumpfile utils, parser utils, xml utils 
-----------------------------------------------------------
"""
from __future__ import division
from collections import deque
from collections import OrderedDict
from datetime import timedelta
from lxml import etree
from random import randint
import codecs
import datetime
import difflib
import nltk
import os

differ = difflib.Differ()
seq_matcher = difflib.SequenceMatcher()

nltk_data_path = os.path.join(os.path.dirname(__file__), 'nltk_data')
nltk.data.path += [nltk_data_path,]
sent_tokenizer = nltk.data.load('tokenizers/punkt/english.pickle')
abbreviations = set(['e.g', 'i.e', 'b.c', 'a.d', 'ca', 'b.s', 'etc', 'esp', 'cf', 'chr', 'f.o.t', 'stat', 'f.o.c', 'b.sc', 'm.sc'])
sent_tokenizer._params.abbrev_types.update(abbreviations)

units = {
    "um" : u"μm",
    "angstrom" : u"Å",
    "km2" : u"km²",
    "m2" : u"m²",
    "cm2" : u"cm²",
    "mm2" : u"mm²",
    "sqmi" : ("square miles", "square mile"),
    "sqyd" : ("square yards", "square yard"),
    "sqft" : "square foot",
    "sqfoot" : "square foot",
    "sqin" : ("square inches", "square inch"),
    "sqnmi" : ("square nautical miles", "square nautical miles"),
    "sqyd" : u"sq yd",
    "m3" : u"m³",
    "cm3" : u"cm³",
    "mm3" : u"mm³",
    "cuft" : ("cubic feet", "cubic foot"),
    "cufoot" : ("cubic feet", "cubic foot"),
    "cuin" : ("cubic inches", "cubic inch"),
    "impbbl" : "imp bbl",
    "impbsh" : "imp bsh",
    "impbu" : "imp bu",
    "impgal" : "imp gal",
    "impqt" : "imp qt",
    "imppt" : "imp pt",
    "impoz" : "imp fl oz",
    "impfloz" : "imp fl oz",
    "USbbl" : ("US barrels", "US barrel"),
    "U.S.bbl" : ("US barrels", "US barrel"),
    "oilbbl" : ("barrels", "barrel"),
    "USbeerbbl" : ("US beer barrels", "US beer barrel"),
    "usbeerbbl" : ("US beer barrels", "US beer barrel"),
    "U.S.beerbbl" : ("US beer barrels", "US beer barrel"),
    "USgal" : ("US gallons", "US gallon"),
    "U.S.gal" : ("US gallons", "US gallon"),
    "USqt" : "US qt",
    "U.S.qt" : "U.S. qt",
    "USpt" : ("US pints", "US pint"),
    "U.S.pt" : ("US pints", "US pint"),
    "USoz" : ("US fluid ounces", "US fluid ounce"),
    "USfloz" : ("US fluid ounces", "US fluid ounce"),
    "U.S.oz" : ("US fluid ounces", "US fluid ounce"),
    "U.S.floz" : ("US fluid ounces", "US fluid ounce"),
    "USdrybbl" : "US dry bbl",
    "U.S.drybbl" : "U.S. dry bbl",
    "USbsh" : "US bsh",
    "U.S.bsh" : "U.S. bsh",
    "USbu" : "US bu",
    "U.S.bu" : "U.S. bu",
    "USdrygal" : "US dry gal",
    "U.S.drygal" : "U.S. dry gal",
    "USdryqt" : "US dry qt",
    "U.S.dryqt" : "U.S. dry qt",
    "USdrypt" : "US dry pt",
    "U.S.drypt" : "U.S. dry pt",
    "foot/s" : ("feet/s", "foot/s"),
    "uN" : u"µN",
    "t-f" : "tf",
    "kg-f" : "kgf",
    "g-f" : "gf",
    "mg-f" : "mgf",
    "LT-f" : "LTf",
    "ST-f" : "STf",
    "lb-f" : "lbf",
    "gr-f" : "grf",
    "uJ" : u"µJ",
    "TW.h" : "TW h",
    "GW.h" : "GW h",
    "MW.h" : "MW h",
    "kW.h" : "kW h",
    "W.h" : "W h",
    "ftpdl" : "ft pdl",
    "ftlbf" : "ft lbf",
    "ftlb-f" : "ft lbf",
    "inlbf" : "in lbf",
    "inlb-f" : "in lbf",
    "inozf" : "in ozf",
    "inoz-f" : "in ozf",
    "hph" : "hp h",
    "GtTNT" : "gigatonne of TNT",
    "GtonTNT" : "gigaton of TNT",
    "MtTNT" : "megatonne of TNT",
    "MtonTNT" : "megaton of TNT",
    "ktTNT" : "kilotonne of TNT",
    "ktonTNT" : "kiloton of TNT",
    "tTNT" : "tonne of TNT",
    "tonTNT" : "ton of TNT",
    "cuftnaturalgas" : "cubic foot of natural gas",
    "cufootnaturalgas" : "cubic foot of natural gas",
    "latm" : u"l·atm",
    "Latm" : u"L·atm",
    "impgalatm" : u"imp gal·atm",
    "USgalatm" : u"US gal·atm",
    "usgalatm" : u"US gal·atm",
    "U.S.galatm" : u"U.S. gal·atm",
    "C" : u"°C",
    "R" : u"°R",
    "F" : u"°R",
    "C-change" : u"°C",
    "F-change" : u"°F",
    "ug" : u"µg",
    "MT" : "t",
    "Nm" : u"N·m",
    "N-m" : u"N·m",
    "kgf-m" : u"kgf·m",
    "lbf-ft" : u"lbf·ft",
    "kg/m3" : u"kg/m³",
    "g/m3" : u"g/m³",
    "lb/ft3" : "lb/cu ft",
    "lb/yd3" : "lb/cu yd",
    "/sqkm" : "per square kilometre",
    "/ha" : "per hectare",
    "/sqmi" : "per squeare mile",
    "/acre" : "per acre",
}


"""Dumpfile utils"""
class MyList(deque):
    """A simple list which provides the function of getting the distance to the nearest identical value."""
    def distance_to_ident_value(self):
        """Get distance of the last element added to the identical value in the list."""
        for i in xrange(len(self)-2, -1, -1):
            if self[len(self)-1] == self[i]:
                return len(self)-1-i
        return -1

    def append(self, item):
        super(MyList, self).append(item)

class MyDeque(deque):
    """Self resizing deque."""
    def __init__(self, limit):
        self.limit = limit
        super(MyDeque, self).__init__()

    def append(self, item):
        if len(self) == self.limit:
            self.popleft()
        super(MyDeque, self).append(item)

def check_tag(tag, tag_name, tag_text=None):
    """Check if tag corresponds to given arguments."""
    if tag_text is None and tag.tag != tag_name:
        return False
    elif tag.tag != tag_name or tag.text != tag_text and tag_text is not None:
        return False
    else: return True

def isWritable(directory):
    """Check if directory is writable.

    Code by user 'khattam' at stackoverflow.com.
    """
    try:
        tmp_prefix = "write_tester"
        count = 0
        filename = os.path.join(directory, tmp_prefix)
        while(os.path.exists(filename)):
            filename = "{}.{}".format(os.path.join(directory, tmp_prefix),count)
            count = count + 1
        f = open(filename,"w")
        f.close()
        os.remove(filename)
        return True
    except Exception:
        return False


"""Parser utils"""
def dummy_temp_result(string):
    """Return dummy for temporal template."""
    date_templates = ("bda", "birth_date", "birth_date_and_age", "date", 
        "death_date_and_age", "death_year_and_age", "dob", "dda", "end_date", "start_date")

    if string in date_templates:
        return random_date(datetime.date(1900, 01, 01), 
            datetime.date(2013, 01, 19)).strftime("%d %B %Y") + " "
    elif string == "age":
        return str(randint(1, 250)) + " "
    elif string == "currentyear":
        return random_date(datetime.date(1900, 01, 01), 
            datetime.date(2013, 01, 19)).strftime("%Y") + " "
    elif string == "time_ago":
        return str(randint(2, 500))+" years ago "
    elif string == "as_of":
        return "As of " + random_date(datetime.date(1900, 01, 01), 
            datetime.date(2013, 01, 19)).strftime("%B %Y") + " "
    else:
        return ""

def dummy_conv_result(arguments):
    """Return dummy for converting template."""
    arguments = [arg.strip() for arg in arguments if arg is not None]
    for arg in arguments:
        if "{" in arg or "}" in arg:
            return ""

    if arguments[1].strip() in ("and", "to", "-", "x", "+/-") and len(arguments) == 4:
        arguments[3] = format_conv_result(2, arguments[3])
        return u"{0}{1}{2} {3}".format(*arguments) 
    else:    
        temp_unit = format_conv_result(arguments[0], arguments[1])
        return u"{0} {1} ".format(arguments[0], temp_unit)

def format_conv_result(value, unitcode):
    """Return formatted unit (see units-dictionary)."""
    try:
        unit = units[unitcode]
        try:
            if type(unit) is tuple:
                if int(value) == 1:
                    unit = unit[1]
                else:
                    unit = unit[0]
        except ValueError:
            unit = unit[0]
    except KeyError:
        unit = unitcode
    return unit

def random_date(start, end):
    """Return a random date between start- and end-date."""
    return start + timedelta(
        seconds=randint(0, int((end - start).total_seconds())))

def split_sentences(string):
    """Returned list of sentences."""
    string = string.strip()
    string = string.replace("\n", " ")
    l = sent_tokenizer.tokenize(string.strip(), realign_boundaries = True)
    return l
    

def filter_additions(diff_delta):
    """Filter diff by returning only additions spanning over at least three consecutive full sentences."""
    added = []
    removed = []
    last_actions = MyDeque(2)
    sequence_counter = 0
    last_append = -2

    for i, element in enumerate(diff_delta):
        if element.startswith('+'):
            if (len(last_actions) == 2 and last_actions[-1] == '?'
                and last_actions[-2] == '-'):
                last_actions.append('?') # helper to avoid popleft() if seq: -,?,+,? => -,?,?,?
            else:
                add = element.lstrip('+ ')
                if i != last_append + 1:
                    # check if sequence is shorter then 3 sentences
                    if sequence_counter < 2 and len(added) > 0:
                        while sequence_counter >= 0:
                            added.pop()
                            sequence_counter -= 1

                    sequence_counter = 0
                    if len(added) != 0 and add != "" and added[-1] != "":
                        added.append("")

                if add != "":
                    if i == last_append + 1:
                        sequence_counter += 1
                    added.append(add)
                    last_append = i

                last_actions.append('+')

        elif element.startswith('-'):
            last_actions.append('-')
            removed.append(element.lstrip('- '))

        elif element.startswith('?'):
            if last_actions[-1] == '+':
                added.pop()
            elif last_actions[-1] == '-':
                removed.pop()
            last_actions.append('?')

    if sequence_counter < 2 and len(added) > 0:
        while sequence_counter >= 0:
            added.pop()
            sequence_counter -= 1

        if len(added) > 0 and added[-1] == "":
            added.pop()

    return [a for a in added if a not in removed or a == ""]


def get_additions(string1, string2):
    """Make diff of two strings and return only additions."""
    delta = differ.compare(string1, string2)
    additions_only = filter_additions(delta)
    return additions_only


"""XML utils"""
def create_xml_tree(article_id, title, authors=0, lines=0):
    """Create new xml_tree.

    xml version 1.0, utf-8. root-element article_id, article_title etc. and return element_tree.
    """
    title = title.encode('UTF-8')
    root = etree.XML('<?xml version="1.0" encoding="UTF-8"?><article article_id="{}" title="{}" authors="{}" lines="{}"></article>'.format(article_id, title, authors, lines))

    return etree.ElementTree(root)

def get_xml_tree(filename):
    """Read existing xml-file and return element_tree."""
    with codecs.open(filename, 'r', 'UTF-8') as xml_file:
        return etree.parse(xml_file)

def add_entry(root_element, attributes, text):
    """Add entry to root-element."""
    new_entry = etree.Element("entry", attributes)
    new_entry.text = text
    root_element.append(new_entry)

