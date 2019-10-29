import requests
from bs4 import BeautifulSoup
import json
import numpy
import re
import time

teamInfo = {}  # stores coordinate points
finishedTeamData = {}  # stores avgSlope and more metrics for each team and their OSs
finalData = {}  # stores data to be looked at by the user (avgSlope for all of one OS, etc.)
images = []


def determineImage():
    main_page = requests.get("http://scoreboard.uscyberpatriot.org/")  # makes initial request, recieves HTML
    soup = BeautifulSoup(main_page.text, 'lxml')
    # Finds the first team number (need this to get images)
    # Actual team does not matter
    firstTeam = ""
    teamIndex = 1  # Index 0 is the table header
    while firstTeam == "":
        teamHTML = soup.select("tr")[1]
        if teamHTML.select("td")[3].text == "Open":  # Makes sure the team is of Open division
            firstTeam = teamHTML.attrs["href"][-7:]
            break
        teamIndex += 1
    # Makes specific team request
    team_page = requests.get("http://scoreboard.uscyberpatriot.org/team.php?team=" + firstTeam)
    soup = BeautifulSoup(team_page.text, 'lxml')
    numberOfImages = int(soup.select("tr")[1].findChildren()[4].text)  # Grabs the number of images
    for i in range(3, numberOfImages + 3):
        fullName = soup.select("tr")[i].findChildren()[0].text
        images.append(fullName[:fullName.find("_")])  # Adds the refined image names to an array


# parses JSON and assembles a list of coordinates
def createData(data, teamNumber):
    # Allows index of the specific image to be found (so the right coords are pulled)
    newList = []
    for value in data[0]:  # Creates a list mimicking CyPat's one, but with refined image names
        # We expect a list that starts with Time and then lists the images
        if "_" in value:
            newList.append(value[:value.find("_")])
        else:  # For the time value at index 0, just add it (real use expectation)
            newList.append(value)
    # Assembles the list of coordinates and places it into a temporary dictionary
    tempDict = {}
    for image in images:
        tempList = []
        for i in range(1, len(data)):  # Omits 0 because that gives information on the data itself, not coordinates
            tempList.append(((i - 1) * 5, data[i][newList.index(image)]))
        tempDict[image] = tempList
    teamInfo[teamNumber] = tempDict


# Access the data for each team
def accessTeamData(teamNumber):
    teamPage = "team.php?team=" + teamNumber
    data = requests.get("http://scoreboard.uscyberpatriot.org/" + teamPage)  # Concatenates to find the URL
    # Finds where the block of necessary data is located (find returns a number) and parses out the pesky comma
    teamData = data.text[data.text.find("arrayToDataTable("):data.text.find("]);")][:-7] + "]"
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
    teamRank = 1
    while len(teams) < numberOfTeams:
        teamHTML = soup.select("tr")[teamRank]
        # Makes sure the team is of Open division
        if teamHTML.select("td")[3].text == "Open":
            # selects a given team and finds the link to their page
            teams.append(teamHTML.attrs["href"][-7:])
        teamRank += 1
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
    slope = (lastPoint[1]-firstPoint[1])/(lastPoint[0]-firstPoint[0])
    return slope


def assembleTeamData(teams):
    for team in teams:
        XData = separateGraphs(teamInfo[team])  # pulls the key xs that section the graph
        minutesWithLowY = lowTeamYChanges(teamInfo[team])
        tempDict = {}  # temporary dictionary to allow for nested dictionaries with x amount of key, values
        for image in images:
            tempDict[image] = {
                "avgSlope": findAvgSlope(team, image),
                "importantXs": XData[image],
                "lowChangeInY": minutesWithLowY[image]
            }
        finishedTeamData[team] = tempDict


