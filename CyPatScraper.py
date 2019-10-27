import requests
from bs4 import BeautifulSoup
import json
import numpy
import re
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
        tempDict = {}  # temporary dictionary to allow for nested dictionaries with x amount of key, values
        for image in images:
            tempDict[image] = {
                "avgSlope": findAvgSlope(team, image)
            }
        finishedTeamData[team] = tempDict


def separateGraph(teamData):
    # Receives a specific team's dict with images and coords

    for coord in teamData:
        h = h


def determineDifficulty(OS):
    difficulty = 22.5 * (finalData[OS]["meanSlope"] - 2) ** 2 + 10  # Based off of the graph of f(x)=22.5(x-2)^2+10
    return round(difficulty, 2)


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
        time.sleep(3)  # implemented so an error is not pulled because of too many requests
    print("\n--------\n")  # User experience
    # At this point, the coordinate point dictionary is complete, so refined team data will be created
    assembleTeamData(teams)
    # adds final, overall information to finalData dictionary
    for image in images:
        tempSlopeList = [finishedTeamData[team][image]["avgSlope"] for team in teams]
        finalData[image] = {
            "meanSlope": numpy.mean(tempSlopeList),
            "medianSlope": numpy.median(tempSlopeList),
            "modeSlope": 0,
            "rangeSlope": {
                "min": sorted(tempSlopeList)[0],
                "max": sorted(tempSlopeList)[-1]
            }
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
        output += pleasingOutput + " is rated at " + str(determineDifficulty(image)) + "% difficulty\n"
    print(output + "\nGood luck!")


main()
# # print(finishedTeamData)
# print(finalData)
