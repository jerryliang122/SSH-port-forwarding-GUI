#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
连接配置对话框模块
"""

import os
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
                           QLabel, QLineEdit, QSpinBox, QPushButton,
                           QComboBox, QFileDialog, QCheckBox, QGroupBox,
                           QMessageBox)
from PyQt5.QtCore import Qt

class ConnectionDialog(QDialog):
    """SSH连接配置对话框"""
    
    def __init__(self, parent=None, connection_data=None):
        super().__init__(parent)
        
        self.connection_data = connection_data or {}
        
        # 设置窗口属性
        self.setWindowTitle("SSH连接配置")
        self.setMinimumWidth(400)
        
        # 初始化UI
        self.init_ui()
        
        # 如果提供了连接数据，填充表单
        if connection_data:
            self.fill_form()
    
    def init_ui(self):
        """初始化用户界面"""
        # 创建主布局
        main_layout = QVBoxLayout(self)
        
        # 创建表单布局
        form_layout = QFormLayout()
        
        # 连接名称
        self.name_edit = QLineEdit()
        form_layout.addRow("连接名称:", self.name_edit)
        
        # 主机地址
        self.host_edit = QLineEdit()
        form_layout.addRow("主机地址:", self.host_edit)
        
        # 端口
        self.port_spin = QSpinBox()
        self.port_spin.setRange(1, 65535)
        self.port_spin.setValue(22)
        form_layout.addRow("端口:", self.port_spin)
        
        # 用户名
        self.username_edit = QLineEdit()
        form_layout.addRow("用户名:", self.username_edit)
        
        # 认证方式
        self.auth_combo = QComboBox()
        self.auth_combo.addItems(["密码", "密钥", "密码和密钥"])
        self.auth_combo.currentIndexChanged.connect(self.on_auth_method_changed)
        form_layout.addRow("认证方式:", self.auth_combo)
        
        # 密码
        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(QLineEdit.Password)
        form_layout.addRow("密码:", self.password_edit)
        
        # 密钥文件
        key_layout = QHBoxLayout()
        self.key_path_edit = QLineEdit()
        self.key_path_edit.setReadOnly(True)
        key_layout.addWidget(self.key_path_edit)
        
        self.browse_btn = QPushButton("浏览...")
        self.browse_btn.clicked.connect(self.browse_key_file)
        key_layout.addWidget(self.browse_btn)
        
        form_layout.addRow("密钥文件:", key_layout)
        
        # 密钥密码
        self.passphrase_edit = QLineEdit()
        self.passphrase_edit.setEchoMode(QLineEdit.Password)
        form_layout.addRow("密钥密码:", self.passphrase_edit)
        
        # 添加表单布局到主布局
        main_layout.addLayout(form_layout)
        
        # 高级选项组
        advanced_group = QGroupBox("高级选项")
        advanced_layout = QFormLayout(advanced_group)
        
        # 保持连接
        self.keep_alive_check = QCheckBox()
        self.keep_alive_check.setChecked(True)
        advanced_layout.addRow("保持连接:", self.keep_alive_check)
        
        # 压缩
        self.compression_check = QCheckBox()
        advanced_layout.addRow("启用压缩:", self.compression_check)
        
        main_layout.addWidget(advanced_group)
        
        # 按钮布局
        button_layout = QHBoxLayout()
        
        # 确定按钮
        self.ok_btn = QPushButton("确定")
        self.ok_btn.clicked.connect(self.accept)
        button_layout.addWidget(self.ok_btn)
        
        # 取消按钮
        self.cancel_btn = QPushButton("取消")
        self.cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_btn)
        
        # 添加按钮布局到主布局
        main_layout.addLayout(button_layout)
        
        # 初始化认证方式UI
        self.on_auth_method_changed(0)
    
    def on_auth_method_changed(self, index):
        """认证方式改变时更新UI"""
        # 密码认证
        if index == 0:
            self.password_edit.setEnabled(True)
            self.key_path_edit.setEnabled(False)
            self.browse_btn.setEnabled(False)
            self.passphrase_edit.setEnabled(False)
        # 密钥认证
        elif index == 1:
            self.password_edit.setEnabled(False)
            self.key_path_edit.setEnabled(True)
            self.browse_btn.setEnabled(True)
            self.passphrase_edit.setEnabled(True)
        # 密码和密钥认证
        elif index == 2:
            self.password_edit.setEnabled(True)
            self.key_path_edit.setEnabled(True)
            self.browse_btn.setEnabled(True)
            self.passphrase_edit.setEnabled(True)
    
    def browse_key_file(self):
        """浏览并选择密钥文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择SSH密钥文件", os.path.expanduser("~/.ssh"),
            "所有文件 (*);;PEM文件 (*.pem);;PPK文件 (*.ppk)"
        )
        
        if file_path:
            self.key_path_edit.setText(file_path)
    
    def fill_form(self):
        """使用现有连接数据填充表单"""
        self.name_edit.setText(self.connection_data.get("name", ""))
        self.host_edit.setText(self.connection_data.get("host", ""))
        self.port_spin.setValue(self.connection_data.get("port", 22))
        self.username_edit.setText(self.connection_data.get("username", ""))
        
        # 设置认证方式
        has_password = bool(self.connection_data.get("password", ""))
        has_key = bool(self.connection_data.get("key_path", ""))
        
        if has_password and has_key:
            self.auth_combo.setCurrentIndex(2)
        elif has_key:
            self.auth_combo.setCurrentIndex(1)
        else:
            self.auth_combo.setCurrentIndex(0)
        
        self.password_edit.setText(self.connection_data.get("password", ""))
        self.key_path_edit.setText(self.connection_data.get("key_path", ""))
        self.passphrase_edit.setText(self.connection_data.get("passphrase", ""))
        
        # 高级选项
        self.keep_alive_check.setChecked(self.connection_data.get("keep_alive", True))
        self.compression_check.setChecked(self.connection_data.get("compression", False))
    
    def get_connection_data(self):
        """获取连接配置数据"""
        # 基本连接信息
        connection_data = {
            "name": self.name_edit.text(),
            "host": self.host_edit.text(),
            "port": self.port_spin.value(),
            "username": self.username_edit.text(),
            "connected": False,
            "client": None,
            "forwarding_rules": self.connection_data.get("forwarding_rules", [])
        }
        
        # 认证信息
        auth_index = self.auth_combo.currentIndex()
        
        if auth_index == 0 or auth_index == 2:  # 密码 或 密码和密钥
            connection_data["password"] = self.password_edit.text()
        
        if auth_index == 1 or auth_index == 2:  # 密钥 或 密码和密钥
            connection_data["key_path"] = self.key_path_edit.text()
            connection_data["passphrase"] = self.passphrase_edit.text()
        
        # 高级选项
        connection_data["keep_alive"] = self.keep_alive_check.isChecked()
        connection_data["compression"] = self.compression_check.isChecked()
        
        return connection_data
    
    def accept(self):
        """确认按钮点击处理"""
        # 验证必填字段
        if not self.name_edit.text():
            QMessageBox.warning(self, "验证失败", "请输入连接名称")
            return
        
        if not self.host_edit.text():
            QMessageBox.warning(self, "验证失败", "请输入主机地址")
            return
        
        if not self.username_edit.text():
            QMessageBox.warning(self, "验证失败", "请输入用户名")
            return
        
        # 验证认证信息
        auth_index = self.auth_combo.currentIndex()
        
        if auth_index == 0 and not self.password_edit.text():  # 密码认证
            QMessageBox.warning(self, "验证失败", "请输入密码")
            return
        
        if auth_index == 1 and not self.key_path_edit.text():  # 密钥认证
            QMessageBox.warning(self, "验证失败", "请选择密钥文件")
            return
        
        if auth_index == 2:  # 密码和密钥认证
            if not self.password_edit.text():
                QMessageBox.warning(self, "验证失败", "请输入密码")
                return
            
            if not self.key_path_edit.text():
                QMessageBox.warning(self, "验证失败", "请选择密钥文件")
                return
        
        super().accept()