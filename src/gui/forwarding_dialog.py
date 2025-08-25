#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
端口转发配置对话框模块
"""

from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
                           QLabel, QLineEdit, QSpinBox, QPushButton,
                           QComboBox, QTabWidget, QWidget, QTableWidget,
                           QTableWidgetItem, QHeaderView, QAbstractItemView,
                           QMessageBox, QGroupBox, QRadioButton)
from PyQt5.QtCore import Qt

class ForwardingDialog(QDialog):
    """端口转发配置对话框"""
    
    def __init__(self, parent=None, connection=None, ssh_manager=None):
        super().__init__(parent)
        
        self.connection = connection or {}
        self.ssh_manager = ssh_manager
        self.forwarding_rules = connection.get("forwarding_rules", [])
        self.active_forwardings = []
        
        # 设置窗口属性
        self.setWindowTitle("端口转发配置")
        self.setMinimumSize(600, 400)
        
        # 初始化UI
        self.init_ui()
        
        # 加载现有转发规则
        self.load_forwarding_rules()
    
    def init_ui(self):
        """初始化用户界面"""
        # 创建主布局
        main_layout = QVBoxLayout(self)
        
        # 创建标签显示连接信息
        connection_info = f"连接: {self.connection.get('name', '')} ({self.connection.get('host', '')})"
        info_label = QLabel(connection_info)
        main_layout.addWidget(info_label)
        
        # 创建选项卡
        self.tab_widget = QTabWidget()
        
        # 本地转发选项卡
        self.local_tab = QWidget()
        self.setup_local_tab()
        self.tab_widget.addTab(self.local_tab, "本地转发")
        
        # 远程转发选项卡
        self.remote_tab = QWidget()
        self.setup_remote_tab()
        self.tab_widget.addTab(self.remote_tab, "远程转发")
        
        # 动态转发选项卡
        self.dynamic_tab = QWidget()
        self.setup_dynamic_tab()
        self.tab_widget.addTab(self.dynamic_tab, "动态转发")
        
        # 添加选项卡到主布局
        main_layout.addWidget(self.tab_widget)
        
        # 按钮布局
        button_layout = QHBoxLayout()
        
        # 关闭按钮
        self.close_btn = QPushButton("关闭")
        self.close_btn.clicked.connect(self.accept)
        button_layout.addWidget(self.close_btn)
        
        # 添加按钮布局到主布局
        main_layout.addLayout(button_layout)
    
    def setup_local_tab(self):
        """设置本地转发选项卡"""
        layout = QVBoxLayout(self.local_tab)
        
        # 表单组
        form_group = QGroupBox("添加本地转发")
        form_layout = QFormLayout(form_group)
        
        # 本地地址
        self.local_host_edit = QLineEdit("127.0.0.1")
        form_layout.addRow("本地地址:", self.local_host_edit)
        
        # 本地端口
        self.local_port_spin = QSpinBox()
        self.local_port_spin.setRange(1, 65535)
        self.local_port_spin.setValue(8080)
        form_layout.addRow("本地端口:", self.local_port_spin)
        
        # 远程地址
        self.remote_host_edit = QLineEdit("localhost")
        form_layout.addRow("远程地址:", self.remote_host_edit)
        
        # 远程端口
        self.remote_port_spin = QSpinBox()
        self.remote_port_spin.setRange(1, 65535)
        self.remote_port_spin.setValue(80)
        form_layout.addRow("远程端口:", self.remote_port_spin)
        
        # 添加按钮
        self.add_local_btn = QPushButton("添加")
        self.add_local_btn.clicked.connect(self.add_local_forwarding)
        form_layout.addRow("", self.add_local_btn)
        
        layout.addWidget(form_group)
        
        # 转发列表
        list_group = QGroupBox("本地转发列表")
        list_layout = QVBoxLayout(list_group)
        
        self.local_table = QTableWidget()
        self.local_table.setColumnCount(5)
        self.local_table.setHorizontalHeaderLabels(["本地地址", "本地端口", "远程地址", "远程端口", "状态"])
        self.local_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.local_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.local_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.local_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        list_layout.addWidget(self.local_table)
        
        # 按钮布局
        button_layout = QHBoxLayout()
        
        # 启动按钮
        self.start_local_btn = QPushButton("启动")
        self.start_local_btn.clicked.connect(lambda: self.toggle_forwarding("local", True))
        button_layout.addWidget(self.start_local_btn)
        
        # 停止按钮
        self.stop_local_btn = QPushButton("停止")
        self.stop_local_btn.clicked.connect(lambda: self.toggle_forwarding("local", False))
        button_layout.addWidget(self.stop_local_btn)
        
        # 删除按钮
        self.delete_local_btn = QPushButton("删除")
        self.delete_local_btn.clicked.connect(lambda: self.delete_forwarding("local"))
        button_layout.addWidget(self.delete_local_btn)
        
        list_layout.addLayout(button_layout)
        layout.addWidget(list_group)
    
    def setup_remote_tab(self):
        """设置远程转发选项卡"""
        layout = QVBoxLayout(self.remote_tab)
        
        # 表单组
        form_group = QGroupBox("添加远程转发")
        form_layout = QFormLayout(form_group)
        
        # 远程地址
        self.remote_bind_host_edit = QLineEdit("0.0.0.0")
        form_layout.addRow("远程绑定地址:", self.remote_bind_host_edit)
        
        # 远程端口
        self.remote_bind_port_spin = QSpinBox()
        self.remote_bind_port_spin.setRange(1, 65535)
        self.remote_bind_port_spin.setValue(8080)
        form_layout.addRow("远程绑定端口:", self.remote_bind_port_spin)
        
        # 本地地址
        self.local_dest_host_edit = QLineEdit("localhost")
        form_layout.addRow("本地目标地址:", self.local_dest_host_edit)
        
        # 本地端口
        self.local_dest_port_spin = QSpinBox()
        self.local_dest_port_spin.setRange(1, 65535)
        self.local_dest_port_spin.setValue(80)
        form_layout.addRow("本地目标端口:", self.local_dest_port_spin)
        
        # 添加按钮
        self.add_remote_btn = QPushButton("添加")
        self.add_remote_btn.clicked.connect(self.add_remote_forwarding)
        form_layout.addRow("", self.add_remote_btn)
        
        layout.addWidget(form_group)
        
        # 转发列表
        list_group = QGroupBox("远程转发列表")
        list_layout = QVBoxLayout(list_group)
        
        self.remote_table = QTableWidget()
        self.remote_table.setColumnCount(5)
        self.remote_table.setHorizontalHeaderLabels(["远程绑定地址", "远程绑定端口", "本地目标地址", "本地目标端口", "状态"])
        self.remote_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.remote_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.remote_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.remote_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        list_layout.addWidget(self.remote_table)
        
        # 按钮布局
        button_layout = QHBoxLayout()
        
        # 启动按钮
        self.start_remote_btn = QPushButton("启动")
        self.start_remote_btn.clicked.connect(lambda: self.toggle_forwarding("remote", True))
        button_layout.addWidget(self.start_remote_btn)
        
        # 停止按钮
        self.stop_remote_btn = QPushButton("停止")
        self.stop_remote_btn.clicked.connect(lambda: self.toggle_forwarding("remote", False))
        button_layout.addWidget(self.stop_remote_btn)
        
        # 删除按钮
        self.delete_remote_btn = QPushButton("删除")
        self.delete_remote_btn.clicked.connect(lambda: self.delete_forwarding("remote"))
        button_layout.addWidget(self.delete_remote_btn)
        
        list_layout.addLayout(button_layout)
        layout.addWidget(list_group)
    
    def setup_dynamic_tab(self):
        """设置动态转发选项卡"""
        layout = QVBoxLayout(self.dynamic_tab)
        
        # 表单组
        form_group = QGroupBox("添加动态转发")
        form_layout = QFormLayout(form_group)
        
        # 本地地址
        self.dynamic_host_edit = QLineEdit("127.0.0.1")
        form_layout.addRow("本地绑定地址:", self.dynamic_host_edit)
        
        # 本地端口
        self.dynamic_port_spin = QSpinBox()
        self.dynamic_port_spin.setRange(1, 65535)
        self.dynamic_port_spin.setValue(1080)
        form_layout.addRow("本地绑定端口:", self.dynamic_port_spin)
        
        # 添加按钮
        self.add_dynamic_btn = QPushButton("添加")
        self.add_dynamic_btn.clicked.connect(self.add_dynamic_forwarding)
        form_layout.addRow("", self.add_dynamic_btn)
        
        layout.addWidget(form_group)
        
        # 转发列表
        list_group = QGroupBox("动态转发列表")
        list_layout = QVBoxLayout(list_group)
        
        self.dynamic_table = QTableWidget()
        self.dynamic_table.setColumnCount(3)
        self.dynamic_table.setHorizontalHeaderLabels(["本地绑定地址", "本地绑定端口", "状态"])
        self.dynamic_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.dynamic_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.dynamic_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.dynamic_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        list_layout.addWidget(self.dynamic_table)
        
        # 按钮布局
        button_layout = QHBoxLayout()
        
        # 启动按钮
        self.start_dynamic_btn = QPushButton("启动")
        self.start_dynamic_btn.clicked.connect(lambda: self.toggle_forwarding("dynamic", True))
        button_layout.addWidget(self.start_dynamic_btn)
        
        # 停止按钮
        self.stop_dynamic_btn = QPushButton("停止")
        self.stop_dynamic_btn.clicked.connect(lambda: self.toggle_forwarding("dynamic", False))
        button_layout.addWidget(self.stop_dynamic_btn)
        
        # 删除按钮
        self.delete_dynamic_btn = QPushButton("删除")
        self.delete_dynamic_btn.clicked.connect(lambda: self.delete_forwarding("dynamic"))
        button_layout.addWidget(self.delete_dynamic_btn)
        
        list_layout.addLayout(button_layout)
        layout.addWidget(list_group)
    
    def load_forwarding_rules(self):
        """加载现有转发规则"""
        for rule in self.forwarding_rules:
            rule_type = rule.get("type")
            
            if rule_type == "local":
                self.add_rule_to_table(self.local_table, [
                    rule.get("local_host", ""),
                    str(rule.get("local_port", "")),
                    rule.get("remote_host", ""),
                    str(rule.get("remote_port", "")),
                    "已停止"
                ])
            elif rule_type == "remote":
                self.add_rule_to_table(self.remote_table, [
                    rule.get("remote_host", ""),
                    str(rule.get("remote_port", "")),
                    rule.get("local_host", ""),
                    str(rule.get("local_port", "")),
                    "已停止"
                ])
            elif rule_type == "dynamic":
                self.add_rule_to_table(self.dynamic_table, [
                    rule.get("bind_host", ""),
                    str(rule.get("bind_port", "")),
                    "已停止"
                ])
    
    def add_rule_to_table(self, table, values):
        """添加规则到表格"""
        row_position = table.rowCount()
        table.insertRow(row_position)
        
        for i, value in enumerate(values):
            table.setItem(row_position, i, QTableWidgetItem(value))
    
    def add_local_forwarding(self):
        """添加本地转发规则"""
        local_host = self.local_host_edit.text()
        local_port = self.local_port_spin.value()
        remote_host = self.remote_host_edit.text()
        remote_port = self.remote_port_spin.value()
        
        # 验证输入
        if not local_host or not remote_host:
            QMessageBox.warning(self, "验证失败", "请填写所有必填字段")
            return
        
        # 检查是否已存在相同规则
        for rule in self.forwarding_rules:
            if (rule.get("type") == "local" and
                rule.get("local_host") == local_host and
                rule.get("local_port") == local_port):
                QMessageBox.warning(self, "规则已存在", "已存在相同的本地转发规则")
                return
        
        # 添加到规则列表
        rule = {
            "type": "local",
            "local_host": local_host,
            "local_port": local_port,
            "remote_host": remote_host,
            "remote_port": remote_port,
            "active": False
        }
        self.forwarding_rules.append(rule)
        
        # 添加到表格
        self.add_rule_to_table(self.local_table, [
            local_host,
            str(local_port),
            remote_host,
            str(remote_port),
            "已停止"
        ])
        
        # 清空输入
        self.local_port_spin.setValue(self.local_port_spin.value() + 1)
    
    def add_remote_forwarding(self):
        """添加远程转发规则"""
        remote_host = self.remote_bind_host_edit.text()
        remote_port = self.remote_bind_port_spin.value()
        local_host = self.local_dest_host_edit.text()
        local_port = self.local_dest_port_spin.value()
        
        # 验证输入
        if not remote_host or not local_host:
            QMessageBox.warning(self, "验证失败", "请填写所有必填字段")
            return
        
        # 检查是否已存在相同规则
        for rule in self.forwarding_rules:
            if (rule.get("type") == "remote" and
                rule.get("remote_host") == remote_host and
                rule.get("remote_port") == remote_port):
                QMessageBox.warning(self, "规则已存在", "已存在相同的远程转发规则")
                return
        
        # 添加到规则列表
        rule = {
            "type": "remote",
            "remote_host": remote_host,
            "remote_port": remote_port,
            "local_host": local_host,
            "local_port": local_port,
            "active": False
        }
        self.forwarding_rules.append(rule)
        
        # 添加到表格
        self.add_rule_to_table(self.remote_table, [
            remote_host,
            str(remote_port),
            local_host,
            str(local_port),
            "已停止"
        ])
        
        # 清空输入
        self.remote_bind_port_spin.setValue(self.remote_bind_port_spin.value() + 1)
    
    def add_dynamic_forwarding(self):
        """添加动态转发规则"""
        bind_host = self.dynamic_host_edit.text()
        bind_port = self.dynamic_port_spin.value()
        
        # 验证输入
        if not bind_host:
            QMessageBox.warning(self, "验证失败", "请填写所有必填字段")
            return
        
        # 检查是否已存在相同规则
        for rule in self.forwarding_rules:
            if (rule.get("type") == "dynamic" and
                rule.get("bind_host") == bind_host and
                rule.get("bind_port") == bind_port):
                QMessageBox.warning(self, "规则已存在", "已存在相同的动态转发规则")
                return
        
        # 添加到规则列表
        rule = {
            "type": "dynamic",
            "bind_host": bind_host,
            "bind_port": bind_port,
            "active": False
        }
        self.forwarding_rules.append(rule)
        
        # 添加到表格
        self.add_rule_to_table(self.dynamic_table, [
            bind_host,
            str(bind_port),
            "已停止"
        ])
        
        # 清空输入
        self.dynamic_port_spin.setValue(self.dynamic_port_spin.value() + 1)
    
    def toggle_forwarding(self, rule_type, start):
        """启动或停止端口转发"""
        if rule_type == "local":
            table = self.local_table
        elif rule_type == "remote":
            table = self.remote_table
        elif rule_type == "dynamic":
            table = self.dynamic_table
        else:
            return
        
        selected_rows = table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.warning(self, "警告", "请先选择一个转发规则")
            return
        
        row = selected_rows[0].row()
        
        # 查找对应的规则
        rule_index = -1
        for i, rule in enumerate(self.forwarding_rules):
            if rule.get("type") == rule_type:
                if rule_type == "local":
                    if (rule.get("local_host") == table.item(row, 0).text() and
                        int(rule.get("local_port")) == int(table.item(row, 1).text())):
                        rule_index = i
                        break
                elif rule_type == "remote":
                    if (rule.get("remote_host") == table.item(row, 0).text() and
                        int(rule.get("remote_port")) == int(table.item(row, 1).text())):
                        rule_index = i
                        break
                elif rule_type == "dynamic":
                    if (rule.get("bind_host") == table.item(row, 0).text() and
                        int(rule.get("bind_port")) == int(table.item(row, 1).text())):
                        rule_index = i
                        break
        
        if rule_index == -1:
            QMessageBox.warning(self, "错误", "找不到对应的转发规则")
            return
        
        rule = self.forwarding_rules[rule_index]
        
        try:
            if start:
                # 启动转发
                if rule_type == "local":
                    forwarding = self.ssh_manager.start_local_forwarding(
                        self.connection.get("client"),
                        rule.get("local_host"),
                        rule.get("local_port"),
                        rule.get("remote_host"),
                        rule.get("remote_port")
                    )
                    if forwarding:
                        self.active_forwardings.append(forwarding)
                        rule["active"] = True
                        table.setItem(row, 4, QTableWidgetItem("已启动"))
                
                elif rule_type == "remote":
                    forwarding = self.ssh_manager.start_remote_forwarding(
                        self.connection.get("client"),
                        rule.get("remote_host"),
                        rule.get("remote_port"),
                        rule.get("local_host"),
                        rule.get("local_port")
                    )
                    if forwarding:
                        self.active_forwardings.append(forwarding)
                        rule["active"] = True
                        table.setItem(row, 4, QTableWidgetItem("已启动"))
                
                elif rule_type == "dynamic":
                    forwarding = self.ssh_manager.start_dynamic_forwarding(
                        self.connection.get("client"),
                        rule.get("bind_host"),
                        rule.get("bind_port")
                    )
                    if forwarding:
                        self.active_forwardings.append(forwarding)
                        rule["active"] = True
                        table.setItem(row, 2, QTableWidgetItem("已启动"))
            
            else:
                # 停止转发
                for i, forwarding in enumerate(self.active_forwardings):
                    if rule_type == "local":
                        if (forwarding.get("type") == "local" and
                            forwarding.get("local_host") == rule.get("local_host") and
                            forwarding.get("local_port") == rule.get("local_port")):
                            self.ssh_manager.stop_forwarding(forwarding)
                            del self.active_forwardings[i]
                            rule["active"] = False
                            table.setItem(row, 4, QTableWidgetItem("已停止"))
                            break
                    
                    elif rule_type == "remote":
                        if (forwarding.get("type") == "remote" and
                            forwarding.get("remote_host") == rule.get("remote_host") and
                            forwarding.get("remote_port") == rule.get("remote_port")):
                            self.ssh_manager.stop_forwarding(forwarding)
                            del self.active_forwardings[i]
                            rule["active"] = False
                            table.setItem(row, 4, QTableWidgetItem("已停止"))
                            break
                    
                    elif rule_type == "dynamic":
                        if (forwarding.get("type") == "dynamic" and
                            forwarding.get("bind_host") == rule.get("bind_host") and
                            forwarding.get("bind_port") == rule.get("bind_port")):
                            self.ssh_manager.stop_forwarding(forwarding)
                            del self.active_forwardings[i]
                            rule["active"] = False
                            table.setItem(row, 2, QTableWidgetItem("已停止"))
                            break
        
        except Exception as e:
            QMessageBox.critical(self, "转发错误", str(e))
    
    def delete_forwarding(self, rule_type):
        """删除转发规则"""
        if rule_type == "local":
            table = self.local_table
        elif rule_type == "remote":
            table = self.remote_table
        elif rule_type == "dynamic":
            table = self.dynamic_table
        else:
            return
        
        selected_rows = table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.warning(self, "警告", "请先选择一个转发规则")
            return
        
        row = selected_rows[0].row()
        
        # 查找对应的规则
        rule_index = -1
        for i, rule in enumerate(self.forwarding_rules):
            if rule.get("type") == rule_type:
                if rule_type == "local":
                    if (rule.get("local_host") == table.item(row, 0).text() and
                        int(rule.get("local_port")) == int(table.item(row, 1).text())):
                        rule_index = i
                        break
                elif rule_type == "remote":
                    if (rule.get("remote_host") == table.item(row, 0).text() and
                        int(rule.get("remote_port")) == int(table.item(row, 1).text())):
                        rule_index = i
                        break
                elif rule_type == "dynamic":
                    if (rule.get("bind_host") == table.item(row, 0).text() and
                        int(rule.get("bind_port")) == int(table.item(row, 1).text())):
                        rule_index = i
                        break
        
        if rule_index == -1:
            QMessageBox.warning(self, "错误", "找不到对应的转发规则")
            return
        
        rule = self.forwarding_rules[rule_index]
        
        # 如果规则处于活动状态，先停止
        if rule.get("active", False):
            if rule_type == "local":
                self.toggle_forwarding("local", False)
            elif rule_type == "remote":
                self.toggle_forwarding("remote", False)
            elif rule_type == "dynamic":
                self.toggle_forwarding("dynamic", False)
        
        # 从规则列表中删除
        del self.forwarding_rules[rule_index]
        
        # 从表格中删除
        table.removeRow(row)
    
    def get_forwarding_rules(self):
        """获取转发规则列表"""
        return self.forwarding_rules
    
    def closeEvent(self, event):
        """窗口关闭事件处理"""
        # 停止所有活动的转发
        for forwarding in self.active_forwardings:
            try:
                self.ssh_manager.stop_forwarding(forwarding)
            except:
                pass
        
        event.accept()