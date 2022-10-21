
" WE WILL IMPORT GPIO FOR RPI USE ONLY ! COMMENT THIS ALWAYS EXCEPT FOR RPI"
# import RPi.GPIO as GPIO
# GPIO.setwarnings(False) # Ignore warning for now
# GPIO.setmode(GPIO.BCM) # Use BCM pin numbering i.e the GPIOs not the physical
# GPIO.setup(20, GPIO.OUT, initial=GPIO.LOW) # Set GPIO 20 to be an output pin and set initial



# WE IMPORT PYSIDE2
from PySide2 import QtCore, QtGui, QtWidgets,QtUiTools
#from PyQt5 import QtCore
# WE IMPORT THE MAINWINDOW APLLICATION CLASS
#from Thermo_Ui import*
from Thermo_Ui import*
# IMPORT SYSTEM TOOLS
import  sys
# IMPORT THE MQTT CLIENT
import paho.mqtt.client as mqqt
# IMPORT TIME FUNCTION TO HANDLE TRANSMISSION INTERVALS
from time import sleep
# WE IMPORT CSV FOR DATA SAVER
import csv

# WE IMPORT JSON FOR DUMPS AND LOADS
import json
"NOW DECLARE GLOBAL VARIABLES"

# FOR CLIENT TO THROW DISCONNECTION ERROR THE BROKER MANAGES
# THE NOTIFICATION AND WILL BE TRIGGER  AUTOMATICALLY AFTER 1.5 TIMES THE
# KEEPALIVE IS INACTIVE
# THE BROKER MANAGE THE PINGRESP FROM PINGREQ PACKECT
keepalive = 40   # APPROXMATELY 60 Sec (1.5*40)

# PUT YOUR BROKER IP / ADDRESS HERE
#broker = "192.168.54.33"
broker = "192.168.88.242"


# PORT NUMBER TO LISTEN TO 641203207
port = 1883
" IF YOU NEED TO SETUP A USERNAME AND PASSWORD GOTO LINE 881 "

# WE CONNECT TO TASMOTA TEMPERATURE DATA
Tasmota = "tele/tasmota_CEE9D5/SENSOR"


# WE SUBCRIBE TO GET TEMPERATURE DATAS
SubTempTopic = "Nymea/Temp"

# WE SUBSCRIBE TO GET HUMIDTY DATAS
SubHumTopic = "Nymea/Hum"
# WE PUBLISH TO THIS TO TURN ON THE TEMP RELAY
PubRly1Topic = "temp1relay1"
# WE PUBLISH TO THIS TO TURN ON HUM RELAY
PubRly2Topic = "Nymea/Rly2/Pub"
# WE SUBSCRIBE TO CONFIRM IF TEMP RELAY IS WORKING FINE MAKE SURE YOU PUBLISH FROM THE DEVICE TO THIS TOPIC
SubRly1Topic = "temperature1"
# WE SUBSCRIBE TO CONFIRM IF HUM RELAY IS WORKING FINE MAKE SURE YOU PUBLISH FROM THE OTHER DEVICE TO THIS TOPIC
SubRly2Topic = "Nymea/Rly2/Sub"
# WE SUBCRIBE TO MAKE SURE F1 WORKING BEFORE CHANGING STATE MAKE SURE YOU PUBLISH FROM THE OTHER DEVICE TO THIS TOPIC
F1_Sub_Topic = "F1buttonCollor"
# WE PUBLISH WITH F1 BUTTON ( ANYTHING YOU LIKE )
F1_Pub_Topic = "Nymea/F1/LED"
#WE SUBSCRIBE TO GPI0_21 TO CHECK ITS STATE
GPIO_21 =  "GPIO21/msg/Sub"

#WE PUT ALL THE TOPICS TO SUBSCRIBE TO IN A LIST
sus_ = [SubTempTopic,SubHumTopic,SubRly2Topic,SubRly1Topic,
        F1_Sub_Topic,GPIO_21,Tasmota]

# WE SET UP COUNT AND COUNTER FOR LOW AND HIGH METHOD
" SINCE WE CAN'T UNSUBCRIBE FROM BROKER PER PACKECT RECEIVED WE DEFINE METHOD TO HANDLE LOCAL " \
"SUBSCRIPTON AND UNSUBCRIPTION WHEN COUNT AND COUNTER IS TRUE OR FALSE"
count = 0
counter= 0

# Monitor the Disconection of broker and GUi
client_disconnect = False
# Monitor the connection of GUI
client_connect  = False

# Montior the connection establishment between the broker and GUI making sure the Ip and address is correct
noSignal  = False

# Trigger the Relay Inversion
Relay_inverted_Temp = False
Relay_inverted_Hum = False

