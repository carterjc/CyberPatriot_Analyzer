import requests
from bs4 import BeautifulSoup
import re
import json
import time


def locateNJIndex(soup):
    teamData = soup.select("tr")
    # Very helpful source
    # https://stackoverflow.com/questions/9007653/how-to-find-tag-with-particular-text-with-beautiful-soup
    NJIndex = teamData.index(soup.find('td', text=re.compile('NJ')).parent)
    return NJIndex


def selectNJTeams(start, listLength, soup, division):
    teams = []
    teamData = soup.select("tr")
    for i in range(start, listLength):
        if teamData[i].select("td")[2].text == "NJ":
            if teamData[i].select("td")[3].text == division:
                teams.append(soup.select("tr")[i].attrs["href"][-7:])
                # Adds the team number of every NJ team
        else:
            break  # if team is not NJ, end the loop
    return teams


def getTeamInfo(NJTeam):  # gets individual team info
    teamPage = "team.php?team=" + NJTeam
    data = requests.get("http://scoreboard.uscyberpatriot.org/" + teamPage)  # Concatenates to find the URL
    # Locates coordinate information
    coordinates = data.text[data.text.find("arrayToDataTable("):data.text.find("]);")][:-7] + "]"
    j_info = coordinates.partition("ToDataTable(")[2].replace("'", '"')
    json1 = json.loads(j_info)  # formats the data as JSON to be accessed easily
    return json1[1][0]  # returns time from the first coordinate


def teamInfo(teams):  # assembles all NJ team info
    NJTeamData = {}
    complete = 1
    for team in teams:
        print("Team " + str(complete) + " out of " + str(len(teams)))
        firstCoord = getTeamInfo(team)
        NJTeamData[team] = firstCoord
        complete += 1
        time.sleep(3)
    return NJTeamData


def checkTeamData(timeData, selectedDate, selectedTime):
    suspectedSchoolTeams = []
    for key in timeData:
        data = timeData[key]
        date, time = data.split(" ")[0], data.split(" ")[1]
        if date == selectedDate:  # Checks if the team competed on a specific data
            if time[:2] == selectedTime:  # If so, checks if they competed around the same time (checks hour)
                suspectedSchoolTeams.append(key)
    return suspectedSchoolTeams


def endResult(schoolTeams, numOfTeams):
    possibleTeamsLength = len(schoolTeams)
    print("Teams that matched your filter\n-------")
    for team in schoolTeams:
        print(team)
    print("-------")
    print("There were " + str(possibleTeamsLength) + " teams that matched your filter. Your school "
          "has " + str(numOfTeams) + ", so the results were off by " + str(abs(possibleTeamsLength - numOfTeams))
          + " teams.")
    findData = str(input("Do you want to find the data for these teams? (Y/N)"))


def main():
    # state = "NJ"
    dateFilter = "10/26"
    startHour = "13"
    division = "Open"
    numOfTeams = 10
    # Makes initial request
    mainPage = requests.get("http://scoreboard.uscyberpatriot.org/index.php?sort=Location")
    soup = BeautifulSoup(mainPage.text, 'lxml')
    # Finds the first NJ team when sorting by location
    NJIndex = locateNJIndex(soup)
    print("Located NJ Teams\n-------")
    # Creates a list of all NJ teams
    NJTeams = selectNJTeams(NJIndex, len(soup.select("tr")), soup, division)
    print("Created NJ team list\n-------")
    # Creates dictionary with the team and the first coordinate time data
    timeData = teamInfo(NJTeams)
    print("Pulled team specific information\n-------")
    # Refines list to teams with a certain date/time
    schoolTeams = checkTeamData(timeData, dateFilter, startHour)
    endResult(schoolTeams, numOfTeams)
    # Note: it might be good to get this information for multiple competitions and cross out teams that only appear
    # once, etc. Keep it mind coicendencees happen
    # Also, just for R1 a freshmen team started very late, making them not appear on this list


main()
