#!/usr/bin/python2

# -*- coding: utf-8 -*-
#
#  vkfavorm.py
#  
#  Copyright 2013 Nickolay Scalzi <me@cybsol.in.ua>
#  
#  

import sqlite3 as db
import sys
import os
import pycurl
import StringIO
import re
import urllib

PROFILE = 'default'

if len(sys.argv) < 2:
	sys.exit('Usage: %s \"songname\"' %sys.argv[0])
songname=sys.argv[1]
if len(sys.argv) > 2:
	lenght=len(sys.argv)
	for i in range(2,lenght):
		songname=songname+' '+sys.argv[i]

# find needed profile dir and cookiesdb from it
cookiedbpath = os.environ['HOME']+'/.mozilla/firefox/'
for name in os.listdir(cookiedbpath):
	if os.path.isdir(cookiedbpath+name) and (PROFILE in name):
		cookiedbpath=cookiedbpath+name+'/cookies.sqlite'
		break

what = '.vk.com'
addHash='undef'
connection = db.connect(cookiedbpath)
cursor = connection.cursor()
contents = "name, value"

cursor.execute("SELECT " +contents+ " FROM moz_cookies WHERE host='" +what+ "'")
cookiemas=[]
for row in cursor.fetchall():
	cookiemas.append(row[0]+'='+row[1])
connection.close()

cookiestr='; '.join(cookiemas)

tmpdir = '/tmp/add_audio_vk'

# this is first run, so lets write hash value
if not os.path.isdir(tmpdir):
	mus = pycurl.Curl()
	ans = StringIO.StringIO()
	# let's figure out our pageid
	mus.setopt(pycurl.HTTPHEADER, ['Cookie: '+cookiestr])
	mus.setopt(pycurl.URL, 'https://vk.com/feed')
	mus.setopt(pycurl.FOLLOWLOCATION, 1)
	mus.setopt(pycurl.WRITEFUNCTION, ans.write)
	mus.setopt(pycurl.USERAGENT, "Mozilla/5.0 (X11; Linux x86_64; rv:20.0) Gecko/20100101 Firefox/20.0")

	mus.perform()
	mus.close()
	
	data=ans.getvalue()
	profile=re.search('<a href=\"/([^\"]+)\" onclick=\"return nav.go\(this, event, {noback: true}\)\" id=\"myprofile\" class=\"left_row\">',data)
	pageid=profile.group(1)
	
	# figure out our hash
	mus = pycurl.Curl()
	ans = StringIO.StringIO()
	mus.setopt(pycurl.HTTPHEADER, ['Cookie: '+cookiestr])
	mus.setopt(pycurl.URL, 'https://vk.com/'+pageid)
	mus.setopt(pycurl.FOLLOWLOCATION, 1)
	mus.setopt(pycurl.WRITEFUNCTION, ans.write)
	mus.setopt(pycurl.USERAGENT, "Mozilla/5.0 (X11; Linux x86_64; rv:20.0) Gecko/20100101 Firefox/20.0")

	mus.perform()
	mus.close()
	
	data=ans.getvalue()
	addhash=re.search('Page.audioStatusUpdate\(\'([^\']+)\'\)',data).group(1)
	
	os.mkdir(tmpdir)
	fwrite=open(tmpdir+'/addhash','w')
	fwrite.write(addhash)
	fwrite.close()

fread=open(tmpdir+'/addhash','r')
HASHSUM=fread.read()
fread.close()

# looking for first match
mus = pycurl.Curl()
ans = StringIO.StringIO()
mus.setopt(pycurl.URL, 'https://m.vk.com/audio')
mus.setopt(pycurl.HTTPHEADER, [str('Cookie: '+cookiestr),'X-Requested-With: XMLHttpRequest'])
mus.setopt(pycurl.POSTFIELDS, 'act=search&_ajax=1&'+urllib.urlencode({'q':songname}))
mus.setopt(pycurl.POST, 1)
mus.setopt(pycurl.VERBOSE, 0)
mus.setopt(pycurl.FOLLOWLOCATION, 1)
mus.setopt(pycurl.WRITEFUNCTION, ans.write)
mus.perform()

mus.close()

data=ans.getvalue()

# adding him to our music list
str1=re.search(ur'audioplayer.add\((\'([^\\]+)\'), event\)',data)
if str1:
	res=str1.group(2)
	aid=re.search(ur'_([^_]+)',res).group(1)
	oid=re.search(ur'([^_]+)',res).group(0)
	mus = pycurl.Curl()
	ans = StringIO.StringIO()
	mus.setopt(pycurl.URL, 'https://m.vk.com/audio')
	mus.setopt(pycurl.HTTPHEADER, [str('Cookie: '+cookiestr),'X-Requested-With: XMLHttpRequest'])
	mus.setopt(pycurl.POSTFIELDS, 'act=add&aid='+aid+'&hash='+HASHSUM+'&al=1&oid='+oid+'&search=1&top=0')
	mus.setopt(pycurl.POST, 1)
	mus.setopt(pycurl.FOLLOWLOCATION, 1)
	mus.perform()
	mus.close()
	print 'success'
else:
	print 'failed'
	sys.exit(1)

sys.exit(0)