class MainWindow(QMainWindow):

    "WE DECLARE GLOBAL VARIABLE WITHIN THE CLASS"

    # GLOBAL VARIABLE FOR TEMPERATURE SETTING
    tem_start = 0

    # GLOBAL VARIABLE FOR HUMIDITY SETTING
    hum_start =0



    # GLOBAL VARIABLE FOR TEMPERATURE SETTING STATUS BEFORE PUBLISHING IS ALWAYS BETWEEN (0 and 1)
    Temp_Status = 0
    # GLOBAL VARIABLE FOR HUMIDTY SETTING STATUS BEFORE PUBLISHING IS ALWAYS BETWEEN (0 and 1)
    Hum_Status = 0
    #print(HumValue(payload))

    myPopUp = QtCore.Signal(str)
    ## WE WOULD SAVE DATA AND RECOLLET IT BACK
    Temp_Max_file = 'data/Temp1.csv'
    Temp_Min_file = 'data/Temp2.csv'
    Hum_Max_file = 'data/Hum1.csv'
    Hum_Min_file = 'data/Hum2.csv'
    Temp_Relay_Invert = 'data/rly_temp_invert.csv'
    Hum_Relay_Invert = 'data/rly_hum_invert.csv'
    Temp_MaxValue_file = "data/temp_maxValue.csv"
    Hum_MaxValue_file = "data/hum_maxValue.csv"
    Temperature_Differenece ="data/tem_diff.csv"
    Humidty_Differenece ="data/tem_diff.csv"



    def __init__(self):

        #QMainWindow.__init__(self)
        super(MainWindow,self).__init__()
        self.ui = Ui_THERMOSTAT()
        self.ui.setupUi(self)


        # SHOW WINDOW APPLICATION
        self.show()

        # SET CURRENT PAGE TO HOME
        self.ui.home.setCurrentWidget(self.ui.Home)

        # SET THE HOME PAGE TITLE
        self.ui.home_title.setText("MQQT THERMO GUI")

        #SET THE SENSOR PAGE TITLE
        self.ui.sensor_title.setText("THERMOSTAT  SENSOR ")

        # SET THE  TEMPERATUURE LABEL TEXT
        self.ui.temp_label.setText("Food Area Fridge")
        self.ui.temp_label_2.setText(self.ui.temp_label.text())
        #self.ui.temp_label_3.setText(self.ui.temp_label.text())

        # SET THE  HUMIDITY LABEL TEXT
        self.ui.hum_label.setText("Fridge Diary")
        self.ui.hum_label_2.setText(self.ui.hum_label.text())
        #self.ui.hum_label_3.setText(self.ui.hum_label.text())

        # INSTANCE FOR BUTTON ACTION AND SIGNALS
        self.ui.NextBtn.clicked.connect(self.Next_page)
        self.ui.PreviuosBtn.clicked.connect(self.Previous_page)
        # SET THE PREVIOUS COLOUR TO NONE

        # ALWAYS DSIABLE THE PREVIOUS BUTTON ON START
        self.ui.PreviuosBtn.setDisabled(True)
        self.ui.PreviuosBtn.setStyleSheet('color: transparent ; '
                                          'border :none;background-color:none;')

        # DELETE THE NEXT AND PREVIOUS PAGE FOR NOW
        self.ui.label_17.setText("")


        # CREATE FUNCTION FOR TEMP AND HUM BUTTON
        self.ui.Temp_btn.clicked.connect(self.Next_page)
        self.ui.Hum_btn.clicked.connect(self.Next_page)


        # DISABLE SET MAX AND MIN TEMP BTN AND ENABLE IT WITH SET BTN
        self.ui.SetMax_Temp_btn.setDisabled(True)
        self.ui.SetMin_Temp_btn.setDisabled(True)

        # DISABLE SET MAX AND MIN HUM BTN AND ENABLE IT WITH SET BTN
        self.ui.SetMax_Hum_btn.setDisabled(True)
        self.ui.SetMin_Hum_btn.setDisabled(True)


        # DISABLE THE TEMP AT THE START BTN AND RENABLE WITH SETHUM FUNCTON
        self.ui.Up_Temp_btn.setDisabled(True)
        self.ui.Down_Temp_btn.setDisabled(True)
        self.ui.SetMax_Temp_btn.clicked.connect(self.setMaxTemp)
        self.ui.SetMin_Temp_btn.clicked.connect(self.setMinTemp)
        self.ui.SetDifference_Temp_btn.clicked.connect(self.setDiffTemp)



        # DISABLE THE HUMIDTY AT THE START BTN AND RENABLE WITH SETHUM FUNCTON
        self.ui.Up_Hum_btn.setDisabled(True)
        self.ui.Down_Hum_btn.setDisabled(True)
        self.ui.SetMax_Hum_btn.clicked.connect(self.setMaxHum)
        self.ui.SetMin_Hum_btn.clicked.connect(self.setMinHum)
        self.ui.SetDifference_Hum_btn.clicked.connect(self.setDiffHum)

        #  BTN MANAGMENT FOR HUMIDTY AND TEMPERATURE TRIGGER SETTING
        self.ui.Set_Temp_btn.clicked.connect(lambda :self.SetBtn("Temperature"))
        self.ui.Set_Hum_btn.clicked.connect(lambda :self.SetBtn('Humidity'))

        # CONNECT THE NAVIGATION BTN TO FUNCTION
        self.ui.Up_Hum_btn.clicked.connect(lambda :self.Hum_settings("Up"))
        self.ui.Down_Hum_btn.clicked.connect(lambda: self.Hum_settings("Down"))
        self.ui.Up_Temp_btn.clicked.connect(lambda :self.Temp_settings('Up'))
        self.ui.Down_Temp_btn.clicked.connect(lambda: self.Temp_settings("Down"))

        # INITIALISE THE TARGET TEMPERATURE
        self.ui.Up_Max_Temp.clicked.connect(lambda : self.Temp_settings("Up_Max"))
        self.ui.Down_Max_Temp.clicked.connect(lambda: self.Temp_settings("Down_Max"))

        # INITIALISE THE TARGET Humidity
        self.ui.Up_Max_Hum.clicked.connect(lambda: self.Hum_settings("Up_Max"))
        self.ui.Down_Max_Hum.clicked.connect(lambda: self.Hum_settings("Down_Max"))


       # SET THE BAR STYLE (Example: Donet, Line,Pie, Pizza,Pie,Hybrid1,Hybrid2
        self.ui.widget_5.rpb_setBarStyle('Hybrid1')
        self.ui.widget_6.rpb_setBarStyle('Hybrid1')

        # SET PROGRESS BAR LINE CAP
        self.ui.widget_5.rpb_setLineCap('SquareCap')
        self.ui.widget_6.rpb_setLineCap('SquareCap')

       # SET PROGRESS BAR LINE COLOR
        self.ui.widget_5.rpb_setLineColor ((255, 40, 43)) # ARGUMENT RGB AS TUPLE
        self.ui.widget_6.rpb_setLineColor((41, 66, 255))  # ARGUMENT RGB AS TUPLE

        # SET PROGRESS BAR PATH COLOR
        self.ui.widget_5.rpb_setPathColor((44, 44, 44))  # ARGUMENT RGB AS TUPLE
        self.ui.widget_6.rpb_setPathColor((44, 44, 44))

        # SET PROGRESS BAR LINE STYLE
        self.ui.widget_5.rpb_setLineStyle('DotLine')
        self.ui.widget_6.rpb_setLineStyle('DotLine')

        # SET BAR PATH WIDTH
        self.ui.widget_5.rpb_setLineWidth(10)  # ARGUMENT RGB AS TUPLE
        self.ui.widget_6.rpb_setLineWidth(10)

        # SET PROGRESS BAR LiNE WIDTH
        self.ui.widget_5.rpb_setPathWidth(10)  # ARGUMENT RGB AS TUPLE
        self.ui.widget_6.rpb_setPathWidth(10)

       # SET PROGRESS BAR Text COLOR
        self.ui.widget_5.rpb_setTextColor ((255, 255, 255)) # ARGUMENT RGB AS TUPLE
        self.ui.widget_6.rpb_setTextColor((255, 255, 255))


      # SET BAR PROGRESS TEXT TYPE : VALUE OR PERCENTAGE
        self.ui.widget_5.rpb_setTextFormat('Value')
        self.ui.widget_5.rpb_setTextFont('Arial')
        self.ui.widget_5.rpb_setCircleColor((28, 23, 36))  # ARGUMENT RGB AS A TUPLE
        self.ui.widget_6.rpb_setTextFormat('Value')
        self.ui.widget_6.rpb_setTextFont('Arial')
        self.ui.widget_6.rpb_setCircleColor((28, 23, 36))  # ARGUMENT RGB AS A TUPLE

        # Circle:
        self.ui.widget_5.rpb_setCircleColor((12, 2, 33))  # ARGUMENT RGB AS A TUPLE
        self.ui.widget_6.rpb_setCircleColor((12, 2, 33))



        # DISABLE PROGRESS BAR TEXT
        self.ui.widget_5.rpb_enableText(False)
        self.ui.widget_6.rpb_enableText(False)

        # SETTING THE RANGE : MIN-0 & MAX:360
        # self.ui.widget_5.rpb_setRange(-30, 100)
        # self.ui.widget_6.rpb_setRange(1, 100)

        # SET PROGRESS BAR STARTING POS EXAPAMPLE (West, South, East, North)
        self.ui.widget_5.rpb_setInitialPos('West')
        self.ui.widget_6.rpb_setInitialPos('West')

         # SET A DEFAULT VALUE FOR WIDGET_5 AND WIDGET__6
        self.ui.widget_5.rpb_setValue(0)
        self.ui.widget_6.rpb_setValue(0)

        # INITIALISE F1 AND F2 BUTTONS
        self.ui.F1btn.clicked.connect(self.checkF1Button)
        self.ui.F2btn.clicked.connect(self.checkF2Button)


        # WE INITIALISE RELAY INVERSION
        self.ui.checkBox.clicked.connect(self.Relay_inversion)
        self.ui.checkBox_2.clicked.connect(self.Relay_inversion2)

        # WE CALL THE TEMPERATURE PRESET FUNCTION AND CONNECT IT TO A SIGNAL SLOT

        self.ui.Preset_I_Temp.clicked.connect(lambda : self.Temperature_Preset("I"))
        self.ui.Preset_N_Temp.clicked.connect(lambda : self.Temperature_Preset("N"))


        # WE CALL THE HUMIDTY PRESET FUNCTION AND CONNECT IT TO A SIGNAL SLOT

        self.ui.Preset_I_Hum.clicked.connect(lambda : self.Humidity_Preset("I"))
        self.ui.Preset_N_Hum.clicked.connect(lambda : self.Humidity_Preset("N"))


        # WE WILL USE QTIMER TO CALL OUR POP UP WINDOW SINCE IS FROM DIFFERENT THREAD
        " timer 1"
        self.timer1 = QTimer()
        self.timer1.setInterval(1000)
        self.timer1.timeout.connect(self.ManageThread1)
        self.timer1.start()

        " timer 2"
        self.timer2 = QTimer()
        self.timer2.setInterval(1000)
        self.timer2.timeout.connect(self.ManageThread2)
        self.timer2.start()

        " timer 3"
        # THIS PULL AND HANDLE MQTT CONNECTION
        self.timer3 = QTimer()
        self.timer3.setInterval(1000)
        self.timer3.timeout.connect(self.ManageThread3)
        self.timer3.start()

        " timer 4"
        # THIS PULL AND HANDLE NO SIGNAL
        self.timer4 = QTimer()
        self.timer4.setInterval(1000)
        self.timer4.timeout.connect(self.ManageThread4)
        self.timer4.start()

        # WE READ AND POUR MIN TEMPERATE  TRIGGER DATA
        with open(self.Temp_Min_file, 'r') as file:
            reader = csv.reader(file)

            for i in reader:
                #print(f"THE MINIMUM TEMP IS :{i[0]}")

                self.ui.MinTemVal.setText(f'{i[0]}')

        # WE READ AND POUR MAX TEMPERATE  TRIGGER DATA
        with open(self.Temp_Max_file, 'r') as file:
            reader = csv.reader(file)
            for i in reader:
             self.ui.MaxTempVal.setText(f'{i[0]}')
             self.ui.widget_5.rpb_setMaximum(int(i[0]))

        # WE READ AND POUR MAX Humidty  TRIGGER DATA
        with open(self.Hum_Max_file, 'r') as file:
            reader = csv.reader(file)
            for i in reader:
                self.ui.MaxHumVal.setText(f'{i[0]}')
                self.ui.widget_6.rpb_setMaximum(int(i[0]))
                print(f"The Max value of Hum is {i[0]}")

        # WE READ AND POUR Min TEMPERATE  TRIGGER DATA
        with open(self.Hum_Min_file, 'r') as file:
            reader = csv.reader(file)
            for i in reader:
                self.ui.MinHumVal.setText(f'{i[0]}')

       # WE READ AND THE TEMP RELAY INVERTER
        global Relay_inverted_Temp, Relay_inverted_Hum
        with open(self.Temp_Relay_Invert, 'r') as file:
            reader = csv.reader(file)
            for i in reader:
                if i[0] == 'True':
                    self.ui.checkBox.setChecked(True)
                    Relay_inverted_Temp = True
                else:

                   Relay_inverted_Temp = False
                   self.ui.checkBox.setChecked(False)

        with open(self.Hum_Relay_Invert, 'r') as file:
            reader = csv.reader(file)
            for i in reader:
                if i[0] == 'True':
                    self.ui.checkBox_2.setChecked(True)
                    Relay_inverted_Hum = True
                else:
                   self.ui.checkBox_2.setChecked(False)
                   Relay_inverted_Hum = False


            # # READ THE TMEP MAX VALUE
            with open(self.Temp_MaxValue_file, 'r') as file:
                reader = csv.reader(file)
                for i in reader:
                    self.temp_Max = int(i[0])
                    self.ui.TempValue.setText(f'{int(i[0])} °C')

            # # READ THE HUM MAX VALUE
            with open(self.Hum_MaxValue_file, 'r') as file:
                reader = csv.reader(file)
                for i in reader:
                    self.hum_Max = int(i[0])
                    self.ui. HumValue.setText(f'{int(i[0])} %')


            #
            # # POUR THE DIFFERENCE  Humidty DATA
            with open(self.Humidty_Differenece, 'r') as file:
                reader  =csv.reader(file)
                for i in reader:
                    self.ui.DiffHumVal.setText(i[0])
            #
            # # POUR THE DIFFERENCE Temp DATA
            with open(self.Temperature_Differenece, 'r')as file :
                reader  =csv.reader(file)
                for i in reader:
                    self.ui.DiffTemVal.setText(i[0])

