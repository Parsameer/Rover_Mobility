#include <ros/ros.h>
#include <std_msgs/Float64MultiArray.h>

ros::Publisher arm_pub;

void armCallback(const std_msgs::Float64MultiArray::ConstPtr& msg) {

	std::vector<double> inp = msg -> data;
	float basemotor = inp[2]
	float shoulderactuator = inp[3];
	float elbowmotor = inp[4];
	float pitchmotor = inp[5];
	float rollmotor = inp[6];
	float grippermotor = inp[7]; 

	std::vector<double> out(6, 0);
	
	out[1] = basemotor;
	out[2] = shoulderactuator;
	out[3] = elbowmotor;
	out[4] = pitchmotor;
	out[5] = rollmotor;
	out[6] = grippermotor;

	std_msgs::Float64MultiArray outMsg;
	outMsg.data = out;
	ard_pub.publish(outMsg);
}

int main(int argc, char** argv) {

	ros::init(argc, argv, "arm_driver");
	ros::NodeHandle _nh;
	
	arm_pub = _nh.advertise<std_msgs::Float64MultiArray>("/rover/arm_directives", 100);
	ros::Subscriber arm_sub = _nh.subscribe("/rover/control_directives", 100, armCallback);
	ros::Rate loop_rate(10);

	ros::spin();

	return 0;
}
