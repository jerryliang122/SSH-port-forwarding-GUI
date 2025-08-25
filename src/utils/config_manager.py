#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
配置管理器模块
"""

import os
import json
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

class ConfigManager:
    """配置管理器类"""
    
    def __init__(self, config_dir=None):
        """
        初始化配置管理器
        
        Args:
            config_dir (str, optional): 配置目录路径，默认为用户目录下的.ssh-port-forwarding
        """
        # 设置配置目录
        if config_dir is None:
            self.config_dir = os.path.join(os.path.expanduser("~"), ".ssh-port-forwarding")
        else:
            self.config_dir = config_dir
        
        # 确保配置目录存在
        if not os.path.exists(self.config_dir):
            os.makedirs(self.config_dir)
        
        # 配置文件路径
        self.connections_file = os.path.join(self.config_dir, "connections.json")
        self.settings_file = os.path.join(self.config_dir, "settings.json")
        
        # 加密密钥
        self.encryption_key = self._get_encryption_key()
    
    def _get_encryption_key(self):
        """
        获取加密密钥
        
        Returns:
            bytes: 加密密钥
        """
        key_file = os.path.join(self.config_dir, "key.bin")
        
        # 如果密钥文件存在，读取密钥
        if os.path.exists(key_file):
            with open(key_file, "rb") as f:
                return f.read()
        
        # 否则生成新密钥
        key = Fernet.generate_key()
        
        # 保存密钥
        with open(key_file, "wb") as f:
            f.write(key)
        
        return key
    
    def _encrypt(self, data):
        """
        加密数据
        
        Args:
            data (str): 要加密的数据
            
        Returns:
            str: 加密后的数据
        """
        if not data:
            return ""
        
        f = Fernet(self.encryption_key)
        encrypted = f.encrypt(data.encode("utf-8"))
        return base64.b64encode(encrypted).decode("utf-8")
    
    def _decrypt(self, encrypted_data):
        """
        解密数据
        
        Args:
            encrypted_data (str): 加密的数据
            
        Returns:
            str: 解密后的数据
        """
        if not encrypted_data:
            return ""
        
        try:
            f = Fernet(self.encryption_key)
            decrypted = f.decrypt(base64.b64decode(encrypted_data))
            return decrypted.decode("utf-8")
        except:
            return ""
    
    def save_connections(self, connections):
        """
        保存连接配置
        
        Args:
            connections (list): 连接配置列表
            
        Returns:
            bool: 是否成功保存
        """
        try:
            # 处理连接配置，移除不需要保存的字段
            connections_to_save = []
            
            for conn in connections:
                # 创建连接副本
                conn_copy = conn.copy()
                
                # 移除不需要保存的字段
                if "client" in conn_copy:
                    del conn_copy["client"]
                
                # 加密敏感信息
                if "password" in conn_copy and conn_copy["password"]:
                    conn_copy["password"] = self._encrypt(conn_copy["password"])
                
                if "passphrase" in conn_copy and conn_copy["passphrase"]:
                    conn_copy["passphrase"] = self._encrypt(conn_copy["passphrase"])
                
                connections_to_save.append(conn_copy)
            
            # 保存到文件
            with open(self.connections_file, "w", encoding="utf-8") as f:
                json.dump(connections_to_save, f, indent=2)
            
            return True
        
        except Exception as e:
            print(f"保存连接配置错误: {str(e)}")
            return False
    
    def load_connections(self):
        """
        加载连接配置
        
        Returns:
            list: 连接配置列表
        """
        try:
            # 如果文件不存在，返回空列表
            if not os.path.exists(self.connections_file):
                return []
            
            # 从文件加载
            with open(self.connections_file, "r", encoding="utf-8") as f:
                connections = json.load(f)
            
            # 解密敏感信息
            for conn in connections:
                if "password" in conn and conn["password"]:
                    conn["password"] = self._decrypt(conn["password"])
                
                if "passphrase" in conn and conn["passphrase"]:
                    conn["passphrase"] = self._decrypt(conn["passphrase"])
                
                # 添加运行时字段
                conn["connected"] = False
                conn["client"] = None
            
            return connections
        
        except Exception as e:
            print(f"加载连接配置错误: {str(e)}")
            return []
    
    def save_settings(self, settings):
        """
        保存应用设置
        
        Args:
            settings (dict): 应用设置
            
        Returns:
            bool: 是否成功保存
        """
        try:
            # 保存到文件
            with open(self.settings_file, "w", encoding="utf-8") as f:
                json.dump(settings, f, indent=2)
            
            return True
        
        except Exception as e:
            print(f"保存应用设置错误: {str(e)}")
            return False
    
    def load_settings(self):
        """
        加载应用设置
        
        Returns:
            dict: 应用设置
        """
        try:
            # 如果文件不存在，返回默认设置
            if not os.path.exists(self.settings_file):
                return self.get_default_settings()
            
            # 从文件加载
            with open(self.settings_file, "r", encoding="utf-8") as f:
                settings = json.load(f)
            
            # 合并默认设置
            default_settings = self.get_default_settings()
            for key, value in default_settings.items():
                if key not in settings:
                    settings[key] = value
            
            return settings
        
        except Exception as e:
            print(f"加载应用设置错误: {str(e)}")
            return self.get_default_settings()
    
    def get_default_settings(self):
        """
        获取默认应用设置
        
        Returns:
            dict: 默认应用设置
        """
        return {
            "window_width": 800,
            "window_height": 600,
            "keep_alive_interval": 60,
            "connection_timeout": 10,
            "log_level": "INFO",
            "theme": "system",
            "language": "zh_CN",
            "check_update": True,
            "start_minimized": False,
            "minimize_to_tray": True,
            "confirm_on_exit": True
        }
    
    def export_connections(self, file_path, connections=None):
        """
        导出连接配置
        
        Args:
            file_path (str): 导出文件路径
            connections (list, optional): 要导出的连接列表，默认为所有连接
            
        Returns:
            bool: 是否成功导出
        """
        try:
            # 如果未提供连接列表，加载所有连接
            if connections is None:
                connections = self.load_connections()
            
            # 处理连接配置，移除不需要导出的字段
            connections_to_export = []
            
            for conn in connections:
                # 创建连接副本
                conn_copy = conn.copy()
                
                # 移除不需要导出的字段
                if "client" in conn_copy:
                    del conn_copy["client"]
                
                if "connected" in conn_copy:
                    del conn_copy["connected"]
                
                connections_to_export.append(conn_copy)
            
            # 保存到文件
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(connections_to_export, f, indent=2)
            
            return True
        
        except Exception as e:
            print(f"导出连接配置错误: {str(e)}")
            return False
    
    def import_connections(self, file_path):
        """
        导入连接配置
        
        Args:
            file_path (str): 导入文件路径
            
        Returns:
            list: 导入的连接列表，失败返回空列表
        """
        try:
            # 从文件加载
            with open(file_path, "r", encoding="utf-8") as f:
                imported_connections = json.load(f)
            
            # 处理导入的连接
            for conn in imported_connections:
                # 添加运行时字段
                conn["connected"] = False
                conn["client"] = None
            
            return imported_connections
        
        except Exception as e:
            print(f"导入连接配置错误: {str(e)}")
            return []
    
    def merge_connections(self, imported_connections):
        """
        合并导入的连接到现有连接
        
        Args:
            imported_connections (list): 导入的连接列表
            
        Returns:
            list: 合并后的连接列表
        """
        try:
            # 加载现有连接
            existing_connections = self.load_connections()
            
            # 合并连接
            for imported_conn in imported_connections:
                # 检查是否已存在相同名称的连接
                exists = False
                for i, existing_conn in enumerate(existing_connections):
                    if existing_conn.get("name") == imported_conn.get("name"):
                        # 更新现有连接
                        existing_connections[i] = imported_conn
                        exists = True
                        break
                
                # 如果不存在，添加到列表
                if not exists:
                    existing_connections.append(imported_conn)
            
            # 保存合并后的连接
            self.save_connections(existing_connections)
            
            return existing_connections
        
        except Exception as e:
            print(f"合并连接配置错误: {str(e)}")
            return self.load_connections()