# PRESET BUTTONS FOR TEMPERATURE




# THIS METHOD CALL THE GPIO 21 LOW POP UP
    number1 = 0
    def ManageThread1(self):
        global count,counter
        if count ==1 and self.number1 >2:
            #self.myPopUp.connect(self.PopUpWindow())
            self.PopUpWindow("LOW")
            self.number1=0
            self.timer2.start()
            self.timer1.stop()
        elif self.number1 > 100:
            self.number1 =0
        self.number1 = self.number1 + 1


# THIS METHOD CALL THE GPIO 21 HIGH POP UP
    number2 = 0
    def ManageThread2(self):
        global count,counter


        if counter ==1 and self.number2 > 2:
            self.PopUpWindow("HIGH")
            #self.myPopUp.connect(self.PopUpWindow())
            self.number2 =0
            self.timer2.stop()
            self.timer1.start()
        elif self.number2 > 100:
            self.number2 = 0
        # elif counter ==0 and self.number2 == 2:
        #     self.handleNoSignal()
        self.number2 = self.number2 + 1

## THIS METHOD CALL THE handleNoSignal Pop Up
    number3 =0
    def ManageThread3(self):
        global client_disconnect,noSignal
        if client_disconnect and self.number3 >2:
            self.handleNoSignal()
        elif noSignal  and self.number3 >2:
            self.noConnection()
            noSignal = False
        elif self.number3 > 100:
            self.number3 = 0
        self.number3= self.number3+1

## THIS METHOD CALL THE handleMQTTConnetion Pop Up
    number4 =0
    def ManageThread4(self):
        global client_connect
        if client_connect and self.number4 > 1:
            self.handleMQTTConnection()
        elif self.number4 > 100:
            self.number4 = 0
        self.number4 = self.number4+1

# PUT THE INVERSION TO TRUE
    def Relay_inversion(self):
        global Relay_inverted_Temp
        print(self.ui.checkBox.isChecked())
        if self.ui.checkBox.isChecked():
            Relay_inverted_Temp = True
            with open(self.Temp_Relay_Invert, 'w') as file:
                writer = csv.writer(file)
                writer.writerow([Relay_inverted_Temp])


        else:

            Relay_inverted_Temp = False
            with open(self.Temp_Relay_Invert, 'w') as file:
                writer = csv.writer(file)
                writer.writerow([Relay_inverted_Temp])

    # Relay Inversion for Hum
    def Relay_inversion2(self):
        global Relay_inverted_Hum
        if self.ui.checkBox_2.isChecked():
            Relay_inverted_Hum = True
            with open(self.Hum_Relay_Invert, 'w') as file:
                writer = csv.writer(file)
                writer.writerow([Relay_inverted_Hum])
        else:
            Relay_inverted_Hum = False
            with open(self.Hum_Relay_Invert, 'w') as file:
                writer = csv.writer(file)
                writer.writerow([Relay_inverted_Hum])



