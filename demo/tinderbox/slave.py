#!/usr/bin/env python
#
"""
This is a sample Tinderbox2 buildslave script.

NOTE: WAIT at least 6 minutes after the last build before starting
      the next build!

Create config.ini file with the following contents:

[build]
name = identify your build slave, for example Ubuntu 8.04 32-bit
;;optional fields:
;;uname = uname -a
;;swig = swig -version
;;cc = gcc --version
;;openssl = openssl version
;;python = python --version
;;svn = svn co http://svn.osafoundation.org/m2crypto/trunk m2crypto
;;build = python setup.py clean --all build
;;test = python setup.py test
;;wait = 3600

[email]
from = your email
to = Email Heikki Toivonen to get the address
user = smtp username
password = smtp password
server = smtp server
port = smtp port
"""

import time, smtplib, os, ConfigParser
import build_lib as bl

# Change to True when you are troubleshooting this build script
debug_script = False

# These commands assume we are running on a unix-like system where default
# build options work and all prerequisites are installed and in PATH etc.
DEFAULT_COMMANDS = {
  'uname': ['uname', '-a'],
  'swig': ['swig', '-version'],
  'cc': ['gcc', '--version'],
  'openssl': ['openssl', 'version'],
  'python': ['python', '--version'],
  'svn': ['svn', 'co', 'http://svn.osafoundation.org/m2crypto/trunk', 'm2crypto'],
  'build': ['python', 'setup.py', 'clean', '--all', 'build'],
  'test': ['python', 'setup.py', 'test']
}

def load_config(cfg='config.ini'):
    config = {}
    cp = ConfigParser.ConfigParser()
    cp.read(cfg)
    for section in cp.sections():
        for option in cp.options(section):
            config[option] = cp.get(section, option).strip()
    return config


def build(commands, config):
    status = 'success'
    
    cwd = os.getcwd()
    
    bl.initLog('tbox.log', echo=debug_script)
    
    starttime = int(time.time())
    
    for command in commands:
        cmd = config.get(command) 
        if not cmd:
            cmd = DEFAULT_COMMANDS[command]
        else:
            cmd = cmd.split()
        
        bl.log('*** ' + ' '.join(cmd))
        
        exit_code = bl.runCommand(cmd, timeout=120) 
        if exit_code:
            bl.log('*** error exit code = %d' % exit_code)
            if command == 'test':
                status = 'test_failed'
            else:
                status = 'build_failed'
            break
        if command == 'svn':
            os.chdir('m2crypto')
        
    timenow = int(time.time())
    
    bl.closeLog()
    
    os.chdir(cwd)

    return 'tbox.log', starttime, timenow, status


def email(logpath, starttime, timenow, status, config):
    msg = """From: %(from)s
To: %(to)s
Subject: tree: M2Crypto


tinderbox: tree: M2Crypto
tinderbox: starttime: %(starttime)d
tinderbox: timenow: %(timenow)d
tinderbox: status: %(status)s
tinderbox: buildname: %(buildname)s
tinderbox: errorparser: unix
tinderbox: END

""" % {'from': config['from'], 'to': config['to'], 
           'starttime': starttime, 'timenow': timenow,
           'status': status,
           'buildname': config['name']}
    
    msg += open(logpath).read()
    
    server = smtplib.SMTP(host=config['server'], port=int(config['port']))
    if debug_script:
        server.set_debuglevel(1)
    server.starttls() # if your server supports STARTTLS
    server.login(config['user'], config['password'])
    server.sendmail(config['from'], config['to'], msg)
    server.quit()


if __name__ == '__main__':
    config = load_config()    
    
    wait_seconds = config.get('wait') or 3600
    
    commands = ['uname', 'swig', 'cc', 'openssl', 'python', 'svn', 'build', 'test']

    while True:
        logpath, starttime, timenow, status = build(commands, config)
        email(logpath, starttime, timenow, status, config)
        time.sleep(wait_seconds)
