#!/usr/bin/env python

import sys
from optparse import OptionParser
from getpass import getpass
from kpdb import Database
from infoblock import EntryInfo
from keepass import generate_key, load_filekey
import os


def inputdefault(prompt, default=""):
    "Prompt user for input, and return either default, or input"
    data = raw_input(prompt + "[" + default + "]: ")
    if data is '':
        return default
    else:
        return data

def inputYN(question, default="no"):
    "Prompt user for input to a yes/no question"
    out = inputdefault(question, default)
    if out == "y" or out == "Y" or out == "yes":
        return 1
    else:
        return 0

def newpasswd():
    passwd1 = getpass('Password:')
    passwd2 = getpass('Re-type Password:')
    while passwd1 != passwd2:
        print "Passwords don't match!"
        passwd1 = getpass('Password:')
        passwd2 = getpass('Re-type Password:')
    return passwd1

def create_database(filename, options):
    'create a keepass database and generate appropriate keyfile'

    keyopt = inputdefault('Use keyfile, password, or both?', 'keyfile')
    passwd = None
    filekey = None
    existing_filekey = None
    if keyopt == 'password' or keyopt == 'both':
        passwd = newpasswd()
    if keyopt == 'keyfile' or keyopt == 'both':
        if options.keyfilename is not None:
            try:
                filekey = load_filekey(options.keyfilename)
            except IOError:
                pass
        newkey = False
        if filekey:
            if not inputYN('Existing keyfile found. Use it?', 'yes'):
                filekey = generate_key()
                newkey = True
        else:
            if inputYN('Existing keyfile not found. Generate?', 'yes'):
                filekey = generate_key()
                newkey = True
        if newkey:
            print 'Saving filekey to {}'.format(options.keyfilename)
            keyfile = file(options.keyfilename, 'w+')
            keyfile.write(filekey)
            keyfile.close()

    db = Database(None, filekey=filekey, passphrase=passwd)
    db.add_group('default')
    db.write(filename)
    return passwd


def main():
    usage = """%prog [options] <kdb file> <command>
    
    Commands:
        list - List entries in file
        get <title> <key> - Get entry from file and display to stdout
        set <title> <key>=<value> [...] - Set entry key(s) to value(s)
        add <title> <key>=<value> [...] - Add entry and set key(s) to value(s).
        del <title> - Delete entry."""
    parser = OptionParser(usage, version="%prog 1.0")
    parser.add_option("-p", "--passphrase", action="store", dest="passphrase", type="str",
                      help="Passphrase to open kdb with. (Use 'ask' to be prompted) [%default]")
    parser.add_option("-k", "--keyfile", action="store", dest="keyfilename", type="str",
                      help="Keyfile containg a key to open kdb with. [%default]")


    (options, args) = parser.parse_args()

    if len(args) < 2:
        parser.error("incorrect number of arguments")
    else:
        filename = args[0]
        command = args[1]

    if command == 'del' and len(args) != 3:
        parser.error("incorrect number of arguments for command 'add'")

    if command == 'get' and len(args) != 4:
        parser.error("incorrect number of arguments for command 'get'")

    if command == 'set' and len(args) < 4:
        parser.error("incorrect number of arguments for command 'set'")

    if command == 'add' and len(args) < 4:
        parser.error("incorrect number of arguments for command 'add'")

    if not os.access(filename, os.F_OK):
        if inputYN('Database does not exist. Create?', default='yes'):
            options.passphrase = create_database(filename, options)
        else:
            sys.exit(4)

    if options.passphrase == 'ask' or not (options.passphrase or options.keyfilename):
        options.passphrase = getpass()

    filekey = None
    if options.keyfilename:
        filekey = load_filekey(options.keyfilename)

    db = Database(filename, filekey=filekey, passphrase=options.passphrase)
    
    if command == 'list':
        print 'Groups:'
        for group in db.groups:
            print group.group_name

        print
        print 'Entries:'
        print("{0:20} {1:15} {2:20} {3:20}".format("Group", "Title", "Username", "URL"))
        for entry in db.entries:
            if hasattr(entry, 'title') and entry.title == 'Meta-Info':
                continue
            for group in db.groups:
                if hasattr(entry, 'groupid') and group.groupid == entry.groupid:
                    break
            print("{0:<20} {1:15} {2:20} {3:20}".format(group.group_name, entry.title,
                                                        entry.username, entry.url))

    elif command == 'get':
        (title, key) = (args[2], args[3])
        entry = db.get(title)
        print("{0}".format(getattr(entry, key)))

    elif command == 'set' or command == 'add':
        title = args[2]
        setpairs = {}
        for kp in args[3:]:
            (key, value) = kp.split("=")
            setpairs[key] = value
        if command == 'set':
            entry = db.get(title)
        elif command == 'add':
            entry = EntryInfo()
            entry.title = title
            db.entries.append(entry)
        for (key, value) in setpairs.items():
            setattr(entry, key, value)
        if not hasattr(entry, 'groupid'):
            entry.groupid = 0

        db.write()

    elif command == 'del':
        title = args[2]
        entry = db.get(title)
        db.entries.remove(entry)
        db.write()

if __name__ == '__main__':
    main()