# SETTING UP THE PRESET BUTTON ## Memory 1 =  MAX Temp = 45, Difference =2 relay = True
    #     ## Memory 2 = Max Tem = 40 Difference = 1, Relay = false

    def Humidity_Preset(self, preset):
        global Relay_inverted_Hum
        msg = QMessageBox()

        if preset == "I":


            # We Make Sure the Relay of the Humidty is inverted when the used Press "I" and then save it
            Relay_inverted_Hum = True
            self.ui.checkBox_2.setChecked(True)
            with open(self.Hum_Relay_Invert, 'w') as file:
                writer = csv.writer(file)
                writer.writerow([Relay_inverted_Hum])



        # AFTER SETTING THE PRESET WE SAVE THE Hum_MAX (target value) AND CHANGE THE GUI TO THE VALUE to 45
            self.hum_Max = 45
            self.ui.HumValue.setText(f'{self.hum_Max} %')

            with open(self.Hum_MaxValue_file, 'w') as file:
                writer = csv.writer(file)
                writer.writerow([self.hum_Max])
            file.close

            # Lastly, we make changes to the difference and Then save it
            difference = 2
            self.ui.DiffTemVal.setText(f"{difference}")
            with open(self.Humidty_Differenece, 'w') as file:
                writer = csv.writer(file)
                writer.writerow([difference])


     # WE PRESET THE MAX HUMIDTY TOO
            self.ui.MaxHumVal.setText(f"{50}")
            with open(self.Hum_Max_file, 'w') as file:
                writer = csv.writer(file)
                writer.writerow([50])
            file.close

    # WE PRESE THE MIN HUMIDTY TOO
            self.ui.MinHumVal.setText(f"{10}")
            with open(self.Hum_Min_file, 'w') as file:
                writer = csv.writer(file)
                writer.writerow([10])
            file.close

            msg.setWindowTitle(f"Preset Alert")
            msg.setText("Humidty Preset")
            msg.setIcon(QMessageBox.Information)
            msg.setInformativeText("Dear user You have just initialised the Humidty for inverted mode")
            rec = msg.exec_()

        else:
             # We Assume the user pressed the opposite button therefore We set it to Default

             # We Make Sure the Relay of the Humidty is inverted when the used Press "I" and then save it
             Relay_inverted_Hum = False
             self.ui.checkBox_2.setChecked(False)
             with open(self.Hum_Relay_Invert, 'w') as file:
                 writer = csv.writer(file)
                 writer.writerow([Relay_inverted_Hum])

             # AFTER SETTING THE PRESET WE SAVE THE Hum_MAX (target value) AND CHANGE THE GUI TO THE VALUE to 45
             self.hum_Max = 40
             self.ui.HumValue.setText(f'{self.hum_Max} °%')

             with open(self.Hum_MaxValue_file, 'w') as file:
                 writer = csv.writer(file)
                 writer.writerow([self.hum_Max])
             file.close

             # Lastly, we make changes to the difference and Then save it
             difference = 1
             self.ui.DiffTemVal.setText(f"{difference}")
             with open(self.Humidty_Differenece, 'w') as file:
                 writer = csv.writer(file)
                 writer.writerow([difference])

             # WE PRESET THE MAX HUMIDTY TOO
             self.ui.MaxHumVal.setText(f"{50}")
             with open(self.Hum_Max_file, 'w') as file:
                 writer = csv.writer(file)
                 writer.writerow([50])
             file.close

             # WE PRESE THE MIN HUMIDTY TOO
             self.ui.MinHumVal.setText(f"{10}")
             with open(self.Hum_Min_file, 'w') as file:
                 writer = csv.writer(file)
                 writer.writerow([10])
             file.close

             msg.setWindowTitle(f"Preset Alert")
             msg.setText("Humidty Preset")
             msg.setIcon(QMessageBox.Information)
             msg.setInformativeText("Dear user You have just initialised the Humidty for Normal mode")
             rec = msg.exec_()

    def Temperature_Preset(self, preset):
        msg =QMessageBox()
        # I signify Inverter Relay While N signafiy Normal Relay working Condition

        global Relay_inverted_Temp
        if preset == "I":

         # We First make sure the relay is Inverted setting theRelay_inverted_Temp to True and saving it
            self.ui.checkBox.setChecked(True)
            Relay_inverted_Temp = True

            with open(self.Temp_Relay_Invert, 'w') as file:
                writer = csv.writer(file)
                writer.writerow([Relay_inverted_Temp])

        # AFTER SETTING THE PRESET WE SAVE THE TEMP_MAX (target value) AND CHANGE THE GUI TO THE VALUE to 45
            self.temp_Max = 45
            self.ui.TempValue.setText(f'{self.temp_Max} °C')


            with open(self.Temp_MaxValue_file, 'w') as file:
                writer = csv.writer(file)
                writer.writerow([self.temp_Max])
            file.close
        # Lastly, we make changes to the difference and Then save it
            difference = 2
            self.ui.DiffTemVal.setText(f"{difference}")
            with open(self.Temperature_Differenece, 'w') as file:
                writer = csv.writer(file)
                writer.writerow([difference])

        # WE PRE-SET THE MINIMUM TEMP TOO
            self.ui.MinTemVal.setText(f"{10}")
            with open(self.Temp_Min_file, 'w') as file:
                writer = csv.writer(file)
                writer.writerow([10])
            file.close
        # WE PRESET THE MAX TEMP TOO
            self.ui.MaxTempVal.setText(f"{50}")
            with open(self.Temp_Max_file, 'w') as file:
                writer = csv.writer(file)
                writer.writerow([50])
            file.close

            msg.setWindowTitle(f"Preset Alert")
            msg.setText("Temperature Preset")
            msg.setIcon(QMessageBox.Information)
            msg.setInformativeText("Dear user You have just initialised the Temperature for inverted mode")
            rec = msg.exec_()
        else:
            # We Assume the user pressed the opposite button therefore We set it to Default
            # We First make sure the relay is Normal setting theRelay_inverted_Temp to True and saving it
            self.ui.checkBox.setChecked(False)
            Relay_inverted_Temp = False

            with open(self.Temp_Relay_Invert, 'w') as file:
                writer = csv.writer(file)
                writer.writerow([Relay_inverted_Temp])

            # AFTER SETTING THE PRESET WE SAVE THE TEMP_MAX (target value) AND CHANGE THE GUI TO THE VALUE to 40
            self.temp_Max = 40
            self.ui.TempValue.setText(f'{self.temp_Max} °C')

            with open(self.Temp_MaxValue_file, 'w') as file:
                writer = csv.writer(file)
                writer.writerow([self.temp_Max])
            file.close
            # Lastly, we make changes to the difference and Then save it
            difference = 1
            self.ui.DiffTemVal.setText(f"{difference}")
            with open(self.Temperature_Differenece, 'w') as file:
                writer = csv.writer(file)
                writer.writerow([difference])

            # WE PRE-SET THE MINIMUM TEMP TOO
            self.ui.MinTemVal.setText(f"{10}")
            with open(self.Temp_Min_file, 'w') as file:
                writer = csv.writer(file)
                writer.writerow([10])
            file.close


            # WE PRESET THE MAX TEMP TOO
            self.ui.MaxTempVal.setText(f"{50}")
            with open(self.Temp_Max_file, 'w') as file:
                writer = csv.writer(file)
                writer.writerow([50])
            file.close


            msg.setWindowTitle(f"Preset Alert")
            msg.setText("Temperature Preset")
            msg.setIcon(QMessageBox.Information)
            msg.setInformativeText("Dear user You have just initialised the Temperature for Normal mode")
            rec = msg.exec_()



