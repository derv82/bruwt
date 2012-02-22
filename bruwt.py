#!/usr/bin/env python

"""

University of Washington, Tacoma course registration brute-forcer.

Repeatedly tries to register for 'full' or 'closed' courses until registered.


   To execute on windows, navigate to the directory and type:

C:\Python27\python.exe bruwt.py

   On Linux, navigate to the directory and type:

chmod +x bruwt.py
./uw.py

"""

#
# these values will be prompted at runtime if not filled in here.
#

# login information
USERNAME=''
PASSWORD=''

SLN    ='' # 5 digit code of the course to register for
ADDCODE='' # add code for the class
CREDITS='' # number of credits to take

QUARTER=''

WAIT_TIME = 61 # minutes to wait between registration attempts

import os, sys                    # just 'cause
import time                       # for sleeping
import getpass                    # for reading password without echoing

import urllib2, cookielib, Cookie # for communicating with the UW website
from urllib import quote_plus     # also encoding postdata

# setup urlopener so it uses the same cookie jar
urlopen = urllib2.urlopen
Request = urllib2.Request
cj = cookielib.LWPCookieJar()
opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))
urllib2.install_opener(opener)

# Returns HTML source from website, 
# by default, does a GET request.
# however, acts as a POST (using 'data' as postdata) if data is not blank
def web(url, data=None):
  if data != None:
    #postdata = urlencode(data)
    postdata = data
  else:
    postdata = ''
  
  headers = {'User-agent' : 'Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US; rv:1.9.2.16) Gecko/20110319 Firefox/3.6.16'}
  
  try_again = True
  while try_again:
    try:
      req = Request(url, postdata, headers)
      handle = urlopen(req)
    except IOError, e:
      print '\n  Error accessing "' + url + '":', str(e)
      if str(e) == 'HTTP Error 504: Gateway Time-out':
        try_again = True
      elif str(e) == 'getaddrinfo failed':
        try_again = True
      else:
        return ''
      
    else:
      try_again = False
  
  result = handle.read()
  
  return result

# Looks through a source string for all items between two other strings, 
# Returns the list of items between start and finish (or empty list if none are found)
def between(source, start, finish):
  result = []
  
  i = source.find(start)
  j = source.find(finish, i + len(start) + 1)
  
  while i >= 0 and j >= 0:
    i = i + len(start)
    
    result.append(source[i:j])
    
    i = source.find(start, i + len(start))
    j = source.find(finish, i + len(start))
  
  return result

# Logs user into UW. Returns True if successful, False otherwise
def login(user, pw):
  #https://sdb.admin.washington.edu/students/uwnetid/register.asp
  
  r = web('https://weblogin.washington.edu/')
  
  postdata = 'user=' + quote_plus(user) + '&'
  postdata += 'pass=' + quote_plus(pw) + '&'
  hidden_data = between(r, 'type="hidden" name="', '">')
  for section in hidden_data:
    data = section.split('" value="')
    postdata += quote_plus(data[0]) + '=' + quote_plus(data[1]) + '&'
  postdata += 'submit=Log+in'
  
  r = web('https://weblogin.washington.edu/', postdata)
  
  if r.find('Login failed.') != -1:
    print 'FAILED!\n Invalid password?'
    return False
  
  elif r.find('Log in successful') != -1:
    print 'success.'
    return True
  else:
    print 'FAILED!\n\n Unable to login for unknown reasons\n Please see HTML output in uw_debug.html for more information'
    f = open('uw_debug.html', 'wb')
    f.write(r)
    f.close()
    return False

# Gets past the first "no javascript". Returns source to the second 'no javascript' page.
def first():
  r = web('https://sdb.admin.washington.edu/students/uwnetid/register.asp')
  
  postdata = ''
  hidden_data = between(r, 'type=hidden name=', '">')
  for section in hidden_data:
    data = section.split(' value="')
    postdata += quote_plus(data[0]) + '=' + quote_plus(data[1]) + '&'
  postdata += 'go=Continue'
  
  r = web('https://weblogin.washington.edu', postdata)
  
  return r

