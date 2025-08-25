#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Linux SSH 端口转发工具
主程序入口
"""

import sys
import os
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QIcon
from gui.main_window import MainWindow

def main():
    """主函数"""
    # 创建应用
    app = QApplication(sys.argv)
    app.setApplicationName("Linux SSH 端口转发工具")
    
    # 设置应用图标
    icon_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                           "resources", "icons", "app_icon.png")
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))
    
    # 创建并显示主窗口
    window = MainWindow()
    window.show()
    
    # 运行应用
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()