# CHECK F1 BUTTON WHEN IT IS PRESS TO PUBLISH AND CHANGE BUTTON STATE
    def checkF1Button(self):


        if self.ui.F1btn.isChecked():

            client.publish(F1_Pub_Topic,"ON", retain= True)
            sleep(1)


        else:
            #self.ui.F1btn.setStyleSheet('border :2px ;background-color:transparent; background-hover: yellow;')
            client.publish(F1_Pub_Topic, "OFF",retain= True)
            sleep(1)


    """F2 Is USED TO ACTIVATE GPIO 20 USING BCM AS A GPIO SETUP PLEASE 
    COMMENT THIS SECTION WHEN RUNNING ON OTHER OS APART FROM RPI
    """
    def checkF2Button(self):
     pass

        #
        # if self.ui.F2btn.isChecked():
        #     GPIO.output(20, GPIO.HIGH)
        #     self.ui.F2btn.setStyleSheet(
        #         'border :2px ;background-color:rgb(0, 253, 82)')
        #
        # else:
        #     self.ui.F2btn.setStyleSheet('border :2px ;background-color:transparent'
        #                                 'background-hover: yellow')
        #     GPIO.output(20, GPIO.LOW)

        # THIS HANDLE THE PACKET DATAS FROM THE HUMIDITY SENSOR
    def Handle_Humidty(self, payload):
        print(payload)

        # CHECK IF THE MAX HUMIDTY VALUE MEETS THE CONDITION SET
        #if int(payload) >= int(self.ui.MaxHumVal.text()) and self.Hum_Status == 0:
        if int(payload) >= self.hum_Max and self.Hum_Status == 0:
            self.Hum_Status = 1


        #elif self.Hum_Status == 1 and int(payload) > int(self.ui.MinHumVal.text()):
        elif self.Hum_Status == 1 and int(payload) > self.hum_Max - int(self.ui.DiffHumVal.text()):

            # TURN ON THE RELAY WHEN THE HUMIDTY VALUE REACHED THE MAX TRIGGER
            # THIS MEANS THAT FRIDGE WILL START WORKING BECAUSE IT IS HOT
            # WE WOULD PUBLISH ON TO THE BROKER AND THE CLIENT TEMPERATURE
            # RELAY WOULD SUBSCRIBE TO MAKE THE PIN HIGH
           # self.HumValue = self.HumValue - 1
            #self.RelayONStatus2()
            client.publish(PubRly2Topic, "ON",retain= True)
            sleep(1)
            self.ui.HumLcd.display('{:.01f}'.format(payload))
            self.ui.HumLcd_2.display(payload)
            self.ui.widget_6.rpb_setValue(payload)


        # CHECK IF THE MIN HUMIDTY VALUE MEETS THE CONDITION SET
        #elif payload <= int(self.ui.MinHumVal.text()) and self.Hum_Status == 1:
        elif payload <= self.hum_Max - int(self.ui.DiffHumVal.text()) and self.Hum_Status == 1:

            self.Hum_Status = 0




        else:

            # TURN OFF THE RELAY WHEN THE HUMIDTY VALUE REACHED THE MAX TRIGGER
            # THIS MEANS THAT FRIDGE WILL START WORKING BECAUSE IT IS HOT
            # WE WOULD PUBLISH ON TO THE BROKER AND THE CLIENT TEMPERATURE
            # RELAY WOULD SUBSCRIBE TO MAKE THE PIN LOW
           # self.HumValue = self.HumValue + 1
            client.publish(PubRly2Topic, "OFF",retain= True)
            sleep(1)
            self.ui.HumLcd.display('{:.01f}'.format(payload))
            self.ui.HumLcd_2.display(payload)
            self.ui.widget_6.rpb_setValue(payload)

    Hum_Status2 = 0

    def Handle_Humidty2(self, payload):
        print(payload)

        #if int(payload) >= int(self.ui.MaxHumVal.text()) and self.Hum_Status2 == 0:
        if int(payload) >= self.hum_Max and self.Hum_Status2 == 0:
            self.Hum_Status2 = 1

        #elif self.Hum_Status2 == 1 and int(payload) > int(self.ui.MinHumVal.text()):
        elif self.Hum_Status2 == 1 and int(payload) > self.hum_Max - int(self.ui.DiffHumVal.text()):

            client.publish(PubRly2Topic, "OFF", retain=True)
            sleep(1)
            self.ui.HumLcd.display('{:.01f}'.format(payload))
            self.ui.HumLcd_2.display(payload)
            self.ui.widget_6.rpb_setValue(payload)
        #elif payload <= int(self.ui.MinHumVal.text()) and self.Hum_Status2 == 1:
        elif payload <= self.hum_Max - int(self.ui.DiffHumVal.text()) and self.Hum_Status2 == 1:
            self.Hum_Status2 = 0

        else:

            client.publish(PubRly2Topic, 'ON', retain=True)
            sleep(1)
            self.ui.HumLcd.display('{:.01f}'.format(payload))
            self.ui.HumLcd_2.display(payload)
            self.ui.widget_6.rpb_setValue(payload) 


    # THIS HANDLES THE PACKET DATAS FROM THE TEMPERATURE SENSORS
    def Handle_Temperature(self,payload):
        print(payload)



            # CHECK IF THE MAX TEMPERATURE VALUE MEETS THE CONDITION SET
        #if  int(payload) >= int(self.ui.MaxTempVal.text()) and self.Temp_Status == 0:
        if int(payload) >= self.temp_Max and self.Temp_Status == 0:
            self.Temp_Status = 1

        # elif self.Temp_Status == 1 and int(payload) > int(self.ui.MinTemVal.text()) :
        elif self.Temp_Status == 1 and int(payload) > self.temp_Max - int(self.ui.DiffTemVal.text()):

             # TURN ON THE RELAY WHEN THE TEMPERATURE VALUE REACHED THE MAX TRIGGER
             # THIS MEANS THAT FRIDGE WILL START WORKING BECAUSE IT IS HOT
             # WE WOULD PUBLISH ON TO THE BROKER AND THE CLIENT TEMPERATURE
             # RELAY WOULD SUBSCRIBE TO MAKE THE PIN HIGH

            client.publish(PubRly1Topic, "ON",retain= True)
            sleep(1)

            """ ONCE THE CONDITIONS ARE MET WE USE 'self.publish(SubRly1Topic, "ON")' TO
             PUBLISH TO THE BROKER SO THAT IT CAN TRIGGER THE CONNECTED
              TEMPERATURE RELAY TO WORK, THEN GOTO THE ON_MESSAGE TO MAKE
              SURE THE RELAY HAS STATED WORKING
              """
            #self.RelayONStatus1()

            self.ui.TempLcd.display('{:.01f}'.format(payload))
            self.ui.TempLcd_2.display(payload)
            self.ui.widget_5.rpb_setValue(payload)


        # CHECK IF THE MIN TEMPERATURE VALUE MEETS THE CONDITION SET
        # elif payload <= int(self.ui.MinTemVal.text()) and self.Temp_Status == 1:
        elif payload <= self.temp_Max - int(self.ui.DiffTemVal.text()) and self.Temp_Status == 1:
            self.Temp_Status = 0




        else:

            # TURN OFF THE RELAY WHEN THE TEMPERATURE VALUE REACHED THE MAX TRIGGER
            # THIS MEANS THAT FRIDGE WILL START WORKING BECAUSE IT IS HOT
            # WE WOULD PUBLISH ON TO THE BROKER AND THE CLIENT TEMPERATURE
            # RELAY WOULD SUBSCRIBE TO MAKE THE PIN LOW
            #self.TempValue = self.TempValue + 1
            client.publish(PubRly1Topic, 'OFF',retain= True)
            sleep(1)
            self.ui.TempLcd.display('{:.01f}'.format(payload))
            self.ui.TempLcd_2.display(payload)
            self.ui.widget_5.rpb_setValue(payload)

    Temp_Status2 = 0
    def Handle_Temperature2(self,payload):
        print(payload)

        #if int(payload) >= int(self.ui.MaxTempVal.text()) and self.Temp_Status2 ==0:
        if int(payload) >= self.temp_Max and self.Temp_Status2 ==0:
               self.Temp_Status2 = 1

       # elif self.Temp_Status2 == 1 and  int(payload) > int(self.ui.MinTemVal.text()):
        elif self.Temp_Status2 == 1 and int(payload) > self.temp_Max - int(self.ui.DiffTemVal.text()):

            client.publish(PubRly1Topic, "OFF", retain=True)
            sleep(1)
            self.ui.TempLcd.display('{:.01f}'.format(payload))
            self.ui.TempLcd_2.display(payload)
            self.ui.widget_5.rpb_setValue(payload)
        #elif payload <= int(self.ui.MinTemVal.text()) and self.Temp_Status2 == 1:
        
        elif payload <= self.temp_Max - int(self.ui.DiffTemVal.text()) and self.Temp_Status2 == 1:
            self.Temp_Status2 =0

        else:

            client.publish(PubRly1Topic, 'ON', retain=True)
            sleep(1)
            self.ui.TempLcd.display('{:.01f}'.format(payload))
            self.ui.TempLcd_2.display(payload)
            self.ui.widget_5.rpb_setValue(payload)




   #SET DIFF TEMP SETTINGS
    def setDiffTemp(self):

        if (self.temp_Max) - (self.tem_start) >= int(self.ui.MinTemVal.text()) and  (self.temp_Max) - (self.tem_start) < self.temp_Max  :
            self.ui.DiffTemVal.setText(f"{self.tem_start}")
            with open(self.Temperature_Differenece, 'w') as file:
                writer  =csv.writer(file)
                writer.writerow([self.tem_start])

        else:

            msg = QMessageBox()
            msg.setWindowTitle(f" Alert")
            msg.setText("SET ERROR !!")
            msg.setStandardButtons(QMessageBox.Ok)
            msg.setDefaultButton(QMessageBox.Ok)
            msg.setInformativeText(f"The difference temperature can't be less than the Min Value or more than Target temperature")
            msg.setDetailedText("\n--> When you are setting you difference between the max and min value it should not be greater"
                                "than the minimum value\n Thanks !! ")
            msg.setIcon(QMessageBox.Warning)
            ret = msg.exec_()


    #SET DIFF HUM SETTINGS

    def setDiffHum(self):
        if (self.hum_Max) - (self.hum_start) >= int(self.ui.MinHumVal.text()) and  (self.hum_Max) - (self.hum_start) < self.hum_Max :
            self.ui.DiffHumVal.setText(f"{self.hum_start}")
            with open(self.Humidty_Differenece, 'w') as file:
                writer = csv.writer(file)
                writer.writerow([self.hum_start])


        else:

            msg = QMessageBox()
            msg.setWindowTitle(f" Alert")
            msg.setText("SET ERROR !!")
            msg.setStandardButtons(QMessageBox.Ok)
            msg.setDefaultButton(QMessageBox.Ok)
            msg.setInformativeText(f"The difference temperature can't be less than the Min Value  more than Target Humidty")
            msg.setDetailedText(
                "\n--> When you are setting you difference between the max and min value it should not be greater"
                "than the minimum value\n Thanks !! ")
            msg.setIcon(QMessageBox.Warning)
            ret = msg.exec_()

    # SET TEMP MINIMUM TRIGGER VALUE
    def setMinTemp(self):
        msg = QMessageBox()
        msg.setWindowTitle(f" Alert")
        msg.setText("Are You Sure ?")
        msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        msg.setDefaultButton(QMessageBox.Yes)
        msg.setInformativeText(f"Do you want to make changes to triggers threshold ?")
        msg.setDetailedText("Once you change the Min trigger threshold it will control the relay On/Off\n"
                            "make sure you what you are doing ! 🤓")
        msg.setIcon(QMessageBox.Question)
        ret = msg.exec_()

        if ret == QMessageBox.Yes:

            # CONFIRM IF MIN VALUE IS NOT EQUALS AND GREATER THAN MAX VALUE
            #if int(self.ui.MaxTempVal.text())!= self.tem_start and self.tem_start < int(self.ui.MaxTempVal.text()):
            if self.tem_start <= (self.temp_Max - int(self.ui.DiffTemVal.text())) and self.tem_start < self.temp_Max:
                # IF IS NOT THEN SET MiN TRIGGER VALUE
                self.ui.MinTemVal.setText(f"{self.tem_start}")
                self.ui.Set_Temp_btn.setDisabled(False)
                self.ui.SetMin_Temp_btn.setDisabled(True)
                #self.ui.widget_5.rpb_setMinimum(self.tem_start)


                with open(self.Temp_Min_file, 'w') as file:
                    writer = csv.writer(file)
                    writer.writerow([self.tem_start])
                file.close


            else:
                # IF IT IS  THEN DISPLAY POP UP MESSAGES AND DONT SET MIN TRIGGER VALUE
                msg.setText("MIN TRIGGER VALUE INVALID")
                msg.setWindowTitle(f" Alert")
                msg.setStandardButtons(QMessageBox.Ok)
                msg.setInformativeText(f"Hey the Min trigger value can't be equal or greater than max value")
                msg.setDetailedText("The Minimum Value should not be greater and equals to Max Value \n"
                                    "for example you can only set trigger value as \n MIN:2 AND MAX 4 ")
                msg.setIcon(QMessageBox.Warning)
                ret = msg.exec_()
        else:

            # DISABLE SET BUTTONS AFTER SUCCESSFULLY SET
            self.ui.Set_Temp_btn.setDisabled(True)
            self.ui.SetMin_Temp_btn.setDisabled(False)
            self.ui.MinTemVal.setText(self.ui.MinTemVal.text())
            #self.ui.widget_5.rpb_setMinimum(int(self.ui.MinTemVal.text()))

            with open(self.Temp_Min_file, 'w') as file:
                writer = csv.writer(file)
                writer.writerow(self.ui.MinTemVal.text())
            file.close

 # SET TEMPERATURE MAXIMUM VALUE
    def setMaxTemp(self):
