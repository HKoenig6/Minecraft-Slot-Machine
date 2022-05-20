# AUTHOR: Hans Koenig
# 
# This class contains several functions that
# analyze certain metrics of the machine:
#   -Collision Analysis (test_combinations)
#   -Payout Frequency Analysis (find_frequencies)
#   -Two types of simulations (using sql data):
#       -Static betting (run_simulator, optimize_profit)
#       -Dynamic betting (find_probabilities, maximize_profit)
#
# The data retrieved does not involve the special amethyst
# bonus payout as I had not implemented the functionality in
# minecraft before taking the screenshots. Therefore, amethyst
# payouts are not relevant in this code. The emphasis of these
# simulations can be broken down into three objectives:
#   -test the established offset values' performance regarding
#    how many unique states are reached in x spins assuming the
#    machine performs closely to random.
#   -find the desired payout values for each symbol so as to generate
#    a reasonable profit to the machine over time assuming a simple betting pattern
#   -expose the vulnerabilities of the machine by developing an algorithm
#    that bets dynamically and increases the profit to the player

import mysql.connector
import numpy as np
import random as r

# mysql connection
mydb = mysql.connector.connect(
    host='localhost',
    user='<user>',
    password='<password>'
)

# all possible state offsets per spin. I took advantage of
# prime offset behavior to theoretically minimize collisions.
offsets = [[5,7,12],[5,7,10],[5,12,13],[7,11,13]]

# input: number of spins the method will simulate
# output: number of spins to achieve all states OR
#         number of states achieved in all spins
#
# Simulates the slot machine I made in minecraft by
# representing each state in a 3d array and checking
# if every state has been reached after each spin. The
# console then displays relevant information regarding
# collisions. 
def test_combinations(numspins):
    # the starting indices can be arbitrary since the randomness
    # of a player's session is unaffected by previous states
    indices = [0,0,0]

    # each reel is 20 blocks long for a possible 20^3 = 8000 states
    states = [[[0 for i in range(20)] for j in range(20)] for k in range(20)]

    for n in range(numspins):
        randval = r.random()
        offsetindex = -1
        if randval > 0.5: # 7-11-13
            offsetindex = 3
        elif randval > 0.25: # 5-12-13
            offsetindex = 2
        elif randval > 0.125: # 5-7-12
            offsetindex = 0
        else: # 5-7-10
            offsetindex = 1
        for i in range(3):
            indices[i] = (indices[i] + offsets[offsetindex][i]) % 20
        states[indices[0]][indices[1]][indices[2]] = 1

        # check for termination
        done = 0
        for i in range(20):
            if done:
                break
            for j in range(20):
                if done:
                    break
                for k in range(20):
                    if not states[i][j][k]:
                        done = 1
                        break
        if not done: # all combinations have been reached
            print("ALL COMBINATIONS REACHED. TOOK " + str(n) + " SPINS.")
            return n

    # all spins exhausted without completion
    combinationsfound = 0
    # calculate total number of states achieved
    for i in states:
        for j in i:
            for k in j:
                if k:
                    combinationsfound = combinationsfound + 1
    print(str(combinationsfound) + " COMBINATIONS ACHIEVED IN " + str(numspins) + " SPINS.")
    return numspins

# input: mysql cursor, # of diamonds to bet
# output: dictionary of payout frequencies for all labels and lines w.r.t. betsize
#
# Collects frequency data from the mysql server by filtering each payout through a set
# of sql SELECT statements and incrementing each payout occurence accordingly.
def find_frequencies(dbcursor, betsize):
    dbcursor.execute('USE slots_data;')
    values = {'1':0, '2':0, '3':0, '4':0, '5':0, '6':0, '7':0, 'mid':0, 'top':0, 'bot':0, 'di1':0, 'di2':0}
    sqlfiles = ['clover.txt', 'mid.txt', 'top.txt', 'bot.txt', 'di1.txt', 'di2.txt']
    for payout in range(6):
        # terminate if not all payouts apply to spin of betsize
        if (betsize == 1 and payout > 1) or (betsize == 2 and payout > 3):
            break
        f = open('wins/' + sqlfiles[payout])
        dbcursor.execute(f.read())
        wins = dbcursor.fetchall()
        if payout == 0: # clover payout
            if betsize > 1:
                values['7'] = len(wins)
            continue
        else:
            key = sqlfiles[payout][0:3]
            values[key] = len(wins) 
        for spin in wins:
            for block in spin:
                if block != 0:
                    values[str(block)] = values[str(block)] + 1
                    break
    return values

