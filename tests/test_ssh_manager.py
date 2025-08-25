#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
SSH连接测试模块
"""

import unittest
import paramiko
import socket
import threading
import time
import os
import sys

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.core.ssh_manager import SSHManager

class TestSSHManager(unittest.TestCase):
    """SSH管理器测试类"""
    
    def setUp(self):
        """测试前准备"""
        self.ssh_manager = SSHManager()
    
    def test_connection_creation(self):
        """测试创建SSH连接管理器"""
        self.assertIsNotNone(self.ssh_manager)
    
    def test_invalid_connection(self):
        """测试无效连接"""
        # 使用不存在的主机测试连接失败
        result = self.ssh_manager.connect(
            "non-existent-host.example.com",
            22,
            "testuser",
            "testpassword"
        )
        self.assertIsNone(result)

if __name__ == "__main__":
    unittest.main()