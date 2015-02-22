#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#=============#
#   imports   #
#=============#
import curses
#import locale
import math #for calculating jackpot portions
import random #for randomizing stuff
import time #for pausing/sleeping
from collections import deque #for queues

#===============#
#   constants   #
#===============#
DEBUG_SPIN = False
NUMBER_OF_ICONS_PER_REEL = 13
NUMBER_OF_REELS = 3
NUMBER_OF_ROWS = 3
REEL_STOPS_ACTUAL = 22
REEL_STOPS_VIRTUAL = 64

#=============#
#   globals   #
#=============#
screen = None


#====================#
#   custom classes   #
#====================#
class BaseIcon(object):
	def __init__(self,weight=None,displayChar=None):
		""" Constructor """
		
		self.weight = weight
		self.displayChar = displayChar
	
	def __str__(self):
		""" toString method """
		
		return self.displayChar
	
	def __repr__(self):
		""" toString method alternative """
		
		return self.__str__()

class BlankIcon(BaseIcon):
	def __init__(self,weight=0,displayChar='☒'):
		""" Constructor """
		
		#call the super class's constructor
		super(self.__class__,self).__init__(weight,displayChar)

class JackpotIcon(BaseIcon):
	def __init__(self,weight=1,displayChar='✔'):
		""" Constructor """
		
		#call the super class's constructor
		super(self.__class__,self).__init__(weight,displayChar)
	
	@staticmethod
	def matches(icon):
		""" Class method to check type """
		try:
			doesItMatch = (icon.weight == 1)
		except:
			doesItMatch = False
		return doesItMatch

class Reel(object):
	""" A reel of a slot machine - Either actual or virtual """
	
	#--------------------#
	#   Initialization   #
	#--------------------#
	def __init__(self,numberOfStops):
		""" Constructor """
		
		self.stops = deque()
		for i in range(numberOfStops):
			self.stops.append(None)
	
	#---------------#
	#   Accessors   #
	#---------------#
	def __str__(self):
		""" toString method """
		
		return "\n\tReel: %s" % (self.stops)
	
	def __repr__(self):
		""" toString method alternative """
		
		return self.__str__()
	
	def __getitem__(self,index):
		""" Returns the icon at a specific index """
		
		return self.stops[index]
	
	def __len__(self):
		""" Returns the length of the reel """
		
		return len(self.stops)
	
	#--------------#
	#   Mutators   #
	#--------------#
	def __setitem__(self,index,icon):
		""" Sets a stop on the reel to a certain icon """
		
		self.stops[index] = icon
	
	def loadActualReelLoad(self,icons):
		""" Loads the reel full of icons """
		
		self.stops = icons
	
	def loadVirtualReelMap(self,reelMap):
		""" Loads the reel full of virtual to actual reel mappings """
		
		self.stops = reelMap
	
	def rotateStop(self):
		""" Rotates the reel by 1 stop """
		
		raise NotImplemented("ERROR: This has been deprecated")
		
		#put the last icon at the front
		try:
			holdIcon = self.stops.pop()
		except IndexError as e:
			raise RuntimeError("ERROR: Cannot rotate stop.  Reel is empty")
		self.stops.appendleft(holdIcon)

class StopAddress(object):
	""" A 2 dimensional reel stop address """
	
	def __init__(self,x=None,y=None):
		""" constructor """
		self.coordinate = [x,y]
	
	def __getitem__(self,index):
		return self.coordinate[i]
	def getColumn(self):
		return self.coordinate[0]
	def getRow(self):
		return self.coordinate[1]

class PayLine(object):
	""" List of 2 dimensional stop addresses that determine wins """
	
	def __init__(self,coordinates=[]):
		""" constructor """
		
		self.stopAddresses = coordinates
	
	#---------------#
	#   Utilities   #
	#---------------#
	
	def checkReelsForWin(self,reels):
		""" Checks the stop addresses against the reels to see if pay line is a winner """
		
		paylineIcons = []
		
		#get the icons at the coordinates
		for coordinate in self.stopAddresses:
			col = coordinate.getColumn()
			row = coordinate.getRow()
			icon = reels[col][row]
			paylineIcons.append(icon)
		
		#check icons for winning combinations
		return self.isWinningCombination(paylineIcons)
	
	def isWinningCombination(self,paylineIcons):
		""" Checks the payline for a winning combination """
		
		#default to True
		isAWin = True
		
		#check each icon for a match
		for icon in paylineIcons:
			isAWin = isAWin and JackpotIcon.matches(icon)
		
		#tell it how it is
		return isAWin

