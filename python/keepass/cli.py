#!/usr/bin/env python
'''
Command line interface to manipulating keepass files
'''

class Cli(object):
    '''
    Process command line
    '''

    commands = [
        'help',                 # print help message
        'open',                 # open and decrypt a file
        'save',                 # save current DB to file
        'dump',                 # dump current DB to text
        ]

    def __init__(self,args=None):
        self.db = None
        self.command_line = None
        self.ops = {}
        if args: self.parse_args(args)
        return

    def parse_args(self,args):
        '''
        keepass.cli [options] [cmd [options]] [...]

        The command line consists of general options followed by zero
        or more commands and their options.

        '''

        def splitopts(argv):
            'Split optional command and its args removing them from input'
            if not argv: return None

            cmd=""
            if argv[0][0] != '-':
                if argv[0] not in Cli.commands:
                    raise ValueError,'Unknown command: "%s"'%argv[0]
                cmd = argv.pop(0)
                pass
            copy = list(argv)
            cmdopts = []
            for arg in copy:
                if arg in Cli.commands: break
                cmdopts.append(argv.pop(0))
                continue
            return [cmd,cmdopts]

        cmdline = []
        copy = list(args)
        while copy:
            chunk = splitopts(copy)
            if not chunk: break

            if not chunk[0]: chunk[0] = 'general'
            meth = eval('self._%s_op'%chunk[0])
            self.ops[chunk[0]] = meth()
            cmdline.append(chunk)
            continue

        self.command_line = cmdline

        return

    def __call__(self):
        'Process commands'
        if not self.command_line:
            print self._general_op().print_help()
            return
        for cmd,cmdopts in self.command_line:
            meth = eval('self._%s'%cmd)
            meth(cmdopts)
            continue
        return

    def _general_op(self):
        '''
        keepassc [options] [cmd cmd_options] ...
        
        execute "help" command for more information.
        '''
        from optparse import OptionParser
        op = OptionParser(usage=self._general_op.__doc__)
        return op

    def _general(self,opts):
        'Process general options'
        opts,args = self.ops['general'].parse_args(opts)
        return


    def _help_op(self):
        return None
    def _help(self,opts):
        'Print some helpful information'

        print 'Available commands:'
        for cmd in Cli.commands:
            meth = eval('self._%s'%cmd)
            print '\t%s: %s'%(cmd,meth.__doc__)
            continue
        print '\nPer-command help:\n'

        for cmd in Cli.commands:
            meth = eval('self._%s_op'%cmd)
            op = meth()
            if not op: continue
            print '%s'%cmd.upper()
            op.print_help()
            print
            continue

    def _open_op(self):
        'open [options] filename'
        from optparse import OptionParser
        op = OptionParser(usage=self._open_op.__doc__,add_help_option=False)
        op.add_option('-m','--masterkey',type='string',default="",
                      help='Set master key for decrypting file, default: ""')
        return op

    def _open(self,opts):
        'Read a file to the in-memory database'
        opts,files = self.ops['open'].parse_args(opts)
        import kpdb
        # fixme - add support for openning/merging multiple DBs!
        self.db = kpdb.Database(files[0],opts.masterkey)
        return

    def _save_op(self):
        'save [options] filename'
        from optparse import OptionParser
        op = OptionParser(usage=self._save_op.__doc__,add_help_option=False)
        op.add_option('-m','--masterkey',type='string',default="",
                      help='Set master key for encrypting file, default: ""')
        return op

    def _save(self,opts):
        'Save the current in-memory database to a file'
        opts,files = self.ops['save'].parse_args(opts)
        self.db.write(files[0],opts.masterkey)
        return

    def _dump_op(self):
        'dump [options] [name|/group/name]'
        from optparse import OptionParser
        op = OptionParser(usage=self._dump_op.__doc__,add_help_option=False)
        op.add_option('-p','--show-passwords',action='store_true',default=False,
                      help='Show passwords as plain text')
        op.add_option('-f','--format',type='string',
                      default='%(group_name)s/%(username)s: %(title)s %(url)s',
                      help='Set the format of the dump')
        return op

    def _dump(self,opts):
        'Print the current database in a formatted way.'
        opts,files = self.ops['dump'].parse_args(opts)
        self.db.dump_entries(opts.format,opts.show_passwords)
    

if '__main__' == __name__:
    import sys
    cliobj = Cli(sys.argv[1:])
    cliobj()