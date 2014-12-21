# -*- coding: utf-8 -*-
#!/usr/bin/env python

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

"""WikidumpParser - wikidump module
-----------------------------------------------------------

Use:
    Parse wikidump files by setting the right paths
    in the config file. The script was tested with files
    from 2013/06/04:
    'All pages with complete page edit history (.bz2)'
    http://dumps.wikimedia.org/enwiki/

Note:
    You can add new dump files during the runtime of the script
    (there is a checking for newly added files after the
    processing of one file ends).

Config file ".\\config.cfg":
    dump_file_path: path to the dumpfiles (every bz2-file in
            this directory is getting processed)
    outdir_path: path where to store parsed articles
    backup_path: path where backup zip-files get stored
        (backups are made after each dump-file)
    max_revisions: number of revisions after which to stop
        processing an article
    revsize_threshold: minimum bytes added by a revision to
        consider it
    del_files: turn deleting of wikidump files on (1) and off (0)
-----------------------------------------------------------
"""
from article import article
from collections import deque
from entry import entry
from lxml import etree
from multiprocessing import Pool
from multiprocessing import TimeoutError
from revision import Contributor
from revision import Revision
import bz2
import codecs
import ConfigParser
import datetime
import glob
import logging
import os
import parse
import regex
import sys
import time
import utils
import zipfile