class SlotMachine(object):
	""" A slot machine """
	
	#--------------------#
	#   Initialization   #
	#--------------------#
	def __init__(self):
		""" Constructor """
		
		#instantiate object attributes
		self.actualReels = []
		self.virtualReels = []
		self.paylines = []
		self.centerLineReelIndices = []
		self.stopsInView = []
		self.balance = 0
		
		#initialize reels
		self.initializeActualReels()
		self.initializeVirtualReels()
		self.initializeStopsInView()
		
		#initialize pay lines
		self.initializePayLines()
	
	def initializeActualReels(self):
		""" Sets up the actual reels """
		
		#determine the center lines for the display
		middleIndices = int(REEL_STOPS_ACTUAL / 2)
		
		#create reels
		for i in range(NUMBER_OF_REELS):
			#create a new actual reel
			actualReel = Reel(REEL_STOPS_ACTUAL)
			
			#load actual reel with icons
			reelLoad = self.getRandomActualReelLoad()
			actualReel.loadActualReelLoad(reelLoad)
			
			#add reel to slot machine
			self.actualReels.append(actualReel)
			
			#default the center line display index for this reel
			self.centerLineReelIndices.append(middleIndices)
	
	def initializeVirtualReels(self):
		""" Sets up the virtual reels """
		
		for reelIndex in range(NUMBER_OF_REELS):
			#create a new virtual reel
			virtualReel = Reel(REEL_STOPS_VIRTUAL)
			
			#load virtual reel with a mapping to actual reel
			virtualToActualReelMap = self.getRandomReelMap(reelIndex)
			virtualReel.loadVirtualReelMap(virtualToActualReelMap)
			
			#add reel to slot machine
			self.virtualReels.append(virtualReel)
	
	def initializeStopsInView(self):
		""" sets up the dummy reels to display the stops that can be seen """
		
		#set up reel-like objects
		for i in range(NUMBER_OF_REELS):
			emptyReel = Reel(NUMBER_OF_ROWS)
			self.stopsInView.append(emptyReel)
		
		#refresh the display with the stops in view
		self.refreshDisplay()
	
	def initializePayLines(self):
		""" Sets up the valid pay lines """
		
		#standard pay lines
		row1 = PayLine([StopAddress(0,0),StopAddress(1,0),StopAddress(2,0)])
		self.paylines.append(row1)
		
		row2 = PayLine([StopAddress(0,1),StopAddress(1,1),StopAddress(2,1)])
		self.paylines.append(row2)
		
		row3 = PayLine([StopAddress(0,2),StopAddress(1,2),StopAddress(2,2)])
		self.paylines.append(row3)
	
	#---------------#
	#   Utilities   #
	#---------------#
	def getRandomActualReelLoad(self):
		""" Returns a list of random icons to load into an actual reel """
		
		#container for load
		reelLoad = deque()
		
		#determine amount of blank icons
		numberOfBlankIcons = REEL_STOPS_ACTUAL - NUMBER_OF_ICONS_PER_REEL
		if(numberOfBlankIcons < 0):
			raise ValueError("ERROR: There are more icons than stops")
		
		#load in jackpot icons
		for i in range(NUMBER_OF_ICONS_PER_REEL):
			#jackpotIcon = JackpotIcon(displayChar='')
			jackpotIcon = JackpotIcon()
			reelLoad.append(jackpotIcon)
		
		#load in blank icons
		for i in range(numberOfBlankIcons):
			blankIcon = BlankIcon()
			reelLoad.append(blankIcon)
		
		#shuffle the load
		random.shuffle(reelLoad)
		
		#give it away
		return reelLoad
	
	def getRandomReelMap(self,reelIndex):
		""" Returns a random mapping from virtual reel stops to actual reel stops """
		
		#get the actual reel that will be mapped to
		actualReel = self.actualReels[reelIndex]
		reelMap = deque()
		
		#link to the jackpot icons once
		stopIndex = 0
		for actualStop in actualReel:
			if JackpotIcon.matches(actualStop):
				reelMap.append(stopIndex)
			stopIndex += 1
		
		#link to the adjacent blank icons twice
		stopIndex = 0
		adjacentBlankIndices = []
		nonAdjacentBlankIndices = []
		for actualStop in actualReel:
			previousIndex = stopIndex-1
			nextIndex = (stopIndex+1) % REEL_STOPS_ACTUAL
			prevJackpotIcon = JackpotIcon.matches(actualReel[previousIndex])
			nextJackpotIcon = JackpotIcon.matches(actualReel[nextIndex])
			currJackpotIcon = JackpotIcon.matches(actualStop)
			#check for current jackpot
			if(not currJackpotIcon):
				#check for adjacency
				if(prevJackpotIcon or nextJackpotIcon):
					#check to see if virtual reel is already full and add if not
					if(len(reelMap) < REEL_STOPS_VIRTUAL):
						#add this stop
						reelMap.append(stopIndex)
					#check to see if virtual reel is already full and add again if not
					if(len(reelMap) < REEL_STOPS_VIRTUAL):
						#add this stop
						reelMap.append(stopIndex)
					adjacentBlankIndices.append(stopIndex)
				else:
					nonAdjacentBlankIndices.append(stopIndex)
			else:
				pass #skip the jackpot icons
			stopIndex += 1
		
		#fill remainder of reel map with filler icons
		nextIndex = 0
		if(nonAdjacentBlankIndices):
			filler = nonAdjacentBlankIndices
		else:
			filler = adjacentBlankIndices
		for emptyVirtualStopIndex in range(len(reelMap),REEL_STOPS_VIRTUAL):
			try:
				#get the index of the next non-adjacent blank stop index
				stopIndex = nextIndex % len(filler)
				#get the non-adjacent blank stop index
				stop = filler[stopIndex]
				#add the nonAdjacent stop index to the reel map
				reelMap.append(stop)
				#increment the next index
				nextIndex += 1
			except:
				import pdb; pdb.set_trace()
		
		return reelMap
	
	#---------------#
	#   Accessors   #
	#---------------#
	def __str__(self):
		""" toString method """
		
		#build the display
		display = ""
		for row in range(NUMBER_OF_ROWS):
			display += '\n'
			for displayReel in self.stopsInView:
				display += "\t%s" % (displayReel[row])
			display += "\n"
		display += "Progressive Jackpot: %d credits\n" % (self.balance)
		
		return display
	
	def __repr__(self):
		""" toString method alternative """
		
		return self.__str__()
	
	def getBalance(self):
		""" Returns the current progressive jackpot balance """
		
		return self.balance
	
	#==============#
	#   Mutators   #
	#==============#
	def payout(self,numberOfWins,betAmount):
		""" pays out based on bet amount and number of wins """
		
		#determine how the jackpot should be divided
		portionOfJackpotPerBet = math.floor(self.balance / betAmount)
		
		#determine how much of the jackpot the user won
		portionWon = portionOfJackpotPerBet * numberOfWins
		
		#remove winnings from machine jackpot balance
		self.balance -= portionWon
		
		return portionWon
	
	def placeBet(self,bet):
		""" places a bet """
		self.balance += bet
	
	def spin(self):
		""" Spins the slot machine reels """
		
		#spin the reels
		if(DEBUG_SPIN):
			#move the reels one place
			for reelIndex in range(NUMBER_OF_REELS):
				self.centerLineReelIndices[reelIndex] = (self.centerLineReelIndices[reelIndex] + 1) % REEL_STOPS_ACTUAL #wraps around list
		else:
			#spin the reels for reals
			for reelIndex in range(NUMBER_OF_REELS):
				#get the virtual reel
				virtualReel = self.virtualReels[reelIndex]
				
				#get a random virtual stop
				virtualStop = random.choice(virtualReel)
				
				#set the centerline to the location that the virtual stop maps to
				self.centerLineReelIndices[reelIndex] = virtualStop
		
		#refresh the display to reflect spin
		self.refreshDisplay()
		
		#check wins
		wins = 0
		for payline in self.paylines:
			if(payline.checkReelsForWin(self.stopsInView)):
				wins += 1
		
		return wins
	
	def refreshDisplay(self):
		""" refreshes the display of stops that are able to be seen """
		
		#get the indices of the stops that are in view at the top
		stopIndices = []
		numberOfStopsShownAboveCenter = (NUMBER_OF_ROWS - 1) / 2 #removing the center line row, and dividing in half
		for centerLineIndex in self.centerLineReelIndices:
			topStopIndex = int((centerLineIndex - numberOfStopsShownAboveCenter) % REEL_STOPS_ACTUAL) #wraps around list
			stopIndices.append(topStopIndex)
		
		#build the display reels
		display = ""
		for row in range(NUMBER_OF_ROWS):
			for reelIndex in range(NUMBER_OF_REELS):
				#get the actual reel
				actualReel = self.actualReels[reelIndex]
				
				#get the next stop index for this reel
				stopIndex = stopIndices[reelIndex]
				
				#get the stop based on the index
				stop = actualReel[stopIndex]
				
				#set the display reel accordingly
				displayReel = self.stopsInView[reelIndex]
				displayReel[row] = stop
				
				#increment the next stop index
				stopIndices[reelIndex] = (stopIndices[reelIndex] + 1) % REEL_STOPS_ACTUAL #wraps around list