# input: mysql cursor, dictionary of payout winning values
# output: profit over all bet sizes
#
# finds the profit of diamonds to the machine, assuming the player
# does not bet dynamically. No dictionary passed prompts
# interactive mode, where results are both printed and passed.
def run_simulator(dbcursor, winnings = {}):
    interactive = 0
    if len(winnings) == 0: # prompt the user for payout values
        interactive = 1
        print('ENTER PRIZE WINNINGS FOR EACH LABEL PAYOUT:')
        print('IRON:')
        winnings['1'] = input()
        print('RAW GOLD:')
        winnings['2'] = input()
        print('GOLD:')
        winnings['3'] = input()
        print('EMERALD:')
        winnings['4'] = input()
        print('DIAMOND:')
        winnings['5'] = input()
        print('NETHERITE:')
        winnings['6'] = input()
        print('CLOVER:')
        winnings['7'] = input()
    prizes = [0,0,0]
    for bet in range(3):
        profit = 1000 * (bet + 1)
        values = find_frequencies(dbcursor, bet + 1)
        for label in range(7):
            profit = profit - (int(winnings[str(label + 1)]) * values[str(label + 1)])
        if interactive:
            print(str(bet + 1) + ' DIAMOND BET RESULTS:')
            print('PROFIT: ' + str(profit))
            print()
        prizes[bet] = profit
    return prizes

# input: mysql cursor
# output: list of payout values that fall within the
# profit threshold
#
# iterate through all combinations in payouts and filter
# profits to fit between the ranges defined in threshold.
def optimize_profit(dbcursor):

    threshold = [[200,500],[500,900],[800,1300]]
    payouts = [[2,4,8],[4,8,12],[12,16,20],[32,48,64]]

    validentries = []
    for ival in payouts[0]:
        for rval in payouts[1]:
            for gval in payouts[2]:
                for dval in payouts[3]:
                    winnings = {'1': ival, '2': rval, '3': gval, '4': 0, '5': dval, '6': 0, '7': 0}
                    prizes = run_simulator(dbcursor, winnings)
                    inrange = 1
                    for bet in range(3):
                        if prizes[bet] < threshold[bet][0] or prizes[bet] > threshold[bet][1]:
                            inrange = 0
                            break
                    if inrange:
                        validentries.append(winnings)
    return validentries

# input: three blocks from the spin to compare
# output: the symbol of the payout present, else 0
#
# Helper function to make the same comparisons as
# find_frequencies. These comparisons have to be made
# for the adversary function since all future options need
# to be checked for their weights.
def compareline(x1, x2, x3):
    symbol = 0
    if (x1 == x2 and x2 == x3 or
        x1 == x2 and x3 == 0 or
        x2 == x3 and x1 == 0 or
        x1 == x3 and x2 == 0 or
        x1 == 0 and x2 == 0 and x3 != 0 or
        x2 == 0 and x3 == 0 and x1 != 0 or
        x1 == 0 and x3 == 0 and x2 != 0) and x1 != 7 and x2 != 7 and x3 != 7:
        if x1 != 0:
            symbol = x1
        elif x2 != 0:
            symbol = x2
        elif x3 != 0:
            symbol = x3
    return symbol

# this structure represents the order of symbols in
# each reel, using the same labels in the sql server.
# If the player spins at least 4 times, they have
# access to this information as well.
reels = [[4,1,2,3,0,1,1,3,2,4,5,1,1,2,1,7,7,3,6,2],
[2,3,1,1,0,1,2,5,4,7,7,2,3,6,2,1,7,7,3,4],
[2,4,1,3,1,0,2,6,3,1,4,1,7,7,2,1,3,2,5,1]]

