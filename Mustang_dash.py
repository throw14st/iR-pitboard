#!python3

#This is the desktop client side of the Arduino pit board
#This is a conglomeration of several different projects

#https://github.com/Grimzentide/iRacing-Arduino-Pit-Board/blob/master/arduinopitboard.py
#https://github.com/kutu/pyirsdk/blob/master/tutorials/03%20Base%20application.md
 
import time                                                                         # Required for time.sleep function
import os                                                                           # Required to clear the console screen
import irsdk                                                                        # iRacing SDK - https://github.com/kutu/pyirsdk
import serial                                                                       # Required for the serial connection to the Arduino
import datetime                                                                     # Required to convert session times in human readable form
import sys                                                                          # Required for command line arguments and to clear the console screen
import argparse
import math

#####################################################################################
versionNumber = 1.00
#####################################################################################

 
now = datetime.datetime.now()
 
arduinoSerialSpeed = 250000                                                         # Arduino connection speed (must match speed in Arduino code)
arduinoSerialTimeout = 0                                                            # Timeout length when trying to establish serial connection
waitAfterSerialWrite = 0.3                                                          # Time delay to ensure the data is written to the Arduino - Suggest not going below 0.2
fuelMultiplier = .264172                                                            # Multiplier used to change liters to gallons 
logFileName = None
driverID = 0


ir = irsdk.IRSDK()
os.system('cls')
parser = argparse.ArgumentParser(epilog="Mustang Pit Board")

parser.add_argument('comport', help='This is the port of your Arduino eg. COM6')
parser.add_argument('--version', action='version', version='iRacing Mustang Pit Board v' + str(versionNumber))

results = parser.parse_args()
os.system('cls')

if not (results.comport):
    parser.error('COM Port not specified')

if (str(results.comport)[0:3].upper() != "COM"):                                          # Are the first 3 letters of the argument 'COM'
    parser.error('Specified com port cause an error')
    sys.exit()
else:
    ser = serial.Serial(results.comport, arduinoSerialSpeed, timeout=arduinoSerialTimeout) # set up the serial port
#TODO:  Add multi-Arduino setup support with new serial call.

    

# Clear the command prompt \ console screen function in Windows
#####################################################################################
def clearScreen():
    os.system('cls')
 
 
# Check if the iRacing service is running
#####################################################################################
while True:
    clearScreen()
    count = 5
    if ir.startup():
        print("Loading iRacing Arduino Pit Board...")
        time.sleep(2)
        break
    else:
        while (count > 0):
            print ("iRacing is currently not running. Retrying connection in " + str(count) + " seconds")
            time.sleep(1)
            count -= 1
            clearScreen()

            
# Send to serial port (ie. Arduino)
#####################################################################################
def sendViaSerial(str):                                                             # Function to send data to the Arduino
        ser.write(bytes(str.encode('ascii')))                                       # Send the string to the Arduino 1 byte at a time.
        time.sleep(waitAfterSerialWrite)                                            # A delay after sending the string via serial to the Arduino prevents the arduino from getting confused
 
         
# Setup information message and send to serial port (ie. Arduino)
#####################################################################################
def sendInfoMessage(str):                                                           # Function to construct an informational message and limit the characters to 26
    # 1st char in str (set elswhere) defines the colour on the Arduino end          # @ = White; # = Yellow; $ = Red
    infoMessageVar = ('-' + str[:26] + '!')                                         # '-' tells the Arduino that it is an info message, '!' tells the arduino that its the end of the message
    time.sleep(waitAfterSerialWrite)                                                # A delay after sending the string via serial to the Arduino prevents the arduino from getting confused
    sendViaSerial(str = infoMessageVar);                                            # Send the string to the Arduino using the sendViaSerial function


#Welcome Screen
#####################################################################################
def welcomeScreen():    
    clearScreen()                                                                       # Clear the console screen
    
    sessionNum = ir['SessionNum']                                                       # Current session number
    currentSurface = ir['CarIdxTrackSurface'][0]                                        # Fuel burn array used for 5 lap and race fuel burn average
    currentCar = ir['DriverInfo']['Drivers'][driverID]['CarScreenName']

    carClassMaxFuel = float(str(ir['DriverInfo']['Drivers'][driverID]['CarClassMaxFuelPct'])[:-2])# Get the class maximum fuel percentage
    lastFuelRemaining = ir['FuelLevel']                                                   # Set the last fuel reading to the current level

    # Get the full event information and send the details to the Arduino    
    rawTrackDisplayName = (ir['WeekendInfo']['TrackDisplayName'])                          # Track Name
    trackDisplayName = str(rawTrackDisplayName.encode('utf-8').decode('ascii', 'ignore'))
    sessionNum = ir['SessionNum']                                                       # Current session number
    sessionType = (ir['SessionInfo']['Sessions'][sessionNum]['SessionType'])            # Session Type = Race, Practice, Qualify, Offline Testing
    trackSkies = (ir['WeekendInfo']['TrackSkies'])                                      # Current cloud cover
    trackRubber = str.title(ir['SessionInfo']['Sessions'][sessionNum]['SessionTrackRubberState'])
                                                                             
    sendInfoMessage("@iRacing Mustang Board")
    sendInfoMessage("@      Version: " + str(versionNumber))
    time.sleep(5)
     
    sendInfoMessage("@Track: " + trackDisplayName)                                      #Track Name 
    sendInfoMessage("@Track Temp: " + trackTemp)                                        # Send the track temperature as an information message in white text
    sendInfoMessage("@Sky: " + trackSkies)                                              # Send the cloud cover as an information message in white text
           


