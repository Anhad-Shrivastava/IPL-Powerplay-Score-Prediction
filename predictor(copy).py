### Custom definitions and classes if any ###
import pandas as pd
import os

#global variables
bat_list,bowl_list=[],[]
data,batsman_data,bowler_data="","",""
batsmen,bowlers = dict(),dict()
bowling_order=[]
data,batsman_data,bowler_data="","",""

def predictRuns(testInput):
    data = pd.read_csv(testInput)
    batsman_data = pd.read_csv("batsman_data.csv", header=0)
    bowler_data = pd.read_csv("bowler_data.csv", header=0)

    batsmen, bowlers, batsmen1, bowlers1 = dict(), dict(), dict(), dict()

    for row in range(0, batsman_data.index[-1]):
        player_name1 = batsman_data.at[row, 'Player_Name']
        player_name = player_name1[0:1] + " " + player_name1[len(player_name1) - 4: len(player_name1) + 1]
        batsmen.update({player_name: player_name1})
        batsmen1.update({player_name1: row})
    for row in range(0, bowler_data.index[-1]):
        player_name1 = bowler_data.at[row, 'Player_Name']
        player_name = player_name1[0:1] + " " + player_name1[len(player_name1) - 4: len(player_name1) + 1]
        bowlers.update({player_name: player_name1})
        bowlers1.update({player_name1: row})

    venue = data.iloc[rowx, 0]
    innings = data.iloc[rowx, 1]
    batting_team = data.iloc[rowx, 2]
    bowling_team = data.iloc[rowx, 3]
    bat_list = list(map(str, data.iloc[rowx, 4].split(",")))
    bowl_list = list(map(str, data.iloc[rowx, 5].split(",")))
    bowling_order=get_bowling_order(bowl_list)

    # predict score by batsman performance
    batsman_model = s_bat(bat_list[0], bat_list[1], 0)
    # predict score by bowler performance
    bowler_model = t_bowl(0, 0, len(bat_list))

    slope=0.80159279
    intercept=12.852516574175887
    prediction = slope*batsman_model + intercept

    return prediction


# create a list of bowlers bowl[0-5] from bowl_list[] based on bowling pattern of the team
def get_bowling_order(bowl_list):
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

def get_batsman_value(b,col):
    b=b.strip()
    player_name = b[0:1] +" "+ b[len(b)-4 : len(b)+1]
    player_name1= batsmen.get(player_name)
    row=batsmen1.get(player_name1)
    try:
        data=batsman_data.at[row,col]
    except KeyError:
        data=0
    return data

def get_bowler_value(b,col):
    b=b.strip()
    player_name = b[0:1] +" "+ b[len(b)-4 : len(b)+1]
    player_name1= bowlers.get(player_name)
    row=bowlers1.get(player_name1)
    try:
        data= bowler_data.at[row,col]
    except KeyError:
        data=0
    return data


# functions for batting calculations
def p_bat(b, k):
    col = "p" + str(k + 1)
    prob = get_batsman_value(b, col)
    if prob == 0 or prob == None:
        col = 'wicket_probability'
        prob = get_batsman_value(b, col)
    if prob == 0 or prob == None:
        prob = batsman_data.at[0, 'average_wicket_probability']
    return prob


def r_bat(b, n):
    col = "r" + str(n + 1)
    score = get_batsman_value(b, col)
    if score == 0 or score == None:
        col = 'strike_rate'
        score = get_batsman_value(b, col)
    if score == 0:
        score = batsman_data.at[0, 'average_strike_rate']
    return score


def s_bat(bx, by, o):
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


# functions for bowling calculations
def p_bowl(b, n):
    col = "p" + str(n + 1)
    prob = get_bowler_value(b, col)
    if prob == 0 or prob == None:
        col = 'wicket_rate'
        prob = get_bowler_value(b, col)
    if prob == 0:
        prob = bowler_data.at[0, 'average_wicket_rate']
    if n == 1:
        return prob
    if n == 2:
        return prob * prob * 5 / 6
    if n == 0:
        return (1 - prob * (1 + prob * 5 / 6))


def c_bowl(b, n, w):
    col = "r(" + str(n + 1) + str(w) + ")"
    val = get_bowler_value(b, col)
    # if val is 0, we need to return the general economy of the bowler
    if val == 0 or val == None:
        col = 'economy'
        val = get_bowler_value(b, col)
    if val == 0:
        val = bowler_data.at[0, 'average_economy']
    return val


def t_bowl(n, w, total):  # runs conceded starting from 0th over to 5th over (0-5) range
    # total is the total number of batsmen
    if n < 6 and w <= total - 2:

        t0 = t_bowl(n + 1, w, total)
        t1 = t_bowl(n + 1, w + 1, total)
        t2 = t_bowl(n + 1, w + 2, total)

        p0 = p_bowl(bowling_order[n], 0)
        p1 = p_bowl(bowling_order[n], 1)
        p2 = p_bowl(bowling_order[n], 2)

        c = c_bowl(bowling_order[n], n, w)

        if total - w >= 4:
            score = c + p0 * t0 + p1 * t1 + p2 * t2
        elif total - w == 3:
            score = c + (p0 + p2) * t0 + p1 * t1
        else:
            score = c + t0
        return score
    else:
        return 0