# ENABLE THE NAVIGATION TEMP BTN

        self.ui.Up_Temp_btn.setDisabled(False)
        self.ui.Down_Temp_btn.setDisabled(False)
        # ENABLE SET BTN
        self.ui.Set_Temp_btn.setDisabled(False)
        msg = QMessageBox()
        msg.setWindowTitle(f" Alert")
        msg.setText("Are You Sure ?")
        msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        msg.setDefaultButton(QMessageBox.Yes)
        msg.setInformativeText(f"Do you want to make changes to triggers threshold ?")
        msg.setDetailedText("Once you change the Max trigger threshold it will control the relay On/Off\n"
                            "make sure you what you are doing ! 🤓")
        msg.setIcon(QMessageBox.Question)
        ret = msg.exec_()

        if ret == QMessageBox.Yes:

# CONFIRM IF MIN VALUE IS NOT EQUALS AND GREATER THAN MAX VALUE
            #if int(self.ui.MinTemVal.text()) != self.tem_start and self.tem_start > int(self.ui.MinTemVal.text()):
            if self.tem_start >= self.temp_Max:

                # IF IS NOT THEN SET MAX TRIGGER VALUE
                self.ui.MaxTempVal.setText(f"{self.tem_start}")
                self.ui.Set_Temp_btn.setDisabled(False)
                self.ui.SetMax_Temp_btn.setDisabled(True)
                self.ui.widget_5.rpb_setMaximum(self.tem_start)


                with open(self.Temp_Max_file, 'w') as file:
                    writer = csv.writer(file)
                    writer.writerow([self.tem_start])
                file.close


            else:
# IF IT IS  THEN DISPLAY POP UP MESSAGES AND DONT SET MIN TRIGGER VALUE
                msg.setText("MIN TRIGGER VALUE INVALID")
                msg.setWindowTitle(f" Alert")
                msg.setStandardButtons(QMessageBox.Ok)
                msg.setInformativeText(f"Hey the MAX trigger value can't be equal or Lesser than Min value")
                msg.setDetailedText("The Maximum Value should not be lesser and equals to Min Value \n"
                                    "for example you can only set trigger value as \n MIN:2 AND MAX 4 ")
                msg.setIcon(QMessageBox.Warning)
                ret = msg.exec_()


        else:
# DISABLE SET BUTTONS AFTER SUCCESSFULLY SET
            self.ui.Set_Temp_btn.setDisabled(True)
            self.ui.SetMax_Temp_btn.setDisabled(False)
            self.ui.MaxTempVal.setText(self.ui.MaxTempVal.text())
            self.ui.widget_5.rpb_setMaximum(int(self.ui.MaxTempVal.text()))


            with open(self.Temp_Max_file, 'w') as file:
                writer = csv.writer(file)
                writer.writerow(self.ui.MaxTempVal.text())
            file.close



# SET HUMIDTY MAX TRIGGER VALUE
    def setMaxHum(self):
        msg = QMessageBox()
        msg.setWindowTitle(f" Alert")
        msg.setText("Are You Sure ?")
        msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        msg.setDefaultButton(QMessageBox.Yes)
        msg.setInformativeText(f"Do you want to make changes to triggers threshold ?")
        msg.setDetailedText("Once you change the Min trigger threshold it will control the relay On/Off\n"
                            "make sure you what you are doing ! 🤓")
        msg.setIcon(QMessageBox.Question)
        ret = msg.exec_()

        if ret == QMessageBox.Yes:

# CONFIRM IF MIN VALUE IS NOT EQUALS AND GREATER THAN MAX VALUE
            #if int(self.ui.MinHumVal.text()) != self.hum_start and self.hum_start > int(self.ui.MinHumVal.text()):
            if self.hum_start >= self.hum_Max:
# IF IS NOT T                                   HEN SET MAX TRIGGER VALUE
                self.ui.MaxHumVal.setText(f"{self.hum_start}")
                self.ui.Set_Hum_btn.setDisabled(False)
                self.ui.SetMax_Hum_btn.setDisabled(True)
                self.ui.widget_6.rpb_setMaximum(self.hum_start)


                with open(self.Hum_Max_file, 'w') as file:
                    writer = csv.writer(file)
                    writer.writerow([self.hum_start])
                file.close

            else:
# IF IT IS  THEN DISPLAY POP UP MESSAGES AND DONT SET MIN TRIGGER VALUE
                msg.setText("MIN TRIGGER VALUE INVALID")
                msg.setWindowTitle(f" Alert")
                msg.setStandardButtons(QMessageBox.Ok)
                msg.setInformativeText(f"Hey the MAX trigger value can't be equal or Lesser than min value")
                msg.setDetailedText("The Maximum Value should not be lesser and equals to Min Value \n"
                                    "for example you can only set the trigger value as \n MIN:20 AND MAX 50 ")
                msg.setIcon(QMessageBox.Warning)
                ret = msg.exec_()

        else:
# DISABLE SET BUTTONS AFTER SUCCESSFULLY SET
            self.ui.MaxHumVal.setText(self.ui.MaxHumVal.text())
            self.ui.Set_Hum_btn.setDisabled(True)
            self.ui.SetMax_Hum_btn.setDisabled(False)
            self.ui.widget_6.rpb_setMaximum(int(self.ui.MaxHumVal.text()))


            with open(self.Hum_Max_file, 'w') as file:
                writer = csv.writer(file)
                writer.writerow(self.ui.MaxHumVal.text())
            file.close

# SET HUMIDTY MINIMUM TRIGGER VALUE
    def setMinHum(self):

        msg = QMessageBox()
        msg.setWindowTitle(f" Alert")
        msg.setText("Are You Sure ?")
        msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        msg.setDefaultButton(QMessageBox.Yes)
        msg.setInformativeText(f"Do you want to make changes to triggers threshold ?")
        msg.setDetailedText("Once you change the Min trigger threshold it will control the relay On/Off\n"
                            "make sure you what you are doing ! 🤓")
        msg.setIcon(QMessageBox.Question)
        ret = msg.exec_()

        if ret == QMessageBox.Yes:

# CONFIRM IF MIN VALUE IS NOT EQUALS AND GREATER THAN MAX VALUE
            #if int(self.ui.MaxHumVal.text()) != self.hum_start and self.hum_start < int(self.ui.MaxHumVal.text()):
            if self.hum_start <= (self.hum_Max - int(self.ui.DiffHumVal.text())) and self.hum_start < self.hum_Max:
