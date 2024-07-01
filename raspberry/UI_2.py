import re
import sys
import time
import queue 
import random
from threading import *
import CAN_communicate as CAN
import USB_communicate as USB
from PyQt5 import QtCore, QtGui, QtWidgets, QtTest
from PyQt5.QtCore import QObject, pyqtSignal
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *

usb = USB.USB_communicate()
system = USB.system_cmd()
can_data = CAN.CAN_communicate()


class WorkerThread(QThread):
    update_signal_avr = pyqtSignal(str)
    update_signal_esp = pyqtSignal(int)
    update_signal_gsm = pyqtSignal(str)
    
    def wait_avr(self, port):
        result_data1 = str(can_data.take_status_isp(port))
        self.update_signal_avr.emit(result_data1)
        
    def wait_esp(self, port):
        result_data2 = system.cheak_chip(port)
        self.update_signal_esp.emit(result_data2)
        
    def wait_imei(self, port):
        result_data3 = str(usb.at_read_write(port))
        self.update_signal_gsm.emit(result_data3)
        

class DeviceStatus(QtWidgets.QWidget):
        
    def __init__(self, esp_com = "empty", port_num = "empty", port_id = None):
        super().__init__()
        self.layout = QtWidgets.QGridLayout()
        self.setLayout(self.layout)
        
        self.label_arm = QtWidgets.QLabel("AVR: ")
        self.label_esp = QtWidgets.QLabel("ESP: ")
        self.label_gsm = QtWidgets.QLabel("GSM: ")
        self.usb_port  = QtWidgets.QLabel("")
        
        self.port = port_id
        
        self.avr_status = 0
        self.esp_status = 0
        self.gsm_status = 0
        
        self.layout.addWidget(self.usb_port,  0, 0)
        self.layout.addWidget(self.label_arm, 1, 0)
        self.layout.addWidget(self.label_esp, 2, 0)
        self.layout.addWidget(self.label_gsm, 3, 0)
        
        self.worker_thread = WorkerThread()
        self.worker_thread.update_signal_avr.connect(self.update_avr)
        self.worker_thread.update_signal_esp.connect(self.update_esp)
        self.worker_thread.update_signal_gsm.connect(self.update_gsm)
        
        if port_num == "empty":
            self.label_arm.setText("AVR: None")
            self.label_esp.setText("ESP: None")
            self.label_gsm.setText("GSM: None")
        else:
            self.usb_port.setText(str(port_num))
            
        t1 = Thread (target = self.worker_thread.wait_imei, args = (port_num, ))
        t1.deamon = True
        t1.start()
        
        t2 = Thread (target = self.worker_thread.wait_esp, args = (esp_com, ))
        t2.deamon = True
        t2.start()
        
        t3 = Thread (target = self.worker_thread.wait_avr, args = (port_id, ))
        t3.deamon = True
        t3.start()
        
    def update_avr(self, avr_status):
        self.label_arm.setText("AVR: " + avr_status)
        QtTest.QTest.qWait(50)
        
    def update_esp(self, esp_status):
        self.label_esp.setText("ESP:  " + str(esp_status))
        QtTest.QTest.qWait(150)
        
    def update_gsm(self, gsm_status):
        self.label_gsm.setText("GSM: " + str(gsm_status))
        QtTest.QTest.qWait(100)
                        
    
