#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
加密工具模块
"""

import os
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

class Encryption:
    """加密工具类"""
    
    @staticmethod
    def generate_key():
        """
        生成加密密钥
        
        Returns:
            bytes: 加密密钥
        """
        return Fernet.generate_key()
    
    @staticmethod
    def derive_key_from_password(password, salt=None):
        """
        从密码派生加密密钥
        
        Args:
            password (str): 密码
            salt (bytes, optional): 盐值，默认为随机生成
            
        Returns:
            tuple: (密钥, 盐值)
        """
        if salt is None:
            salt = os.urandom(16)
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000
        )
        
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        return key, salt
    
    @staticmethod
    def encrypt(data, key):
        """
        加密数据
        
        Args:
            data (str): 要加密的数据
            key (bytes): 加密密钥
            
        Returns:
            bytes: 加密后的数据
        """
        if not data:
            return b""
        
        f = Fernet(key)
        return f.encrypt(data.encode("utf-8"))
    
    @staticmethod
    def decrypt(encrypted_data, key):
        """
        解密数据
        
        Args:
            encrypted_data (bytes): 加密的数据
            key (bytes): 加密密钥
            
        Returns:
            str: 解密后的数据
        """
        if not encrypted_data:
            return ""
        
        try:
            f = Fernet(key)
            decrypted = f.decrypt(encrypted_data)
            return decrypted.decode("utf-8")
        except:
            return ""
    
    @staticmethod
    def encrypt_to_string(data, key):
        """
        加密数据并转换为字符串
        
        Args:
            data (str): 要加密的数据
            key (bytes): 加密密钥
            
        Returns:
            str: 加密后的字符串
        """
        encrypted = Encryption.encrypt(data, key)
        return base64.b64encode(encrypted).decode("utf-8") if encrypted else ""
    
    @staticmethod
    def decrypt_from_string(encrypted_string, key):
        """
        从字符串解密数据
        
        Args:
            encrypted_string (str): 加密的字符串
            key (bytes): 加密密钥
            
        Returns:
            str: 解密后的数据
        """
        if not encrypted_string:
            return ""
        
        try:
            encrypted_data = base64.b64decode(encrypted_string)
            return Encryption.decrypt(encrypted_data, key)
        except:
            return ""