### Custom definitions and classes if any ###
import pandas as pd
import os
import numpy as np

#global variables
bat_list=[]
batsmen, bowlers= dict(), dict()
batsman_data,bowler_data,data="","",""

def predictRuns(testInput):
    global bat_list,batsmen,bowlers,batsman_data,bowler_data,data

    data = pd.read_csv(testInput)
    batsman_data = pd.read_csv("batsman_data.csv", header=0)
    bowler_data=pd.read_csv("bowler_data.csv",header=0)
    stadium_data=pd.read_csv("stadium_data.csv",header=0)
    testdata = pd.read_csv('test_data.csv')

    for row in range(0, batsman_data.index[-1]):
        player_name1 = batsman_data.at[row, 'Player_Name']
        player_name = player_name1[0:1] + " " + player_name1[len(player_name1) - 4: len(player_name1) + 1]
        batsmen.update({player_name: row})

    for row in range(0, bowler_data.index[-1]):
        player_name1 = bowler_data.at[row, 'Player_Name']
        player_name = player_name1[0:1] + " " + player_name1[len(player_name1) - 4: len(player_name1) + 1]
        bowlers.update({player_name: row})

    venue = data.iloc[0, 0]
    innings = data.iloc[0, 1]
    batting_team = data.iloc[0, 2]
    bowling_team = data.iloc[0, 3]
    bat_list = list(map(str, data.iloc[0, 4].split(",")))
    bowl_list = list(map(str, data.iloc[0, 5].split(",")))

    bowling_order=get_bowling_order(bowl_list)

    stadiums = dict()

    for row in range(0, stadium_data.index[-1]):
        stadium = stadium_data.at[row, 'stadium_name']
        stadiums.update({stadium: row})

    # predict score by bowler and wicket loss performance
    batsman_model = s_bat(bat_list[0], bat_list[1], 0)
    bowler_model= bowling_prediction(bowling_order)

    wickets= len(bat_list)-2
    prediction = 0.37091807*bowler_model - 3.83388431*wickets + 33.87871819102332

    return int(prediction)

def get_batsman_value(b,col):
    global bat_list,bowl_list,batsmen,bowlers,batsman_data,bowler_data,data

    b=b.strip()
    player_name = b[0:1] +" "+ b[len(b)-4 : len(b)+1]
    row= batsmen.get(player_name)
    try:
        data=batsman_data.at[row,col]
    except KeyError:
        data=0
    return data

def get_bowler_value(b,col):
    global bat_list, batsmen, bowlers, batsman_data, bowler_data, data

    b=b.strip()
    player_name = b[0:1] +" "+ b[len(b)-4 : len(b)+1]

    row= bowlers.get(player_name)
    try:
        data= bowler_data.at[row,col]
    except KeyError:
        data=0
    return data

# functions for batting calculations
def p_bat(b, k):
    global bat_list,batsmen,bowlers,batsman_data,bowler_data,data

    col = "p" + str(k + 1)
    prob = get_batsman_value(b, col)
    if prob == 0 or prob == None:
        col = 'wicket_probability'
        prob = get_batsman_value(b, col)
    if prob == 0 or prob == None:
        prob = batsman_data.at[0, 'average_wicket_probability']
    return prob


def r_bat(b, n):
    global bat_list,batsmen,bowlers,batsman_data,bowler_data,data

    col = "r" + str(n + 1)
    score = get_batsman_value(b, col)
    if score == 0 or score == None:
        col = 'strike_rate'
        score = get_batsman_value(b, col)
    if score == 0:
        score = batsman_data.at[0, 'average_strike_rate']
    return score

def s_bat(bx, by, o):
    global bat_list,batsmen,bowlers,batsman_data,bowler_data,data

    if o < 6 and bx in bat_list and by in bat_list:
        # figure out next and later batsmen
        idx = max(bat_list.index(bx), bat_list.index(by))
        if idx + 1 < len(bat_list):
            nxt = bat_list[idx + 1]
        else:
            nxt = "gen"
            later = "gen"
        if idx + 2 < len(bat_list):
            later = bat_list[idx + 2]
        else:
            later = "gen"

        a = 0.5
        px = s_bat(by, nxt, o + 1) + a * r_bat(bx, o) + r_bat(by, o)
        py = s_bat(bx, nxt, o + 1) + r_bat(bx, o) + a * r_bat(by, o)
        pxy = s_bat(nxt, later, o + 1) + a * (r_bat(bx, o) + r_bat(by, o))
        p0 = s_bat(bx, by, o + 1) + r_bat(bx, o) + r_bat(by, o)
        # if none can get out, we will not find any more probabilities
        if nxt == "gen":
            return p0
        # if one more can get out then we calculate the probability accordingly
        elif later == "gen":
            return p_bat(bx, o) * px + p_bat(by, o) * py + (1 - p_bat(bx, o) - p_bat(by, o)) * p0
        # if more than one can get out then also we calculate the probability accordingly
        else:
            return p_bat(bx, o) * px + p_bat(by, o) * py + p_bat(bx, o) * p_bat(by, o) * pxy + (
                        1 - p_bat(bx, o) - p_bat(by, o) - p_bat(bx, o) * p_bat(by, o)) * p0
    else:
        return 0

def bowling_prediction(bowling_order):
    global bat_list, batsmen, bowlers, batsman_data, bowler_data, data

    score=0
    wickets=0
    for player in bowling_order:
        #get score
        s=get_bowler_value(player,'pp_economy')
        if s==0:
            s=bowler_data.at[0,'avg_pp_econ']
        score+=s
        #get wickets
        w=get_bowler_value(player,'wicket_economy')
        if w==0:
            w=bowler_data.at[0,'avg_pp_wicket']
        wickets+=w
    return score

def get_bowling_order(bowl_list):
    # create a list of bowlers bowl[0-5] from bowl_list[] based on bowling pattern of the team
    global bat_list, batsmen, bowlers, batsman_data, bowler_data, data

    bowling_order=[]
    if len(bowl_list) == 2:
        for i in range(0, 6):
            bowling_order.append(bowl_list[i % 2])
    # for bowler length 3 and 4
    # add team dependent bowling strategy
    elif len(bowl_list) == 3:
        bowling_order = (bowl_list[0], bowl_list[1], bowl_list[0], bowl_list[1], bowl_list[0], bowl_list[2])
    elif len(bowl_list) == 4:
        bowling_order = (bowl_list[0], bowl_list[1], bowl_list[0], bowl_list[1], bowl_list[2], bowl_list[3])
    elif len(bowl_list) == 5:
        bowling_order = (bowl_list[0], bowl_list[1], bowl_list[0], bowl_list[2], bowl_list[3], bowl_list[4])
    elif len(bowl_list) == 6:
        bowling_order = bowl_list
    return bowling_order