# SET MIN TRIGGER VALUE
                self.ui.MinHumVal.setText(f"{self.hum_start}")
                self.ui.Set_Hum_btn.setDisabled(False)
                self.ui.SetMin_Hum_btn.setDisabled(True)


                with open(self.Hum_Min_file, 'w') as file:
                    writer = csv.writer(file)
                    writer.writerow([self.hum_start])
                file.close

            else:
 # IF IT IS  THEN DISPLAY POP UP MESSAGES AND DONT SET MIN TRIGGER VALUE
                msg.setText("MIN TRIGGER VALUE INVALID")
                msg.setWindowTitle(f" Alert")
                msg.setStandardButtons(QMessageBox.Ok)
                msg.setInformativeText(f"Hey the MAX trigger value can't be equal or Lesser than Min value")
                msg.setDetailedText("The Maximum Value should not be lesser and equals to Min Value \n"
                                    "for example you can only set to Trigger value as \n MIN:20 AND MAX 50 ")
                msg.setIcon(QMessageBox.Warning)
                ret = msg.exec_()
        else:
# DISABLE SET BUTTONS AFTER SUCCESSFULLY SET
            self.ui.MinHumVal.setText(self.ui.MinHumVal.text())
            self.ui.Set_Hum_btn.setDisabled(True)
            self.ui.SetMin_Hum_btn.setDisabled(False)

            with open(self.Hum_Min_file, 'w') as file:
                writer = csv.writer(file)
                writer.writerow(self.ui.MinHumVal.text())
            file.close



# CHECK IF THE CONDTION TO PUBLISH AND TURN ON RELAY 1
    def Temperature_Rly_On(self):

# CHANGE TEXT STATUS OF RELAY 1 TO CONNECTED AND GREEN COLOR
        self.ui.Relay_1a.setStyleSheet("background-color:rgb(9, 255, 45)")
        self.ui.Relay_Status1a.setText("Connected !")
        self.ui.Relay_Status1a.setStyleSheet("color:rgb(9, 255, 45)")
        self.ui.Relay_1b.setStyleSheet("background-color:rgb(9, 255, 45)")
        self.ui.Relay_Status1b.setText("Connected !")
        self.ui.Relay_Status1b.setStyleSheet("color:rgb(9, 255, 45)")
    def Temperature_Rly_Off(self):

# CHANGE TEXT STATUS OF RELAY 1 TO CONNECTED AND RED COLOR
        self.ui.Relay_1a.setStyleSheet("background-color:red")
        self.ui.Relay_Status1a.setText("Disconnected !")
        self.ui.Relay_Status1a.setStyleSheet("color:rgb(255, 238, 187)")
        self.ui.Relay_1b.setStyleSheet("background-color:red")
        self.ui.Relay_Status1b.setText("Disconnected !")
        self.ui.Relay_Status1b.setStyleSheet("color:rgb(255, 238, 187)")

# CHECK IF THE CONDTION TO PUBLISH AND TURN ON RELAY 2
    def Humidity_Rly_On(self):
# CHANGE TEXT STATUS OF RELAY 2 TO CONNECTED AND GREEN COLOR
        self.ui.Relay_2a.setStyleSheet("background-color:rgb(9, 255, 45)")
        self.ui.Relay_Status2a.setText("Connected")
        self.ui.Relay_Status2a.setStyleSheet("color:rgb(9, 255, 45)")
        self.ui.Relay_2b.setStyleSheet("background-color:rgb(9, 255, 45)")
        self.ui.Relay_Status2b.setText("Connected")
        self.ui.Relay_Status2b.setStyleSheet("color:rgb(9, 255, 45)")

    def Humidity_Rly_Off(self):
# CHANGE TEXT STATUS OF RELAY 2 TO CONNECTED AND GREEN COLOR
        self.ui.Relay_2a.setStyleSheet("background-color:red")
        self.ui.Relay_Status2a.setText("Disconnected")
        self.ui.Relay_Status2a.setStyleSheet("color:rgb(255, 238, 187)")
        self.ui.Relay_2b.setStyleSheet("background-color:red")
        self.ui.Relay_Status2b.setText("Disconnected")
        self.ui.Relay_Status2b.setStyleSheet("color:rgb(255, 238, 187)")


    def setTemp(self):
# ENABLE THE NAVIGATION TEMPERATURE  BTN
        self.ui.Up_Temp_btn.setDisabled(False)
        self.ui.Down_Temp_btn.setDisabled(False)

# DISABLE THE SET BTN
        self.ui.SetMax_Temp_btn.setDisabled(True)
# ENABLE THE OK BTN
        self.ui.Set_Temp_btn.setDisabled(False)

# NAVIGATION BUTTON AND SET BUTTONS MANAGAEMENTS
    def SetBtn(self,press):

        if press == "Temperature":
            self.ui.Set_Temp_btn.setDisabled(True)
            self.ui.Up_Temp_btn.setDisabled(False)
            self.ui.Down_Temp_btn.setDisabled(False)
            self.ui.SetMax_Temp_btn.setDisabled(False)
            self.ui.SetMin_Temp_btn.setDisabled(False)
        else:
            self.ui.Set_Hum_btn.setDisabled(False)
            self.ui.Up_Hum_btn.setDisabled(False)
            self.ui.Down_Hum_btn.setDisabled(False)
            self.ui.SetMax_Hum_btn.setDisabled(False)
            self.ui.SetMin_Hum_btn.setDisabled(False)


# ADDING NUMBER EVENT TO TEMP NAVIGATION BTN AND LCD DISPLAY
    temp_Max =0
    def Temp_settings(self, nav):
            if nav == "Up":
                self.tem_start = self.tem_start + 1
                self.ui.lcdNumber.display(self.tem_start)
            elif nav == "Down":
                self.tem_start = self.tem_start - 1
                self.ui.lcdNumber.display(self.tem_start)
            elif nav == "Up_Max" and self.temp_Max < int(self.ui.MaxTempVal.text()):
                self.temp_Max =self.temp_Max + 1
                self.ui.TempValue.setText(f'{self.temp_Max} °C')

                with open(self.Temp_MaxValue_file, 'w') as file:
                    writer = csv.writer(file)
                    writer.writerow([self.temp_Max])
                file.close

            else:  #(self.temp_Max) - (self.tem_start) >= int(self.ui.MinTemVal.text())
                if self.temp_Max > int(self.ui.DiffTemVal.text()) + int(self.ui.MinTemVal.text()):
                    self.temp_Max = self.temp_Max - 1
                    self.ui.TempValue.setText(f'{self.temp_Max} °C')
                    with open(self.Temp_MaxValue_file, 'w') as file:
                        writer = csv.writer(file)
                        writer.writerow([self.temp_Max])
                    file.close

# ADDING NUMBER EVENT TO HUM NAVIGATION BTN AND LCD DISPLAY
    hum_Max =0
    def Hum_settings(self, nav):
        if nav == "Up":
            self.hum_start = self.hum_start + 1
            self.ui.lcdNumber_2.display(self.hum_start)
        elif nav == "Down":
            self.hum_start = self.hum_start - 1
            self.ui.lcdNumber_2.display(self.hum_start)
        elif nav == "Up_Max" and self.hum_Max < int(self.ui.MaxHumVal.text())  :

            self.hum_Max = self.hum_Max + 1
            self.ui.HumValue.setText(f'{self.hum_Max} %')

            with open(self.Hum_MaxValue_file, 'w') as file:
                writer = csv.writer(file)
                writer.writerow([self.hum_Max])
            file.close

        else:
            if self.hum_Max > int(self.ui.DiffHumVal.text()) + int(self.ui.MinHumVal.text()):
                self.hum_Max = self.hum_Max - 1
                self.ui.HumValue.setText(f'{self.hum_Max} %')
                with open(self.Hum_MaxValue_file, 'w') as file:
                    writer = csv.writer(file)
                    writer.writerow([self.hum_Max])
                file.close
    ##HANDLE PREVIOUS PAGE
    def Previous_page(self):
        self.ui.home.setCurrentWidget(self.ui.Home)
        self.ui.PreviuosBtn.setDisabled(True)
        self.ui.NextBtn.setDisabled(False)
        self.ui.NextBtn.setStyleSheet('color: green')
        self.ui.PreviuosBtn.setStyleSheet('color: transparent ; '
                                      'border :None;background-color:None;')
        self.ui.label_17.setText("")
        self.ui.label_16.setText("Next Page")

##HANDLE NEXT PAGE
    def Next_page(self):
        self.ui.PreviuosBtn.setDisabled(False)
        self.ui.NextBtn.setDisabled(True)
        self.ui.PreviuosBtn.setStyleSheet('color: green')
        self.ui.NextBtn.setStyleSheet('color: transparent ; '
                                      'border :None;background-color:None;')
        self.ui.home.setCurrentWidget(self.ui.Sensor)
        self.ui.label_17.setText("Previous Page")
        self.ui.label_16.setText("")
