#!/usr/bin/env python

import argparse
import re
import urllib
import json
import time
import datetime

# Parse the arguments.
parser = argparse.ArgumentParser(description='Given a birthdate, this program estimates a date of conception and returns the Billboard Hot 100 singles list for that date.')
parser.add_argument('date', help='a date in ISO 8601 format, "YYYY-MM-DD"')
parser.add_argument('apikey', help='your Billboard developer API key')
parser.add_argument('-n', '--number', type=int, help='number of songs to return')
parser.add_argument('-f', '--format', choices=['json', 'text'], default='text', help='output format')
args = parser.parse_args()

# Validate against ISO 8601.
if re.match(r'^\d{4}-\d{2}-\d{2}$', args.date) is None:
    parser.error('Invalid date. Must be formatted "YYYY-MM-DD"')

# Set the year, month, and day.
year, month, day = map(int, args.date.split('-'))

# Set the birth date.
try:
    birthDate = datetime.date(year, month, day)
except ValueError as e:
    parser.error('Invalid date. {error}'.format(error=e))

# Validate against earliest and latest date available. Feburary 13, 1959 is the 
# earliest date available.
if birthDate < datetime.date(1959, 2, 13) or birthDate > datetime.date.today():
    parser.error('Invalid date. Must be between 1959-02-13 and today.')

# Set the conception date. Human pregnancy is on average 40 weeks (280 days).
conceptionDate = birthDate - datetime.timedelta(days=280)

# Set start and end dates, 3 days before and after conception date. The 
# Billboard Hot 100 came out every week, so a 7 day search is sufficient.
startDate = conceptionDate - datetime.timedelta(days=3)
endDate = conceptionDate + datetime.timedelta(days=3)

# Set paramater defaults.
start = 1
count = 50

conceptionSongs = []

# Iterate the requests.
while True:
    
    # Set the parameters.
    params = urllib.urlencode({'format': 'json', 
                               # The Billboard Hot 100 - Singles
                               'id': 379,
                               # Application key
                               'api_key': args.apikey,
                               'sdate': startDate, 
                               'edate': endDate, 
                               'start': start, 
                               'count': count})
    
    # Set the URL opener.
    opener = urllib.URLopener()
    
    # API does not return JSON unless Accept-Encoding header is set to gzip.
    opener.addheader('Accept-Encoding', 'gzip')
    
    # Make the Billboard API request.
    try:
        response = opener.open('http://api.billboard.com/apisvc/chart/v1/list?{params}'.format(params=params))
    except IOError as e:
        parser.error(e)
    
    # Decode JSON.
    results = json.loads(response.read())
    
    # Iterate the results.
    for chartItem in results['searchResults']['chartItem']:
        
        # Some results have no distrubution.
        try:
            chartItem['distribution']
        except KeyError:
            chartItem['distribution'] = None
        
        # Build a list containing songs.
        conceptionSongs.append([chartItem['rank'], 
                                chartItem['song'], 
                                chartItem['artist'], 
                                chartItem['distribution']])
    
    # Set the new start paramater.
    start = start + count
    
    # Must sleep to comply with the 2 calls per second rate limit.
    time.sleep(0.5)
    
    # Break out of the request loop when there are no more results.
    if (results['searchResults']['firstPosition'] + count) > results['searchResults']['totalRecords']:
        break;

# Sort the song list according to rank.
conceptionSongs = sorted(conceptionSongs)

# Slice the list according to the -n argument.
if args.number is not None:
    conceptionSongs = conceptionSongs[0:args.number]

# JSON output.
if args.format == 'json':
    print json.dumps({'birthDate': birthDate.isoformat(), 
                      'conceptionDate': conceptionDate.isoformat(), 
                      'conceptionSongs': conceptionSongs})
    exit()
    
# Default text output.
else:
    print 'Conception date: {conceptionDate}'.format(conceptionDate=conceptionDate.isoformat())
    print 'Conception songs:'
    for conceptionSong in conceptionSongs:
        print '{rank}. "{song}" by {artist} ({distribution})'.format(rank=conceptionSong[0], 
                                                                     song=conceptionSong[1], 
                                                                     artist=conceptionSong[2], 
                                                                     distribution=conceptionSong[3])