# input: current spin in the dataset
# output: array of weighted profits w.r.t. betsize
#
# calculates the weighted profits of the current
# state of the machine when it is spun. The correct
# indices in reels have to be found, then each offset
# is applied and weights are incremented based on
# likelihood of the win occuring multiplied by its size.
def find_probabilities(spin):
    # holds the pointers to the values in reels
    indices = [-1,-1,-1]

    # find the correct indices in this spin as represented by
    # reels. 
    for reel in range(3):
        streak = 0
        # if the first block begins at the last or second to last index, the index
        # loops around with modulo
        for block in range(22):
            if spin[streak * 3 + reel] == reels[reel][block % 20]:
                streak = streak + 1
            else:
                if spin[streak * 3 + reel] == reels[reel][block % 20]:
                    streak = 1 
                else:
                    streak = 0
            if streak == 3: # index has been found
                indices[reel] = (block - 2) % 20
                break
    
    # these returned values are the heuristic model for
    # this attack on the machine. The player's next
    # decision will be based on the highest number of
    # the three, and will choose the leftmost value in
    # the case of one or more ties. Each index corresponds
    # to betsize.
    weightedprofits = [0,0,0]

    # these values were found from optimize_profit; I only changed
    # the payout of diamonds from 32 to 64.
    winnings = {'1': 2, '2': 8, '3': 20, '4': 0, '5': 64, '6': 0}

    # the theoretical probabilities of each offset being applied.
    # this array lines up with the offsets array near the top of
    # the class.
    weights = [0.125, 0.125, 0.25, 0.5]

    for offset in range(4):
        # apply the transformation
        newresult = [0,0,0]
        for index in range(3):
            newresult[index] = (indices[index] + offsets[offset][index]) % 20

        # establish variables for comparison
        b1 = reels[0][newresult[0]]
        b2 = reels[1][newresult[1]]
        b3 = reels[2][newresult[2]]
        b4 = reels[0][(newresult[0] + 1) % 20]
        b5 = reels[1][(newresult[1] + 1) % 20]
        b6 = reels[2][(newresult[2] + 1) % 20]
        b7 = reels[0][(newresult[0] + 2) % 20]
        b8 = reels[1][(newresult[1] + 2) % 20]
        b9 = reels[2][(newresult[2] + 2) % 20]

        # middle line
        symbol = compareline(b4, b5, b6)
        if symbol:
            for i in range(3):
                weightedprofits[i] = weightedprofits[i] + (weights[offset] * winnings[str(symbol)])

        # top line
        symbol = compareline(b1, b2, b3)
        if symbol:
            for i in range(2):
                weightedprofits[i+1] = weightedprofits[i+1] + (weights[offset] * winnings[str(symbol)])

        # bottom line
        symbol = compareline(b7, b8, b9)
        if symbol:
            for i in range(2):
                weightedprofits[i+1] = weightedprofits[i+1] + (weights[offset] * winnings[str(symbol)])

        # first diagonal
        symbol = compareline(b1, b5, b9)
        if symbol:
            weightedprofits[2] = weightedprofits[2] + (weights[offset] * winnings[str(symbol)])

        # second diagonal
        symbol = compareline(b7, b5, b3)
        if symbol:
            weightedprofits[2] = weightedprofits[2] + (weights[offset] * winnings[str(symbol)])

    return weightedprofits

# input: mysql cursor, initial state of machine
# output: dictionary of player profit and money saved
# compared to statically betting 3 diamonds a spin
#
# Uses find_probabilities on each spin in the
# dataset to make betting decisions based on the
# weights returned and outputs the relevant
# information.
def maximize_profit(dbcursor, initialspin):
    cost = 0
    # edge case: initial spin
    weights = find_probabilities(initialspin)
    if weights[1] == weights[2]:
        if weights[0] == weights[1]:
            cost = cost + 1
        else:
            cost = cost + 2
    else:
        cost = cost + 3

    # pull from all spins; the assumption that all spins in the dataset are
    # adjacent to one another is made and could potentially skew
    # the data.
    dbcursor.execute('USE slots_data;')
    dbcursor.execute('SELECT b1, b2, b3, b4, b5, b6, b7, b8, b9 FROM spins;')
    spins = dbcursor.fetchall()
    for spin in spins:
        weights = find_probabilities(spin)
        # uncomment this print statement to see all weights in the
        # dataset for each spin
        # print('SPIN ' + str(spin) + ': ' + str(weights))

        # if the weight does not increase upon increasing
        # the bet size, the player saves money by betting
        # the lowest size since nothing is gained from betting
        # higher.
        if weights[1] == weights[2]:
            if weights[0] == weights[1]:
                cost = cost + 1
            else:
                cost = cost + 2
        else:
            cost = cost + 3

    # return the profit of the user; prizes represents the machine
    # profit so it must be negated. Since this heuristic will reach
    # all payouts available in the dataset, I took a shortcut and pulled from
    # runsimulator, then added the cost of betting 3 diamonds 1000
    # times and subtracting what the player spent in this function.
    prizes = run_simulator(dbcursor, {'1': 2, '2': 8, '3': 20, '4': 0, '5': 64, '6': 0, '7': 0})
    diff = 3000 - cost
    return {'profit': -prizes[2] + diff, 'savings': diff} 
    

# main driver; I used this interchangeably with the
# interpreter for debugging
if __name__ == '__main__':
    validentries = optimize_profit(mydb.cursor())
    prizes = []
    for entry in validentries:
        prizes.append(run_simulator(mydb.cursor(), entry))
        print(entry)
    print(prizes)