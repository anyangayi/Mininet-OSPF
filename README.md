# Mininet-OSPF

# 简介

使用Mininet工具和OSPF技术，创建了包含百余个节点的矩形虚拟拓扑。边缘节点与设备网口是绑定的，可以与外部网络设备进行数据包收发

# 拓扑图

![屏幕截图 2022-02-17 165819](https://user-images.githubusercontent.com/99868289/154440924-8c842243-15e8-4dde-a747-d40545239308.png)

# 使用说明

1.运行Mininet创建矩形拓扑：

$ sudo python QuaggaOSPF-rectangle.py

2.打开路由器终端(例如打开左侧汇聚路由器rf)：

$ xterm rf

3.运行抓包程序

$ sudo wireshark