class Screen(object):
	""" Custom extension of curses screen """
	
	#--------------------#
	#   Initialization   #
	#--------------------#
	def __init__(self,cursesScreen):
		#save the default screen
		self.screen = cursesScreen
		
		#default customizations
		curses.echo()
		curses.curs_set(0)
		
		#set interface layout information
		self.LINE_NUMBERS_SLOTS = range(4)
		self.LINE_NUMBER_STATUS = 5
		self.LINE_NUMBER_BALANCE = 6
		self.LINE_NUMBER_PROMPT = 7
	
	#---------------#
	#   Utilities   #
	#---------------#
	def animateReels(self,clearFirst=False):
		""" Animates spinning reels """
		
		#local vars
		pause = 0.1
		
		if(clearFirst):
			self.screen.clear()
		for i in range(5):
			self.screen.addstr(0,0,"\t-\t#\t#")
			self.screen.addstr(1,0,"\t#\t-\t#")
			self.screen.addstr(2,0,"\t#\t#\t-")
			self.screen.refresh()
			time.sleep(pause)
			self.screen.addstr(0,0,"\t#\t#\t-")
			self.screen.addstr(1,0,"\t-\t#\t#")
			self.screen.addstr(2,0,"\t#\t-\t#")
			self.screen.refresh()
			time.sleep(pause)
			self.screen.addstr(0,0,"\t#\t-\t#")
			self.screen.addstr(1,0,"\t#\t#\t-")
			self.screen.addstr(2,0,"\t-\t#\t#")
			self.screen.refresh()
			time.sleep(pause)
	
	def displayAccountBalance(self,accountBalance,clearFirst=False):
		""" Displays the user's account balance """
		
		if(clearFirst):
			self.screen.clear()
		
		#clear line first
		self.screen.move(self.LINE_NUMBER_BALANCE,0)
		self.screen.clrtoeol()
		
		#show the balance
		self.screen.addstr(self.LINE_NUMBER_BALANCE,0,"Your balance is: %d credits\n" % (accountBalance))
		self.screen.refresh()
	
	def displayCashingOut(self,availableCredits,clearFirst=True):
		""" Displays amount being cashed out """
		
		if(clearFirst):
			self.screen.clear()
		self.screen.addstr("Cashing out %d credits.  Please wait...\n" % (availableCredits))
		self.screen.refresh()
		time.sleep(2)
	
	def displaySlotMachine(self,slotMachine,clearFirst=True):
		""" Displays the slot machine """
		
		if(clearFirst):
			self.screen.clear()
		
		#clear the slot machine lines first
		for lineNumber in self.LINE_NUMBERS_SLOTS:
			self.screen.move(lineNumber,0)
			self.screen.clrtoeol()
		
		#display the slot machine
		slotMachineDisplay = str(slotMachine)
		lineNumber = self.LINE_NUMBERS_SLOTS[0]
		for displayLine in slotMachineDisplay.split('\n'):
			if(displayLine):
				self.screen.addstr(lineNumber,0,displayLine)
				lineNumber += 1
		self.screen.refresh()
	
	def displayStatus(self,statusMessage,clearFirst=False):
		""" Shows the informational status message """
		
		if(clearFirst):
			self.screen.clear()
		
		#clear the status line first
		self.screen.move(self.LINE_NUMBER_STATUS,0)
		self.screen.clrtoeol()
		
		#show the status message
		self.screen.addstr(self.LINE_NUMBER_STATUS,0,statusMessage)
		self.screen.refresh()
	
	def promptAction(self,clearFirst=False):
		""" Prompts the user for an action """
		
		#clear screen
		if(clearFirst):
			self.screen.clear()
		
		#output prompt
		self.screen.move(self.LINE_NUMBER_PROMPT,0)
		self.screen.addstr("Input a number of credits, 'c' for cash out, or just press enter to spin: ")
		
		#get input
		currentPosition = self.screen.getyx()
		commandString = self.screen.getstr(currentPosition[0],currentPosition[1])
		
		#clear prompt
		self.screen.move(self.LINE_NUMBER_PROMPT,0)
		self.screen.clrtoeol()
		self.screen.refresh()
		
		#return the command
		return commandString.strip().decode()
	
	def promptInitialCredits(self,clearFirst=True):
		""" Displays the startup screen """
		
		if(clearFirst):
			self.screen.clear()
		self.screen.addstr(0,0,"Welcome!")
		self.screen.addstr(2,0,"Input some credits: ")
		self.screen.refresh()
		currentPosition = self.screen.getyx()
		creditsString = self.screen.getstr(currentPosition[0],currentPosition[1])
		self.screen.clear()
		self.screen.refresh()
		return creditsString


