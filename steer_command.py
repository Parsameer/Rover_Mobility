#!/usr/bin/env python
from math import pi, cos, sin

import diagnostic_msgs
import diagnostic_updater
from roboclaw import RoboClaw
import rospy
import tf
from geometry_msgs.msg import Quaternion, Twist
from nav_msgs.msg import Odometry
from std_msgs.msg import Float64MultiArray
import time
import thread
import numpy as np
from scipy.interpolate import spline
from std_msgs.msg import Float64
from serial.serialutil import SerialException as SerialException
from collections import deque
import matplotlib.pyplot as plt 

plt.ion()
ax1=plt.axes()
time_vec = []
val1_at_t = []
tval1_at_t = []
val2_at_t = []
tval2_at_t = []
class SteerClaw:

    def __init__(self, address, dev_name, baud_rate, name, kp1 = 0.15, kp2=0.15,ki1=0.08,ki2=0.08,kd1=0.06,kd2=0.06,int_windout1=50,int_windout2=50, qpps1 = 5.34, qpps2 = 5.34, deadzone1 = 30, deadzone2 = 20, kon1 = 0, kon2 = 0, sample_time=0.1, last_time=0.00, current_time=0.00):
    	self.ERRORS = {0x0000: (diagnostic_msgs.msg.DiagnosticStatus.OK, "Normal"),
    	0x0001: (diagnostic_msgs.msg.DiagnosticStatus.WARN, "M1 over current"),
    	0x0002: (diagnostic_msgs.msg.DiagnosticStatus.WARN, "M2 over current"),
    	0x0004: (diagnostic_msgs.msg.DiagnosticStatus.ERROR, "Emergency Stop"),
    	0x0008: (diagnostic_msgs.msg.DiagnosticStatus.ERROR, "Temperature1"),
    	0x0010: (diagnostic_msgs.msg.DiagnosticStatus.ERROR, "Temperature2"),
    	0x0020: (diagnostic_msgs.msg.DiagnosticStatus.ERROR, "Main batt voltage high"),
    	0x0040: (diagnostic_msgs.msg.DiagnosticStatus.ERROR, "Logic batt voltage high"),
    	0x0080: (diagnostic_msgs.msg.DiagnosticStatus.ERROR, "Logic batt voltage low"),
    	0x0100: (diagnostic_msgs.msg.DiagnosticStatus.WARN, "M1 driver fault"),
    	0x0200: (diagnostic_msgs.msg.DiagnosticStatus.WARN, "M2 driver fault"),
    	0x0400: (diagnostic_msgs.msg.DiagnosticStatus.WARN, "Main batt voltage high"),
    	0x0800: (diagnostic_msgs.msg.DiagnosticStatus.WARN, "Main batt voltage low"),
    	0x1000: (diagnostic_msgs.msg.DiagnosticStatus.WARN, "Temperature1"),
    	0x2000: (diagnostic_msgs.msg.DiagnosticStatus.WARN, "Temperature2"),
    	0x4000: (diagnostic_msgs.msg.DiagnosticStatus.OK, "M1 home"),
    	0x8000: (diagnostic_msgs.msg.DiagnosticStatus.OK, "M2 home")}
        
        self.claw = RoboClaw(address, dev_name, baud_rate)
        self.name = name
        self.claw.ResetEncoders()
        self.targetAngleM1 = 0
        self.targetAngleM2 = 0
        self.kp1 = kp1
        self.kp2 = kp2
        self.ki1 = ki1
        self.ki2 = ki2
        self.kd1 = kd1
        self.kd2 = kd2
        self.qpps1 = qpps1
        self.qpps2 = qpps2
        self.deadzone1 = deadzone1
        self.deadzone2 = deadzone2
        self.int_windout1=int_windout1
        self.int_windout2=int_windout2
        self.kon1 = kon1
        self.kon2 = kon2
        self.sample_time = sample_time
        self.last_time = 0.00
        self.last_error1 = 0.00
        self.last_error2 = 0.00
        self.PTerm1=0.00
        self.ITerm1=0.00
        self.DTerm1=0.00
        self.PTerm2=0.00
        self.ITerm2=0.00
        self.DTerm2=0.00
        self.delta_error1=0.00
        self.delta_error2=0.00
        self.diff1=0.00
        self.diff2=0.00
        self.enc1Pos=0.00
        self.enc2Pos=0.00
        self.finalEnc1Val=0.00
        self.finalEnc2Val=0.00
        self.lenplt1=0.00
        self.lenplt2=0.00
        self.enc1PosData=[0]*50
        self.enc2PosData=[0]*50
        self.enc1plotl, = plt.plot(self.enc1PosData)
        self.enc2plotl, = plt.plot(self.enc2PosData)
        self.enc1plotr, = plt.plot(self.enc1PosData)
        self.enc2plotr, = plt.plot(self.enc2PosData)

    
    def plot_func(self):
        if(self.name=="LeftClaw"):
            self.enc2PosData.append(self.enc2Pos)
            self.enc1PosData.append(self.enc1Pos)
            del self.enc1PosData[0]
            del self.enc2PosData[0]
            self.enc1plotl.set_xdata(np.arange(len(self.enc1PosData)))
            self.enc1plotl.set_ydata(self.enc1PosData)  # update the data
            self.enc2plotl.set_xdata(np.arange(len(self.enc1PosData)))
            self.enc2plotl.set_ydata(self.enc1PosData)  # update the data
            plt.draw() # update the plot
        
        if(self.name=="RightClaw"):
            self.enc2PosData.append(self.enc2Pos)
            self.enc1PosData.append(self.enc1Pos)
            del self.enc1PosData[0]
            del self.enc2PosData[0]
            self.enc1plotr.set_xdata(np.arange(len(self.enc1PosData)))
            self.enc1plotr.set_ydata(self.enc1PosData)  # update the data
            self.enc2plotr.set_xdata(np.arange(len(self.enc1PosData)))
            self.enc2plotr.set_ydata(self.enc1PosData)  # update the data
            plt.draw() # update the plot


    def update(self):
    	self.current_time = time.time()
        delta_time = self.current_time - self.last_time
		#----------------------------------------------------
		#Roboclaw1
        if (delta_time >= self.sample_time):
            time_vec.append(self.current_time)
            self.enc1Pos = self.claw.ReadEncM1()[1]
            self.finalEnc1Val = int(self.qpps1*self.targetAngleM1)
            self.diff1 = self.finalEnc1Val - self.enc1Pos  #Error in 1
            self.delta_error1 = self.diff1 - self.last_error1
            self.PTerm1 = self.diff1 #Pterm
            self.ITerm1+=self.diff1*delta_time
            if (self.ITerm1 < -self.int_windout1):
                self.ITerm1 = -self.int_windout1
            elif (self.ITerm1 > self.int_windout1):
                self.ITerm1 = self.int_windout1
            self.DTerm1 = self.delta_error1 / delta_time
            # Remember last time and last error for next calculation
            self.last_error1 = self.diff1

            velM1 = int((self.kp1*self.PTerm1) + (self.ki1 * self.ITerm1) + (self.kd1 * self.DTerm1))

            if self.enc1Pos < (self.finalEnc1Val - self.deadzone1):
                velM1 = velM1 + self.kon1
                val1_at_t.append(self.enc1Pos)
                tval1_at_t.append(self.targetAngleM1)
                self.claw.ForwardM1(min(255, velM1))
            elif self.enc1Pos > (self.finalEnc1Val + self.deadzone1):
                velM1 = velM1 - self.kon1
                val1_at_t.append(self.enc1Pos)
                tval1_at_t.append(self.targetAngleM1)
                self.claw.BackwardM1(min(255, -velM1))
            else:
                self.claw.ForwardM1(0)


		#----------------------------------------------------

		#----------------------------------------------------
		#Roboclaw2

        if (delta_time >= self.sample_time):
            time_vec.append(self.current_time)
            self.enc2Pos = -self.claw.ReadEncM2()[1]
            self.diff2 = self.finalEnc2Val - self.enc2Pos  #Error in 1
            self.delta_error2 = self.diff2 - self.last_error2
            self.PTerm2 = self.diff2 #Pterm
            self.ITerm2+=self.diff2*delta_time
            if (self.ITerm2 < -self.int_windout2):
                self.ITerm2 = -self.int_windout2
            elif (self.ITerm2 > self.int_windout2):
                self.ITerm2 = self.int_windout2

            self.DTerm2 = 0.0
            if delta_time > 0:
                self.DTerm2 = self.delta_error2 / delta_time

            # Remember last time and last error for next calculation
            self.last_error2 = self.diff2

            velM2 = int((self.kp2*self.PTerm2) + (self.ki2 * self.ITerm2) + (self.kd2 * self.DTerm2))


            if self.enc2Pos < (self.finalEnc2Val - self.deadzone2):
				velM2 = velM2 + self.kon2
				val2_at_t.append(self.enc2Pos)
				tval2_at_t.append(-self.targetAngleM2)
				self.claw.ForwardM2(min(255, velM2))
            elif self.enc2Pos > (self.finalEnc2Val + self.deadzone2):
				velM2 = velM2 - self.kon2
				val2_at_t.append(self.enc2Pos)
				tval2_at_t.append(-self.targetAngleM2)
				self.claw.BackwardM2(min(255, -velM2))
            else:
                self.claw.ForwardM2(0)

        
		#----------------------------------------------------


    #    rospy.loginfo("%s: %d %d %d %d", self.name, self.diff1, self.targetAngleM1,self.claw.ReadEncM1()[1], velM1)
    #    rospy.loginfo("%s: %d %d %d %d", self.name, self.diff2, self.targetAngleM2,self.claw.ReadEncM2()[1], velM2)