def separateGraphs(teamData):
    # Receives a specific team's dict with images and coords
    xDict = {}  # stores x values where the slope changed dramatically - image: [values]
    for image in images:
        coordList = [coord for coord in teamData[image] if not coord[1] is None]  # new list of points with no y = None
        tempXList = []  # list of x values where slope change is dramatic
        changeY = [(coordList[i][0], coordList[i][1] - coordList[i - 1][1])
                   for i in range(1, len(coordList))]  # returns tuples of x value, change in y
        compareIndex = 0
        for i in range(1, len(changeY)):
            if changeY[i][1] < changeY[i - 1][1] * .7:  # Compares current change to previous change *.5
                tempXList.append(changeY[i - 1][0])  # Adds x value if true
                # When the change falls dramatically, cut the previous portion of the graph off, then section the new
                # remaining graph
                compareIndex = i
            if changeY[i - 1][1] < changeY[compareIndex][1] * .5:  # Compares change to starting change
                tempXList.append(changeY[i][0])  # Adds x value where the overall change decreased by .5
                compareIndex = i
        xDict[image] = tempXList  # When all coords have been cycled through, add them to dictionary
    return xDict


def lowTeamYChanges(teamData):  # determines the number of minutes in which the change in Y < 3 for a given team
    minDict = {}
    for image in images:
        coordList = [coord for coord in teamData[image] if not coord[1] is None]  # new list of points with no y = None
        changeY = [(coordList[i][0], coordList[i][1] - coordList[i - 1][1])
                   for i in range(1, len(coordList))]  # returns tuples of x value, change in y
        lowYChangeCount = 0
        for value in changeY:
            if value[1] <= 3:
                lowYChangeCount += 1
        minDict[image] = (lowYChangeCount * 5)/coordList[-1][0]
    return minDict


def avgLowYChanges(image):
    avgLowY = 0
    for team in finishedTeamData:
        avgLowY += finishedTeamData[team][image]["lowChangeInY"]
    return round(avgLowY/len(finishedTeamData), 2)


def mapTo(oldMax, oldMin, newMax, newMin, oldValue):
    oldRange = oldMax - oldMin
    if oldRange == 0:
        newValue = newMin
    else:
        newRange = newMax - newMin
        newValue = (((oldValue - oldMin) * newRange)/oldRange) + newMin
    return newValue


def determineDifficulty(OS, teams):
    # Creates adjusted average slope
    slopeList = sorted([finishedTeamData[team][OS]["avgSlope"] for team in teams])
    oldSlopeMax = slopeList[-1]
    oldSlopeMin = slopeList[0]
    oldSlopeValue = finalData[OS]["meanSlope"]
    adjustedAvgSlope = mapTo(oldSlopeMax, oldSlopeMin, 1, 0, oldSlopeValue)
    print(oldSlopeValue, adjustedAvgSlope)

    # Finds slope range
    slopeRange = oldSlopeMax - oldSlopeMin
    weightedSlopeRange = mapTo(oldSlopeMax, oldSlopeMin, 1, 0, slopeRange)
    print(oldSlopeMax, oldSlopeMin)
    print(slopeRange, weightedSlopeRange)

    # firstDifficultTime
    fDT = finalData[OS]["firstDifficultTime"]
    fDTList = sorted([finishedTeamData[team][OS]["importantXs"][0] for team in finishedTeamData])
    oldFDTMax = fDTList[-1]
    oldFDTMin = fDTList[0]
    weightedFDT = mapTo(oldFDTMax, oldFDTMin, 1, 0, fDT)
    print(fDT, weightedFDT)

    # timeWithLowY
    avgTime = finalData[OS]["timeWithLowYChange"]
    avgTimeList = sorted([finishedTeamData[team][OS]["lowChangeInY"] for team in finishedTeamData])
    oldTimeMax = avgTimeList[-1]
    oldTimeMin = avgTimeList[0]
    weightedAvgTime = mapTo(oldTimeMax, oldTimeMin, 1, 0, avgTime)
    print(avgTime, weightedAvgTime)

    # Creates one number to base the calculations off of
    print(adjustedAvgSlope, weightedSlopeRange, weightedFDT, weightedAvgTime)
    # Variable has the goal of determining the difficulty of an image
    # If a variable increasing would represent an easier image, it was subtracted

    def moreDifficult(value):
        return -22.5 * (value - 2) ** 2 + 100

    def lessDifficult(value):
        return 22.5 * (value - 2) ** 2 + 10

    temp = lessDifficult(adjustedAvgSlope) + moreDifficult(weightedSlopeRange) + lessDifficult(weightedFDT) + moreDifficult(weightedAvgTime)
    weightedVariable = weightedAvgTime - weightedFDT + weightedSlopeRange - adjustedAvgSlope
    # Calculates rating
    difficulty = 22.5 * (weightedVariable - 2) ** 2 + 10  # Based off of the graph of f(x)=22.5(x-2)^2+10
    return round(temp, 2)