class WikiDump(object):
    """WikiDump class - parses a wikidump.bz2 file"""
    # _NS = '{http://www.mediawiki.org/xml/export-0.8/}'
    _NS = None
    _DEL_FILES = False
    _MAX_REVISIONS = 3000
    _REVSIZE_THRESHOLD = 1000

    def __init__(self, dump_filepath, outputdir, logfiledir=None):
        """Initializes a WikiDump object

        Args:
            dump_filepath: A path to a bz2 wikipedia dump file.
            outputdir: The output directory path where the resulting
                    text corpus should get saved.
            logfiledir: An optional path for the logfile, 
                    if it is not set, the logfile will 
                    get saved in the same directory 
                    as the outputdir.
        """
        self.dump_filepath, self.outputdir = dump_filepath, outputdir
        if logfiledir is None:
            self.logfiledir = outputdir
        self.dump_file, self.dump_filename, self.logfile = None, None, None
        self.check_files()
        self.pool = Pool(processes=2)
        self.templates = {}

        init_logging(self.logfile)
        logging.info('Parser up and running.')

    def check_files(self):
        """Checks if dump_file, outputdir & logfile are valid"""
        try:
            tail = os.path.split(self.dump_filepath)[1]
            ext = os.path.splitext(tail)[1]
            if ext == '.bz2':
                self.dump_file = bz2.BZ2File(self.dump_filepath, "r", 2048)
            elif ext == '.xml':
                self.dump_file = file(self.dump_filepath, "r", 1024)
        except IOError, e:
            logging.error('Could not open dump file: {}'.format(e))
            sys.exit(1)

        try:
            if not os.path.exists(self.outputdir):
                os.makedirs(self.outputdir)
            if not utils.isWritable(self.outputdir):
                logging.warning('Outputdir "{}" is not writable\n'.format(self.outputdir))
                raise IOError("[Errno 13] Permission denied: '{}'".format(self.outputdir))

        except (OSError, IOError), e:
            logging.error('Outputdir "{}" not created: {}'.format(self.outputdir, e))
            sys.exit(1)

        try:
            if not os.path.exists(self.logfiledir):
                os.makedirs(self.logfiledir)
            if not utils.isWritable(self.logfiledir):
                logging.warning('Logfiledir "{}" is not writable\n'.format(self.logfiledir))
                raise IOError("[Errno 13] Permission denied: '{}'".format(self.logfiledir))
            else:
                tail = os.path.split(self.dump_filepath)[1]
                self.dump_filename = os.path.splitext(tail)[0]
                self.logfile = os.path.join(self.logfiledir, self.dump_filename+'.log')
                open(self.logfile,"w").close()

        except (OSError, IOError), e:
            logging.error('Logfile "{}" not created: {}'.format(self.logfile, e))
            sys.exit(1)

    def process_dump(self):
        """Process and parse the dump_file."""
        self.usable_pages = 0
        self.total_pages = 0
        
        self.usable_revisions = 0
        self.total_revisions = 0
        self.actual_revisions = 0
        self.skipped_revisions = 0
        stop = False

        with self.dump_file as f:
            ns_not_set = True
            iter_tree = etree.iterparse(f, events=("start", "end"))
            for event, elem in iter_tree:
                if ns_not_set:
                    WikiDump._NS = "{"+etree.QName(elem).namespace+"}"
                    ns_not_set = False

                # if self.usable_pages > 0:
                #     break

                if stop:
                    break

                if event == "start" and elem.tag == self._NS + "page":
                    current_page = elem
                    self.total_pages += 1
                    page_id = None
                    page_meta_processed = False
                    skip_page = False

                    self.rev_old = None
                    self.rev_new = None
                    self.revision_count = 0
                    self.md5hash_list = utils.MyList()
                    self.current_article = None

                    for event, elem in iter_tree:
                        if page_meta_processed == False:
                            if event == "start" and elem.tag == self._NS + "title":
                                self.article_title = elem.text
                            elif event == "start" and elem.tag == self._NS + "id":
                                self.article_id = elem.text

                            if event == "start" and elem.tag == self._NS + "revision":
                                page_meta_processed = True
                                if skip_page:
                                    logging.info("skip page {}".format(page_id))
                                else:
                                    logging.info("processing page {}".format(page_id))
                                    self.usable_pages += 1
                                    self.current_article = article(self.article_id, self.article_title)

                            elif event == "end" and elem.tag == self._NS + "ns" and elem.text != "0":
                                skip_page = True
                            elif event == "end" and elem.tag == self._NS + "id":
                                page_id = elem.text
                            elif event == "end" and elem.tag == self._NS + "redirect":
                                skip_page = True

                        if event == "start" and elem.tag == self._NS + "revision":
                            if self._MAX_REVISIONS != -1 and self.revision_count >= self._MAX_REVISIONS:
                                if not skip_page:
                                    logging.info("maximum revisions ({}) reached. page-id {}".format(self._MAX_REVISIONS, page_id))
                                    skip_page = True
                                self.skipped_revisions += 1
                            self.process_rev(elem, iter_tree, skip_page)

                        elif event == "end" and elem.tag == self._NS + "page":
                            # print "PAGE ENDET"
                            if self.current_article and self.current_article.authors > 0:
                                xml_tree = utils.create_xml_tree(self.current_article.article_id, self.current_article.article_title, self.current_article.authors, self.current_article.lines)


                                for e in self.current_article.entries:
                                    attr = {"author_id":e.author_id,
                                            "start":str(e.start),
                                            "end":str(e.end)}
                                    text = e.text
                                    utils.add_entry(xml_tree.getroot(), attr, text)
                                
                                pathname = os.path.join(self.outputdir, self.current_article.article_id)
                                if not os.path.exists(pathname):
                                    # print "didnt exist - create"
                                    os.makedirs(pathname)
                                filename = os.path.join(pathname, self.current_article.article_id+'_'+self.current_article.article_title+'.xml')

                                with codecs.open(filename, 'w') as newFile:
                                    newFile.write(etree.tostring(xml_tree, encoding='UTF-8', pretty_print=True, xml_declaration=True))
                                
                                self.current_article = None
                            current_page.clear()
                            break

        self.pool.close()
        self.pool.join()
        logging.info("-----------------------------------------")
        logging.info("revision delta size threshold: {}".format(self._REVSIZE_THRESHOLD))
        logging.info("maximum revision per page: {}".format(self._MAX_REVISIONS))
        logging.info("#########################################")
        logging.info("usable pages: {:,} total pages: {:,}".format(self.usable_pages, self.total_pages))
        logging.info("usable revisions: {:,};  total revisions (of usable pages): {:,} ({:,} of those skipped)".format(self.usable_revisions, self.total_revisions, self.skipped_revisions))
        logging.info("actual revisions saved: {:,}".format(self.actual_revisions))
        logging.info("-----------------------------------------")

    def get_rev(self, elem):
        """Get and return revision data."""
        rev_values = {
            "id": None,
            "timestamp": None,
            "username": None,
            "contr_id": None,
            "ip": None,
            "comment": None,
            "minor": False,
            "text": None,
            "sha1": None,
            "model": None,
            "format": None
        }

        for rev_elem in elem.iter():
            tag = etree.QName(rev_elem).localname
            if tag == "id":
                if etree.QName(rev_elem.getparent()).localname == "revision":
                    rev_values["id"] = rev_elem.text
                elif etree.QName(rev_elem.getparent()).localname == "contributor":
                    rev_values["contr_id"]= rev_elem.text
            elif tag == "minor":
                rev_values["minor"] = True
            else:
                rev_values[tag] = rev_elem.text

        return rev_values



    def process_rev(self, elem, context, skip_page):
        """Process revision (parse/diff/save text)."""
        current_rev = elem
        self.revision_count += 1
        self.total_revisions += 1

        for event, elem in context:
            if event == "end" and etree.QName(elem).localname == "revision":
                if skip_page is False:
                    rev_values = self.get_rev(elem)
                    # logging.info("------process revision {}".format(rev_values['id']))
                    valid_revision = True
                    contributor = None

                    try:
                        contributor = Contributor(rev_values['contr_id'], rev_values['username'], 
                        rev_values['ip'])
                    except ValueError:
                        valid_revision = False

                    self.md5hash_list.append(rev_values['sha1'])
                    distance = self.md5hash_list.distance_to_ident_value()
                    comment_match = None
                    
                    if rev_values['comment'] is not None:
                        comment_match = regex.revert_comment.match(rev_values['comment'].lower())
                    
                    if rev_values['minor'] or rev_values['contr_id'] is None or distance != -1 or comment_match:
                        valid_revision = False
                        
                    if self.rev_new is None:
                        # first revision of the article: parse wiki-text and save entry
                        self.rev_new = Revision(rev_values, contributor)

                        if valid_revision and self.rev_new.wiki_text is not None:
                            self.usable_revisions += 1
                            result = self.pool.apply_async(parse.parse_wiki_text_cropped, (self.rev_new.wiki_text,))
                            try:
                                self.rev_new.parsed_text, cropped_text, self.rev_new.is_malformed = result.get(timeout=10)
                            except TimeoutError:
                                logging.warning("----revision {} parsing timed out".format(self.rev_new.rev_id))
                                self.rev_new.parsed_text = ""
                                cropped_text = ""
                                self.rev_new.is_malformed = True

                                self.pool.terminate()
                                self.pool.join()
                                self.pool = Pool(processes=2)

                            if not self.rev_new.is_malformed:
                                if len(cropped_text) >= 12:

                                    new_entry = entry(self.rev_new.contributor.con_id, cropped_text, self.current_article.current_pos())
                                    self.current_article.append(new_entry)
                                    logging.info("----revision {} by user {} saved".format(self.rev_new.rev_id, self.rev_new.contributor.con_id))
                                    self.actual_revisions += 1              

                    else:
                        # not the first revision of the article: parse wiki-text of prev. rev. (if not already parsed)
                        # compare new with old rev, save resulting lines
                        self.rev_old = self.rev_new
                        self.rev_new = Revision(rev_values, contributor)
                        
                        if valid_revision and self.rev_new.wiki_text is not None and self.rev_new.size - self.rev_old.size >= self._REVSIZE_THRESHOLD and not self.rev_old.is_malformed:
                            self.usable_revisions += 1
                            result = self.pool.apply_async(parse.parse_wiki_text, (self.rev_new.wiki_text,))

                            try:
                                self.rev_new.parsed_text, self.rev_new.is_malformed = result.get(timeout=10)
                            except TimeoutError:
                                logging.warning("----revision {} parsing timed out".format(self.rev_new.rev_id))
                                self.rev_new.parsed_text = ""
                                self.rev_new.is_malformed = True

                                self.pool.terminate()
                                self.pool.join()
                                self.pool = Pool(processes=2)


                            if self.rev_old.parsed_text is None:
                                result = self.pool.apply_async(parse.parse_wiki_text, (self.rev_old.wiki_text,))
                                try:
                                    self.rev_old.parsed_text, self.rev_old.is_malformed = result.get(timeout=10)
                                except TimeoutError:
                                    logging.warning("----revision {} parsing timed out".format(self.rev_new.rev_id))
                                    self.rev_old.parsed_text = ""
                                    self.rev_old.is_malformed = True

                                    self.pool.terminate()
                                    self.pool.join()
                                    self.pool = Pool(processes=2)

                                if self.rev_old.is_malformed:
                                    self.usable_revisions -= 1
                                    
                            if not self.rev_old.is_malformed:
                                diff_additions = []
                                result = self.pool.apply_async(utils.get_additions, (self.rev_old.parsed_text, self.rev_new.parsed_text,))

                                try:
                                    diff_additions = result.get(timeout=120)
                                except TimeoutError:
                                    logging.warning("----revision {} diff calculation timed out".format(self.rev_new.rev_id))
                                    self.pool.terminate()
                                    self.pool.join()
                                    self.pool = Pool(processes=2)
                               
                                if not self.rev_new.is_malformed:
                                    if len(diff_additions) >= 12:
                                        new_entry = entry(self.rev_new.contributor.con_id, diff_additions, self.current_article.current_pos())
                                        self.current_article.append(new_entry)
                                        logging.info("----revision {} by user {} saved".format(self.rev_new.rev_id, self.rev_new.contributor.con_id))
                                        self.actual_revisions += 1
                
                current_rev.clear()
                break