#Variable Declarations
estimatedLaps = 0
boxThisLap = 0
pitWindowOpen = 0
onPitRoadFlag = 0
isTimedSession = 0
sessionExitFlag = 0
driverID = ir['DriverInfo']['DriverCarIdx']
currentSurface = ir['CarIdxTrackSurface'][0]
sessionNum = ir['SessionNum'] 
carClassMaxFuel = float(str(ir['DriverInfo']['Drivers'][driverID]['CarClassMaxFuelPct'])[:-2])
lastFuelRemaining = ir['FuelLevel']
sessionType = (ir['SessionInfo']['Sessions'][sessionNum]['SessionType'])
fuelBurn = []
distanceRead = []
uploadedLogs = 0
startSavingFuelFlag = 0
startSavingFuelTargetFlag = 0
currentDistance = 0
lastDistance = 0
distance = 0
currentFuel = 0
currentLap = 0
changeToPitLaneScreen = 0
lastPitStopOnLap = 0
optRepairLeft = 0
pittedUnderFlag = ""
fuelRequiredAtPitstopVarPitScreen = 0
averageDistanceRead = -1
fuelToLeaveWith = 0
fuelAddedLastStop = 0
pitFuelAddedStart = 0

#global flags
irsdk_checkered     = 0x0001
irsdk_white         = 0x0002
irsdk_green         = 0x0004
irsdk_yellow        = 0x0008
irsdk_red           = 0x0010
irsdk_blue          = 0x0020
irsdk_debris        = 0x0040
irsdk_crossed       = 0x0080
irsdk_yellowWaving  = 0x0100
irsdk_oneLapToGreen = 0x0200
irsdk_greenHeld     = 0x0400
irsdk_tenToGo       = 0x0800
irsdk_fiveToGo      = 0x1000
irsdk_randomWaving  = 0x2000
irsdk_caution       = 0x4000
irsdk_cautionWaving = 0x8000

#drivers black flags
irsdk_black         = 0x010000
irsdk_disqualify    = 0x020000
irsdk_servicible    = 0x040000
irsdk_furled        = 0x080000
irsdk_repair        = 0x100000

#start lights
irsdk_startHidden   = 0x10000000
irsdk_startReady    = 0x20000000
irsdk_startSet      = 0x40000000
irsdk_startGo       = 0x80000000

irsdk_LFTireChange  = 0x01
irsdk_RFTireChange  = 0x02
irsdk_LRTireChange  = 0x04
irsdk_RRTireChange  = 0x08

irsdk_FuelFill          = 0x10
irsdk_WindshieldTearoff = 0x20
irsdk_FastRepair        = 0x40

   
trackTemp = (ir['WeekendInfo']['TrackSurfaceTemp'])                                 # Current track temperature
trackTemp = trackTemp[:-2]
trackTemp = (float(trackTemp) * 9/5) + 32
trackTemp = "%.2f" % round(trackTemp,2)    

welcomeScreen()  

