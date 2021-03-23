import smbus
import time
import os
import cmd
import threading
from Adafruit_LED_Backpack import BicolorBargraph24
from Adafruit_LED_Backpack import SevenSegment
import RPi.GPIO as GPIO
import sys
import cmd
import pygame
from pygame.locals import *
from subprocess import Popen
import random


##############################################################################
###############################Set up, Movies, and Images#####################
##############################################################################

#Setup GPIOs and Bus specification.
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(0)

#Creates a variable to reference libraries for I2C communication
bus = smbus.SMBus(1) 

#Setting up sound effects
pygame.mixer.init()

#Door open sound
door = pygame.mixer.Sound("/home/pi/Modules/adjust.wav")

#Booster Sounds
powerupSound = pygame.mixer.Sound("/home/pi/Modules/powerup.wav")
boosterSound = pygame.mixer.Sound("/home/pi/Modules/booster.wav")

#O2 and CO2 Sounds
alarm1Sound = pygame.mixer.Sound("/home/pi/Modules/alarm1.wav")
co2AlarmSound = pygame.mixer.Sound("/home/pi/Modules/alert.wav")
o2AlarmSound = pygame.mixer.Sound("/home/pi/Modules/alert.wav")

#Adjust roll and yaw sounds
adjust = pygame.mixer.Sound("/home/pi/Modules/adjust.wav")

#parachute sound during landing
parachute = pygame.mixer.Sound("/home/pi/Modules/parachute.wav")


#Camera Movies
movie1 = ("/home/pi/Modules/earth1.mp4")
movie2 = ("/home/pi/Modules/earth2.mp4")
movie3 = ("/home/pi/Modules/earth3.mp4")
movie4 = ("/home/pi/Modules/earth4.mp4")
movie5 = ("/home/pi/Modules/spaceman1.mp4")
movie6 = ("/home/pi/Modules/spaceman2.mp4")

#Mission Movies
mars_mission = ("/home/pi/Modules/mars_mission.mp4")

#Images
nasa_logo = "/home/pi/Modules/NASA.jpg"


#=========================================================================
#---------------------Setting up GPIOs.-----------------#
#=========================================================================

