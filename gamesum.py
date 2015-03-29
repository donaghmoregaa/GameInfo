#!/usr/bin/python
# coding: utf8

# Pyhon script to download fixtures and results from ServaSport (GAA) results service,
# parse the output and generate a json file.
#
# Program written by Colin Woods (cwoods@talk21.com) - June 2013 - No warranty or support.
#

#imports
import urllib2;
import xml.dom.minidom as minidom
import datetime
import time
import os
import io
import json
import sys
import re
from optparse import OptionParser

VERSION = "0.1"
parser = OptionParser(usage="%prog [OPTION]", version=VERSION)
parser.add_option("-o", "--outfile", dest="outfile", help="write output to json file")
parser.add_option("-c", "--clubid", dest="clubid", help="ServaSport Club ID")
parser.add_option("-d", "--days", dest="days", help="Windows of days. 14max")
parser.add_option("-a", "--appendsip", dest="appendsip", help="Use ServaSport SIP query parameter")
(options, args) = parser.parse_args()

if options.outfile:
    print options.outfile

# set the club id.  Read from args or default
if options.clubid:
   clubId=options.clubid
else:
   clubId = '1425' # Donaghmore club_1_name

# set the days window. Read from args or default.
if options.days:
   daysAfter = options.days
   daysPrevious = options.days
else:  
   daysAfter = '14'
   daysPrevious = '14'
  
sip = 'ODQuMjMuMTEuMTc='
debug = 1;

# json output files
outputJsonFile = "RecentResultComingFixtrues.json"

# URL for upcoming fixtures and recent results
comingFixtures='http://people.gaa.ie/api/fixtures/xml?clubID=' + clubId + '&daysAfter=' + daysAfter + '&sip=' + sip
#comingFixtures='http://people.gaa.ie/api/fixtures/xml?clubID=' + clubId + '&daysAfter=' + daysAfter
recentResults='http://people.gaa.ie/api/fixtures/xml?clubID=' + clubId + '&daysPrevious=' + daysAfter + '&sip=' + sip

# Adjust timezone to London as server may be in different locale.
os.environ['TZ'] = 'Europe/London'
time.tzset()
now = time.strftime("%c")
print "Last updated: %s" % now
print "comingFixtures:", comingFixtures
print "recentResults:", recentResults	

comingFixtures='http://people.gaa.ie/api/fixtures/xml?clubID=1425&daysAfter=16&sip=ODQuMjMuMTEuMTc='
recentResults='http://people.gaa.ie/api/fixtures/xml?clubID=1425&daysPrevious=16&sip=ODQuMjMuMTEuMTc='

def printDebug (msg):

  if debug:
    print msg;

# Function to shorten competition name into a more
# familiar format such as Championship and League
# look at the compType and then add the roundName.
def shortenCompetitionName (compType, roundName):

# Debug print statements
#  print "compType :%s:" % (compType)
#  print "roundName :%s:" % (roundName)

  # strip out round and leading spaces from roundName
  roundName = re.sub("(?i)round","", roundName)
  roundName = roundName.lstrip()

  comp = compType
  if (compType == "league"):
      comp = "League Round " + roundName
  else:
      comp = "Championship " + roundName

  return comp

# Function to determine the team level such as
# First check the compLevel
# Senior: Could be senior or reserve
# u21: under 21
# juvenile: under 16
# underage: Could be u14 or u13
#
# In the cases where multiple options then the compName
# needs to be parse to work out the team level.
def getTeamLevel (compName, compNameShort, compLevel):

# debug print statements
#  print "compName :%s:" % (compName)
#  print "compNameShort :%s:" % (compNameShort)
#  print "compLevel :%s:" % (compLevel)
  
  if compLevel.find("senior") >= 0:
      teamLevel = "Senior"
      if compName.find("Reserve") >= 0:
          teamLevel = "Reserve"
  elif compLevel.find("u21") >= 0:
          teamLevel = "u21"
  elif compLevel.find("minor") >= 0:
          teamLevel = "Minor"
  elif compLevel.find("juvenile") >= 0:
	  teamLevel = "u16"
  elif compLevel.find("underage") >= 0:
      teamLevel = "Underage"
      if compNameShort.find("U14") >= 0:
          teamLevel = "u14"
      elif compNameShort.find ("U13") >=0:
	  teamLevel = "u13"
  else:
      teamLevel = compLevel
  
  return teamLevel

