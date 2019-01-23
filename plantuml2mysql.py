#!/usr/bin/env python3
#-*-coding:utf-8-*-
# Usage: ./plantuml2mysql <dbsource.plu> <dbname>
# Author: Alexander I.Grafov <grafov@gmail.com>
# See https://github.com/grafov/plantuml2mysql
# The code is public domain.

CHARSET="utf8_unicode_ci"

import sys
import re
import time

# PlantUML allows some HTML tags in comments.
# We don't want them anymore here...
TAG_RE = re.compile(r'<[^>]+>')
def strip_html_tags(t):
    return TAG_RE.sub('', t)

# A minimal help
def print_usage():
  print("Convert PlantUML classes schema into mySQL database creation script")
  print("Usage:\n", sys.argv[0], "<dbsource.plu> <dbname>")
  print("\nSee https://github.com/grafov/plantuml2mysql for details\n")

def main():
    # Check arguments (exactly 1 + 2):
    if len(sys.argv) != 3:
        print_usage()
        sys.exit()
    try: # Avoid exception on STDOUT
        with open(sys.argv[1]) as src:
            data = src.readlines()
    except:
        print("Cannot open file: '" + sys.argv[1] + "'")
        sys.exit()
    # Add information for future self ;-)
    print("# Database created on", time.strftime('%d/%m/%y %H:%M',time.localtime()), "from", sys.argv[1])
    print("CREATE DATABASE %s CHARACTER SET = utf8 COLLATE = %s;" % (sys.argv[2], CHARSET))
    print("USE %s;\n" % sys.argv[2])
    uml = False; table = False; field = False
    pk = False; idx = False
    primary = []; index = ""
    # read source doc line by line
    for l in data:
        # remove nothing from it (y tho) to get a copy
        l = l.strip()
        # continue if it's not empty
        if not l:
            continue
        # rise UML flag if there's this string in any line
        #   So it means that it could be parsed wrong?!
        #   at least it skips everything before expected string value
        if l == "@startuml":
            uml = True
            continue
        # Y tho?! We're continuing anyway. Or not?
        if not uml:
            continue
        # What for?!
        if l == "--": # Separator
            continue
        comment = ""
        # again remove nothing (or end of a string) to get copy of given string
        i = l.split()
        # gets the first word of it
        fname = i[0]
        if fname == ".." or fname == "__": # Separators in table definition
            continue
        # if it's a table field that includes comment anywhere in given string
        if field and ("--" in l):
            # get raw field content as 'i' var and comment data
            i, comment = l.split("--", 2)
            # againg IDK y
            i = i.split()

        # make shure all of this false by the second loop and futher
        pk = False; idx = False
        # if given word includes "+" or "#"
        if fname[0] in ("+", "#"):
            #  "#" sign means it's a primary key
            if fname[0] == "#":
                pk = True
            # otherwise it's INDEX
            else:
                idx = True
            # gets whole field name
            fname = fname[1:]
        if l == "@enduml":
            uml = False
            continue
        # Break loop in we're done with UML
        if not uml:
             continue
        # if the first word of given line is "class"
        if l.startswith("class"):
            # we get a table actually; drop field flag
            table = True; field = False
            # there's planty of primary keys and indexes
            primary = []; index = ""
            # Table names are quoted and lower cased to avoid conflict with a mySQL reserved word
            print("CREATE TABLE IF NOT EXISTS `" + i[1].lower() + "` (")
            continue
        # if we're on table (class above) and we've got separator sign "=="
        if table and not field and l == "==": # Seperator after table description
            # we definetly on a field raws
            field = True
            continue
        # if we got end of a table (class)
        if field and l == "}":
            # drop all the flags
            table = False; field = False
            # print out all the primary keys and indexes
            print("  PRIMARY KEY (%s)" % ", ".join(primary), end="")
            if index:
                print(",\n%s" % index[:-2],)
                index = ""
            print(");\n")
            continue
        # some king of magic that need to be debugged out
        if field and l == "#id":
            print("  %-16s SERIAL," % "id")
        if field and l != "#id":
            print("  %-16s %s" % (fname, " ".join(i[2:]).upper()), end="")
            if comment:
                # Avoid conflict with apostrophes (use double quotation marks)
                print(" COMMENT \"%s\"" % strip_html_tags(comment.strip()), end="")
            print(",")
        if field and pk:
            primary.append(fname)
        if field and idx:
            index += "  INDEX (%s),\n" % fname


if __name__ == "__main__":
    main()