# Gets past the second "no javascript" wall. Returns source for the registration page.
def second(r):
  postdata = 'post_stuff=&get_args=&'
  hidden_data = between(r, 'type=hidden name=', '">')
  for section in hidden_data:
    data = section.split(' value="')
    postdata += quote_plus(data[0].replace('"', '')) + '=' + quote_plus(data[1].replace('"', '')) + '&'
  postdata += 'go=Continue'
  
  host = between(r, 'action="', '"')[0]
  
  r = web(host, postdata)
  
  return r

# Finds current quarter and possible other quarters,
# Asks user if they want to change the quarter and changes depending on their answer.
# Returns HTML source for new quarter registration page.
def quarter(r):
  global QUARTER
  
  if QUARTER == 'dont_change':
    # don't change quarters
    return r
    
  elif QUARTER != '':
    seasons = between(r, '<OPTION VALUE="', '</OPTION>')[1:]
    code    = between(r, 'NAME=INPUTFORM VALUE="', '">')[0]
    name    = between(r, '<SELECT NAME="', '"')[0]
    
    postdata = quote_plus(name) + '=' + quote_plus(QUARTER) + '&INPUTFORM=' + quote_plus(code)
    
    print ' Changing quarter to "' + seasons[i-1].split('">&nbsp;')[1] + '"...',
    sys.stdout.flush()
    r = web('https://sdb.admin.washington.edu/students/uwnetid/register.asp', postdata)
    print 'changed to "' + between(r, '<BR><H1>', '</H1>')[0].replace('Registration - ', '') + '"\n'
    return r
  
  QUARTER = 'dont_change'
  
  current = between(r, '<BR><H1>', '</H1>')[0].replace('Registration - ', '')
  print '\r Selected quarter: %s     ' % current
  
  seasons = between(r, '<OPTION VALUE="', '</OPTION>')[1:]
  if len(seasons) == 0:
    print ' No other quarters are available.'
    return r
  
  print ' Do you want to select a different quarter? (Y/N)',
  answer = raw_input().lower()
  if answer == '' or answer[0] != 'y':
    print '\n Registering for quarter "' + current + '"\n'
    return r
  
  print '\n Quarter selection menu:\n'
  
  print '   0) %s quarter' % current
  for (i, s) in enumerate(seasons): # print list of quarters
    print '   %d) %s quarter' % (i + 1, s.split('">&nbsp;')[1])
  
  print '\n Enter a number (0-%d):' % len(seasons),
  
  answer = raw_input()
  print ''
  
  if answer == '' or not answer.isdigit():
    print ' Invalid selection: %s, defaulting to %s' % (answer, s.split('">&nbsp;')[1])
    return r
  
  i = int(answer)
  if i < 0 or i > len(seasons):
    print ' Invalid number selection: %d, defaulting to %s' % (i, s.split('">&nbsp;')[1])
    return r
  elif i == 0:
    print ' Staying in the %s quarter' % (current)
    return r
  
  quarter = seasons[i-1].split('">&nbsp;')[0]
  code    = between(r, 'NAME=INPUTFORM VALUE="', '">')[0]
  name    = between(r, '<SELECT NAME="', '"')[0]
  
  QUARTER = quarter
  
  postdata = quote_plus(name) + '=' + quote_plus(quarter) + '&INPUTFORM=' + quote_plus(code)
  
  print ' Changing quarter to "' + seasons[i-1].split('">&nbsp;')[1] + '"...',
  sys.stdout.flush()
  r = web('https://sdb.admin.washington.edu/students/uwnetid/register.asp', postdata)
  print 'changed to "' + between(r, '<BR><H1>', '</H1>')[0].replace('Registration - ', '') + '"\n'
  
  return r

