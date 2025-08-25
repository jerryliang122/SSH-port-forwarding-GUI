#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
主窗口模块
"""

import os
import sys
from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                           QTableWidget, QTableWidgetItem, QPushButton, 
                           QLabel, QMessageBox, QAction, QMenu, QStatusBar,
                           QHeaderView, QAbstractItemView, QToolBar)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QIcon

from gui.connection_dialog import ConnectionDialog
from gui.forwarding_dialog import ForwardingDialog
from core.ssh_manager import SSHManager
from utils.config_manager import ConfigManager

class MainWindow(QMainWindow):
    """主窗口类"""
    
    def __init__(self):
        super().__init__()
        
        # 初始化配置管理器
        self.config_manager = ConfigManager()
        
        # 初始化SSH管理器
        self.ssh_manager = SSHManager()
        
        # 存储连接配置和状态
        self.connections = []
        
        # 设置窗口属性
        self.setWindowTitle("Linux SSH 端口转发工具")
        self.setMinimumSize(800, 500)
        
        # 初始化UI
        self.init_ui()
        
        # 加载保存的连接配置
        self.load_connections()
    
    def init_ui(self):
        """初始化用户界面"""
        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 创建主布局
        main_layout = QVBoxLayout(central_widget)
        
        # 创建工具栏
        self.create_toolbar()
        
        # 创建连接表格
        self.create_connection_table()
        main_layout.addWidget(self.connection_table)
        
        # 创建按钮区域
        button_layout = QHBoxLayout()
        
        # 添加连接按钮
        self.add_btn = QPushButton("添加连接")
        self.add_btn.clicked.connect(self.add_connection)
        button_layout.addWidget(self.add_btn)
        
        # 编辑连接按钮
        self.edit_btn = QPushButton("编辑连接")
        self.edit_btn.clicked.connect(self.edit_connection)
        button_layout.addWidget(self.edit_btn)
        
        # 删除连接按钮
        self.delete_btn = QPushButton("删除连接")
        self.delete_btn.clicked.connect(self.delete_connection)
        button_layout.addWidget(self.delete_btn)
        
        # 连接/断开按钮
        self.connect_btn = QPushButton("连接")
        self.connect_btn.clicked.connect(self.toggle_connection)
        button_layout.addWidget(self.connect_btn)
        
        # 端口转发按钮
        self.forward_btn = QPushButton("端口转发")
        self.forward_btn.clicked.connect(self.manage_forwarding)
        button_layout.addWidget(self.forward_btn)
        
        # 添加按钮布局到主布局
        main_layout.addLayout(button_layout)
        
        # 创建状态栏
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)
        self.statusBar.showMessage("就绪")
        
        # 更新按钮状态
        self.update_button_states()
    
    def create_toolbar(self):
        """创建工具栏"""
        toolbar = QToolBar("主工具栏")
        toolbar.setIconSize(QSize(16, 16))
        self.addToolBar(toolbar)
        
        # 添加操作
        new_action = QAction("新建连接", self)
        new_action.triggered.connect(self.add_connection)
        toolbar.addAction(new_action)
        
        # 添加分隔符
        toolbar.addSeparator()
        
        # 添加帮助操作
        help_action = QAction("帮助", self)
        help_action.triggered.connect(self.show_help)
        toolbar.addAction(help_action)
        
        # 添加关于操作
        about_action = QAction("关于", self)
        about_action.triggered.connect(self.show_about)
        toolbar.addAction(about_action)
    
    def create_connection_table(self):
        """创建连接表格"""
        self.connection_table = QTableWidget()
        self.connection_table.setColumnCount(5)
        self.connection_table.setHorizontalHeaderLabels(["名称", "主机", "端口", "用户名", "状态"])
        self.connection_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.connection_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.connection_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.connection_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.connection_table.itemSelectionChanged.connect(self.update_button_states)
    
    def load_connections(self):
        """加载保存的连接配置"""
        self.connections = self.config_manager.load_connections()
        self.update_connection_table()
    
    def update_connection_table(self):
        """更新连接表格"""
        self.connection_table.setRowCount(0)
        
        for connection in self.connections:
            row_position = self.connection_table.rowCount()
            self.connection_table.insertRow(row_position)
            
            # 设置表格项
            self.connection_table.setItem(row_position, 0, QTableWidgetItem(connection.get("name", "")))
            self.connection_table.setItem(row_position, 1, QTableWidgetItem(connection.get("host", "")))
            self.connection_table.setItem(row_position, 2, QTableWidgetItem(str(connection.get("port", 22))))
            self.connection_table.setItem(row_position, 3, QTableWidgetItem(connection.get("username", "")))
            
            # 设置状态
            status = "已断开"
            if connection.get("connected", False):
                status = "已连接"
            self.connection_table.setItem(row_position, 4, QTableWidgetItem(status))
    
    def update_button_states(self):
        """更新按钮状态"""
        selected_rows = self.connection_table.selectionModel().selectedRows()
        has_selection = len(selected_rows) > 0
        
        self.edit_btn.setEnabled(has_selection)
        self.delete_btn.setEnabled(has_selection)
        self.connect_btn.setEnabled(has_selection)
        self.forward_btn.setEnabled(has_selection)
        
        if has_selection:
            row = selected_rows[0].row()
            is_connected = self.connections[row].get("connected", False)
            self.connect_btn.setText("断开" if is_connected else "连接")
            self.forward_btn.setEnabled(is_connected)
    
    def add_connection(self):
        """添加新连接"""
        dialog = ConnectionDialog(self)
        if dialog.exec_():
            connection_data = dialog.get_connection_data()
            self.connections.append(connection_data)
            self.config_manager.save_connections(self.connections)
            self.update_connection_table()
            self.statusBar.showMessage(f"已添加连接: {connection_data['name']}")
    
    def edit_connection(self):
        """编辑选中的连接"""
        selected_rows = self.connection_table.selectionModel().selectedRows()
        if not selected_rows:
            return
        
        row = selected_rows[0].row()
        connection = self.connections[row]
        
        # 如果连接已经建立，不允许编辑
        if connection.get("connected", False):
            QMessageBox.warning(self, "警告", "请先断开连接后再编辑")
            return
        
        dialog = ConnectionDialog(self, connection)
        if dialog.exec_():
            self.connections[row] = dialog.get_connection_data()
            self.config_manager.save_connections(self.connections)
            self.update_connection_table()
            self.statusBar.showMessage(f"已更新连接: {self.connections[row]['name']}")
    
    def delete_connection(self):
        """删除选中的连接"""
        selected_rows = self.connection_table.selectionModel().selectedRows()
        if not selected_rows:
            return
        
        row = selected_rows[0].row()
        connection = self.connections[row]
        
        # 如果连接已经建立，先断开
        if connection.get("connected", False):
            self.disconnect_ssh(row)
        
        # 确认删除
        reply = QMessageBox.question(self, "确认删除", 
                                    f"确定要删除连接 '{connection['name']}' 吗?",
                                    QMessageBox.Yes | QMessageBox.No, 
                                    QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            del self.connections[row]
            self.config_manager.save_connections(self.connections)
            self.update_connection_table()
            self.statusBar.showMessage(f"已删除连接: {connection['name']}")
    
    def toggle_connection(self):
        """切换连接状态（连接/断开）"""
        selected_rows = self.connection_table.selectionModel().selectedRows()
        if not selected_rows:
            return
        
        row = selected_rows[0].row()
        connection = self.connections[row]
        
        if connection.get("connected", False):
            self.disconnect_ssh(row)
        else:
            self.connect_ssh(row)
    
    def connect_ssh(self, row):
        """连接到SSH服务器"""
        connection = self.connections[row]
        
        try:
            # 尝试建立SSH连接
            self.statusBar.showMessage(f"正在连接到 {connection['host']}...")
            
            result = self.ssh_manager.connect(
                connection["host"],
                connection["port"],
                connection["username"],
                connection.get("password", ""),
                connection.get("key_path", ""),
                connection.get("passphrase", "")
            )
            
            if result:
                connection["connected"] = True
                connection["client"] = result
                self.connections[row] = connection
                self.update_connection_table()
                self.update_button_states()
                self.statusBar.showMessage(f"已连接到 {connection['host']}")
            else:
                QMessageBox.critical(self, "连接失败", f"无法连接到 {connection['host']}")
                self.statusBar.showMessage("连接失败")
        
        except Exception as e:
            QMessageBox.critical(self, "连接错误", str(e))
            self.statusBar.showMessage("连接错误")
    
    def disconnect_ssh(self, row):
        """断开SSH连接"""
        connection = self.connections[row]
        
        try:
            # 尝试断开SSH连接
            self.statusBar.showMessage(f"正在断开与 {connection['host']} 的连接...")
            
            self.ssh_manager.disconnect(connection.get("client"))
            
            connection["connected"] = False
            connection["client"] = None
            self.connections[row] = connection
            self.update_connection_table()
            self.update_button_states()
            self.statusBar.showMessage(f"已断开与 {connection['host']} 的连接")
        
        except Exception as e:
            QMessageBox.critical(self, "断开连接错误", str(e))
            self.statusBar.showMessage("断开连接错误")
    
    def manage_forwarding(self):
        """管理端口转发"""
        selected_rows = self.connection_table.selectionModel().selectedRows()
        if not selected_rows:
            return
        
        row = selected_rows[0].row()
        connection = self.connections[row]
        
        # 确保连接已建立
        if not connection.get("connected", False):
            QMessageBox.warning(self, "警告", "请先建立SSH连接")
            return
        
        dialog = ForwardingDialog(self, connection, self.ssh_manager)
        if dialog.exec_():
            # 更新转发规则
            forwarding_rules = dialog.get_forwarding_rules()
            connection["forwarding_rules"] = forwarding_rules
            self.connections[row] = connection
            self.config_manager.save_connections(self.connections)
            self.statusBar.showMessage("端口转发规则已更新")
    
    def show_help(self):
        """显示帮助信息"""
        help_text = """
        <h3>Linux SSH 端口转发工具使用帮助</h3>
        <p><b>基本操作:</b></p>
        <ul>
            <li>添加连接: 点击"添加连接"按钮，填写SSH连接信息</li>
            <li>编辑连接: 选择一个连接，点击"编辑连接"按钮</li>
            <li>删除连接: 选择一个连接，点击"删除连接"按钮</li>
            <li>连接/断开: 选择一个连接，点击"连接"或"断开"按钮</li>
            <li>端口转发: 连接建立后，点击"端口转发"按钮设置转发规则</li>
        </ul>
        <p><b>端口转发类型:</b></p>
        <ul>
            <li>本地转发: 将本地端口转发到远程服务器上的端口</li>
            <li>远程转发: 将远程服务器上的端口转发到本地端口</li>
            <li>动态转发: 创建SOCKS代理</li>
        </ul>
        """
        QMessageBox.information(self, "使用帮助", help_text)
    
    def show_about(self):
        """显示关于信息"""
        about_text = """
        <h3>Linux SSH 端口转发工具</h3>
        <p>版本: 1.0.0</p>
        <p>一个基于PyQt的图形化工具，用于管理SSH连接和端口转发，方便访问内部网络资源。</p>
        <p>Copyright © 2025</p>
        """
        QMessageBox.about(self, "关于", about_text)
    
    def closeEvent(self, event):
        """窗口关闭事件处理"""
        # 断开所有连接
        for i, connection in enumerate(self.connections):
            if connection.get("connected", False):
                self.disconnect_ssh(i)
        
        event.accept()