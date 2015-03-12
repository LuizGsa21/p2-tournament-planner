# p2-tournament-planner
This Python module uses PostgreSQL database to keep track of players and matches in a game tournament.

## Overview
The game tournament uses Swiss system for pairing up players in each round: players are not eliminated, and each player should be paired with another player with the same number of wins, or as close as possible.

##Prerequisites
- [VirtualBox](https://www.virtualbox.org/wiki/Downloads)
- [Vagrant](http://www.vagrantup.com/downloads.html)

# Instructions
```sh
# Clone this repo and navigate to project folder
$ git clone https://github.com/LuizGsa21/p2-tournament-planner
$ cd p2-tournament-planner/

# Start up vagrant and wait for it to install any dependencies
$ vagrant up
# SSH into virtual machine
$ vagrant ssh

# Setup PostgreSQL
$ cd /vagrant/tournament
$ createdb tournament
$ psql tournament
tournament=> \i tournament.sql
tournament=> \q
```
And you're done! You can run the tests from the command line:
```sh
# Go to working your directory
$ cd /vagrant/tournament
# Run tests
$ python tournament_test.py
```