FROM ros:humble-ros-base

RUN apt-get update && apt-get install -y \
    ros-humble-rosbridge-suite \
    && rm -rf /var/lib/apt/lists/*

# exec 等で bash を立ち上げた際に自動で source されるように設定
RUN echo "source /opt/ros/humble/setup.bash" >> /root/.bashrc

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
CMD ["ros2", "launch", "rosbridge_server", "rosbridge_websocket_launch.xml", "address:=0.0.0.0"]
