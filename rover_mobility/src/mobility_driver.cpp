#include <ros/ros.h>
#include <std_msgs/Float64MultiArray.h>
#include "std_msgs/String.h"
ros::Publisher ard_pub;

void navCallback(const std_msgs::Float64MultiArray::ConstPtr& msg) {

	std::vector<double> inp = msg -> data;
	float linSpeed = inp[0];
	float angSpeed = inp[1]; 

	std::vector<double> out(10, 0);
	for(int i=0; i<6;i++) {
		out[i] = linSpeed;
	}
	out[6] = angSpeed;
	out[7] = -angSpeed;
	out[8] = -angSpeed;
	out[9] = angSpeed;

	std_msgs::Float64MultiArray outMsg;
	outMsg.data = out;
	ard_pub.publish(outMsg);
}


int main(int argc, char** argv) {

	ros::init(argc, argv, "mobility_driver");
	ros::NodeHandle _nh;
	ros::Publisher chatter_pub = _nh.advertise<std_msgs::String>("chatter", 1000);
	ard_pub = _nh.advertise<std_msgs::Float64MultiArray>("/rover/ard_directives", 100);
	ros::Subscriber nav_sub = _nh.subscribe("/rover/mobility_directives", 100, navCallback);
	ros::Rate loop_rate(10);

	ros::spin();

	return 0;
}