#===============#
#   utilities   #
#===============#
def parseInt(intValue):
	try:
		returnValue = int(intValue)
	except:
		returnValue = None
	return returnValue

#==========#
#   main   #
#==========#
def main(cursesScreen):
	""" starts the work """
	
	#bring global screen object into scope
	global screen
	
	#initialize curses screen
	screen = Screen(cursesScreen)
	
	#initialize variables
	availableCredits = 0
	slotMachine = SlotMachine()
	
	#prompt for initial credits
	creditsString = screen.promptInitialCredits()
	creditsEntered = parseInt(creditsString)
	if(creditsEntered is None):
		raise ValueError("ERROR: Invalid number of credits entered")
	else:
		availableCredits += creditsEntered
	
	#show the beginning slot machine display
	screen.displaySlotMachine(slotMachine)
	
	#start game
	while(True):
		#display what they're working with
		screen.displayAccountBalance(availableCredits)
		
		#get command
		time.sleep(1)
		command = screen.promptAction()
		
		#clear status
		screen.displayStatus("")
		
		#check for added credits
		creditsEntered = parseInt(command)
		if(creditsEntered is not None):
			availableCredits += creditsEntered
			continue
		#check for cash out
		elif(command == 'c'):
			screen.displayCashingOut(availableCredits)
			break
		elif(command == ""):
			#bet credits
			betAmount = len(slotMachine.paylines)
			if(availableCredits >= betAmount):
				availableCredits -= betAmount
				
				#update information based on bet
				slotMachine.placeBet(betAmount)
				screen.displaySlotMachine(slotMachine,clearFirst=False)
				screen.displayAccountBalance(availableCredits)
				
				#animate spinning reels
				screen.animateReels()
				
				#spin the reels
				wins = slotMachine.spin()
				screen.displaySlotMachine(slotMachine,clearFirst=False)
				#break
				
				#show results
				wonCredits = slotMachine.payout(wins,betAmount)
				screen.displayStatus("You won %d credits on %d pay lines" % (wonCredits,wins))
				
				#update user balance
				availableCredits += wonCredits
			else:
				screen.displayStatus("You do not have enough credits to spin.  Please enter more money")
		else:
			screen.displayStatus("ERROR: '%s' command not recognized" % (command))

#call main function
if __name__ == "__main__":
	#call main method inside of a curses wrapper (for console drawing)
	curses.wrapper(main)
