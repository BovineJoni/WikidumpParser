WikidumpParser
=============
## About
WikidumpParser is a tool to extract articles of Wikipedia dump files with authorship attribution of the corresponding text passages. Regular expressions are used to parse and filter the Wikipedia markup language. Each valid article is stored as an xml-file with the information, which part was written by whom. 

## Install
##### Python
You need python 2.7 (32-bit):

https://www.python.org/downloads/

_Note: Version 2.7.9 has pip included (which you will need to install the external packages)_

_Note that pip.exe is placed inside your Python installation's Scripts folder (e.g. C:\Python27\Scripts on Windows), which may not be on your path._ [Further instructions on installing pip.](https://pip.pypa.io/en/latest/installing.html)

##### External packages
To install all external dependencies, switch to the project directory and use the following command:

    pip install -r requirements.txt --find-links=./win32_wheelhouse/

For non windows users:

    pip install -r requirements.txt

##### Dump files
You can get the dump files from 

http://dumps.wikimedia.org/enwiki/

The script was tested with files from 2013/06/04, but it should work with newer data dump files as well. The files to use are labeled as **All pages with complete page edit history (.bz2)**.

## Use
Download data dump files and specify their parent directory in the config-file (config.cfg). Start the extraction of articles by executing the wikidump script:

    wikidump.py
	
The following properties can be changed in the config file:
    
    dump_file_path=./ (path to the dumpfiles - every bz2-file in this directory is getting processed)
    outdir_path=./articles (path where to store extracted articles)
    backup_path=./articles_backup (path where to store backup zip files)

    max_revisions=3000 (number of revisions after which to stop processing of an article)
    revsize_threshold=1000 (minimum bytes added by a revision to consider it valid)
    del_files=0 (turn deleting of wikidump files after processing on or off)
	
_Note: A zipped backup of the outdir contents is made after the processing of each dump file._

### License
Stylometric Clustering, Copyright 2014 Daniel Schneider.
schneider.dnl(at)gmail.com

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