# shorten team names for compact display
def shortenTeamName (teamName):

    teamName = teamName.replace (u"An Droim Mór Naoimh Damhnait", "Dromore")
    teamName = teamName.replace (u"Coalisland Fianna", "Coalisland")
    teamName = teamName.replace (u"Coalisland GFC", "Coalisland")
    teamName = teamName.replace (u"Omagh St Enda's", "Omagh")
    teamName = teamName.replace (u"Moy Tír na nÓg", "Moy")
    teamName = teamName.replace (u"Clonoe O`Rahilly's CLG", "Clonoe")
    teamName = teamName.replace (u"Ardboe O'Donovan Rossa", "Ardboe")
    teamName = teamName.replace (u"Coill an Chlochair Naomh Mhuire", "Killyclogher")
    teamName = teamName.replace (u"Trí Leac C. Naoimh Mhic Artáin", "Trillick")
    teamName = teamName.replace (u"Carrickmore St Colmcille's", "Carrickmore")
    teamName = teamName.replace (u"An Eaglais, Naoimh Pádraig", "Eglish")
    teamName = teamName.replace (u"Cookstown Fr Rocks", "Cookstown")
    #teamName = teamName.replace (u"Errigal Ciaran", "Errigal Ciaran")
    teamName = teamName.replace (u"Augher St Macartan's GFC", "Augher")
    teamName = teamName.replace (u"Greencastle St Patrick's", "Greencastle")
    teamName = teamName.replace (u"Domhnach Mór Naoimh Pádraig", "Donaghmore")
    teamName = teamName.replace (u"Domhnach Mór", "Donaghmore")
    teamName = teamName.replace (u"Derrylaughan Kevin Barry's GAC", "Derrylaughan")
    teamName = teamName.replace (u"Moortown St Malachy's", "Moortown")
    teamName = teamName.replace (u"Pomeroy Plunketts", "Pomeroy")
    teamName = teamName.replace (u"Edendork St Malachy's", "Edendork")
    teamName = teamName.replace (u"Strabane Sigersons", "Strabane")
    teamName = teamName.replace (u"Galbally Pearses", "Galbally")
    teamName = teamName.replace (u"Urney St Colmcille's", "Urney")
    teamName = teamName.replace (u"Gortin St Patrick's", "Gortin")
    teamName = teamName.replace (u"Eskra Emmetts", "Eskra")
    teamName = teamName.replace (u"Derrytresk Fir aChnoic", "Derrytresk")
    teamName = teamName.replace (u"Brackaville Owen Roes", "Brackaville")
    teamName = teamName.replace (u"Kildress Wolfe Tones", "Kildress")
    teamName = teamName.replace (u"Dungannon Thomas Clarkes", "Dungannon")
    teamName = teamName.replace (u"Aghyaran St Davogs", "Aghyaran")
    teamName = teamName.replace (u"Rock St Patrick's", "Rock")
    teamName = teamName.replace (u"Stewartstown Harps", "Stewartstown")
    teamName = teamName.replace (u"Clann na Gael", "Clann na Gael")
    teamName = teamName.replace (u"Loughmacrory St Teresa's", "Loughmacrory")
    teamName = teamName.replace (u"Castlederg St Eugene's", "Castlederg")
    teamName = teamName.replace (u"Killyman St Mary's", "Killyman")
    teamName = teamName.replace (u"Clogher Eire Óg", "Clogher")
    teamName = teamName.replace (u"Glenelly St Joseph's", "Glenelly")
    teamName = teamName.replace (u"Killeeshil St Mary's", "Killeeshil")
    teamName = teamName.replace (u"Newtownstewart St Eugene's", "Newtownstewart")
    teamName = teamName.replace (u"Fintona Na Piarsaigh", "Fintona")
    teamName = teamName.replace (u"Aghaloo O`Neill's", "Aghaloo")
    teamName = teamName.replace (u"Tattyreagh St Patrick's", "Tattyreagh")
    teamName = teamName.replace (u"Beragh Red Knights GAA	5", "Beragh")
    teamName = teamName.replace (u"Owen Roe O`Neill's GAC, Leckpatrick", "Owen Roe ")
    teamName = teamName.replace (u"Brockagh Emmetts", "Brockagh")
    teamName = teamName.replace (u"Drumquin Wolfe Tones", "Drumquin")
    #teamName = teamName.replace (u"Droim Ratha an tSáirsealaigh", "")
    teamName = teamName.replace (u"Dregish Pearse Óg", "Dregish")
    teamName = teamName.replace (u"Beragh Red Knights GAA", "Beragh")
    teamName = teamName.replace (u"Droim Ratha an tSáirsealaigh", "Drumragh")

    return teamName