#Arm GPIO for launch. Toggle switch
GPIO.setup(4, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

#Launch GPIO Button. Button press
GPIO.setup(17, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

#Yaw minus and plus GPIO button. 27 is -, 22 is + Button press
GPIO.setup(27, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(22, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

#Roll minus and plus GPIO Buttons 10 is -, 9 is + Button press
GPIO.setup(10, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(9, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

#Arm for landing. Toggle switch.
GPIO.setup(8, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

#Landing GPIO button. Button press.
GPIO.setup(7, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

#Power Main Cabin
GPIO.setup(5, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
#Power Main Bay
GPIO.setup(6, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
#Power Aux Cabin
GPIO.setup(13, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
#Power Aux Bay
GPIO.setup(19, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

#Cabin Bay Door open or closed
GPIO.setup(11, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

#Mission status - arm status
GPIO.setup(15, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

#Mission start
GPIO.setup(14, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

#O2 replacement trigger
GPIO.setup(23, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

#CO2 replacement trigger
GPIO.setup(24, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

#Booster replacement trigger
GPIO.setup(25, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

#Camera open
GPIO.setup(12, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

#Camera close
GPIO.setup(16, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

#Canadarm extend and retract
GPIO.setup(20, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

#Canadarm retract
GPIO.setup(21, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)


#The following are SD GPIOs and I'm unsure if they can be used
#GPIO.setup(27, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
#GPIO.setup(28, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)


#########################################################################
#############################MCP23017 Set up#############################
#########################################################################

#This is where addresses are set, devices named, and LEDs are intialized
#(e.g. importing librarys and naming them for use)

#=========================================================================
#-Booster MCP23017---------------------------------------------------------
#=========================================================================

#Specifying MCP bus address
DA_27 = 0x27 # Device address

#Specifying the register for pin direction
APolarity27 = 0x00 # Device address
BPolarity27 = 0x00 # Device address

#This specifies the register address (you actually write to a latch)
RegisterLatchA27  = 0x12 # Register for inputs for bank A
RegisterLatchB27  = 0x13 # Register for inputs for bank B

#Using the DA_27 address, and pin direction above, and then the hex to specify input
bus.write_byte_data(DA_27,APolarity27,0xFF) #Bank A set as all inputs
bus.write_byte_data(DA_27,BPolarity27,0xFF) #Bank B set as all inputs

#write 0 to both latches - this effectively clears them.
bus.write_byte_data(DA_27,RegisterLatchA27,0)
bus.write_byte_data(DA_27,RegisterLatchB27,0)


#=========================================================================
#-Alarm Panel MCP23017----------------------------------------------------
#=========================================================================
DA_24 = 0x24 # Device address (A0-A2)

APolarity20 = 0x00 # Pin Polarity
BPolarity20 = 0x01 # Pin Polarity

#This specifies the register address
RegisterLatchA20  = 0x12 # Output latch for A
RegisterLatchB20  = 0x13 # Output latch for B

#Using the DA_27 address, and pin direction, and then the hex to specify output
bus.write_byte_data(DA_24,APolarity20,0x00)
bus.write_byte_data(DA_24,BPolarity20,0x00)

#write 0 to both latches - this effectively clears them.
bus.write_byte_data(DA_24,RegisterLatchA20,0)
bus.write_byte_data(DA_24,RegisterLatchB20,0)


###########################################################################
###########################LED Set up######################################
###########################################################################


#=========================================================================
#-Booster Bargraph LED----------------------------------------------------
#=========================================================================

#Creating a variable to reference libraries
boosterdisplay = BicolorBargraph24.BicolorBargraph24(address=0x70)

#Intitalize the display
boosterdisplay.write_display()
boosterdisplay.begin()

#Color and Brigtness  LED bicolor display
brightness = 12


#=========================================================================
#-O2 & CO2 Bargraph LED---------------------------------------------------
#=========================================================================

#Creating a variable to reference libraries according to address
o2display = BicolorBargraph24.BicolorBargraph24(address=0x71)
Co2display = BicolorBargraph24.BicolorBargraph24(address=0x74)

# Initialize the display. 
o2display.begin()
Co2display.begin()
o2display.write_display()
Co2display.write_display()


#=========================================================================
#-Seven Segment LED-------------------------------------------------------
#=========================================================================

#Creating a variable to reference libraries for altitude, roll, and, yaw

displayaltitude = SevenSegment.SevenSegment(address=0x75)
#displayroll = SevenSegment.SevenSegment(address=0x74)
displayyaw = SevenSegment.SevenSegment(address=0x72)

#calling write and intitalize functions from libraries

displayaltitude.write_display()
#displayroll.write_display()
displayyaw.write_display()

displayaltitude.begin()
#displayroll.begin()
displayyaw.begin()

#no colon
colon = False


##########################################################################
######################Variables and States################################
##########################################################################

#=========================================================================
#-Booster Bargraph LED-------------------------------------------------------------
#=========================================================================

#Establishing Boolean states, ranges, variables, file names, and supportive variables
#check if the threads are already running (for GPIO) and booster level
booster_state=False

booster_recharge_state = False
booster_level = 0


g = BicolorBargraph24.GREEN
y = BicolorBargraph24.YELLOW
r = BicolorBargraph24.RED
b = BicolorBargraph24.OFF

#LED arrays used to set color and level after Booster Use.
booster_led = [r, r, r, r, y, y, y, y, y, y, y, y, y, y, y, y, g, g, g, g, g, g, g, g]

led_2 = [r, r, r, r, y, y, y, y, y, y, y, y, y, y, y, y, g, g, g, g, b, b, b, b]

led_3 = [r, r, r, r, y, y, y, y, y, y, y, y, y, y, y, g, b, b, b, b, b, b, b, b]

led_4 = [r, r, r, r, y, y, y, y, y, y, y, y, b, b, b, b, b, b, b, b, b, b, b, b]

led_5 = [r, r, r, r, y, y, y, y, b, b, b, b, b, b, b, b, b, b, b, b, b, b, b, b]

led_b = [b, b, b, b, b, b, b, b, b, b, b, b, b, b, b, b, b, b, b, b, b, b, b, b]

"""
#=========================================================================
#-Alarm Panel-------------------------------------------------------------
#=========================================================================

#will have to esbalish boolean state here for alarm panel use
"""


#=========================================================================
#-Mission States-------------------------------------------------------------
#=========================================================================

"""switch5_state = False
switch6_state = False
switch13_state = False
switch19_state = False
switch15_state = False"""

#=========================================================================
#-Door -------------------------------------------------------------
#=========================================================================

door_status = GPIO.input(19)
door_boolean = 0

#=========================================================================
#----------------O2 & CO2 Bargraph LED------------------------------------
#=========================================================================
#check if the threads are already running (for GPIO)
RechargingOxygen=False
ReplacingCo2Scrubber=False

#global variable to track Oxygen Level, will be between 0 (empty) and 23 (full)
OxygenLevel = 0

#global variable to avoid multiple empty warnings, False if not alarmed / True if alarm already triggered 
OxygenEmptyKnown = False

#global variable to track Co2 Level, will be between 0 (empty) and 23 (full)
Co2Level = 0

#global variable to avoid multiple warnings, False if not alarmed / True if alarm already triggered 
Co2FullKnown = False

#LED arrays used to set color and level after during O2/CO2 Use and recharge.
g = BicolorBargraph24.GREEN
y = BicolorBargraph24.YELLOW
r = BicolorBargraph24.RED
b = BicolorBargraph24.OFF

o2ledON = [r, r, r, r, y, y, y, y, y, y, y, y, y, y, y, g, g, g, g, g, g, g, g, g]

Co2ledON = [g, g, g, g, g, y, y, y, y, y, y, y, y, y, y, r, r, r, r, r, r, r, r, r]


#=========================================================================
#--Seven Segments---------------------------------------------------------
#=========================================================================

#7 Segment numerical ranges and count down range
altitude_range = list(range(1500))
roll_range = list(range(281))
yaw_range = list(range(60))

count_down = [10,10,10,10, 9, 8, 8, 8, 7, 7, 6, 5, 5, 4, 4, 3, 2, 2, 1, 1, 0]

#setting up range for minor adjustments in roll and yaw. Fine to use the same in both since its just being referneced
index = 0
int_list = range(0,360)


altitude_range_land = list(reversed(range(850)))
#roll_range_land = list(reversed(range(10)))
yaw_range_land = list(reversed(range(15,50,1)))
yaw_range_nose_down = list(reversed(range(0,15)))


####################################################################################
##############################Define functions######################################
####################################################################################

#===================================================================================
#-Booster functions-----------------------------------------------------------------
#===================================================================================
#This is the ACTION variable that replaces the booster level LED display
"""TEMPORARILY COMMENTED TO COMBINE WITH BOOSTER RECHARGE
def replace_booster_action():
    powerupSound.play(loops=0)
    time.sleep(.5)
    for index, colour in enumerate(booster_led):
        count = 1
        os.system('') #unsure if I'll need this, may want to delete. Test later
        boosterdisplay.set_bar(index, colour)
        boosterdisplay.write_display()
        count += 1
        print index, colour, count
        time.sleep(.015)"""


#This calls the action depending on state
def booster_recharge():
    print booster_state
    booster_state = False
    something = True
    while something == True:
        global booster_state
        if(not booster_state):
            boostertest = GPIO.input(25)
            print boostertest
            while boostertest == 0:
                global boostertest
                print boostertest, 'waiting for button'                
            booster_state=True
            powerupSound.play(loops=0)
            time.sleep(.5)

            #this next bit fills the LED
            for index, colour in enumerate(booster_led):
                count = 1
                boosterdisplay.set_bar(index, colour)
                boosterdisplay.write_display()
                count += 1
                print index, colour, count
                time.sleep(.015)
            print booster_state
                
        if (booster_state):
            global counter
            while counter < 5:
                MySwitchA = bus.read_byte_data(DA_27,RegisterLatchA27)
                MySwitchB = bus.read_byte_data(DA_27,RegisterLatchA27)
                MySwitchC = bus.read_byte_data(DA_27,RegisterLatchA27)
                print counter, 'switches are ready'
                
                if MySwitchA & 0b10000000 == 0b10000000 or MySwitchB & 0b01000000 == 0b01000000 or MySwitchC & 0b00100000 ==0b00100000:
                    print "BLLLOMP1!"
                    counter += 1
                    print counter
                    boosterSound.play(loops=0)

                    if counter == 1:
                        xcount = 0
                        for index, colour in reversed(list(enumerate(led_2))):
                            boosterdisplay.set_bar(index, colour)
                            boosterdisplay.write_display()
                            print index, colour
                            xcount = xcount + 1
                    if counter == 2:
                        xcount = 0
                        for index, colour in reversed(list(enumerate(led_3))):
                            boosterdisplay.set_bar(index, colour)
                            boosterdisplay.write_display()
                            print index, colour
                            xcount = xcount + 1
                    if counter == 3:
                        xcount = 0
                        for index, colour in reversed(list(enumerate(led_4))):
                            boosterdisplay.set_bar(index, colour)
                            boosterdisplay.write_display()
                            print index, colour
                            xcount = xcount + 1
                    if counter == 4:
                        xcount = 0
                        for index, colour in reversed(list(enumerate(led_5))):
                            boosterdisplay.set_bar(index, colour)
                            boosterdisplay.write_display()
                            print index, colour
                            xcount = xcount + 1
                    if counter == 5:
                        xcount = 0
                        for index, colour in reversed(list(enumerate(led_b))):
                            boosterdisplay.set_bar(index, colour)
                            boosterdisplay.write_display()
                            print index, colour
            booster_state = False
        print booster_state
            
               

#Define interrupts for switches (on Pin 26). These are the callbacks that bring button presses (like replacing booster)
#to the booster interrupts that start the thread containing replace booster.     

        
def my_callback(channel):
    powerupSound.play(loops=0)
    for index, colour in enumerate(booster_led):
        count = 1
        os.system('')
        if count >= 1 and count < 23:
                boosterdisplay.set_bar(index, colour)
                boosterdisplay.write_display()
                count += 1
                print index, colour, count
    #limited_boost()
    boosterthread.start()

#this reads the button press and sets the level of remaining boost accorrdingly
"""def limited_boost():
    counter = 0
    while counter < 5:
        MySwitchA = bus.read_byte_data(DA_27,RegisterLatchA27)
        MySwitchB = bus.read_byte_data(DA_27,RegisterLatchA27)
        MySwitchC = bus.read_byte_data(DA_27,RegisterLatchA27)
        if MySwitchA & 0b10000000 == 0b10000000 or MySwitchB & 0b01000000 == 0b01000000 or MySwitchC & 0b00100000 ==0b00100000:
            print "BLLLOMP1!"
            counter += 1
            print counter
            boosterSound.play(loops=0)
            
            if counter == 1:
                xcount = 0
                for index, colour in reversed(list(enumerate(led_2))):
                    boosterdisplay.set_bar(index, colour)
                    boosterdisplay.write_display()
                    print index, colour
                    xcount = xcount + 1 
            if counter == 2:
                xcount = 0
                for index, colour in reversed(list(enumerate(led_3))):
                    boosterdisplay.set_bar(index, colour)
                    boosterdisplay.write_display()
                    print index, colour
                    xcount = xcount + 1
            if counter == 3:
                xcount = 0
                for index, colour in reversed(list(enumerate(led_4))):
                    boosterdisplay.set_bar(index, colour)
                    boosterdisplay.write_display()
                    print index, colour
                    xcount = xcount + 1
            if counter == 4:
                xcount = 0
                for index, colour in reversed(list(enumerate(led_5))):
                    boosterdisplay.set_bar(index, colour)
                    boosterdisplay.write_display()
                    print index, colour
                    xcount = xcount + 1
            if counter == 5:
                xcount = 0
                for index, colour in reversed(list(enumerate(led_6))):
                    boosterdisplay.set_bar(index, colour)
                    boosterdisplay.write_display()
                    print index, colour
                    xcount = xcount + 1"""

def start_up_action():
    powerupSound.play(loops=0)
    time.sleep(.5)
    for index, colour in enumerate(booster_led):
        count = 1
        boosterdisplay.set_bar(index, colour)
        boosterdisplay.write_display()
        count += 1
        print index, colour, count
        time.sleep(.015)
    

#=======================================================================================
#-O2 and CO2 functions------------------------------------------------------------------
#=======================================================================================
            
#THESE 2 FUNCTIONS ARE FOR SENSING THE o2 RECHARGE (Initiated by button press interrupt on pin 22)
##02interrupt is triggered whenever o2  button pressed, run quickly and start rechargeOxygen via a thread
def o2interrupt(channel):
        global RechargingOxygen
        if( not RechargingOxygen):
                RechargingOxygen=True
                o2_thread = threading.Thread(target=rechargeOxygen)
                o2_thread.start()
                print "STARTING OXYGEN RECHARGE!"
        else:
                print "WARNING : You are already recharging oxygen"

#...started via thread in interrupt code (only runs when button is pressed), increases OxygenLevel variable back to 23                       
def rechargeOxygen():
        global RechargingOxygen
        global OxygenLevel
        global OxygenEmptyKnown
        o2AlarmSound.stop()

        while (OxygenLevel < 23):
                OxygenLevel += 1
                try:
                        o2display.set_bar(OxygenLevel, o2ledON[OxygenLevel])
                        o2display.write_display()
                except IOError as e:
                        print "I/O error({0}): {1}".format(e.errno, e.strerror)
                except:
                        print "Unexpected error:", sys.exc_info()[0]

                time.sleep(.1)

        RechargingOxygen = False
        OxygenEmptyKnown = False
        print ('OXYGEN RECHARGE COMPLETE')
       
                       
#THESE 2 FUNCTIONS ARE FOR SENSING THE Co2 SCRUBBER REPLACEMENT (Iniated by button press interrupt)           
#Quickly run this...
def Co2interrupt(channel):
        global ReplacingCo2Scrubber
        if( not ReplacingCo2Scrubber):
                ReplacingCo2Scrubber=True
                o2_thread = threading.Thread(target=replaceCo2Scrubber)
                o2_thread.start()
                print "STARTING CO2 SCRUBBER REPLACEMENT!"
        else:
                print "WARNING : You are already replacing CO2 scrubber"

#...Which then starts this via a thread, drops Co2Level variable back to zero        
def replaceCo2Scrubber():
        global ReplacingCo2Scrubber
        global Co2Level
        global Co2FullKnown
        co2AlarmSound.stop()
        

        while (Co2Level > 0):
                Co2Level -= 1
                try:
                        Co2display.set_bar(Co2Level, b)
                        Co2display.write_display()
                except IOError as e:
                        print "I/O error({0}): {1}".format(e.errno, e.strerror)
                except:
                        print "Unexpected error:", sys.exc_info()[0]

                time.sleep(.1)

        ReplacingCo2Scrubber = False
        Co2FullKnown = False
        print ('CO2 SCRUBBER REPLACEMENT COMPLETE')


#started via a thread in main program loop (Co2 thread, always running, and always increasing Co2Level variable
def increaseCo2():
        try:
            GPIO.add_event_detect(23, GPIO.FALLING, callback = Co2interrupt, bouncetime=3000)
        except KeyboardInterrupt:
            GPIO.cleanup()
        global co2AlarmSound
        global ReplacingCo2Scrubber
        global Co2ledON
        global Co2Level
        global Co2FullKnown
        while(True):
                if(not ReplacingCo2Scrubber):
                        if (Co2Level == 23 and Co2FullKnown == False):
                                print "Your Co2 scrubber is toast! Replace your Co2 cartridge!"
                                co2AlarmSound.play(loops=3)
                                #os.system('aplay alarm1.wav &')
                                Co2FullKnown = True
                        elif (Co2Level >= 0 and Co2Level <= 23):
                                try:
                                        Co2display.set_bar(Co2Level, Co2ledON[Co2Level])
                                        Co2display.write_display()
                                        Co2Level += 1
                                except IOError as e:
                                        print "I/O error({0}): {1}".format(e.errno, e.strerror)
                                except:
                                        print "Unexpected error:", sys.exc_info()[0]
                time.sleep(1)


#started via a thread in main program loop (o2thread, always running and always decreasing OxygenLevel variable)
                
def useoxygen():
    try:
        GPIO.add_event_detect(24, GPIO.FALLING, callback = o2interrupt, bouncetime=3000)   
    except KeyboardInterrupt:
        GPIO.cleanup() 
    global o2AlarmSound
    global RechargingOxygen
    global OxygenLevel
    global OxygenEmptyKnown
    while(True):
            if(not RechargingOxygen):
                    if OxygenLevel == 0 and OxygenEmptyKnown == False:
                            print "You've run out of Oxygen! Replace your o2 Cartridge!"
                            o2AlarmSound.play(loops=3)
                            OxygenEmptyKnown = 1
                            #os.system('aplay alarm1.wav &')
                    elif (OxygenLevel >= 0 and OxygenLevel <= 23):
                            try:
                                o2display.set_bar(OxygenLevel, b)
                                o2display.write_display()
                                OxygenLevel -= 1
                            except IOError as e:
                                    print "I/O error({0}): {1}".format(e.errno, e.strerror)
                            except:
                                    print "Unexpected error:", sys.exc_info()[0]
            time.sleep(1)       



#======================================================================================
#-Display background function----------------------------------------------------------
#======================================================================================


#displays background----------------------#
def display_nasa():
    global nasa_logo
    width = 1920
    height = 1080
    pygame.init()
    nasa = pygame.display.set_mode((width,height))
    pygame.display.set_caption("Nate's NASA Shuttle")
    image = pygame.image.load(nasa_logo)
    image = pygame.transform.scale(image,(width,height))
    nasa.blit(image,(0,0))
    pygame.display.update()
    time.sleep(0.01)



#======================================================================================
#-Launch functions---------------------------------------------------------------------
#======================================================================================

#count down function ----------------------#
def start_count():
    for c in count_down:
        # Clear the display buffer.
        displayaltitude.clear()
        #displayroll.clear()
        displayyaw.clear()
        # Print a floating point number to the display.
        displayaltitude.print_float(c, decimal_digits=0)
        #displayroll.print_float(c, decimal_digits=0)
        displayyaw.print_float(c, decimal_digits=0)
        # Set the colon on or off (True/False).
        displayaltitude.set_colon(colon)
        #displayroll.set_colon(colon)
        displayyaw.set_colon(colon)
        # Write the display buffer to the hardware.  This must be called to
        # update the actual display LEDs.
        displayaltitude.write_display()
        #displayroll.write_display()
        displayyaw.write_display()
        # Delay for a second.
    
        time.sleep(1)


#altitude function runs through altitude_range above-----------#
def altitude():
    try:
        for currentalt in altitude_range:
            displayaltitude.clear()
            displayaltitude.write_display()
            displayaltitude.print_float(currentalt, decimal_digits=0)
            displayaltitude.set_colon(colon)
            displayaltitude.write_display()
            time.sleep(.05)
    except KeyboardInterrupt:
        
        GPIO.cleanup()

#yaw function runs through yaw_range variable above -------------#
def yaw():
    try:
        for currentyaw in yaw_range:
            displayyaw.clear()
            displayyaw.write_display()
            displayyaw.print_float(currentyaw, decimal_digits=1)
            displayyaw.set_colon(colon)
            displayyaw.write_display()
            time.sleep(1.5)
    except KeyboardInterrupt:
        GPIO.cleanup()


#roll function runs through roll_range variable above------------#

"""def roll():
    try:
        for currentroll in roll_range:
            #displayroll.clear()
            #displayroll.write_display()
            #displayroll.print_float(currentroll, decimal_digits=1)
            #displayroll.set_colon(colon)
            #displayroll.write_display()
            time.sleep(.5)
    except KeyboardInterrupt:
        GPIO.cleanup()"""
        

#launch function and call to video----------# 
def launch_p5():
    #os.system('omxplayer liftoff.mp4')
    print ('WE HAVE LIFTOFF!!')

def liftoff(channel):
    GPIO.cleanup()
    print ('WE HAVE LIFTOFF!!')
    global start_count
    
    p1_launch = threading.Thread(target=altitude)
    #p2_launch = threading.Thread(target=roll)
    p3_launch = threading.Thread(target=yaw)
    p4_launch = threading.Thread(target=start_count)
    p5_launch = threading.Thread(target=launch_p5)

    p5_launch.start()
    time.sleep(1)
    p4_launch.start()
    time.sleep(23)
    p1_launch.start()
    time.sleep(15)
    #p2_launch.start()
    time.sleep(1)
    p3_launch.start()

"""def launch_status_go(channel):

    try:
        GPIO.add_event_detect(17,GPIO.RISING, callback = liftoff, bouncetime=2000)
        
    except KeyboardInterrupt:
        GPIO.cleanup()"""

#======================================================================================
#-Landing functions---------------------------------------------------------------------
#======================================================================================

#-------------altitude_land function runs through altitude_range above-----------#
def altitude_land():
    for i in altitude_range_land:
            displayaltitude.clear()
            displayaltitude.print_float(i, decimal_digits=0)
            displayaltitude.set_colon(colon)
            displayaltitude.write_display()
            time.sleep(.05)

#-------------roll_land function runs through roll_range variable above------------#

"""def roll_land():
    for j in roll_range_land:
            #displayroll.clear()
            #displayroll.print_float(j, decimal_digits=1)
            #displayroll.set_colon(colon)
            #displayroll.write_display()
            time.sleep(.25)"""

        
#-------------yaw_land function runs through yaw_range variable above -------------#
def yaw_land():
    for k in yaw_range_land:
            displayyaw.clear()
            displayyaw.print_float(k, decimal_digits=1)
            displayyaw.set_colon(colon)
            displayyaw.write_display()
            time.sleep(.7)

def yaw_nose_down():
    for l in yaw_range_nose_down:
            displayyaw.clear()
            displayyaw.print_float(l, decimal_digits=1)
            displayyaw.set_colon(colon)
            displayyaw.write_display()
            time.sleep(.8)

#sound effect for parachute deployment - will need a new sound (or may edit new sound to movie)
def parachute_sound():
    parachute.play(loops=0)
    

#--------------landing function and call to video----------# 

def landing_p1_video():
    #os.system('omxplayer Landing.mp4')
    print ('Prepare for landing')

def landing(channel):
    GPIO.cleanup()

    p1_land = threading.Thread(target=landing_p1_video)
    p2_land = threading.Thread(target=altitude_land)
    #p3_land = threading.Thread(target=roll_land)
    p4_land = threading.Thread(target=yaw_land)
    p5 = threading.Thread(target = yaw_nose_down)
    p6 = threading.Thread(target = parachute_sound)
    
    p1_land.start()
    time.sleep(1)
    p2_land.start()
    time.sleep(1)
    p3_land.start()
    time.sleep(1)
    p4_land.start()
    time.sleep(51)
    p5.start()
    time.sleep(5)
    p6.start()

#After GPIO 7 is switched on, this call back is "activated" so that a button press will start the landing function
def landing_status_go(channel):
    try:
        GPIO.add_event_detect(7,GPIO.RISING, callback = landing, bouncetime=2000)
    except KeyboardInterrupt:
        GPIO.cleanup()

#======================================================================================
#-Roll and Yaw adjustment functions----------------------------------------------------
#======================================================================================


"""#rotation adjustment functions----------#
def plus_rotation(channel):
    #displayroll.clear()
    #displayroll.write_display()
    global index
    global image
    global int_list
    print int_list[index]
    index =  index + 1
    global adjustsound
    adjust.play(loops=0)
    #displayroll.print_float(int_list[index], decimal_digits=1)
    #displayroll.set_colon(colon)
    #displayroll.write_display()

def minus_rotation(channel):
    #displayroll.clear()
    #displayroll.write_display()
    global index
    global int_list
    print int_list[index]
    index =  index - 1
    global adjustsound
    adjust.play(loops=0)
    #displayroll.print_float(int_list[index], decimal_digits=1)
    #displayroll.set_colon(colon)
    #displayroll.write_display()
"""
#yaw adjustment functions----------#

def plus_yaw(channel):
    displayyaw.clear()
    displayyaw.write_display()
    global index
    global int_list
    print int_list[index]
    index =  index + 1
    global adjustsound
    adjust.play(loops=0)
    displayyaw.print_float(int_list[index], decimal_digits=1)
    displayyaw.set_colon(colon)
    displayyaw.write_display()

def minus_yaw(channel):
    displayyaw.clear()
    displayyaw.write_display()
    global index
    global int_list
    print int_list[index]
    index =  index - 1
    global adjustsound
    adjust.play(loops=0)
    displayyaw.print_float(int_list[index], decimal_digits=1)
    displayyaw.set_colon(colon)
    displayyaw.write_display()


#=========================================================================
#-Mission functions------------------------------------------
#=========================================================================
"""
#a callback function to set the boolean states to the pin value
def switch5_status(channel):
    global switch5_state
    global switch6_state
    switch5_state = GPIO.input(5)
    print switch5_state, ('on 5')

#a callback function to set the boolean states to the pin value
def switch6_status(channel):
    global switch6_state
    global switch5_state
    switch6_state = GPIO.input(6)
    print switch6_state, ('on 6')

#a callback function to set the boolean states to the pin value
def switch13_status(channel):
    global switch13_state
    switch13_state = GPIO.input(13)
    print switch13_state, ('on 13')

def switch19_status(channel):
    global switch19_state
    switch19_state = GPIO.input(19)
    print switch19_state, ('on 19')

def switch15_status(channel):
    global switch15_state
    switch15_state = GPIO.input(15)
    print switch15_state, ('on 15')

#this is the function that determines whether the correct settings (i.e. the 3-4
#switches) are applied. If they aren't then it makes suggestions to turn on whats missing
def launch_mars_probe(channel):
    global switch5_state
    global switch6_state
    if switch5_state == True and switch6_state == True:
        #this extend sound is just a testing sound and will get replaced by video soon
        extend.play(loops=0)
        switch6_state=False
        switch5_state=False
    elif switch5_state == True and switch6_state != True:
        print ('please turn on your switch6_state switch')
    elif switch5_state != True and switch6_state == True:
        print ('please turn on your switch5_state switch')
    elif switch5_state != True and switch6_state != True:
        print ('please check settings and turn on switch5_state and switch6_state')

"""

def mission(channel):
    value = random.randint(1,7)
    global movie1
    if value == 1:
        Popen(['omxplayer', '-b', mars_mission])
    """elif value == 2:
        Popen(['omxplayer', '-b', [other mission video name here])
    """

def mission_status_go(channel):
    try:
        GPIO.add_event_detect(14,GPIO.RISING, callback = mission, bouncetime=2000)
    except KeyboardInterrupt:
        GPIO.cleanup()
        
        
#=========================================================================
#-Camera functions------------------------------------------
#=========================================================================

def open_camera(channel):
    value = random.randint(1,7)
    global movie1
    if value == 1:
        Popen(['omxplayer', '-b', movie1])
    elif value == 2:
        Popen(['omxplayer', '-b', movie2])
    elif value == 3:
        Popen(['omxplayer', '-b', movie3])
    elif value == 4:
        Popen(['omxplayer', '-b', movie4])
    elif value == 4:
        Popen(['omxplayer', '-b', movie5])
    elif value == 4:
        Popen(['omxplayer', '-b', movie6])

def close_camera(channel):
    os.system('killall omxplayer.bin')

#=========================================================================
#-Door functions--------------------------------------------
#=========================================================================

def pod_bay_door(channel):
    global door_boolean, status
    door_boolean += 1
    if (door_boolean % 2) == 0:
        door.play(loops=0)
        door_alarm_light_on()
        print door_status
    
    else:
        door_alarm_light_off()

"""
#=========================================================================
#-Alarm Panel functions--------------------------------------------
#=========================================================================
#these functions are called when some module wants to communicate with the alarm panel
#TODO: will have to fix these so that I put in the correct light MCP23017 address and BANK
#Door shut alarm panel lights----------#


def power_alarm_light_on():
    bus.write_byte_data(DA_24,RegisterLatchA20,0x80)
    time.sleep(.2)
    bus.write_byte_data(DA_24,RegisterLatchA20,0x00)
    time.sleep(.2)
    bus.write_byte_data(DA_24,RegisterLatchA20,0x80)
    time.sleep(.2)
    bus.write_byte_data(DA_24,RegisterLatchA20,0x00)
    time.sleep(.2)
    bus.write_byte_data(DA_24,RegisterLatchA20,0x80)

def power_alarm_light_off(channel):
    global __________
    if ____________ == True:
        print ('turning off alarm panel light for main power')
        bus.write_byte_data(DA_24,RegisterLatchA20,0x00)
        time.sleep(2)

#Booster alarm panel lights----------#
def master_alarm_light_on():
    bus.write_byte_data(DA_24,RegisterLatchB20,0x80)
    time.sleep(.2)
    bus.write_byte_data(DA_24,RegisterLatchB20,0x00)
    time.sleep(.2)
    bus.write_byte_data(DA_24,RegisterLatchB20,0x80)
    time.sleep(.2)
    bus.write_byte_data(DA_24,RegisterLatchB20,0x00)
    time.sleep(.2)
    bus.write_byte_data(DA_24,RegisterLatchB20,0x80)
    
def master_alarm_light_off(channel):
    global booster_recharge_state
    if booster_recharge_state == True:
        print ('turning off alarm panel light for master alarm')
        bus.write_byte_data(DA_24,RegisterLatchB20,0x00)
        time.sleep(2)


def door_alarm_light_on():
    bus.write_byte_data(DA_24,RegisterLatchA20,0x20)
    time.sleep(.2)
    bus.write_byte_data(DA_24,RegisterLatchA20,0x00)
    time.sleep(.2)
    bus.write_byte_data(DA_24,RegisterLatchA20,0x20)
    time.sleep(.2)
    bus.write_byte_data(DA_24,RegisterLatchA20,0x00)
    time.sleep(.2)
    bus.write_byte_data(DA_24,RegisterLatchA20,0x20)

def door_alarm_light_off():
    print ('turning off alarm panel light for adjar door')
    bus.write_byte_data(DA_24,RegisterLatchA20,0x00)
    time.sleep(2)

#Booster alarm panel lights----------#
def booster_alarm_light_on():
    bus.write_byte_data(DA_24,RegisterLatchB20,0xFF)
    time.sleep(.2)
    bus.write_byte_data(DA_24,RegisterLatchB20,0x00)
    time.sleep(.2)
    bus.write_byte_data(DA_24,RegisterLatchB20,0xFF)
    time.sleep(.2)
    bus.write_byte_data(DA_24,RegisterLatchB20,0x00)
    time.sleep(.2)
    bus.write_byte_data(DA_24,RegisterLatchB20,0xFF)
    
def booster_alarm_light_off(channel):
    global booster_recharge_state
    if booster_recharge_state == True:
        print ('turning off alarm panel light for booster')
        bus.write_byte_data(DA_24,RegisterLatchB20,0x00)
        time.sleep(2)

#O2 alarm panel lights----------#
def O2_alarm_light_on():
    bus.write_byte_data(DA_24,RegisterLatchB20,0x40)
    time.sleep(.2)
    bus.write_byte_data(DA_24,RegisterLatchB20,0x00)
    time.sleep(.2)
    bus.write_byte_data(DA_24,RegisterLatchB20,0x40)
    time.sleep(.2)
    bus.write_byte_data(DA_24,RegisterLatchB20,0x00)
    time.sleep(.2)
    bus.write_byte_data(DA_24,RegisterLatchB20,0x40)

def O2_alarm_light_off(channel):
    global __________
    if ____________ == True:
        print ('turning off alarm panel light for oxygen')
        bus.write_byte_data(DA_24,RegisterLatchB20,0x00)
        time.sleep(2)

#CO2 alarm panel lights----------#
def CO2_alarm_light_on():
    #will have to specify new bank and light address according to its position on the MCP23017
    bus.write_byte_data(DA_24,RegisterLatchA20,0x40)
    time.sleep(.2)
    bus.write_byte_data(DA_24,RegisterLatchA20,0x00)
    time.sleep(.2)
    bus.write_byte_data(DA_24,RegisterLatchA20,0x40)
    time.sleep(.2)
    bus.write_byte_data(DA_24,RegisterLatchA20,0x00)
    time.sleep(.2)
    bus.write_byte_data(DA_24,RegisterLatchA20,0x40)

def CO2_alarm_light_off(channel):
    global __________
    if ____________ == True:
        print ('turning off alarm panel light for CO2')
        bus.write_byte_data(DA_24,RegisterLatchA20,0x40)
        time.sleep(2)
 """     
#######################################################################################
#####################Interupts and Callbacks###########################################
#######################################################################################
#TODO: might put all callbacks together here below. the section after this is where its separated


def set_Interrupts():
    try:

        #Launch arming. This is the arming interupt that calls on a function with an interupt for launch
        #GPIO.add_event_detect(4,GPIO.RISING, callback = launch_status_go, bouncetime=2000)
        GPIO.add_event_detect(17,GPIO.RISING, callback = liftoff, bouncetime=2000)

        
    
        #Camera. These two open randomly selected videos for external camera and then close it.
        GPIO.add_event_detect(12, GPIO.RISING, callback = open_camera, bouncetime=500)
        GPIO.add_event_detect(16, GPIO.RISING, callback = close_camera, bouncetime=500)
        
        

        #Adjusters
        GPIO.add_event_detect(22, GPIO.RISING, callback = plus_yaw, bouncetime=300)
        GPIO.add_event_detect(27, GPIO.RISING, callback = minus_yaw, bouncetime=300)

        """GPIO.add_event_detect(9, GPIO.RISING, callback = plus_rotation, bouncetime=300)
        GPIO.add_event_detect(10, GPIO.RISING, callback = minus_rotation, bouncetime=300)"""

        #Landing arming. This is the arming interupt that calls on a function with an interupt for landing
        GPIO.add_event_detect(8,GPIO.RISING, callback = landing_status_go, bouncetime=2000)

        """#This is the callback for the door opening and closing. 
        GPIO.add_event_detect(11, GPIO.RISING, callback = pod_bay_door, bouncetime=800)"""

        #Missions - mission status is a toggle, and then the following callbacks are 15 and 18 for start and next image
        GPIO.add_event_detect(15, GPIO.RISING, callback = mission_status_go , bouncetime=300)

        """#TODO this calls back to a next mission step function that is not developed
        GPIO.add_event_detect(18, GPIO.RISING, callback = _________ , bouncetime=300)"""
    
    except KeyboardInterrupt:
        GPIO.cleanup()   


#$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$#
#$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$START$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$#
#$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$#
#--------------------------START-----------------------------------------#
#---------A while loop will run until pin 17 state changes-----#
#---------Once changed, sctip will initiate call backs using try---------#
#Starts up Booster







test = GPIO.input(4)
print test
while test == 0:
    print test
    test = GPIO.input(4)
    time.sleep(1)


#Configures and sets ALL buttons for interrupts
set_Interrupts()


#FILL UP o2
for index, colour in enumerate(o2ledON):
    o2display.set_bar(index, colour)
    o2display.write_display()
    time.sleep(.1)
    print "o2 level : ",index
OxygenLevel = 23



#START DECREASING o2 AND INCREASING Co2.
o2thread = threading.Thread(target=useoxygen)
Co2thread = threading.Thread(target=increaseCo2)
boosterthread = threading.Thread(target=booster_recharge)


#limited_boostthread = threading.Thread(target=limited_boost)


#boosterthread.start()
#limited_boostthread.start()
counter = 0
Co2thread.start()
o2thread.start()
boosterthread.start()
#limited_boostthread.start()

#KEEP PROCESSOR ALIVE
while(1):
    time.sleep(1)

#Displays background
#display_nasa()



#this gives Nate 10 seconds or so to launch the shuttle before the Boosters become available o2/co start.
#may want to debate how this will play out. It'll look cool that everything boosts up
#but unsure on whether it makes sense to boost early on.
#time.sleep(10)






