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

"""WikidumpParser - parser module
-----------------------------------------------------------

Note:
    Parser module for parsing wikipedia markup syntax into
    english sentences by multi pass regular expressions. 
-----------------------------------------------------------
"""
import HTMLParser
import logging
import regex
import time
import utils

apostrophes = ["'''''", "''''", "'''", "''"]
double_space = ['  ']
horizontal = ['\n----']
html_delete = ['<br>']
magicwords = ['FORETOC', 'TOC', 'NOTOC', 'NOEDITSECTION', 'NEWSECTIONLINK', 
'NONEWSECTIONLINK', 'NOGALLERY', 'HIDDENCAT', 'INDEX', 'NOINDEX', 'STATICREDIRECT', 'DISAMBIG']
magicwords = ['__'+str(m)+'__' for m in magicwords]
newlines = ['\n\n', '\n']
newlines = []
signature = ['~~~~~', '~~~~', '~~~']
strip_punctuation = [' .', ' ,', ' ;', ' !', ' ?', ' :']

remove_strings = apostrophes + horizontal + magicwords + signature
to_space = newlines + double_space + html_delete
remove_all = False
htmlParser = HTMLParser.HTMLParser()

def first_pass(string):
    """Filter html entities and check if wiki-markup is malformed."""
    temp = regex.html_entities.sub(unescape, string)
    is_malformed = False
    malformed = False

    found_pos = 0
    while(found_pos != -1):
        found_pos = temp.find("{", found_pos)
        if found_pos != -1:
            add_temp, malformed = remove_bracket(temp[found_pos:])
            if malformed:
                is_malformed = True
            temp = temp[:found_pos] + add_temp

    for r in remove_strings:
        temp = temp.replace(r, "")
    return temp, is_malformed

def second_pass(string):
    """Parse syntax and filter markup."""
    temp = regex.second_pass.sub(process_reg, string)
    temp = regex.emptylines.sub("\n\n", temp)
    for t in to_space:
        temp = temp.replace(t, " ")
    for s in strip_punctuation:
        temp = temp.replace(s, s.lstrip(' '))
    return temp

def parse_wiki_text(string, get_cropped=False):
    """Parse wiki text."""
    if string is None:
        return ""
    
    is_malformed = False
    string, is_malformed = first_pass(string)
    
    if is_malformed:
        return "", True
    
    string = second_pass(string)
    string = string.strip()
    result = []

    for segment in string.split("\n\n"):
        if len(segment) > 10000:
            is_malformed = True
            break
        result += utils.split_sentences(segment)
        result.append("")
    
    if len(result) > 0 and result[-1] == "":
        result.pop()

    return result, is_malformed
  
def parse_wiki_text_cropped(string):
    """Parse wiki text and return cropped paragraphs (paras of length > 2)."""
    if string is None:
        return ""
  
    is_malformed = False
    string, is_malformed = first_pass(string)
  
    if is_malformed:
        return "", "", True
    
    string = second_pass(string)
    string = string.strip()
    result = []
    cropped = []

    for segment in string.split("\n\n"):
        if len(segment) > 10000:
            is_malformed = True
            break
        add_segment = utils.split_sentences(segment)
        result += add_segment
        result.append("")

        if len(add_segment) > 2:
            cropped += add_segment
            cropped.append("")

    if len(cropped) > 0 and cropped[-1] == "":
        cropped.pop()
    if len(result) > 0 and result[-1] == "":
        result.pop()

    return result, cropped, is_malformed

