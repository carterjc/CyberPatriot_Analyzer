import requests
from bs4 import BeautifulSoup
import json

teamInfo = {}
finishedTeamData = {}


# Create coordinate points
def createData(data, teamNumber):
    serverCoords = []
    windowsCoords = []
    ubuntuCoords = []
    # Server 2016
    for i in range(1, len(data)):  # Omits 0 because that gives information on the data itself, not coordinates
        serverCoords.append(((i - 1) * 5, data[i][1]))
    # Windows 10
    for i in range(1, len(data)):
        windowsCoords.append(((i - 1) * 5, data[i][3]))
    # Ubuntu
    for i in range(1, len(data)):
        ubuntuCoords.append(((i - 1) * 5, data[i][2]))

    # Adds the data to the dictionary under the team number
    teamInfo[teamNumber] = {
        "Server2016": serverCoords,
        "Windows10": windowsCoords,
        "Ubuntu14": ubuntuCoords
    }


# Access the data for each team
def accessTeamData(teamNumber):
    teamPage = "team.php?team=" + teamNumber
    test = requests.get("http://scoreboard.uscyberpatriot.org/" + teamPage)  # Concatenates to find the URL
    # Finds where the block of necessary data is located (find returns a number) and parses out the pesky comma
    teamData = test.text[test.text.find("arrayToDataTable("):test.text.find("]);")][:-7] + "]"
    # Holy god, apparently a comma at the end of an array is such an agregious error that JSON cannot stand to bear it
    # Essentially, the comma is removed and a bracket added, aligning with the JSON format
    j_info = teamData.partition("ToDataTable(")[2].replace("'", '"')
    print(j_info)
    json1 = json.loads(j_info)  # formats the data as JSON to be accessed easily
    createData(json1, teamNumber)


# Finds the teams to analyze
def teamFinder():
    numberOfTeams = 10
    main_page = requests.get("http://scoreboard.uscyberpatriot.org/")  # makes initial request, recieves HTML
    soup = BeautifulSoup(main_page.text, 'lxml')
    teams = []  # declares array that stores team links to be parsed
    for i in range(1, numberOfTeams + 1):
        teams.append(soup.select("tr")[i].attrs["href"][-7:])  # selects a given team and finds the link to their page
        # Also parses out the ugly link for easier use later on
    return teams


def findAvgSlope(teamNumber, key):
    point = 0  # Sometimes an image might start late, so this ensures the first real point is grabbed
    firstPoint = teamInfo[teamNumber][key][point]
    while firstPoint[1] is None:
        firstPoint = teamInfo[teamNumber][key][point + 1]
        point += 1
    lastPoint = teamInfo[teamNumber][key][-1]
    if lastPoint[1] is None:
        lastPoint = (lastPoint[0], 100)
    slope = (lastPoint[1]-firstPoint[1])/(lastPoint[0]-firstPoint[0])
    return slope


def main():
    teams = teamFinder()
    for team in teams:
        accessTeamData(team)
    # At this point, the coordinate point dictionary is complete
    for team in teams:
        finishedTeamData[team] = {
            "Server2016": {
                "avgSlope": findAvgSlope(team, 'Server2016')
            },
            "Windows10": {
                "avgSlope": findAvgSlope(team, 'Windows10')
            },
            "Ubuntu14": {
                "avgSlope": findAvgSlope(team, 'Ubuntu14')
            }
        }
    sumSlope = 0
    for team in teams:
        sumSlope += finishedTeamData[team]["Server2016"]["avgSlope"]
    print(sumSlope/len(teams))

main()
print(finishedTeamData)