# Registers for SLN. Only tries once. Returns '' if unable to register for class for some permanent reason (restricted, etc).
def register(r, sln):
  print_string = 'Attempting to register for ' + str(sln) + '...'
  print '\r ' + print_string,
  sys.stdout.flush()
  postdata = ''
  
  pairs = between(r, 'TYPE=HIDDEN NAME=', '>')
  for pair in pairs:
    if pair.find('INPUTFORM') != -1 and pair.find('"UPDATE"') == -1:
      continue
    p = pair.split(' VALUE=')
    
    name = p[0]
    if len(p) == 1:
      value = ''
    else:
      value = p[1].replace('" ', '')
      value = value.replace('"', '')
      
    postdata += quote_plus(name) + '=' + quote_plus(value)
    
    postdata += '&'
  
  added_sln =      False
  added_addcode  = False
  added_credits  = False
  
  pairs = between(r, '<INPUT TYPE=TEXT ', '>')
  for pair in pairs:
    pz = pair.split(' ')
    for p in pz:
      if p.startswith('NAME='):
        name = p.replace('NAME=', '')
        
      elif p.startswith('VALUE='):
        value = p.replace('VALUE=', '')
        value = value.replace('"', '')
    
    postdata += quote_plus(name) + '='
    
    if not added_sln and name.startswith('sln'):
      postdata += quote_plus(sln)
      added_sln = True
    elif ADDCODE != '' and added_sln and not added_addcode and name.startswith('entcode'):
      postdata += quote_plus(ADDCODE)
      added_addcode = True
    elif CREDITS != '' and added_sln and not added_credits and name.startswith('credits'):
      postdata += quote_plus(CREDITS)
      added_credits = True
      
    else:
      postdata += quote_plus(value)
    
    postdata += '&'
  
  r = web('https://sdb.admin.washington.edu/students/uwnetid/register.asp', postdata)
  
  if r.find('Schedule updated.') != -1 and r.find('VALUE=' + SLN + '>') != -1:
    # successfully joined course
    print 'SUCCESS!\n REGISTERED for ' + str(SLN) + '! Awww yeeeaaa'
    return ''
  
  if r.find('This section is closed') != -1: # ', and no alternate sections are open.'
    # course is full, but that's fine... we can just try again!
    print_string += ' Course is full'
    for i in xrange(WAIT_TIME * 60, 0, -1):
      print '\r ' + print_string + ' (waiting ' + hms(i) + ')',
      sys.stdout.flush()
      time.sleep(1)
    print '\r ' + ' ' * (len(print_string + ' (waiting 00m00s)')),
    sys.stdout.flush()
    return r
  
  if r.find('Invalid Schedule Line Number (SLN)') != -1:
    print 'FAILURE!\n Invaild SLN!'
    return ''
  
  if r.find('you are already registered for this course') != -1:
    # already registered
    print 'FAILURE! (sorta)\n  Unable to join: The system says you are already registered for ' + str(sln) +'!'
    return ''
    
  if r.find('Restricted section: You do not meet the course') != -1:
    # Do not meet requirements; unable to join *ever*
    print 'FAILURE!\n Unable to join: That course is RESTRICTED to you. Talk to an adviser.'
    return ''
  
  if r.find('You may not register for this course using the web.') != -1:
    print 'FAILURE!\n The course ' + str(sln) + ' cannot be registered for via the web.'
    return ''
  
  if r.find('you must also register for the related') != -1:
    print 'FAILURE!\n You must also register for a related course (probably lecture)'
    return ''
    
  if r.find('Schedule not updated.') != -1:
    # Some other unknown error
    info = between(r, '<INPUT TYPE=HIDDEN SIZE=1 NAME=dup', '</TR>')[0]
    info = between(info, '<TD>', '<')[0]
    print 'FAILURE!\n Unexpected error: "Schedule not updated - ' + info + '"'
    f = open('uw_debug.html', 'wb')
    f.write(r)
    f.close()
    print '\n Debug page saved to uw_debug.html'
    return ''
  
  if r.find('No changes were made to your schedule.') != -1:
    print 'FAILURE!\n Unexpected error! No changes could be made (bug?)'
    f = open('uw_debug.html', 'wb')
    f.write(r)
    f.close()
    print '\n Debug page saved to uw_debug.html'
    return ''
  
  if r.find('You do not have Javascript enabled') != -1:
    # we were logged out!
    print 'FAILURE! (Logged out)\n Logging back in .',
    sys.stdout.flush()
    
    cj.clear() # clear the cookies and start over.
    
    print '\r Logging in...',
    sys.stdout.flush()
    if not login(USERNAME, PASSWORD):
      # login failed
      print "\nUnable to login, exiting."
      return ''
    
    r = first()
    print '.',
    sys.stdout.flush()
    r = second(r)
    print '.',
    sys.stdout.flush()
    r = quarter(r)
    return r
    
  print 'FAILURE!\n The system did not respond (bug?)'
  f = open('uw_debug.html', 'wb')
  f.write(r)
  f.close()
  print '\n Debug page saved to uw_debug.html'
  
  return ''