# Set the venue of the game.
# The venue may not always be present in the XML.  If the game is a league game
# then the venue may be inferred.
# This function will first check for the presence a venueName.  If present then
# it will be used.  Some cleanup may be needed.  The term "at HOME" will be used
# in the event the venue is Donaghmore GAA.  The venue may require some cleanup
# as the name of the pitch can be used.
# If the venueName is not present then the venue will effectively be home or away
# depending if Donaghmore are the home or away club.
# It is assumed that the homeClub and awayClub parameters have been cleaneed by shortenTeamName
def shortenVenueName (venueName, homeClub, awayClub):

    if (venueName != ""):
      # Perform replacement cleanup onthe venue name and return
      venueName = venueName.replace (u"Donaghmore GAA", "HOME")
      venueName = venueName.replace (u"Domhnach Mór", "HOME")
      venueName = venueName.replace (u"Páirc An tAthair Uí Conghalaigh", "Eglish")
      venueName = venueName.replace (u"Páirc Uí Raithile", "Clonoe")
      venueName = venueName.replace (u"Dungannon Thomas Clarke", "Dungannon")

      if (venueName == "HOME"):
          venueName = "(" + venueName + ")"
      else:
          venueName = "(in " + venueName + ")"
          
    else:
       # Assume league game and work on home or away
       if (homeClub == "Donaghmore"):
           venueName = "(HOME)"
       else:
           venueName = "(in " + awayClub + ")"

    return venueName

#format the date
def formatDate(dateToFormat, timeToFormat):
  
    today = datetime.datetime.today()
    dateString = dateToFormat + ' ' + timeToFormat
    dateFormat = "%Y-%m-%d %I %M %p"
    
    d = datetime.datetime.strptime(dateString, dateFormat)
    
    if 4 <= d.day <= 20 or 24 <= d.day <= 30:
       suffix = "th"
    else:
       suffix = ["st", "nd", "rd"][d.day % 10 - 1]
       
    dayDate = d.__format__('%a %-d')  
    month = d.__format__('%b')
    year = d.__format__('%Y')
    matchTime = d.__format__('%-I:%M%p')
    matchTime = matchTime.replace ("PM", "pm")
    matchTime = matchTime.replace ("AM", "am")

    if (d < today):
       formattedDate = dayDate + suffix + ' ' + month + ' ' + year
    elif (d.year != today.year):
       formattedDate = dayDate + suffix + ' ' + month + ' ' + year
    elif (d.month != today.month):
       formattedDate = dayDate + suffix + ' ' + month
    else:
       formattedDate = dayDate + suffix
    
    return (formattedDate, matchTime)

# parse XML
def getText(nodelist):
    rc = []
    for node in nodelist:
        if node.nodeType == node.TEXT_NODE:
            rc.append(node.data)
    return ''.join(rc)
 