def init_logging(logfile):
    """Initialize logging."""
    root_logger = logging.getLogger()
    for hdlr in root_logger.handlers:
        root_logger.removeHandler(hdlr)

    logging.shutdown()
    reload(logging)
    logging.basicConfig(format='%(asctime)s %(levelname)-7s: %(message)s', 
        datefmt='%Y/%m/%d %H:%M:%S',
        level=logging.DEBUG,
        filename=logfile,
        filemode='w')

    console = logging.StreamHandler()
    console.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(levelname)-7s: %(message)s')
    console.setFormatter(formatter)

    logging.getLogger('').addHandler(console)
    lxmlErrorLog = etree.PyErrorLog()
    etree.use_global_python_log(lxmlErrorLog)


def zip_backup(path, backup_path, filename):
    """Backup files collected in outdir_path."""
    logging.info("zip_backup({}, {}, {})\n\n\n\n\n\n".format(path, backup_path, filename))
    filename += ".zip"
    zipfile_name = os.path.join(backup_path, filename)

    if not os.path.exists(backup_path):
        os.makedirs(backup_path)

    zf = zipfile.ZipFile(zipfile_name, "w", zipfile.ZIP_DEFLATED)
    for dirname, subdirs, files in os.walk(path):
        zf.write(dirname)
        for filename in files:
            zf.write(os.path.join(dirname, filename))
    zf.close()

