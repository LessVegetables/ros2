"""ПР07: odom_adapter сохраняет stamp/pose/twist/covariance и меняет только frames."""

import math

from course_simulation.odom_adapter import normalize, to_transform
from nav_msgs.msg import Odometry


def raw(frame: str = 'course_ackermann/odom', child: str = 'course_ackermann/base_link'):
    msg = Odometry()
    msg.header.stamp.sec, msg.header.stamp.nanosec = 42, 125_000_000
    msg.header.frame_id, msg.child_frame_id = frame, child
    msg.pose.pose.position.x, msg.pose.pose.position.y = 1.5, -0.2
    msg.pose.pose.orientation.z, msg.pose.pose.orientation.w = 0.0998, 0.995
    msg.twist.twist.linear.x, msg.twist.twist.angular.z = 0.5, 0.1
    msg.pose.covariance[0] = 0.01
    msg.twist.covariance[35] = 0.02
    return msg


def test_frames_normalized_values_preserved() -> None:
    out = normalize(raw())
    assert out is not None
    assert (out.header.frame_id, out.child_frame_id) == ('odom', 'base_link')
    assert (out.header.stamp.sec, out.header.stamp.nanosec) == (42, 125_000_000)
    assert out.pose.pose.position.x == 1.5 and out.twist.twist.linear.x == 0.5
    assert out.pose.covariance[0] == 0.01 and out.twist.covariance[35] == 0.02


def test_transform_has_same_stamp_and_pose() -> None:
    tf = to_transform(normalize(raw()))
    assert (tf.header.frame_id, tf.child_frame_id) == ('odom', 'base_link')
    assert tf.header.stamp.sec == 42 and tf.transform.translation.x == 1.5
    assert tf.transform.rotation.w == 0.995


def test_other_prefix_rejected() -> None:
    assert normalize(raw('robot2/odom', 'robot2/base_link')) is None
    assert normalize(raw('odom', 'base_link')) is None


def test_non_finite_rejected() -> None:
    msg = raw()
    msg.pose.pose.position.x = math.nan
    assert normalize(msg) is None
    msg = raw()
    msg.twist.covariance[0] = math.inf
    assert normalize(msg) is None