def processComingFixturesToJson():
    try:
        doc = minidom.parse(urllib2.urlopen(comingFixtures))
    except:
	print "Error download fixtures XML:", comingFixtures, ":", sys.exc_value
	sys.exit(0)
    else:
	node = doc.documentElement
	fixtures = doc.getElementsByTagName("fixture")
	
	fixtureJson = []

	print "Fixtures"

	for fixture in fixtures:
	    dateObj = fixture.getElementsByTagName("date")[0]
	    timeObj = fixture.getElementsByTagName("time")[0]

	    club_1_nameObj = fixture.getElementsByTagName("club_1_name")[0]
	    club_2_nameObj = fixture.getElementsByTagName("club_2_name")[0]
	    competition_nameObj = fixture.getElementsByTagName("competition_name")[0]
	    competitionShort_nameObj = fixture.getElementsByTagName("competition_short_name")[0]
	    comp_levelObj = fixture.getElementsByTagName("comp_level")[0]
	    comp_typeObj = fixture.getElementsByTagName("comp_type")[0]
	    roundNameObj = fixture.getElementsByTagName("round_name")[0]
	    venueObj = fixture.getElementsByTagName("venue_name")[0]

	    fixtureDate = getText(dateObj.childNodes)
	    fixtureTime = getText(timeObj.childNodes)
	    (matchDate, matchTime) = formatDate ( fixtureDate, fixtureTime );

	    compName = getText(competition_nameObj.childNodes)
	    compNameShort = getText(competitionShort_nameObj.childNodes)
	    compLevel = getText(comp_levelObj.childNodes)
	    compType = getText(comp_typeObj.childNodes)
	    roundName = getText(roundNameObj.childNodes)

	    teamLevel = getTeamLevel(compName, compNameShort, compLevel)
	    compNameClean = shortenCompetitionName(compType, roundName)

	    homeClub = getText(club_1_nameObj.childNodes)
	    homeClubRenamed = shortenTeamName(homeClub)

	    awayClub = getText(club_2_nameObj.childNodes)
	    awayClubRenamed = shortenTeamName(awayClub)

	    venueName = getText(venueObj.childNodes)
	    venueNameRenamed = shortenVenueName(venueName, homeClubRenamed, awayClubRenamed )

	    thisFixture = '{"date": "%s","time": "%s","level": "%s","comp": "%s","home": "%s","away": "%s", "venue": "%s"}' % (matchDate, matchTime, teamLevel, compNameClean, homeClubRenamed,
	    awayClubRenamed, venueNameRenamed);
	    fixtureJson.append(thisFixture)

	    print "%s %s : %s - %s %s - %s V %s" % (matchDate, matchTime, teamLevel, compNameClean,venueNameRenamed, homeClubRenamed, awayClubRenamed)

	#print ''.join(fixtureJson)

	fixturesJson =  '"Fixtures":['

	for i in range (0, len(fixtureJson)-1):
	    x = "%s,"  % (fixtureJson[i])
	    fixturesJson = fixturesJson + x

	fixturesJson = fixturesJson + fixtureJson[len(fixtureJson)-1]

	fixturesJson = fixturesJson + (']')

	#json=json.dumps(fixturesJson)

	return fixturesJson
	#fh = open('comingFixtures.json', 'w');
	#fh.write  (fixturesJson);
	#fh.close();    