def steer_callback(inp):

    roboclaw1.targetAngleM1 = inp.data[6]
    roboclaw1.targetAngleM2 = inp.data[7]
    roboclaw2.targetAngleM1 = -inp.data[8]
    roboclaw2.targetAngleM2 = -inp.data[9]


if __name__ == "__main__":

    rospy.init_node("roboclaw_node")
    rospy.loginfo("Starting steer node")
    rospy.Subscriber("/rover/ard_directives", Float64MultiArray, steer_callback)
    rospy.loginfo("I'm here")

    r_time = rospy.Rate(1)

    for i in range(20):
		try:
			roboclaw2 = SteerClaw(0x81, "/dev/roboclaw2", 9600, "LeftClaw")
		except SerialException:
			rospy.logwarn("Could not connect to RoboClaw2, retrying...")
			r_time.sleep()
    rospy.loginfo("Connected to RoboClaw2")
    print "RoboClaw2 is connected"


    for i in range(20):
		try:
			roboclaw1 = SteerClaw(0x80, "/dev/roboclaw1", 9600, "RightClaw")
		except SerialException:
			rospy.logwarn("Could not connect to RoboClaw1, retrying...")
			r_time.sleep()
    rospy.loginfo("Connected to RoboClaw1")


    r_time = rospy.Rate(5)
    roboclaw1.claw.ForwardM1(0)
    roboclaw1.claw.ForwardM2(0)
    roboclaw2.claw.ForwardM1(0)
    roboclaw2.claw.ForwardM2(0)

    roboclaw1.targetAngleM1 = 0
    roboclaw1.targetAngleM2 = 0
    roboclaw2.targetAngleM1 = 0
    roboclaw2.targetAngleM2 = 0


    while not rospy.is_shutdown():
		try:
            thread.start_new_thread(roboclaw1.update)
		    thread.start_new_thread(roboclaw2.update)
            thread.start_new_thread(roboclaw1.plot_func)
            thread.start_new_thread(roboclaw2.plot_func)
            r_time.sleep()
        except:
            print "Unable to do threading "

    roboclaw1.claw.ForwardM1(0)
    roboclaw1.claw.ForwardM2(0)
    roboclaw2.claw.ForwardM1(0)
    roboclaw2.claw.ForwardM2(0)