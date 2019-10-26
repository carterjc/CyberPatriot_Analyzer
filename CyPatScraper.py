import requests
from bs4 import BeautifulSoup
import json
import numpy
import matplotlib.pyplot as plt
import pandas as pt
import scipy as stats
import statistics
from sklearn.preprocessing import PolynomialFeatures
from sklearn.linear_model import LinearRegression
import time

teamInfo = {}  # stores coordinate points
finishedTeamData = {}  # stores avgSlope and more metrics for each team and their OSs
finalData = {}  # stores data to be looked at by the user (avgSlope for all of one OS, etc.)


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
    json1 = json.loads(j_info)  # formats the data as JSON to be accessed easily
    createData(json1, teamNumber)


# Finds the teams to analyze
def teamFinder(numberOfTeams):
    main_page = requests.get("http://scoreboard.uscyberpatriot.org/")  # makes initial request, recieves HTML
    soup = BeautifulSoup(main_page.text, 'lxml')
    teams = []  # declares array that stores team links to be parsed
    for i in range(1, numberOfTeams + 1):
        teams.append(soup.select("tr")[i].attrs["href"][-7:])  # selects a given team and finds the link to their page
        # Also parses out the ugly link for easier use later on
    return teams


def findAvgSlope(teamNumber, OS):
    firstIndex = 0  # Sometimes an image might start late, so this ensures the first real point is grabbed
    firstPoint = teamInfo[teamNumber][OS][firstIndex]
    while firstPoint[1] is None:
        firstPoint = teamInfo[teamNumber][OS][firstIndex + 1]
        firstIndex += 1
    lastIndex = -1
    lastPoint = teamInfo[teamNumber][OS][lastIndex]
    while lastPoint[1] is None:
        lastPoint = teamInfo[teamNumber][OS][lastIndex - 1]
        lastIndex -= 1
    print(lastPoint, firstPoint)
    slope = (lastPoint[1]-firstPoint[1])/(lastPoint[0]-firstPoint[0])
    return slope


def polynomialRegression(teamNumber, OS):
    points = teamInfo[teamNumber][OS]
    X = []
    y = []
    for point in points:
        firstX = point[0]
        firstY = point[1]
        if firstY is None:
            if firstX <= 4:
                firstY = 0
            else:
                firstY = 100
        X.append([firstX, firstY])
        y.append(firstY)
    poly = PolynomialFeatures(degree=6)
    X_poly = poly.fit_transform(X)
    poly.fit(X_poly, y)
    lin2 = LinearRegression()
    lin2.fit(X_poly, y)
    print(lin2)
    plt.plot(X, lin2.predict(poly.fit_transform(X)), color='red')
    plt.show()


def determineDifficulty(OS):
    # benchmarkSlope = .2
    difficulty = 22.5 * (finalData[OS]["meanSlope"] - 2) ** 2 + 10  # Based off of the graph of f(x)=22.5(x-2)^2+10
    return round(difficulty, 2)


def main():
    numberOfTeams = 2
    teams = teamFinder(numberOfTeams)
    completed = 1
    for team in teams:
        accessTeamData(team)
        print("Team " + str(completed) + " out of " + str(numberOfTeams))
        completed += 1
        time.sleep(3)  # implemented so an error is not pulled because of too many requests
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
    # creates a data set of all server slopes
    serverSlopes = []
    [serverSlopes.append(finishedTeamData[team]["Server2016"]["avgSlope"])for team in teams]
    # creates a data set of all server slopes
    windowsSlopes = []
    [windowsSlopes.append(finishedTeamData[team]["Windows10"]["avgSlope"])for team in teams]
    # creates a data set of all server slopes
    ubuntuSlopes = []
    [ubuntuSlopes.append(finishedTeamData[team]["Ubuntu14"]["avgSlope"])for team in teams]
    global finalData
    finalData = {
        "Server2016": {
            "meanSlope": numpy.mean(serverSlopes),
            "medianSlope": numpy.median(serverSlopes),
            "modeSlope": 0,
            "rangeSlope": {
                "min": sorted(serverSlopes)[0],
                "max": sorted(serverSlopes)[-1]
            }
        },
        "Windows10": {
            "meanSlope": numpy.mean(windowsSlopes),
            "medianSlope": numpy.median(windowsSlopes),
            "modeSlope": 0,
            "rangeSlope": {
                "min": sorted(windowsSlopes)[0],
                "max": sorted(windowsSlopes)[-1]
            }
        },
        "Ubuntu14": {
            "meanSlope": numpy.mean(ubuntuSlopes),
            "medianSlope": numpy.median(ubuntuSlopes),
            "modeSlope": 0,
            "rangeSlope": {
                "min": sorted(ubuntuSlopes)[0],
                "max": sorted(ubuntuSlopes)[-1]
            }
        }
    }
    # polynomialRegression(teams[4], "Server2016")
    serverDifficulty = determineDifficulty("Server2016")
    windowsDifficulty = determineDifficulty("Windows10")
    ubuntuDifficulty = determineDifficulty("Ubuntu14")
    return "Windows 10 is rated at " + str(windowsDifficulty) + "% difficulty\n" \
           "Windows Server 2016 is rated at " + str(serverDifficulty) + "% difficulty\n" \
           "Ubuntu 14 is rated at " + str(ubuntuDifficulty) + "% difficulty\n" \
           "Good luck!"


print(main())
# print(finishedTeamData)
print(finalData)