def findDifficultTimes(image):  # Calculates the average time in which most teams start to slow down
    avgX = 0
    teamsCounted = 0  # If a team is skipped (doesn't have any x values) the entire average won't be weighted
    for team in finishedTeamData:
        if len(finishedTeamData[team][image]["importantXs"]) > 0:
            avgX += finishedTeamData[team][image]["importantXs"][0]  # Grabs first point in which slope changed
            teamsCounted += 1
    return avgX/teamsCounted


def assembleFinalData(teams):
    for image in images:
        tempSlopeList = [finishedTeamData[team][image]["avgSlope"] for team in teams]
        finalData[image] = {
            "meanSlope": numpy.mean(tempSlopeList),
            "medianSlope": numpy.median(tempSlopeList),
            "modeSlope": 0,
            "rangeSlope": {
                "min": sorted(tempSlopeList)[0],
                "max": sorted(tempSlopeList)[-1]
            },
            "firstDifficultTime": findDifficultTimes(image),  # Finds the avg minute in which y change decreases
            "timeWithLowYChange": avgLowYChanges(image)  # time with low y change
        }
    # Determines difficulty and outputs result
    output = ""
    for image in images:
        pleasingOutput = image
        # Finds the index in which a space should be added (see Windows10 vs Windows 10)
        # Didn't know how to break, so take the first index (first number in the string)
        if re.search(r'\d', image):  # Checks if the image name actually has numbers in it
            index = [i for i in range(len(image)) if image[i].isdigit()][0]
            pleasingOutput = image[:index] + " " + image[index:]
        output += pleasingOutput + " is rated at " + str(determineDifficulty(image, teams)) + "% difficulty\n"
    print(output + "\nGood luck!")


def main():
    # Introduction to the program
    print("Welcome to the CyberPatriot competition sentiment Analyzer!")
    print("This program scans a number of teams and determines the difficulty of the image based on performance. "
          "Select the number of teams you want to scan and let the program do the rest!")
    print("\n--------\n")  # User experience
    # Main program
    determineImage()
    numberOfTeams = int(input("How many teams do you want to run an analysis on?"))
    print("\n--------\n")  # User experience
    teams = teamFinder(numberOfTeams)
    completed = 1
    for team in teams:
        accessTeamData(team)
        teamScore = requests.get("http://scoreboard.uscyberpatriot.org/team.php?team=" + team)
        soup = BeautifulSoup(teamScore.text, 'lxml')
        score = int(soup.select("tr")[1].findChildren()[8].text)
        print("Team " + str(completed) + " out of " + str(numberOfTeams) + " - Team Number: "
              "" + team + " {" + str(score) + "}")
        completed += 1
        time.sleep(5)  # implemented so an error is not pulled because of too many requests
    print("\n--------\n")  # User experience
    # At this point, the coordinate point dictionary is complete, so refined team data will be created
    assembleTeamData(teams)
    # adds final, overall information to finalData dictionary
    assembleFinalData(teams)


main()
# # print(finishedTeamData)
print(finalData)