class Ui_MainWindow(QMainWindow):
        
    can_ = CAN.CAN_communicate()
    update_signal = pyqtSignal(int)
    
    def setupUi(self, MainWindow, isp_queue):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(1200, 800)
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.Devices = QtWidgets.QTabWidget(self.centralwidget)
        self.Devices.setGeometry(QtCore.QRect(10, 10, 1160, 780))
        font = QtGui.QFont()
        font.setPointSize(12)
        self.Devices.setFont(font)
        self.Devices.setObjectName("Devices")
        
        #tab 1
        ## top widgets
        self.tab = QtWidgets.QWidget()
        self.tab.setObjectName("tab")
        self.select_version = QtWidgets.QComboBox(self.tab)
        self.select_version.setGeometry(QtCore.QRect(160, 10, 161, 31))
        self.select_version.setObjectName("select_version")
        self.select_version.addItem("")
        self.select_version.addItem("")
        self.select_version.addItem("")
        self.version = QtWidgets.QLabel(self.tab)
        self.version.setGeometry(QtCore.QRect(10, 20, 151, 20))
        self.version.setObjectName("version")
        self.dateTimeEdit = QtWidgets.QDateTimeEdit(self.tab)
        self.dateTimeEdit.setGeometry(QtCore.QRect(700, 10, 194, 31))
        self.dateTimeEdit.setObjectName("dateTimeEdit")
        self.pushButton = QtWidgets.QPushButton(self.tab)
        self.pushButton.setGeometry(QtCore.QRect(340, 10, 171, 31))
        self.pushButton.setObjectName("pushButton")
        self.widget = QtWidgets.QWidget(self.tab)
        self.widget.setGeometry(QtCore.QRect(20, 60, 1180, 600))
        self.widget.setObjectName("widget")
        
        ### class devices
        
        self.gridLayout_5 = QtWidgets.QGridLayout(self.widget)
        self.gridLayout_5.setContentsMargins(0, 0, 0, 0)
        self.gridLayout_5.setObjectName("gridLayout_5")
        
        comports = usb.detect_ports("ttyCH")
        if not comports:
            comports = ["1", "2", "3", "4",
                        "5", "6", "7", "8"]
        
        esp_com = ["/dev/ttyUSB0", "/dev/ttyUSB1",
                   "/dev/ttyUSB2", "/dev/ttyUSB3",
                   "/dev/ttyUSB4", "/dev/ttyUSB5",
                   "/dev/ttyUSB6", "/dev/ttyUSB7"]
        
        grid_list = [[0, 0, 1, 1], [0, 1, 1, 1],
                     [0, 2, 1, 1], [0, 3, 1, 1],
                     [1, 0, 1, 1], [1, 1, 1, 1],
                     [1, 2, 1, 1], [1, 3, 1, 1]]
        
        for id_dev in range(0,8):
            if comports[id_dev]:
                self.dev = DeviceStatus(esp_com[id_dev], comports[id_dev], id_dev)
            else:
                self.dev = DeviceStatus(port_id = id_dev)
            self.gridLayout_5.addWidget(self.dev, grid_list[id_dev][0], grid_list[id_dev][1], grid_list[id_dev][2], grid_list[id_dev][3])
            
        '''for id_dev in range(0,8):
            if comports[id_dev]:
                self.dev = DeviceStatus("empty", "empty", id_dev)
            else:
                self.dev = DeviceStatus(port_id = id_dev)
            self.gridLayout_5.addWidget(self.dev, grid_list[id_dev][0], grid_list[id_dev][1], grid_list[id_dev][2], grid_list[id_dev][3])'''
           
        self.Devices.addTab(self.tab, "")
        
        #tab 2
        self.tab_2 = QtWidgets.QWidget()
        self.tab_2.setObjectName("tab_2")
        self.change_value = QtWidgets.QLabel(self.tab_2)
        self.change_value.setGeometry(QtCore.QRect(140, 10, 95, 19))
        font = QtGui.QFont()
        font.setPointSize(12)
        self.change_value.setFont(font)
        self.change_value.setToolTipDuration(5)
        self.change_value.setAlignment(QtCore.Qt.AlignCenter)
        self.change_value.setObjectName("change_value")
        self.current_value = QtWidgets.QLabel(self.tab_2)
        self.current_value.setGeometry(QtCore.QRect(520, 10, 95, 19))
        font = QtGui.QFont()
        font.setPointSize(12)
        self.current_value.setFont(font)
        self.current_value.setToolTipDuration(5)
        self.current_value.setAlignment(QtCore.Qt.AlignCenter)
        self.current_value.setObjectName("current_value")
        self.layoutWidget = QtWidgets.QWidget(self.tab_2)
        self.layoutWidget.setGeometry(QtCore.QRect(10, 36, 1180, 780))
        self.layoutWidget.setObjectName("layoutWidget")
        self.gridLayout_4 = QtWidgets.QGridLayout(self.layoutWidget)
        self.gridLayout_4.setContentsMargins(0, 0, 0, 0)
        self.gridLayout_4.setObjectName("gridLayout_4")
        self.gridLayout_3 = QtWidgets.QGridLayout()
        self.gridLayout_3.setObjectName("gridLayout_3")
        self.gridLayout_2 = QtWidgets.QGridLayout()
        self.gridLayout_2.setObjectName("gridLayout_2")
        self.ACC = QtWidgets.QLabel(self.layoutWidget)
        font = QtGui.QFont()
        font.setPointSize(12)
        self.ACC.setFont(font)
        self.ACC.setAlignment(QtCore.Qt.AlignCenter)
        self.ACC.setObjectName("ACC")
        self.gridLayout_2.addWidget(self.ACC, 0, 0, 1, 1)
        self.ACC_slider = QtWidgets.QSlider(self.layoutWidget)
        self.ACC_slider.setProperty("value", 25)
        self.ACC_slider.setOrientation(QtCore.Qt.Horizontal)
        self.ACC_slider.setObjectName("ACC_slider")
        self.gridLayout_2.addWidget(self.ACC_slider, 0, 1, 1, 2)
        self.DEC = QtWidgets.QLabel(self.layoutWidget)
        font = QtGui.QFont()
        font.setPointSize(12)
        self.DEC.setFont(font)
        self.DEC.setAlignment(QtCore.Qt.AlignCenter)
        self.DEC.setObjectName("DEC")
        self.gridLayout_2.addWidget(self.DEC, 1, 0, 1, 1)
        self.DEC_slider = QtWidgets.QSlider(self.layoutWidget)
        self.DEC_slider.setProperty("value", 25)
        self.DEC_slider.setOrientation(QtCore.Qt.Horizontal)
        self.DEC_slider.setObjectName("DEC_slider")
        self.gridLayout_2.addWidget(self.DEC_slider, 1, 1, 1, 2)
        self.Speed = QtWidgets.QLabel(self.layoutWidget)
        font = QtGui.QFont()
        font.setPointSize(12)
        self.Speed.setFont(font)
        self.Speed.setAlignment(QtCore.Qt.AlignCenter)
        self.Speed.setObjectName("Speed")
        self.gridLayout_2.addWidget(self.Speed, 2, 0, 1, 1)
        self.Speed_slider = QtWidgets.QSlider(self.layoutWidget)
        self.Speed_slider.setProperty("value", 25)
        self.Speed_slider.setOrientation(QtCore.Qt.Horizontal)
        self.Speed_slider.setObjectName("Speed_slider")
        self.gridLayout_2.addWidget(self.Speed_slider, 2, 1, 1, 2)
        self.Step = QtWidgets.QLabel(self.layoutWidget)
        font = QtGui.QFont()
        font.setPointSize(12)
        self.Step.setFont(font)
        self.Step.setAlignment(QtCore.Qt.AlignCenter)
        self.Step.setObjectName("Step")
        self.gridLayout_2.addWidget(self.Step, 3, 0, 1, 1)
        self.Step_slider = QtWidgets.QSlider(self.layoutWidget)
        self.Step_slider.setProperty("value", 35)
        self.Step_slider.setOrientation(QtCore.Qt.Horizontal)
        self.Step_slider.setObjectName("Step_slider")
        self.gridLayout_2.addWidget(self.Step_slider, 3, 1, 1, 2)
        self.irection = QtWidgets.QLabel(self.layoutWidget)
        font = QtGui.QFont()
        font.setPointSize(12)
        self.irection.setFont(font)
        self.irection.setAlignment(QtCore.Qt.AlignCenter)
        self.irection.setObjectName("irection")
        self.gridLayout_2.addWidget(self.irection, 4, 0, 1, 1)
        self.radioButton = QtWidgets.QRadioButton(self.layoutWidget)
        self.radioButton.setChecked(True)
        self.radioButton.setObjectName("radioButton")
        self.gridLayout_2.addWidget(self.radioButton, 4, 1, 1, 1)
        self.radioButton_2 = QtWidgets.QRadioButton(self.layoutWidget)
        self.radioButton_2.setObjectName("radioButton_2")
        self.gridLayout_2.addWidget(self.radioButton_2, 4, 2, 1, 1)
        self.gridLayout_3.addLayout(self.gridLayout_2, 0, 0, 1, 2)
        self.sendButton = QtWidgets.QPushButton(self.layoutWidget)
        font = QtGui.QFont()
        font.setPointSize(12)
        self.sendButton.setFont(font)
        self.sendButton.setObjectName("sendButton")
        self.gridLayout_3.addWidget(self.sendButton, 1, 0, 1, 1)
        self.startButton = QtWidgets.QPushButton(self.layoutWidget)
        font = QtGui.QFont()
        font.setPointSize(12)
        self.startButton.setFont(font)
        self.startButton.setObjectName("startButton")
        self.gridLayout_3.addWidget(self.startButton, 1, 1, 1, 1)
        self.startButton_2 = QtWidgets.QPushButton(self.layoutWidget)
        font = QtGui.QFont()
        font.setPointSize(12)
        self.startButton_2.setFont(font)
        self.startButton_2.setObjectName("startButton_2")
        self.gridLayout_3.addWidget(self.startButton_2, 1, 2, 1, 1)
        self.stepButton = QtWidgets.QPushButton(self.layoutWidget)
        font = QtGui.QFont()
        font.setPointSize(12)
        self.stepButton.setFont(font)
        self.stepButton.setObjectName("stepButton")
        self.gridLayout_3.addWidget(self.stepButton, 1, 3, 1, 1)
        self.gridLayout = QtWidgets.QGridLayout()
        self.gridLayout.setObjectName("gridLayout")
        self.acc_val = QtWidgets.QLabel(self.layoutWidget)
        font = QtGui.QFont()
        font.setPointSize(12)
        self.acc_val.setFont(font)
        self.acc_val.setAlignment(QtCore.Qt.AlignCenter)
        self.acc_val.setObjectName("acc_val")
        self.gridLayout.addWidget(self.acc_val, 0, 0, 1, 1)
        self.dec_val = QtWidgets.QLabel(self.layoutWidget)
        font = QtGui.QFont()
        font.setPointSize(12)
        self.dec_val.setFont(font)
        self.dec_val.setAlignment(QtCore.Qt.AlignCenter)
        self.dec_val.setObjectName("dec_val")
        self.gridLayout.addWidget(self.dec_val, 1, 0, 1, 1)
        self.speed_val = QtWidgets.QLabel(self.layoutWidget)
        font = QtGui.QFont()
        font.setPointSize(12)
        self.speed_val.setFont(font)
        self.speed_val.setAlignment(QtCore.Qt.AlignCenter)
        self.speed_val.setObjectName("speed_val")
        self.gridLayout.addWidget(self.speed_val, 2, 0, 1, 1)
        self.step_val = QtWidgets.QLabel(self.layoutWidget)
        font = QtGui.QFont()
        font.setPointSize(12)
        self.step_val.setFont(font)
        self.step_val.setAlignment(QtCore.Qt.AlignCenter)
        self.step_val.setObjectName("step_val")
        self.gridLayout.addWidget(self.step_val, 3, 0, 1, 1)
        self.direction_val = QtWidgets.QLabel(self.layoutWidget)
        font = QtGui.QFont()
        font.setPointSize(12)
        self.direction_val.setFont(font)
        self.direction_val.setAlignment(QtCore.Qt.AlignCenter)
        self.direction_val.setObjectName("direction_val")
        self.gridLayout.addWidget(self.direction_val, 4, 0, 1, 1)
        self.gridLayout_3.addLayout(self.gridLayout, 0, 2, 1, 2)
        self.gridLayout_4.addLayout(self.gridLayout_3, 0, 0, 1, 4)
        self.programming = QtWidgets.QPushButton(self.layoutWidget)
        font = QtGui.QFont()
        font.setPointSize(12)
        self.programming.setFont(font)
        self.programming.setObjectName("programming")
        self.gridLayout_4.addWidget(self.programming, 1, 0, 1, 1)
        self.started = QtWidgets.QLabel(self.layoutWidget)
        self.started.setAlignment(QtCore.Qt.AlignCenter)
        self.started.setObjectName("started")
        self.gridLayout_4.addWidget(self.started, 1, 1, 1, 1)
        self.sucsess = QtWidgets.QLabel(self.layoutWidget)
        self.sucsess.setAlignment(QtCore.Qt.AlignCenter)
        self.sucsess.setObjectName("sucsess")
        self.gridLayout_4.addWidget(self.sucsess, 1, 2, 1, 1)
        self.error = QtWidgets.QLabel(self.layoutWidget)
        self.error.setAlignment(QtCore.Qt.AlignCenter)
        self.error.setObjectName("error")
        self.gridLayout_4.addWidget(self.error, 1, 3, 1, 1)
        self.Devices.addTab(self.tab_2, "")
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 800, 22))
        self.menubar.setObjectName("menubar")
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QtWidgets.QStatusBar(MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)
        
        can_ = CAN.CAN_communicate()
        
        value =  self.Speed_slider.value()
        self.speed_val.setText("Speed val: " + str(value))
        can_.motor[4] = value
        
        value =  self.Step_slider.value()
        self.step_val.setText("Step val: " + str(value))
        can_.motor[5] = value
        
        value =  self.ACC_slider.value()
        self.acc_val.setText("ACC val: " + str(value))
        can_.motor[1] = value
        
        value =  self.DEC_slider.value()
        self.dec_val.setText("DEC val: " + str(value))
        can_.motor[2] = value
        
        self.sendButton.clicked.connect(lambda: can_.producer("motor"))
        self.startButton.clicked.connect(lambda: can_.producer("start_run"))
        self.startButton_2.clicked.connect(lambda: can_.producer("start_move"))
        self.stepButton.clicked.connect(lambda: can_.producer("stop"))
        self.programming.clicked.connect(lambda: can_.producer("programm"))
        
        self.programming.clicked.connect(lambda: self.detect())
        self.Step_slider.sliderMoved.connect(lambda: self.update_data("step"))
        self.Speed_slider.sliderMoved.connect(lambda: self.update_data("speed"))
        self.ACC_slider.sliderMoved.connect(lambda: self.update_data("acc"))
        self.DEC_slider.sliderMoved.connect(lambda: self.update_data("dec"))
        self.radioButton.clicked.connect(lambda: self.cheak_direction("CV"))
        self.radioButton_2.clicked.connect(lambda: self.cheak_direction("CCV"))
        
        if self.radioButton.isChecked():
            self.direction_val.setText("Direction: CV")
            can_.motor[3] = 0
        else:
            self.direction_val.setText("Direction: CCV")
            can_.motor[3] = 1

        self.retranslateUi(MainWindow)
        self.Devices.setCurrentIndex(0)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)
        
        timer_dev = QTimer(self)
        timer_dev.timeout.connect(self.searchDev)
        timer_dev.start(100)
        self.flag_search = False
        
        '''timer_isp = QTimer(self)
        timer_isp.timeout.connect(can_.wait_data_from_isp())
        timer_isp.start(200)'''
        
        
    def searchDev(self):
        if not self.flag_search:
            self.comports = usb.detect_ports("ttyCH")
            if self.comports:
                print ("Detect!")
                self.flag_search = True
            else:
                print ("Empty!")

        
    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "MainWindow"))
        self.select_version.setItemText(0, _translate("MainWindow", "V1"))
        self.select_version.setItemText(1, _translate("MainWindow", "V2"))
        self.select_version.setItemText(2, _translate("MainWindow", "V3"))
        self.version.setToolTip(_translate("MainWindow", "<html><head/><body><p align=\"center\"><br/></p></body></html>"))
        self.version.setText(_translate("MainWindow", "Выбор прошивки:"))
        self.pushButton.setText(_translate("MainWindow", "Srart programming"))
        self.Devices.setTabText(self.Devices.indexOf(self.tab), _translate("MainWindow", "Devices"))
        self.change_value.setText(_translate("MainWindow", "Change value"))
        self.current_value.setText(_translate("MainWindow", "Current value"))
        self.ACC.setText(_translate("MainWindow", "ACC"))
        self.DEC.setText(_translate("MainWindow", "DEC"))
        self.Speed.setText(_translate("MainWindow", "Speed"))
        self.Step.setText(_translate("MainWindow", "Step"))
        self.irection.setText(_translate("MainWindow", "Direction"))
        self.radioButton.setText(_translate("MainWindow", "CV"))
        self.radioButton_2.setText(_translate("MainWindow", "CCV"))
        self.sendButton.setText(_translate("MainWindow", "Send"))
        self.startButton.setText(_translate("MainWindow", "Start (Move)"))
        self.startButton_2.setText(_translate("MainWindow", "Start (Run)"))
        self.stepButton.setText(_translate("MainWindow", "Stop"))
        #self.acc_val.setText(_translate("MainWindow", "ACC val:  0"))
        #self.dec_val.setText(_translate("MainWindow", "DEC val:  0"))
        #self.speed_val.setText(_translate("MainWindow", "Speed val:  0"))
        #self.step_val.setText(_translate("MainWindow", "Step val:  0"))
        #self.direction_val.setText(_translate("MainWindow", "Direction:  CV"))
        self.programming.setText(_translate("MainWindow", "Strat programming"))
        #self.started.setText(_translate("MainWindow", "Started"))
        #self.sucsess.setText(_translate("MainWindow", "Sucsess"))
        #self.error.setText(_translate("MainWindow", "Error"))
        self.Devices.setTabText(self.Devices.indexOf(self.tab_2), _translate("MainWindow", "Service"))
        
    def update_data(self, _str):
        match _str:
            case "speed":
                value_spd =  self.Speed_slider.value()
                self.speed_val .setText("Speed val: " + str(value_spd))
                self.can_.motor[4] = value_spd
            case "step":
                value_stp =  self.Step_slider.value()
                self.step_val .setText("Step val: " + str(value_stp))
                self.can_.motor[5] = value_stp
            case "acc":
                value_acc = self.ACC_slider.value()
                self.acc_val.setText("ACC val: " + str(value_acc))
                self.can_.motor[1] = value_acc
            case "dec":
                value_dec = self.DEC_slider.value()
                self.dec_val.setText("DEC val: " + str(value_dec))
                self.can_.motor[2] = value_dec
        
        
    def cheak_direction(self, _str):
        match _str:
            case "CV":
                if self.radioButton.isChecked():
                    self.direction_val.setText("Direction: CV")
                    self.can_.motor[3] = 0
                                    
            case "CCV":
                if self.radioButton_2.isChecked():
                    self.direction_val.setText("Direction: CCV")
                    self.can_.motor[3] = 1
                    
    def detect(self):
        self.started.setText("Started")
    

        