def remove_bracket(string):
    """Remove curly brackets from text (templates)."""
    open_brackets = 0
    cur_pos = 0
    job_done = False
    dummy_result = ""

    while job_done is False:
        match = regex.curly_brackets.search(string, cur_pos)

        if match is None:
            return recover_malformed(string, open_brackets), True

        if match.group() == "{":
            open_brackets += 1
        elif match.group() == "}":
            open_brackets -= 1

        cur_pos = match.start() + 1

        if cur_pos == 2 and open_brackets == 2:
            # check if template is one of the following
            temp_name = regex.template_name.match(string[cur_pos:])
            if temp_name is not None:
                if temp_name.lastgroup == "convert":
                    dummy_result = utils.dummy_conv_result((temp_name.group('arg1'), temp_name.group('arg2'),
                    temp_name.group('arg3'), temp_name.group('arg4')))
                else:
                    temp_name = temp_name.group().strip().lower().replace(" ", "_")
                    dummy_result = utils.dummy_temp_result(temp_name)

        if open_brackets == 0:
            invalid_post_string = regex.inv_clos_brackets.match(string, cur_pos)
  
            if invalid_post_string:
                cur_pos = invalid_post_string.end()
  
            return dummy_result + string[cur_pos:], False

def recover_malformed(string, open_brackets):
    """Recover from malformed syntax."""
    # Since malformed revisions don't get saved, don't even try to repair them.
    # If revision should get repaired just remove the next line.
    return ""

    cur_pos = 0
    too_many_open = None
    # print open_brackets
    if open_brackets > 0:
        # print "too many opening brackets"
        too_many_open = True
    elif open_brackets < 0:
        # print "too many closing brackets"
        too_many_open = False

    # repair
    while(True):
        if too_many_open:
            match = regex.opening_brackets.search(string, cur_pos)
        elif too_many_open is False:
            match = regex.closing_brackets.search(string, cur_pos)

        if match is None:
            # done
            return string[cur_pos:].lstrip(" ")
        elif match.lastgroup == "del":
            cur_pos = match.end()
        elif match.lastgroup == "valid":
            cur_pos = match.end()
            opening = string[cur_pos:].count("{")
            closing = string[cur_pos:].count("}")

            if opening > closing:
                # still too many open
                too_many_open = True
            elif opening < closing:
                # now too many closed ones
                too_many_open = False
            else:
                # valid braces now
                return string[cur_pos:].lstrip(" ")

def process_reg(matched):
    """Delete or parse markup."""
    group = matched.lastgroup
    del_completely = ("comments", "headings", "lists", 
        "redirect", "regular_tags", "single_curbrac", "single_tags", "tags")

    if group in del_completely:
        return ""

    elif group == "html_entities":
        return htmlParser.unescape(matched.group())

    elif group == "link":
        start = ""
        if matched.group('link').startswith(" "):
            start = " "

        tail = ""
        if matched.group('link').endswith(" "):
            tail = " "

        link_text = matched.group('link_keep')
        if link_text.lower().startswith("wikt:"):
            link_text = link_text[5:]

        if regex.link_blacklist.match(link_text):
            return ""

        stripped_text = split_link(link_text, '|')
        stripped_text = start + stripped_text + tail
        return regex.second_pass.sub(process_reg, stripped_text)

    elif group == 'nowiki':
        return matched.group('nowiki_keep')

    elif group == "single_link":
        start = ""
        if matched.group('single_link').startswith(" "):
            start = " "
        tail = ""
        if matched.group('single_link').endswith(" "):
            tail = " "

        link_text = matched.group('slink_keep')
        stripped_text = split_link(link_text, ' ', False)
        if stripped_text != "":
            stripped_text = start + stripped_text + tail
        return regex.second_pass.sub(process_reg, stripped_text)

    else:
        logging.warning(u"----unknown group <{}>, content:\n{}".format(group, matched.group(group)).encode("UTF-8")) 
        return ""

def split_link(string, split_by, keep_if_not_splittable=True):
    """Process link (return URL if no alternative text is given)."""
    try:
        result = string.split(split_by, 1)
        if result[1] != "":
            return result[1]
        else:
            return result[0]
    except IndexError:
        if keep_if_not_splittable:
            return string
        else:
            return ""

def unescape(matched):
    """Remove html tags."""
    return htmlParser.unescape(matched.group())