## THIS HANDLE THE POP UP WINDOW WHEN MQQT IS CONNECTED

    def handleMQTTConnection(self):
        global client_connect
        client_connect = False
        msg = QMessageBox()
        msg.setWindowTitle("MQTT CONNECTION")
        msg.setText(f"MQTT CONNECTED SUCCESSFULLY !")
        msg.setStandardButtons(QMessageBox.Ok)
        msg.setDefaultButton(QMessageBox.Retry)
        msg.setInformativeText(f"Hey Stelios, \n MQTT have now been connected to this GUI \n "
                               f"you can now  Monitors and and remote control your project")
        msg.setIcon(QMessageBox.Information)
        rec =msg.exec_()


## THIS HANDLES THE POP UP WINDOW WITH RED ICON FOR NO SIGNALS
    def handleNoSignal(self):
        global client_disconnect
        client_disconnect = False
        msg = QMessageBox()
        msg.setWindowTitle("No Signal / Disconnection")
        msg.setText(f"\nNo Signal / Disconnection ")
        msg.setStandardButtons(QMessageBox.Ok | QMessageBox.Close)
        msg.setDefaultButton(QMessageBox.Retry)
        msg.setInformativeText(f"\nNo Signal / Disconnection \nYou can close and retart or ok to reconnect other close and check connection")
        msg.setIcon(QMessageBox.Warning)

        rec =msg.exec_()
        if rec == QMessageBox.Close:
            self.close()

## THIS HANDLES BROKER SERVER CONNCETION
    def noConnection(self):
        msg = QMessageBox()
        msg.setWindowTitle("Broker Server")
        msg.setText(f"\nBroker Server Error ")
        msg.setStandardButtons(QMessageBox.Ok | QMessageBox.Close)
        msg.setDefaultButton(QMessageBox.Retry)
        msg.setInformativeText(f"\n Error Connecting Please check your broker Address / Ip")
        msg.setIcon(QMessageBox.Warning)

        rec = msg.exec_()
        if rec == QMessageBox.Close:
            self.close()
## THIS HANDLES THE POP UP WINDOW WITH RED ICON FOR GPIO_21
    def PopUpWindow(self,payload):

        msg = QMessageBox()
        msg.setWindowTitle("GPIO 21 ALERT")
        msg.setText(f" GPIO 21 ALERT !!! ")
        msg.setInformativeText(f"The GPIO_21 of your Raspberry pi is {payload} P")
        msg.setDetailedText(f" Hey Stelios, \n --> GPIO 21 is {payload}  \n --> Please confirm what might be wrong")
        msg.setDefaultButton(QMessageBox.Ok)
        msg.setIcon(QMessageBox.Critical)
        rec= msg.exec_()


if __name__ == "__main__":
    import PySide2
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()




    def on_connect(client, userdata, flag, rc):


        if rc == 0:
            global client_connect
            client_connect = True
            print(f"clinet_connect is {client_connect}")
            print("Connected with result code" + str(rc) + str(flag))
            # IF CONNECTION IS CONFRIM THEN SUBSCRIBE TO ALL TOPIC
            for i in sus_:
                client.subscribe(i)
                # client.subscribe(PubRly1Topic)
                # client.subscribe(PubRly2Topic)
            # DELETE BEFORE DEPLOY JUST A TEST

        else:
            print("Bad Connection !!")


    def on_disconnect(client, userdata, rc):
            global client_disconnect
            print("client disconnected" + str(rc))
            client_disconnect = True


    def on_message(client, userdata, message):
        global count,counter


        topic = str(message.topic)
        message = str(message.payload.decode("utf-8"))
        print(topic + "-->" + message)

# CHECK IF We ARE CONNECTED TO TASMOTA
        if topic == Tasmota:
            m_j = json.loads(message)
            temp_data = m_j['DS18B20']['Temperature']
            if Relay_inverted_Temp:
                window.Handle_Temperature(float(temp_data))


            else:
                window.Handle_Temperature2(float(temp_data))


# CHECK IF WE ARE CONNECTED TO SUBTEMPTOPIC
        elif topic == SubTempTopic:
            # window.Handle_Temperature(float(message))
            if Relay_inverted_Temp:
                window.Handle_Temperature(float(message))


            else:
                window.Handle_Temperature2(float(message))

    # CHECK IF WE ARE CONNECTED TO SUBHUMTOPIC
        elif topic == SubHumTopic:

           if Relay_inverted_Hum:
               window.Handle_Humidty(float(message))

           else:
               window.Handle_Humidty2(float(message))



        # BEFORE THE STATUS OF THE TEMPERATURE RELAY CHANGE ON THE GUI AFTER PUBLISH
        # WE NEED TO CONFIRM IF TRULY THE RELAY HAS STARTED WORKING
        # BY PUBLISHING TO THE BROKER WITH A  TOPIC
        # CHECK THE RELAY PIN STATE AND THEN PUBLISH TO THIS TOPIC
        # MAKE SURE TO PUBLISH "ON" or "OFF" FOR PIN CHECK  RESPECTIVELY

        elif topic == SubRly1Topic:

            if message == "temp1relayon":

                print(f" the temp relay is  {message}")

                window.Temperature_Rly_On()

                print("TEMPERATURE RElAY HAS STARTED WORKING")

            # elif message == "temp1relayoff":

            else:

                print(f" the temp relay is  {message}")

                window.Temperature_Rly_Off()

                print("TEMPERATURE RELAY HAS STOP WORKING")

        # BEFORE THE STATUS OF THE HUMIDTY RELAY CHANGE ON THE GUI AFTER PUBLISH
        # WE NEED TO CONFIRM IF TRULY THE RELAY HAS STARTED WORKING
        # BY PUBLISHING TO THE BROKER WITH A  TOPIC
        # CHECK THE RELAY PIN STATE AND THEN PUBLISH TO THIS TOPIC
        # MAKE SURE TO PUBLISH "ON" or "OFF" FOR PIN CHECK RESPECTIVELY
        elif topic == SubRly2Topic:
            if message == "ON":
                window.Humidity_Rly_On()
                print("HUMIDITY RElAY HAS STARTED WORKING")
            else:
                window.Humidity_Rly_Off()
                print("HUMIDITY RELAY HAS STOP WORKING")

        # WE NEED TO WAIT TO CONFIRM IF F1 RECEIVE FEEBACK
        # BEFORE THE BUTTON CHANGE  TO GREEN
        # YOU CALL A FUNCTION FROM OTHER CLIENT
        # OR USE A PAYLOAD LIKE "ON" of "OFF" TO CONFIRM
        elif topic == F1_Sub_Topic:
            if message == "ON":
                window.ui.F1btn.setStyleSheet(
                'border :3px ;background-color:rgb(0, 253, 82);') # If is "ON" then change to Green
            else:
                window.ui.F1btn.setStyleSheet('border :2px ;background-color:transparent'
                                        'background-hover: yellow;')
        # WE SUBSCRIBE TO GPIO_21 PIN FOR STATUS CHECK IF LOW/HIGH
        elif topic == GPIO_21:
            if message == "LOW":
                print(f'GPIO_21 IS {message}')
                count = 1
                counter=0

               # window.Handle_GPIO_21(message)
            # To RECEIVE ALERT WHEN GPIO_21 Is HIGH UNCOMMNENT THE NEXT LINE
            else:
                print(f'GPIO_21 IS {message}')
                count = 0
                counter=1
                #window.Handle_GPIO_21(message)
        else:
            sleep(1)


    def on_publish(client, userData, Mid):
        print("Publish successfully")

    def log(client, userdata,level,buf):
        print("log:", buf)


    try:

        client = mqqt.Client("Ayobami@")  # create a unique instance for your client
        # client.username_pw_set(user, password=password)    #set username and password
        client.on_connect = on_connect # attach function to callback
        client.on_log = log # attach function to callback
        client.on_disconnect = on_disconnect # attach function to callback
        client.on_message = on_message # attach function to callback
        client.on_publish = on_publish # attach function to callback
        client.connect(broker, port, keepalive)  # now connect

        client.loop_start() # make it continuous
    except:
        print("ERROR CONNECTING CHECK YOUR NETWORK AND BROKER SERVER")

        noSignal = True

    sys.exit(app.exec_())




