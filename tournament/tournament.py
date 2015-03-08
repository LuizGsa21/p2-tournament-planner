#!/usr/bin/env python
# 
# tournament.py -- implementation of a Swiss-system tournament
#

import psycopg2


def connect():
    """Connect to the PostgreSQL database.  Returns a database connection."""
    return psycopg2.connect("dbname=tournament")


def startNewTournament(name):
    db = connect()
    cursor = db.cursor()
    cursor.execute('INSERT INTO tournaments (name) VALUES (%s)', (name,))
    db.commit()
    db.close()
    return getCurrentTournamentId()


def getCurrentTournamentId():
    db = connect()
    cursor = db.cursor()
    cursor.execute('SELECT id FROM tournaments ORDER BY id DESC LIMIT 1')
    id = cursor.fetchone()
    if id is None:
        raise ValueError('No tournament was found in the database.')
    db.close()
    return id


def deleteMatches():
    """Remove all the match records from the database."""
    db = connect()
    cursor = db.cursor()
    cursor.execute('DELETE FROM matches')
    db.commit()
    db.close()


def deletePlayers():
    """Remove all the player records from the database."""
    db = connect()
    cursor = db.cursor()
    cursor.execute('DELETE FROM players')
    db.commit()
    db.close()


def countPlayers():
    """Returns the number of players currently registered."""
    tournament = getCurrentTournamentId()
    db = connect()
    cursor = db.cursor()
    cursor.execute('SELECT count(id) AS total_players FROM players WHERE tournament = %s', (tournament,))
    count = cursor.fetchone()[0]
    db.close()
    return count


def registerPlayer(name):
    """Adds a player to the tournament database.
  
    The database assigns a unique serial id number for the player.  (This
    should be handled by your SQL database schema, not in your Python code.)
  
    Args:
      name: the player's full name (need not be unique).
    """
    tournament = getCurrentTournamentId()

    db = connect()
    cursor = db.cursor()
    cursor.execute('INSERT INTO players (name, tournament) VALUES (%s, %s)', (name, tournament))
    db.commit()
    db.close()


def playerStandings():
    """Returns a list of the players and their win records, sorted by wins.

    The first entry in the list should be the player in first place, or a player
    tied for first place if there is currently a tie.

    Returns:
      A list of tuples, each of which contains (id, name, wins, matches):
        id: the player's unique id (assigned by the database)
        name: the player's full name (as registered)
        wins: the number of matches the player has won
        matches: the number of matches the player has played
    """
    db = connect()
    cursor = db.cursor()
    cursor.execute('SELECT player_id, player_name, wins, total_matches FROM standings ORDER BY wins DESC')
    standings = cursor.fetchall()
    db.close()
    return standings


def reportMatch(player1, player2, isDraw=False):
    """Records the outcome of a single match between two players.

    Args:
      winner:  the id number of the player who won
      loser:  the id number of the player who lost
    """
    tournament = getCurrentTournamentId()

    if isDraw:
        winner = None
    else:
        winner = player1

    db = connect()
    cursor = db.cursor()
    cursor.execute('INSERT INTO matches (tournament, winner, player1, player2) VALUES (%s, %s, %s, %s)',
                   (tournament, winner, player1, player2))
    db.commit()
    db.close()


def insertByePlayer(standings):
    tournament = getCurrentTournamentId()
    db = connect()
    cursor = db.cursor()
    cursor.execute("""SELECT player_id FROM standings WHERE tournament = %s AND player_id NOT IN
                       (SELECT player1 FROM matches WHERE tournament = %s AND player2 IS NULL)
                        ORDER BY wins LIMIT 1""", (tournament, tournament))
    byePlayer = cursor.fetchone()[0]
    db.close()
    for i, player in reversed(list(enumerate(standings))):
        if byePlayer == player[0]:
            standings.remove(i)
            standings.append(player)
            standings.append((None, None))
            break


def swissPairings():
    """Returns a list of pairs of players for the next round of a match.
  
    Assuming that there are an even number of players registered, each player
    appears exactly once in the pairings.  Each player is paired with another
    player with an equal or nearly-equal win record, that is, a player adjacent
    to him or her in the standings.
  
    Returns:
      A list of tuples, each of which contains (id1, name1, id2, name2)
        id1: the first player's unique id
        name1: the first player's name
        id2: the second player's unique id
        name2: the second player's name
    """
    standings = playerStandings()
    playerCount = countPlayers()
    if playerCount % 2 == 1:
        insertByePlayer(standings)
    return [(p1[0], p1[1], p2[0], p2[1]) for p1, p2 in zip(standings[::2], standings[1::2])]

