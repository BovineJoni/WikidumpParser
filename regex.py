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

"""WikidumpParser - regex module
-----------------------------------------------------------

Note:
    Collection of regular expressions needed for
    parsing wikipedia markup syntax.
-----------------------------------------------------------
"""
import re

html_entities = re.compile(r"""
    (?P<html_entities>&([^;]+);)    # html entities
    """, flags=re.VERBOSE | re.MULTILINE)

first_pass = re.compile(r"""
    (?P<tables>\n?{\|(.|\n)*?\|})|  # tables
    (?P<curly_brackets>\n?{(.|\n)*?}+([^{]+}+)?)   # curly brackets
    
    """, flags=re.VERBOSE | re.MULTILINE)

second_pass = re.compile(r"""
                    (?P<single_curbrac>{(\n?\s?)+)| # single open curly brackets
                    (?P<headings>\n?^={1,6}.+?={1,6}\s?\n?)|    # headings
                    (?P<comments><!--((.|\n)*?)-->\s?\n?)|  # comments
                    (?P<nowiki>\n?(<nowiki>(?P<nowiki_keep>(.|\n)*?))</\s*?nowiki>)|  # nowiki
                    (?P<regular_tags>\n?<(?P<tagname>\w*)(\b[^>])*>((.|\n)*?)</(?P=tagname)>)|  # regular tags
                    (?P<tags>\n?(<[^<>/]+>((.|\n)*?))?</[\w\s]+>)| # tags
                    (?P<single_tags>\n?<.+?/>)| # single tags
                    (?P<link>(\[\[)(?P<link_keep>(((.|\n)*?))(\[\[(.|\n)+?\]\].*?)*?(\[[^[]]+?\].*?)*?)(\]\]))| # link
                    (?P<redirect>\s?\#REDIRECT\s\[\[.+?\]\]([^\s]+)?)|  # redirect
                    (?P<html_entities>&([^; ]+);)|  # html entities (2nd pass)
                    (?P<single_link>(\[)(?P<slink_keep>.+?)(\]))| # single link
                    (?P<lists>\n?^[*#:;|!]+[^{\n]*\s?\n?)  # lists
                    """, flags=re.VERBOSE | re.MULTILINE)

emptylines = re.compile(r"\n{3,}")

curly_brackets = re.compile(r"[{}]")
left_brace = re.compile(r"{")
right_brace = re.compile(r"}")
revert_comment = re.compile(r"(^|\s)rv(\s|$)|(^|\s)revert")
link_blacklist = re.compile(r"((\w[-]?)+:|:)(.|\n)+?")
opening_brackets = re.compile(r"(?P<valid>{+[^{]*?}+)|(?P<del>{+[^{}]*)")
closing_brackets = re.compile(r"(?P<valid>{+[^{]*?}+)|(?P<del>[^{}]*}+)")
inv_clos_brackets = re.compile(r"[^{]+}+")
template_name = re.compile(r"""(?P<convert>(\s*?)(C|c)onvert(\s*?)\|(?P<arg1>.+?)\|(?P<arg2>.+?)
    (\|(?P<arg3>.+?)\|(?P<arg4>.+?))?(\||}))|
(?P<temp_name>.*?(?=\||}}))""", flags=re.VERBOSE)
template_tail = re.compile(r"^[.,;:!?-]")
templates = re.compile(r"{{(?P<temp_name>.+?)(\|).+?}}")