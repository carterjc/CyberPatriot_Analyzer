import requests
from bs4 import BeautifulSoup
import re
import json
import time


def locate_index(soup, loc):
    teamData = soup.select("tr")
    # Very helpful source
    # https://stackoverflow.com/questions/9007653/how-to-find-tag-with-particular-text-with-beautiful-soup
    loc_index = teamData.index(soup.find('td', text=re.compile(loc)).parent)
    return loc_index


def select_teams(start, list_length, soup, division, loc):
    teams = []
    team_data = soup.select("tr")
    for i in range(start, list_length):
        if team_data[i].select("td")[2].text == loc:
            if team_data[i].select("td")[3].text == division:
                teams.append(soup.select("tr")[i].attrs["href"][-7:])
                # Adds the team number of every location team
        else:
            break  # if team is not location, end the loop
    return teams


def get_team_info(loc_team):  # gets individual team info
    team_page = "team.php?team=" + loc_team
    data = requests.get("http://scoreboard.uscyberpatriot.org/" + team_page)  # Concatenates to find the URL
    # Locates coordinate information
    coordinates = data.text[data.text.find("arrayToDataTable("):data.text.find("]);")][:-7] + "]"
    j_info = coordinates.partition("ToDataTable(")[2].replace("'", '"')
    json1 = json.loads(j_info)  # formats the data as JSON to be accessed easily
    return json1[1][0]  # returns time from the first coordinate


def team_info(teams):  # assembles all NJ team info
    loc_team_data = {}
    complete = 1
    for team in teams:
        print("Team " + str(complete) + " out of " + str(len(teams)))
        first_coord = get_team_info(team)
        loc_team_data[team] = first_coord
        complete += 1
        time.sleep(3)
    return loc_team_data


def check_team_data(time_data, selected_date, selected_time):
    suspected_teams = []
    for key in time_data:
        data = time_data[key]
        date, time = data.split(" ")[0], data.split(" ")[1]
        s_month, s_day = selected_date.split("/")
        if len(s_month) == 1:
            s_month = "0" + s_month
        if len(s_day) == 1:
            s_day = "0" + s_day
        selected_date = s_month + "/" + s_day
        print(date, selected_date, date == selected_date)
        if date == selected_date:  # Checks if the team competed on a specific data
            if time[:2] == selected_time:  # If so, checks if they competed around the same time (checks hour)
                suspected_teams.append(key)
    return suspected_teams


def end_result(school_teams, num_of_teams):
    possible_teams_length = len(school_teams)
    print("Teams that matched your filter\n-------")
    for team in school_teams:
        print(team)
    print("-------")
    print("There were " + str(possible_teams_length) + " teams that matched your filter. You wanted"
          " " + str(num_of_teams) + ", so the results were off by " + str(abs(possible_teams_length - num_of_teams))
          + " teams.")
    # findData = str(input("Do you want to find the data for these teams? (Y/N)"))


def main():
    print("""
Welcome to team_finder. This program scrapes the public scoreboard for teams that meet your defined conditions. It can
be used to find teams from certain schools or anything else.
    """)
    loc = input("Enter the location abbreviation of your choice:")
    date_filter = input("Enter a date to filter teams by (ex. 11/16):")
    start_hour = input("Enter a start time to filter teams by (24h UTC time):")
    division = input("What division to you want to filter by (exact):")
    num_of_teams = int(input("How many teams are you looking for?"))
    # Makes initial request
    main_page = requests.get("http://scoreboard.uscyberpatriot.org/index.php?sort=Location")
    soup = BeautifulSoup(main_page.text, 'lxml')
    # Finds the first NJ team when sorting by location
    loc_index = locate_index(soup, loc)
    print(f"\n\nLocated {loc} Teams\n-------\n")
    # Creates a list of all location teams
    loc_teams = select_teams(loc_index, len(soup.select("tr")), soup, division, loc)
    print(f"Created {loc} team list\n-------\n")
    # Creates dictionary with the team and the first coordinate time data
    time_data = team_info(loc_teams)
    print("Pulled team specific information\n-------\n")
    # Refines list to teams with a certain date/time
    teams_match = check_team_data(time_data, date_filter, start_hour)
    end_result(teams_match, num_of_teams)


main()