# converts seconds (integer) into hours:min:sec (string)
def hms(sec):
  result = ''
  #result = str(sec / 3600) + 'h'
  #sec %= 3600
  result += format(sec / 60, '2d') + 'm'
  sec %= 60
  result += '%0*ds' % (2, sec)
  
  return result

# where the magic happens
def start():
  global USERNAME, PASSWORD, SLN
  print ''
  print ' * UW course registration brute-forcer'
  print ''
  print ' By entering your student information, you take full responsibility for what'
  print ' this program will do. You can not hold neither the author, nor UW accountale'
  print ' for any changes that may occur to your student account by using this script.'
  print ''
  print ' Do you agree to these terms and wish to continue? (Y/N)',
  
  answer = raw_input()
  if answer == '' or answer.lower()[0] != 'y':
    return
  
  print ''
  
  if USERNAME == '':
    print ' Enter your UW NetID:',
    USERNAME = raw_input()
  
  if PASSWORD == '':
    #print ' Enter your password: ',
    PASSWORD = getpass.getpass(' Enter your password: ') # raw_input()
  
  if SLN == '':
    print ' Enter the desired course\'s SLN (5-digit number):',
    SLN = raw_input()
    print ''
  
  print '\r Logging in...',
  sys.stdout.flush()
  if not login(USERNAME, PASSWORD):
    # login failed
    # print "\nUnable to login, exiting."
    return
  
  print ''
  print ' Loading registration page .',
  sys.stdout.flush()
  
  r = first()
  print '.',
  sys.stdout.flush()
  r = second(r)
  print '.',
  sys.stdout.flush()
  r = quarter(r)
  
  while r != '':
    r = register(r, SLN)
    # only loops when course is closed, 
    # stops looping when student is registered for the course,
    # or some error occurs.
    

def help():
  print """
  
  UW Course Registration Brute-Forcer
  
  This program will attempt to register you for a specified class repeatedly
  until you finally get in.  This script should only be used to register for
  "full" classes. As soon as someone drops from the class, this program will
  be there to register you in their place.
  
  The program will try to register for a course every """ + str(WAIT_TIME) + """ minutes.
  
  The author of this program takes no responsibility for your actions or the 
  changes this program may cause to your student account.
  """

# only run when executed from main
if __name__ == "__main__":
  
  # check for command-line arguments
  args = sys.argv[1:]
  if len(args) > 0:
    help() # print help
    sys.exit(0)
    
  try:
    start() # everything happens here
    
    print '\n Press enter to exit this program.\n'
    raw_input()
  except KeyboardInterrupt:
    print '\n\nInterrupted (^C)'
   