def processRecentResultsToJson():
    try:
        doc = minidom.parse(urllib2.urlopen(recentResults))
    except:
        print "Error download results XML:", recentResultsFixtures, ":", sys.exc_value
        sys.exit(0)
    else:
	node = doc.documentElement
	fixtures = doc.getElementsByTagName("fixture")

	fixtures.reverse()

	fixtureJson = []

	print "Results:"

	for fixture in fixtures:
	    dateObj = fixture.getElementsByTagName("date")[0]
	    timeObj = fixture.getElementsByTagName("time")[0]

	    club_1_nameObj = fixture.getElementsByTagName("club_1_name")[0]
	    team_1_goalsObj = fixture.getElementsByTagName("team_1_goals")[0]
	    team_1_pointsObj = fixture.getElementsByTagName("team_1_points")[0]
	    club_2_nameObj = fixture.getElementsByTagName("club_2_name")[0]
	    team_2_goalsObj = fixture.getElementsByTagName("team_2_goals")[0]
	    team_2_pointsObj = fixture.getElementsByTagName("team_2_points")[0]
	    roundNameObj = fixture.getElementsByTagName("round_name")[0]
	    venueObj = fixture.getElementsByTagName("venue_name")[0]

	    competition_nameObj = fixture.getElementsByTagName("competition_name")[0]
	    competitionShort_nameObj = fixture.getElementsByTagName("competition_short_name")[0]
	    comp_levelObj = fixture.getElementsByTagName("comp_level")[0]
	    comp_typeObj = fixture.getElementsByTagName("comp_type")[0]

	    fixtureDate = getText(dateObj.childNodes)
	    fixtureTime = getText(timeObj.childNodes)
	    (matchDate, matchTime) = formatDate ( fixtureDate, fixtureTime );

	    compName = getText(competition_nameObj.childNodes)
	    compNameShort = getText(competitionShort_nameObj.childNodes)
	    compLevel = getText(comp_levelObj.childNodes)
	    compType = getText(comp_typeObj.childNodes)
	    roundName = getText(roundNameObj.childNodes)

	    teamLevel = getTeamLevel(compName, compNameShort, compLevel)
	    compNameClean = shortenCompetitionName(compType, roundName)

	    homeClub = getText(club_1_nameObj.childNodes)
	    homeClubRenamed = shortenTeamName(homeClub)
	    homeClubGoals = getText(team_1_goalsObj.childNodes)
	    homeClubPoints = getText(team_1_pointsObj.childNodes)

	    awayClub = getText(club_2_nameObj.childNodes)
	    awayClubRenamed = shortenTeamName(awayClub)
	    awayClubGoals = getText(team_2_goalsObj.childNodes)
	    awayClubPoints = getText(team_2_pointsObj.childNodes)

	    venueName = getText(venueObj.childNodes)
	    venueNameRenamed = shortenVenueName(venueName, homeClubRenamed, awayClubRenamed)

	    thisFixture = '{"date": "%s","time": "%s","level": "%s","comp": "%s","home": "%s","homeScore": "%s-%s", "away": "%s", "awayScore": "%s-%s", "venue": "%s"}' % (matchDate, matchTime, teamLevel, compNameClean, homeClubRenamed, homeClubGoals, homeClubPoints, awayClubRenamed, awayClubGoals, awayClubPoints, venueNameRenamed)
	    fixtureJson.append(thisFixture)

	    print "%s : %s - %s - %s %s-%s V %s %s-%s" % (matchDate, teamLevel, compNameClean, homeClubRenamed,homeClubGoals, homeClubPoints, awayClubRenamed, awayClubGoals, awayClubPoints)

	fixturesJson =  '"Results":['

	for i in range (0, len(fixtureJson)-1):
	    x = "%s,"  % (fixtureJson[i])
	    fixturesJson = fixturesJson + x

	if (len(fixtureJson) > 0):
	    fixturesJson = fixturesJson + fixtureJson[len(fixtureJson)-1]

	fixturesJson = fixturesJson + (']')

	return fixturesJson
	#fh = open('comingFixtures.json', 'w');
	#fh.write  (fixturesJson);
	#fh.close();
        
if __name__ == "__main__":


  
    # Main function to build the json data.  The json data is appended into an array.
    # The array is joined and written to a single file.
    theJsonData = []
    theJsonData.append('{ "Info":[{"lastUpdated": "now"}],')
    theJsonData.append(processComingFixturesToJson())
    theJsonData.append(',')
    theJsonData.append(processRecentResultsToJson())
    theJsonData.append('}')
    
    #print ''.join(theJsonData)
    # write json
    try:
        fh = open(outputJsonFile, 'w');
        fh.write  (''.join(theJsonData));
        print "Data written to file: '" + outputJsonFile + "'"
    except IOError:
        print "Error: can\'t write to file: '" + outputJsonFile + "'"
    else:    
        fh.close(); 