#if((((ir['DriverInfo']['Drivers'][driverID]['CarScreenName']) == "HPD ARX-01c")) or ((ir['DriverInfo']['Drivers'][driverID]['CarScreenName']) == "Williams-Toyota FW31") or ((ir['DriverInfo']['Drivers'][driverID]['CarScreenName']) == "McLaren MP4-30")):
#    writeToLog (logFileName, "Information: Using weight for fuel")
#    if(fuelMultiplier == 1):
#        fuelMultiplier = fuelMultiplier * ir['DriverInfo']['DriverCarFuelKgPerLtr']                                  
#    else:
#        fuelMultiplier = (1 * ir['DriverInfo']['DriverCarFuelKgPerLtr'])* 2.20462



        
while True:    
    if ir.startup():        
        
        if sessionExitFlag == 1:
            sessionExitFlag = 0
            #logFileName = createLogFile()
            #uploadedLogs = 0
            sendViaSerial('?!')
            welcomeScreen()    
        
        sessionNum = ir['SessionNum']        
        
        if (currentLap != ir['Lap']):
            currentLap = ir['Lap']
            #writeToLog (logFileName, "Lap: " + str(currentLap))
            
        currentLap = ir['Lap']   
    
        currentLapVar = ('#' + str(format(currentLap, '.0f') + '!'))
        sendViaSerial(str = currentLapVar)  

        if(ir['IsOnTrack'] == 1):
            fuelTankCapacity = ((ir['FuelLevel'] / ir['FuelLevelPct'])*carClassMaxFuel)         # Calculate the fuel tank capacity 
     
        currentDistance = ir['LapDistPct']
        fuelRemaining = ir['FuelLevel']
        pitFuelStart = fuelRemaining
        
        if 0.00 <= currentDistance <= 0.10:
            startSavingFuelTargetFlag = 0    
            #writeToLog (logFileName, "Lap: " + str(currentLap))
            if (ir['SessionFlags']&irsdk_checkered):
                #writeToLog (logFileName, "Flag: Checkered")
                sendInfoMessage("@" + "Flag: Checkered")
        
        # NEW FUEL CALCULATION CODE as at v2.3
        ###################################################################################################################
        if (ir['IsOnTrack'] == 1):
            if (lastDistance == 0):
                lastDistance = currentDistance
                distance = -1
            elif (currentDistance > lastDistance):
                distance = currentDistance - lastDistance
                if (distance > 0.005):
                    distanceRead.append(distance)
                    currentFuel = lastFuelRemaining - fuelRemaining                
                    fuelPer1Pct = currentFuel / (distance * 100)
                    #writeToLog (logFileName, "Current Distance: " + str(currentDistance))
                    #writeToLog (logFileName, "Last Distance: " + str(lastDistance))
                    #writeToLog (logFileName, "Distance: " + str(distance))
                    #writeToLog (logFileName, "Last Fuel: " + str(lastFuelRemaining))                    
                    #writeToLog (logFileName, "Fuel Remaining: " + str(fuelRemaining*fuelMultiplier))
                    #writeToLog (logFileName, "Fuel Burn: " + str(currentFuel))                    
                    #writeToLog (logFileName, "Fuel per 1 Pct: " + str(fuelPer1Pct))
                    if (fuelPer1Pct > 0):
                        fuelBurn.append(fuelPer1Pct)    
                    lastFuelRemaining = fuelRemaining
                    lastDistance = currentDistance
            elif (currentDistance < lastDistance):
                distance = (1 - lastDistance) + currentDistance
                if (distance > 0.005):                
                    distanceRead.append(distance)                
                    lastDistance = currentDistance
                    currentFuel = lastFuelRemaining - fuelRemaining
                    lastFuelRemaining = fuelRemaining
                    fuelPer1Pct = currentFuel / (distance * 100)
                    if (fuelPer1Pct > 0):
                        fuelBurn.append(fuelPer1Pct)
                        #writeToLog (logFileName, "Current Distance: " + str(currentDistance))
                        #writeToLog (logFileName, "Last Distance: " + str(lastDistance))
                        #writeToLog (logFileName, "Distance: " + str(distance))
                        #writeToLog (logFileName, "Fuel Remaining: " + str(fuelRemaining*fuelMultiplier))
                        #writeToLog (logFileName, "Fuel Burn: " + str(currentFuel))
                        #writeToLog (logFileName, "Fuel per 1 Pct: " + str(fuelPer1Pct))
                    
            fuelRemainingVar = ('* ' + str(format(fuelRemaining*fuelMultiplier, '.2f') + ' !'))        
            sendViaSerial(str = fuelRemainingVar)
        
        
        
        ###################################################################################################################        
        

 
        lastSurface = currentSurface
        currentSurface = ir['CarIdxTrackSurface'][0]      
        
        if (currentSurface == 1) and ((lastSurface > 2) or (lastSurface == 0)):     # reset button used
            #writeToLog (logFileName, "Car Reset")
            del fuelBurn[:]
            del distanceRead[:]            
            boxThisLap = 0                                                              
            pitWindowOpen = 0
            estimatedLaps = 0
            pitWindowOpen = 0
            onPitRoadFlag = 0
            startSavingFuelFlag = 0
            startSavingFuelTargetFlag = 0 
            currentDistance = 0
            lastDistance = 0
            distance = 0
            currentFuel = 0
            currentLap = 0
            lastPitStopOnLap = currentLap            
            sendViaSerial('^       !') # fuel required
            sendViaSerial('%       !') # pit window
            sendViaSerial('&       !') # laps until empty
            sendViaSerial('(       !') # 5 lap avg
            sendViaSerial(')       !') # race avg
 
        if (ir['IsInGarage'] == 0 and ir['IsOnTrack'] == 0):
            #writeToLog (logFileName, "In Pit Box")
            del fuelBurn[:]            
            del distanceRead[:]            
            boxThisLap = 0                                                             
            pitWindowOpen = 0
            estimatedLaps = 0
            pitWindowOpen = 0
            onPitRoadFlag = 0
            startSavingFuelFlag = 0
            startSavingFuelTargetFlag = 0
            currentDistance = 0
            lastDistance = 0
            distance = 0
            currentFuel = 0
            lastPitStopOnLap = currentLap            
            sendViaSerial('^       !') # fuel required
            sendViaSerial('%       !') # pit window
            sendViaSerial('&       !') # laps until empty
            sendViaSerial('(       !') # 5 lap avg
            sendViaSerial(')       !') # race avg
            
            if (changeToPitLaneScreen == 1):
                sendViaSerial('?!')
                changeToPitLaneScreen = 0
         
         
         
        currentFlagStatus = ir['SessionFlags']    
        
        if (ir['SessionFlags']&irsdk_checkered > 0 and ir['SessionTimeRemain'] < 0):
            #writeToLog (logFileName, "Flag: Checkered")
            sendInfoMessage("@" + "Flag: Checkered")
            
            
        #if (currentFlagStatus&irsdk_checkered > 0):
        #    writeToLog (logFileName, ("Flag: Checkered"))
        #if (currentFlagStatus&irsdk_white > 0):
        #    writeToLog (logFileName, ("Flag: White"))
        #if (currentFlagStatus&irsdk_green > 0):
        #    writeToLog (logFileName, ("Flag: Green"))
        #    sendInfoMessage("@" + "Flag: Green")
        #if (currentFlagStatus&irsdk_yellow > 0):
        #    writeToLog (logFileName, ("Flag: Yellow"))
        #if (currentFlagStatus&irsdk_red > 0):
        #    writeToLog (logFileName, ("Flag: Red"))
        #if (currentFlagStatus&irsdk_blue > 0):
        #    writeToLog (logFileName, ("Flag: Blue"))
        #if (currentFlagStatus&irsdk_debris > 0):
        #    writeToLog (logFileName, ("Flag: Debris"))
        #if (currentFlagStatus&irsdk_crossed > 0):
        #    writeToLog (logFileName, ("Flag: Crossed"))
        #if (currentFlagStatus&irsdk_yellowWaving > 0):
        #    writeToLog (logFileName, ("Flag: Yellow Waving"))
        #if (currentFlagStatus&irsdk_oneLapToGreen > 0):
        #    writeToLog (logFileName, ("Flag: One Lap To Green"))
        #if (currentFlagStatus&irsdk_greenHeld > 0):
        #    writeToLog (logFileName, ("Flag: Green Held"))
        #if (currentFlagStatus&irsdk_tenToGo > 0):
        #    writeToLog (logFileName, ("Flag: 10 to go"))
        #if (currentFlagStatus&irsdk_fiveToGo > 0):
        #    writeToLog (logFileName, ("Flag: 5 to go"))
        #if (currentFlagStatus&irsdk_randomWaving > 0):
        #    writeToLog (logFileName, ("Flag: Random Waving"))
        #if (currentFlagStatus&irsdk_caution > 0):
        #    writeToLog (logFileName, ("Flag: Caution"))
        #if (currentFlagStatus&irsdk_cautionWaving > 0):
        #    writeToLog (logFileName, ("Flag: Caution Waving"))
        #if (currentFlagStatus&irsdk_black > 0):
        #    writeToLog (logFileName, ("Flag: Black"))
        #if (currentFlagStatus&irsdk_disqualify > 0):
        #    writeToLog (logFileName, ("Flag: Disqualify"))
        #if (currentFlagStatus&irsdk_servicible > 0):
        #   #writeToLog (logFileName, ("Flag: Servicible"))
        #if (currentFlagStatus&irsdk_furled > 0):
        #    writeToLog (logFileName, ("Flag: Furled"))
        #if (currentFlagStatus&irsdk_repair > 0):
        #    writeToLog (logFileName, ("Flag: Repair"))
            
        #while (ir['OnPitRoad'] == 1 and ir['IsOnTrack'] == 1):        #Used in testing only
        while (ir['OnPitRoad'] == 1 and ir['IsOnTrack'] == 1 and currentLap > 0):
        
            if (pitFuelStart > ir['FuelLevel']):
                pitFuelAddedStart = ir['FuelLevel']
        
            if (changeToPitLaneScreen != 1):
                sendViaSerial('~!')
                changeToPitLaneScreen = 1
                #writeToLog (logFileName, "On Pit Road: Lap " + str(currentLap))                
                
                if (currentLap > 0 and len(distanceRead)> 2):            

                    sendViaSerial('G' + str(format(fuelToLeaveWith, '.2f') + '!'))            # FUEL TO LEAVE WITH                    
                    #writeToLog (logFileName, "Fuel to Leave With: " + str(fuelToLeaveWith))
                    
                    sendViaSerial('E' + str(fuelRequiredAtPitstopVarPitScreen) + '!')        # FUEL REQUIRED AT STOP
                    #writeToLog (logFileName, "Fuel Required at Pit Stop: " + str(fuelRequiredAtPitstopVarPitScreen))
                    
                    if (fuelAddedLastStop > 0):
                        sendViaSerial('H' + str(format(fuelAddedLastStop, '.2f') + '!'))
                        #writeToLog (logFileName, "Fuel Added at Last Stop: " + str(fuelAddedLastStop))
                    else:
                        sendViaSerial('H0.00!')    
                        #writeToLog (logFileName, "Fuel Added at Last Stop: 0.00")
                        
                    lapsOnTires = currentLap - lastPitStopOnLap                
                    sendViaSerial('A' + str(lastPitStopOnLap) + "!")                        # LAST PIT STOP LAP
                    #writeToLog (logFileName, "Last Pitted on Lap: " + str(lastPitStopOnLap))
                    
                    sendViaSerial('D' + str(lapsOnTires) + "!")                                   # LAPS ON TIRES             
                    #writeToLog (logFileName, "Laps on Tires: " + str(lapsOnTires))
                    
                    averageDistanceRead = (sum(distanceRead)/len(distanceRead))
                    readingsReqForStint = int(lapsOnTires / averageDistanceRead)
                    averageFuelBurnStint = (sum(fuelBurn[-readingsReqForStint:])/len(fuelBurn[-readingsReqForStint:])*100)            
                    sendViaSerial('F' + str(format(averageFuelBurnStint, '.2f') + '!'))        # FUEL STINT AVERAGE        
                    #writeToLog (logFileName, "AVG Fuel Burn Stint: " + str(averageFuelBurnStint))
                    
                if (ir['SessionFlags']&irsdk_green > 0):
                    pittedUnderFlag = "Green"
                    sendViaSerial('C' + pittedUnderFlag + "!")    # GREEN OR CAUTION PIT STOP    
                elif (ir['SessionFlags']&irsdk_caution > 0):
                    pittedUnderFlag = "Caution"
                    sendViaSerial('C' + pittedUnderFlag + "!")    # GREEN OR CAUTION PIT STOP    
                elif (ir['SessionFlags']&irsdk_cautionWaving > 0):
                    pittedUnderFlag = "Caution"                    
                    sendViaSerial('C' + pittedUnderFlag + "!")    # GREEN OR CAUTION PIT STOP    
                else:
                    pittedUnderFlag = "Green"                    
                    sendViaSerial('C' + pittedUnderFlag + "!")    # GREEN OR CAUTION PIT STOP            
                    
                #writeToLog (logFileName, "Pitted Under: " + pittedUnderFlag)                    
                        
            if (ir['PitOptRepairLeft'] > 0):
                optRepairLeft = ir['PitOptRepairLeft']
                sendViaSerial('B' + str(format(optRepairLeft, '.2f') + '!'))
                #writeToLog (logFileName, "Optional Repairs Left: " + str(format(optRepairLeft, '.2f')))
            else:
                sendViaSerial('B     !')
                #writeToLog (logFileName, "Optional Repairs Left: 0.00")
       
            currentPitFlagStatus = ir['PitSvFlags']
            if (currentPitFlagStatus&irsdk_FastRepair > 0):
                sendViaSerial("IYES!")
                #writeToLog (logFileName, "Fast Repair: Yes")
            else:
                sendViaSerial("I NO !")   
                #writeToLog (logFileName, "Fast Repair: No")                

            if (currentPitFlagStatus&irsdk_LFTireChange > 0):
                sendViaSerial("JYES!")
                #writeToLog (logFileName, "Change LF: Yes")                
            else:
                sendViaSerial("J NO !")  
                #writeToLog (logFileName, "Change LF: No")                

            if (currentPitFlagStatus&irsdk_RFTireChange > 0):
                sendViaSerial("KYES!")
                #writeToLog (logFileName, "Change RF: Yes")                
            else:
                sendViaSerial("K NO !")  
                #writeToLog (logFileName, "Change RF: No")                

            if (currentPitFlagStatus&irsdk_LRTireChange > 0):
                sendViaSerial("LYES!")
                #writeToLog (logFileName, "Change LR: Yes")                
            else:
                sendViaSerial("L NO !")  
                #writeToLog (logFileName, "Change LR: No")                

            if (currentPitFlagStatus&irsdk_RRTireChange > 0):
                sendViaSerial("MYES!")
                #writeToLog (logFileName, "Change RR: Yes")                
            else:
                sendViaSerial("M NO !")  
                #writeToLog (logFileName, "Change RR: No")                

            sendViaSerial("N1:" + str(format(ir['LFwearL'] * 100, '.0f')) + ":" + str(format(ir['LFwearM'] * 100, '.0f')) + ":" + str(format(ir['LFwearR'] * 100, '.0f')) + ":" + str(format(ir['LFtempCL'], '.0f')) + ":" + str(format(ir['LFtempCM'], '.0f')) + ":" + str(format(ir['LFtempCR'], '.0f')) + "!")
            sendViaSerial("N2:" + str(format(ir['RFwearL'] * 100, '.0f')) + ":" + str(format(ir['RFwearM'] * 100, '.0f')) + ":" + str(format(ir['RFwearR'] * 100, '.0f')) + ":" + str(format(ir['RFtempCL'], '.0f')) + ":" + str(format(ir['RFtempCM'], '.0f')) + ":" + str(format(ir['RFtempCR'], '.0f')) + '!')
            sendViaSerial("N3:" + str(format(ir['LRwearL'] * 100, '.0f')) + ":" + str(format(ir['LRwearM'] * 100, '.0f')) + ":" + str(format(ir['LRwearR'] * 100, '.0f')) + ":" + str(format(ir['LRtempCL'], '.0f')) + ":" + str(format(ir['LRtempCM'], '.0f')) + ":" + str(format(ir['LRtempCR'], '.0f')) + '!')
            sendViaSerial("N4:" + str(format(ir['RRwearL'] * 100, '.0f')) + ":" + str(format(ir['RRwearM'] * 100, '.0f')) + ":" + str(format(ir['RRwearR'] * 100, '.0f')) + ":" + str(format(ir['RRtempCL'], '.0f')) + ":" + str(format(ir['RRtempCM'], '.0f')) + ":" + str(format(ir['RRtempCR'], '.0f')) + '!')
            
            #writeToLog (logFileName, "LF Wear: L:" + str(format(ir['LFwearL'] * 100, '.0f')) + " M:" + str(format(ir['LFwearM'] * 100, '.0f')) + " R:" + str(format(ir['LFwearR'] * 100, '.0f')))
            #writeToLog (logFileName, "LF Temp: L:" + str(format(ir['LFtempCL'], '.0f')) + " M:" + str(format(ir['LFtempCM'], '.0f')) + " R:" + str(format(ir['LFtempCR'], '.0f')))
            #writeToLog (logFileName, "RF Wear: L:" + str(format(ir['RFwearL'] * 100, '.0f')) + " M:" + str(format(ir['RFwearM'] * 100, '.0f')) + " R:" + str(format(ir['RFwearR'] * 100, '.0f')))
            #writeToLog (logFileName, "RF Temp: L:" + str(format(ir['RFtempCL'], '.0f')) + " M:" + str(format(ir['RFtempCM'], '.0f')) + " R:" + str(format(ir['RFtempCR'], '.0f')))
            #writeToLog (logFileName, "LR Wear: L:" + str(format(ir['LRwearL'] * 100, '.0f')) + " M:" + str(format(ir['LRwearM'] * 100, '.0f')) + " R:" + str(format(ir['LRwearR'] * 100, '.0f')))
            #writeToLog (logFileName, "LR Temp: L:" + str(format(ir['LRtempCL'], '.0f')) + " M:" + str(format(ir['LRtempCM'], '.0f')) + " R:" + str(format(ir['LRtempCR'], '.0f')))
            #writeToLog (logFileName, "RR Wear: L:" + str(format(ir['RRwearL'] * 100, '.0f')) + " M:" + str(format(ir['RRwearM'] * 100, '.0f')) + " R:" + str(format(ir['RRwearR'] * 100, '.0f')))
            #writeToLog (logFileName, "RR Temp: L:" + str(format(ir['RRtempCL'], '.0f')) + " M:" + str(format(ir['RRtempCM'], '.0f')) + " R:" + str(format(ir['RRtempCR'], '.0f')))
    
        if (ir['OnPitRoad'] == 0 and changeToPitLaneScreen == 1):
            changeToPitLaneScreen = 0
            lastPitStopOnLap = currentLap
            fuelAddedLastStop = ir['FuelLevel'] - pitFuelAddedStart
            sendViaSerial('?!')
            if (optRepairLeft > 0):
                sendInfoMessage("@Opt Repair Left: " + str(format(optRepairLeft, '.2f')))
 
        if ((ir['SessionInfo']['Sessions'][sessionNum]['SessionType']) != sessionType): # If the session changes, print the updated info on the arduino
            sessionType = ((ir['SessionInfo']['Sessions'][sessionNum]['SessionType']))  # Re-set the sessionType variable
            #writeToLog (logFileName, "Session Type Changed To " + sessionType)
            #logFileName = createLogFile()
            del fuelBurn[:]                                                             # Erase current fuel usage data
            del distanceRead[:]
            boxThisLap = 0                                                              # Remove the box this lap flag
            pitWindowOpen = 0
            estimatedLaps = 0
            pitWindowOpen = 0
            onPitRoadFlag = 0
            isTimedSession = 0
            startSavingFuelFlag = 0
            startSavingFuelTargetFlag = 0
            currentDistance = 0
            lastDistance = 0
            distance = 0
            currentFuel = 0
            currentLap = 0
            #writeSessionInfoToLog()
            sendViaSerial('@       !') # session laps
            sendViaSerial('#       !') # completed laps
            sendViaSerial('$       !') # remaining laps
            sendViaSerial('^       !') # fuel required
            sendViaSerial('%       !') # pit window
            sendViaSerial('&       !') # laps until empty
            sendViaSerial('(       !') # 5 lap avg
            sendViaSerial(')       !') # race avg

            
        if ir['IsInGarage'] == 1:
            #writeToLog (logFileName, "In Garage")
            del fuelBurn[:]
            del distanceRead[:]            
            boxThisLap = 0                                                              # Remove the box this lap flag
            pitWindowOpen = 0
            estimatedLaps = 0
            pitWindowOpen = 0
            onPitRoadFlag = 0
            startSavingFuelFlag = 0
            startSavingFuelTargetFlag = 0    
            currentDistance = 0
            lastDistance = 0
            distance = 0
            currentFuel = 0
            lastPitStopOnLap = currentLap
            sendViaSerial('^       !') # fuel required
            sendViaSerial('%       !') # pit window
            sendViaSerial('&       !') # laps until empty
            sendViaSerial('(       !') # 5 lap avg
            sendViaSerial(')       !') # race avg
     
        if ((ir['SessionInfo']['Sessions'][sessionNum]['SessionLaps']) == "unlimited"):             # Unlimited laps?
            
            isTimedSession = 1
            sessionTimeRemain = int(ir['SessionTimeRemain'])                                    # Get the amount of time in seconds for this session time remaining
            m, s = divmod(sessionTimeRemain, 60)
            h, m = divmod(m, 60)
 
            if ((ir['SessionInfo']['Sessions'][sessionNum]['SessionTime']) == "unlimited"):         # Unlimted time?  
                sessionTime = 604800
                m, s = divmod(sessionTime, 60)
                h, m = divmod(m, 60)                 
                sessionLapsVar =('@Infinite!')
                sendViaSerial(str = sessionLapsVar);                
            else:
                sessionTime = (ir['SessionInfo']['Sessions'][sessionNum]['SessionTime'])            # Get the amount of time in seconds for this session
                sessionTime = float(sessionTime[:-4])
                m, s = divmod(sessionTime, 60)
                h, m = divmod(m, 60)                 
                sessionLapsVar = ('@' + "%d:%02d" % (h, m) + '!')
                sendViaSerial(str = sessionLapsVar); 
                
            if (sessionTimeRemain == 604800): 
                sessionTimeRemainVar = ('$Infinite!')
                sendViaSerial(str = sessionTimeRemainVar);
                remainingLap = (sessionTimeRemain / ir['DriverInfo']['DriverCarEstLapTime'])                
            else:
                sessionTimeRemain = int(ir['SessionTimeRemain'])                                    # Get the amount of time in seconds for this session time remaining
                remainingLap = (sessionTimeRemain / ir['DriverInfo']['DriverCarEstLapTime'])
                remainingLap = remainingLap + 1
                m, s = divmod(sessionTimeRemain, 60)
                h, m = divmod(m, 60)                 
                sessionTimeRemainVar = ('$' + "%d:%02d" % (h, m) + '!')
                if (sessionTimeRemain < 0):
                    sendViaSerial('$       !')
                else:
                    sendViaSerial(str = sessionTimeRemainVar);
                
        else:
            remainingLap = ir['SessionLapsRemainEx']
            if (remainingLap < 0):
                sendViaSerial('$       !')
            else:
                remainingLapVar = ('$' + str(format(remainingLap, '.0f') + '!'))
                sendViaSerial(str = remainingLapVar);
             
            SessionLaps = (ir['SessionInfo']['Sessions'][sessionNum]['SessionLaps'])
            SessionLapsVar = ('@' + str(SessionLaps) + '!')
            sendViaSerial(str = SessionLapsVar);
 
        if len(fuelBurn) >= 2:

            if(fuelBurn[-1] < 0):
                #writeToLog (logFileName, "Removed negative fuel burn figure: " + str(fuelBurn[-1]))
                del fuelBurn[-1]

            if len(fuelBurn) >= 15:

                if(fuelBurn[0] > sum(fuelBurn)/len(fuelBurn) * 2):
                    #writeToLog (logFileName, "Removed excessive fuel burn figure: " + str(fuelBurn[0]))
                    del fuelBurn[0]                
            
            averageDistanceRead = (sum(distanceRead)/len(distanceRead))
            #writeToLog (logFileName, "Average Distance: " + str(averageDistanceRead))
            
            readingsReqFor5Laps = int(5 / averageDistanceRead)
            #writeToLog (logFileName, "Readings Required for 5 Laps: " + str(readingsReqFor5Laps))
            
            readingsReqFor1Laps = int(1 / averageDistanceRead)
            #writeToLog (logFileName, "Readings Required for 1 Lap: " + str(readingsReqFor1Laps))
            
            averageFuelBurnRace = (sum(fuelBurn)/len(fuelBurn)*100)
            averageFuelBurn5Lap = (sum(fuelBurn[-readingsReqFor5Laps:])/len(fuelBurn[-readingsReqFor5Laps:])*100)
            averageFuelBurn1Lap = (sum(fuelBurn[-readingsReqFor1Laps:])/len(fuelBurn[-readingsReqFor1Laps:])*100)

            estimatedLaps = (fuelRemaining / averageFuelBurn5Lap)
 
            averageFuelBurn5LapVar = ('( ' + str(format(averageFuelBurn5Lap*fuelMultiplier, '.2f') + ' !'))
            averageFuelBurnRaceVar = (') ' + str(format(averageFuelBurnRace*fuelMultiplier, '.2f') + ' !'))
            estimatedLapsVar = ('& ' + str(format(estimatedLaps, '.2f') + ' !'))
            
            sendViaSerial(str = averageFuelBurn5LapVar);
            sendViaSerial(str = averageFuelBurnRaceVar);
            sendViaSerial(str = estimatedLapsVar);
            
            #writeToLog (logFileName, "Estimated Laps: " + str(estimatedLaps))
            #writeToLog (logFileName, "Race Burn: " + str(averageFuelBurnRace))            
            #writeToLog (logFileName, "5 Lap Burn: " + str(averageFuelBurn5Lap))
            #writeToLog (logFileName, "1 Lap Burn: " + str(averageFuelBurn1Lap))
             
            if (estimatedLaps <= remainingLap):
 
                fuelRequiredAtPitstop = (((remainingLap * float(averageFuelBurn5Lap))-fuelRemaining) + (float(averageFuelBurn5Lap) /2))     
                 
                if(fuelRequiredAtPitstop <= float(averageFuelBurn5Lap) and currentDistance <= 0.100):
                    if (startSavingFuelFlag == 0):
                        sendInfoMessage("#Start Saving Fuel!")
                        #writeToLog (logFileName, "Start Saving Fuel")
                        startSavingFuelFlag = 1
                    if (startSavingFuelTargetFlag == 0):
                        startSavingFuelTargetFlag = 1
                        sendInfoMessage("@Target Lap AVG: " + str(format((fuelRemaining/remainingLap)*fuelMultiplier,'.3f')))
                        
                        if ((averageFuelBurn1Lap*fuelMultiplier) <= ((fuelRemaining/estimatedLaps)*fuelMultiplier)): 
                            sendInfoMessage("%Last Lap AVG:   " + str(format(averageFuelBurn1Lap*fuelMultiplier, '.3f')))
                        else:
                            sendInfoMessage("#Last Lap AVG:   " + str(format(averageFuelBurn1Lap*fuelMultiplier, '.3f')))                        
                        
                        
                 
                if fuelRequiredAtPitstop > fuelTankCapacity:
                    fuelRequiredAtPitstopVar = ('^' + str(format(fuelTankCapacity*fuelMultiplier,'.2f')) + '!')
                    fuelRequiredAtPitstopVarPitScreen = (str(format(fuelTankCapacity*fuelMultiplier,'.2f')) + '!')
                    #writeToLog (logFileName, "Fuel Required at Pit Stop: " + str(format(fuelTankCapacity*fuelMultiplier,'.2f')))
                    if (ir['OnPitRoad'] == 1 and ir['IsOnTrack'] == 1):
                        if onPitRoadFlag == 0 and currentLap >= 1:                                  # If I have already sent the pit lane message once, ignore that I am on pit road
                            onPitRoadFlag = 1                                                       # Change the flag status to prevent spamming of the info messages
                            fuelToLeaveWith = fuelTankCapacity
                                
                            
                else:
                    fuelRequiredAtPitstopVar = ('^' + str(format(fuelRequiredAtPitstop*fuelMultiplier,'.2f')) + '!')            
                    fuelRequiredAtPitstopVarPitScreen = (str(format(fuelRequiredAtPitstop*fuelMultiplier,'.2f')) + '!')                    
                    #writeToLog (logFileName, "Fuel Required at Pit Stop: " + str(format(fuelRequiredAtPitstop*fuelMultiplier,'.2f')))
                    if (ir['OnPitRoad'] == 1 and ir['IsOnTrack'] == 1):
                        if onPitRoadFlag == 0 and currentLap >= 1:                                  # If I have already sent the pit lane message once, ignore that I am on pit road
                            onPitRoadFlag = 1
                            fuelToLeaveWith = ((fuelRequiredAtPitstop+fuelRemaining)*fuelMultiplier)
                    
                pitEarlyOnLap = int(((fuelRequiredAtPitstop + fuelRemaining - fuelTankCapacity) / averageFuelBurn5Lap) + currentLap + 1) 
                
                              
                if (pitEarlyOnLap == currentLap):
                    if (pitWindowOpen == 0):
                        sendInfoMessage("#Pit Window Open (Lap " + str(format(currentLap, '.0f')) + ")")
                        #writeToLog (logFileName, "Pit Window Open (Lap " + str(format(currentLap, '.0f')))
                        pitWindowOpen = 1
                
                if (pitEarlyOnLap < 0):
                    pitEarlyOnLap = currentLap                

                
                if (ir['CarIdxTrackSurface'][0] == 1):
                    pitWindowOpen = 0
                 
                pitLateOnLap = int((currentLap + estimatedLaps) - 1)            
                 
                if (pitEarlyOnLap > pitLateOnLap):
                    # Can NOT make it to the end with only 1 more stop... Show the latest you can stop
                    pitOnLapVar = ('%' + str(int((currentLap + estimatedLaps) - 1)) + '!')
                    #writeToLog (logFileName, "Pit on Lap: " + str(int((currentLap + estimatedLaps) - 1)))
                else:
                    # Can make it to the end with only one more stop, show the earliest and latest you can stop.
                    pitOnLapVar = ('% ' + str(pitEarlyOnLap) + '-' + str(pitLateOnLap) + ' !')
                    #writeToLog (logFileName, "Pit Window: " + str(pitEarlyOnLap) + '-' + str(pitLateOnLap))
                 
                sendViaSerial(str = pitOnLapVar);
                sendViaSerial(str = fuelRequiredAtPitstopVar);
            else:
                # Clear Pit Window Field
                sendViaSerial('%       !')
                 
                # Clear Required Fuel Field
                sendViaSerial('^       !')
             
            if (fuelRemaining < float(averageFuelBurn5Lap) * 2):
                if(len(fuelBurn) > 20) and (boxThisLap == 0):
                    sendInfoMessage("$Box Box Box (Lap " + str(format(currentLap, '.0f')) + ")")
                    #writeToLog (logFileName, "Box Box Box (Lap " + str(format(currentLap, '.0f')) + ")")
                    boxThisLap = 1
                        
    else:            
        count = 5
        sessionExitFlag = 1
        #if (uploadedLogs == 0):
        #    uploadedLogs = 1
        #    uploadLogsToCloud()
        #writeToLog (logFileName, "Connection Lost: Retrying")
        sendInfoMessage("@Connection Lost: Retrying")
        while (count > 0):
            print ("iRacing is currently not running. Retrying connection in " + str(count) + " seconds")
            time.sleep(1)
            count -= 1
            clearScreen()
                        
                    
            
        
                    
        
            