def is_new_file(element):
    """Return true if bz2-file is a new file and was not yet processed."""
    if element not in files_processed and element not in files_to_process:
        return True
    else:
        return False

def get_parameters(section):
    """Return config-parameters as a dictionary."""
    return dict(config.items(section))

def process_file(f):
    """Process a wikidump file."""
    start = time.clock()
    wikidump = WikiDump(f, outdir_path)

    try:
        wikidump.process_dump()
    except Exception:
        logging.exception("Error while processing dump.")
        raise
    
    del wikidump
    elapsed = (time.clock() - start)
    logging.info("Time elapsed: {}".format(elapsed))
    logging.info("END")

if __name__ == '__main__':
    start = time.clock()

    config = ConfigParser.ConfigParser()
    config.read("config.cfg")

    paths = get_parameters('Paths')
    input_path = paths['dump_file_path']
    outdir_path = paths['outdir_path']
    backup_path = paths['backup_path']

    param = get_parameters('Param')
    WikiDump._MAX_REVISIONS = int(param['max_revisions'])
    WikiDump._REVSIZE_THRESHOLD = int(param['revsize_threshold'])
    WikiDump._DEL_FILES = bool(int(param['del_files']))

    files_to_process = deque()
    files_processed = []
    still_files = True
    count_files = 0

    while(still_files):
        bz2_files = glob.glob(os.path.join(input_path, "*.bz2"))
        xml_files = glob.glob(os.path.join(input_path, "*.xml"))
        list_dir = bz2_files + xml_files
        
        for f in filter(is_new_file, list_dir):
            files_to_process.append(f)

        if len(files_to_process) == 0:
            still_files = False
            break

        valid_file = files_to_process.popleft()
        process_file(valid_file)
        count_files += 1
        if WikiDump._DEL_FILES:
            os.remove(valid_file)

        now = datetime.datetime.now().strftime("%Y%m%d_%H%M")
        valid_file_name = os.path.split(valid_file)[1]
        zipfilename = now +"_"+ os.path.splitext(valid_file_name)[0]
        zip_backup(outdir_path, backup_path, zipfilename)

        files_processed.append(valid_file)

    logging.info("{} files processed.".format(count_files))
