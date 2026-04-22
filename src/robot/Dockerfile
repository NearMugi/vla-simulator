FROM ros:humble-ros-base

RUN apt-get update && apt-get install -y \
    ros-humble-rosbridge-suite \
    ros-humble-moveit \
    ros-humble-robot-state-publisher \
    ros-humble-joint-state-publisher \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

# exec 等で bash を立ち上げた際に自動で source されるように設定
RUN echo "source /opt/ros/humble/setup.bash" >> /root/.bashrc

WORKDIR /app
COPY . /app

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
CMD ["ros2", "launch", "/app/launch/sim.launch.py"]
