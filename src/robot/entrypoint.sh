#!/bin/bash
set -e

# Setup ROS 2 environment
source /opt/ros/humble/setup.bash

# Ensure we execute whatever command is passed
exec "$@"
