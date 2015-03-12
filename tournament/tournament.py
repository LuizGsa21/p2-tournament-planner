#!/usr/bin/env python
# 
# tournament.py -- implementation of a Swiss-system tournament
#
import psycopg2


def connect():
    """Connect to the PostgreSQL database.  Returns a database connection."""
    return psycopg2.connect("dbname=tournament")


def startNewTournament(name):
    """Starts a new tournament with the given name. Returns the tournament's unique id.
    Parameters:
     name: Tournament name
    Returns:
        int - Tournament's unique id
    """
    db = connect()
    cursor = db.cursor()
    cursor.execute('INSERT INTO tournaments (name) VALUES (%s)', (name,))
    db.commit()
    db.close()
    return getCurrentTournamentId()


def getCurrentTournamentId():
    """Returns the current tournament's unique id.
    Throws a ValueError exception when no tournament is found.

    Returns:
      int - Tournament's unique id
    """
    db = connect()
    cursor = db.cursor()
    cursor.execute('SELECT id FROM tournaments ORDER BY id DESC LIMIT 1')
    id = cursor.fetchone()
    if id is None:
        raise ValueError('No tournament was found in the database.')
    db.close()
    return id[0]


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


def playerStandings(allTournaments=False):
    """Returns a list of the players and their win records, sorted by wins
    for the current tournament.

    The first entry in the list should be the player in first place, or a player
    tied for first place if there is currently a tie.

    Parameters:
     allTournaments:
        boolean Default = False
            Set to True to receive player standings for all tournaments
    Returns:
      A list of tuples, each of which contains (id, name, wins, matches):
        id: the player's unique id (assigned by the database)
        name: the player's full name (as registered)
        wins: the number of matches the player has won
        matches: the number of matches the player has played
    """

    db = connect()
    cursor = db.cursor()
    if allTournaments:
        cursor.execute("""SELECT player_id, player_name, wins, total_matches
                          FROM standings""")
    else:
        tournament = getCurrentTournamentId()
        cursor.execute("""SELECT player_id, player_name, wins, total_matches
                          FROM standings
                          WHERE tournament = %s""", (tournament,))
    standings = cursor.fetchall()
    db.close()
    return standings


def reportMatch(player1, player2, isDraw=False):
    """Records the outcome of a single match between two players.

    - No match is not reported when both players are null.

    Args:
      player1: wins by default (player id) type int
      player2: wins only when player1 is null. (player id) type int
      isDraw: set this to True for draw matches.
              Both players must be non-null for a draw to be reported,
              otherwise a win is given to the non-null player.
    Returns:
      Boolean: True when match is reported, false otherwise.
    """
    if player1 is None:
        if player2 is None:
            return False
        else:
            winner = player2
    elif player2 is None or not isDraw:
        winner = player1
    else:
        winner = None

    tournament = getCurrentTournamentId()

    db = connect()
    cursor = db.cursor()
    cursor.execute('INSERT INTO matches (tournament, winner, player1, player2) VALUES (%s, %s, %s, %s)',
                   (tournament, winner, player1, player2))
    db.commit()
    db.close()
    return True


def insertOddPlayer(standings):
    """Shifts the next possible bye player to the bottom of the standings list,
       then appends (None, None, None, None) to represent a bye player.

       Throws a ValueError exception when all players have already been given a bye.

       Note:
        The standings list must be update-to-date with playerStandings(). If the player
        positions where modified, then the wrong player will be given a bye.

    Args:
        standings: an up-to-date list from playerStandings()
    """

    tournament = getCurrentTournamentId()
    db = connect()
    cursor = db.cursor()
    # retrieve the index for the next bye player
    cursor.execute("""
    WITH rankings AS (
            SELECT row_number() OVER () AS row, * FROM standings WHERE tournament = %s),
         next_bye AS (
            SELECT * FROM rankings WHERE player_id NOT IN
                  (SELECT player1 FROM matches WHERE tournament = %s AND player2 is NULL) ORDER BY wins LIMIT 1)

         SELECT r.row - 1 FROM rankings as r, next_bye WHERE r.player_id = next_bye.player_id""",
                   (tournament, tournament))
    index = cursor.fetchone()
    db.close()
    if index is None:
        raise ValueError('No possible bye player found.')
    else:
        standings.append(standings.pop(index[0]))
        standings.append((None, None, None, None))


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

    if countPlayers() % 2 == 1:
        insertOddPlayer(standings)

    return [(p1[0], p1[1], p2[0], p2[1]) for p1, p2 in zip(standings[::2], standings[1::2])]

