#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
SSH连接管理器模块
"""

import os
import socket
import threading
import paramiko
import select
from PyQt5.QtCore import QObject, pyqtSignal

class SSHManager(QObject):
    """SSH连接管理器类"""
    
    # 信号定义
    connection_status_changed = pyqtSignal(str, bool)  # 连接状态变化信号
    forwarding_status_changed = pyqtSignal(dict, bool)  # 转发状态变化信号
    
    def __init__(self):
        super().__init__()
        self.clients = {}  # 存储SSH客户端连接
        self.forwardings = {}  # 存储转发线程
    
    def connect(self, host, port, username, password="", key_path="", passphrase=""):
        """
        建立SSH连接
        
        Args:
            host (str): 主机地址
            port (int): 端口
            username (str): 用户名
            password (str, optional): 密码
            key_path (str, optional): 密钥文件路径
            passphrase (str, optional): 密钥密码
            
        Returns:
            paramiko.SSHClient: SSH客户端对象，连接失败返回None
        """
        try:
            # 创建SSH客户端
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            # 连接参数
            connect_kwargs = {
                "hostname": host,
                "port": port,
                "username": username,
                "timeout": 10
            }
            
            # 根据认证方式设置参数
            if key_path and os.path.exists(key_path):
                # 使用密钥认证
                key = paramiko.RSAKey.from_private_key_file(key_path, password=passphrase) if passphrase else paramiko.RSAKey.from_private_key_file(key_path)
                connect_kwargs["pkey"] = key
            elif password:
                # 使用密码认证
                connect_kwargs["password"] = password
            
            # 建立连接
            client.connect(**connect_kwargs)
            
            # 存储客户端连接
            client_id = f"{host}:{port}:{username}"
            self.clients[client_id] = client
            
            # 发送连接状态变化信号
            self.connection_status_changed.emit(client_id, True)
            
            return client
        
        except Exception as e:
            print(f"SSH连接错误: {str(e)}")
            return None
    
    def disconnect(self, client):
        """
        断开SSH连接
        
        Args:
            client (paramiko.SSHClient): SSH客户端对象
        """
        if not client:
            return
        
        try:
            # 查找客户端ID
            client_id = None
            for cid, cl in self.clients.items():
                if cl == client:
                    client_id = cid
                    break
            
            # 停止所有相关的转发
            if client_id:
                forwardings_to_stop = []
                for fwd_id, forwarding in self.forwardings.items():
                    if forwarding.get("client") == client:
                        forwardings_to_stop.append(fwd_id)
                
                for fwd_id in forwardings_to_stop:
                    self.stop_forwarding(self.forwardings[fwd_id])
            
            # 关闭连接
            client.close()
            
            # 从存储中移除
            if client_id:
                del self.clients[client_id]
                
                # 发送连接状态变化信号
                self.connection_status_changed.emit(client_id, False)
        
        except Exception as e:
            print(f"SSH断开连接错误: {str(e)}")
    
    def start_local_forwarding(self, client, local_host, local_port, remote_host, remote_port):
        """
        启动本地端口转发
        
        Args:
            client (paramiko.SSHClient): SSH客户端对象
            local_host (str): 本地绑定地址
            local_port (int): 本地绑定端口
            remote_host (str): 远程目标地址
            remote_port (int): 远程目标端口
            
        Returns:
            dict: 转发信息，失败返回None
        """
        if not client:
            return None
        
        try:
            # 创建转发线程
            transport = client.get_transport()
            
            # 创建转发信息
            forwarding = {
                "type": "local",
                "client": client,
                "transport": transport,
                "local_host": local_host,
                "local_port": local_port,
                "remote_host": remote_host,
                "remote_port": remote_port,
                "active": True,
                "thread": None
            }
            
            # 启动转发线程
            thread = threading.Thread(
                target=self._local_forwarding_thread,
                args=(forwarding,),
                daemon=True
            )
            forwarding["thread"] = thread
            thread.start()
            
            # 存储转发信息
            forwarding_id = f"local:{local_host}:{local_port}"
            self.forwardings[forwarding_id] = forwarding
            
            # 发送转发状态变化信号
            self.forwarding_status_changed.emit(forwarding, True)
            
            return forwarding
        
        except Exception as e:
            print(f"启动本地转发错误: {str(e)}")
            return None
    
    def start_remote_forwarding(self, client, remote_host, remote_port, local_host, local_port):
        """
        启动远程端口转发
        
        Args:
            client (paramiko.SSHClient): SSH客户端对象
            remote_host (str): 远程绑定地址
            remote_port (int): 远程绑定端口
            local_host (str): 本地目标地址
            local_port (int): 本地目标端口
            
        Returns:
            dict: 转发信息，失败返回None
        """
        if not client:
            return None
        
        try:
            # 获取传输对象
            transport = client.get_transport()
            
            # 创建转发信息
            forwarding = {
                "type": "remote",
                "client": client,
                "transport": transport,
                "remote_host": remote_host,
                "remote_port": remote_port,
                "local_host": local_host,
                "local_port": local_port,
                "active": True,
                "server": None
            }
            
            # 启动远程转发
            server = transport.request_port_forward(
                remote_host,
                remote_port,
                handler=lambda channel, src_addr, dst_addr: self._remote_forwarding_handler(
                    channel, src_addr, dst_addr, local_host, local_port, forwarding
                )
            )
            
            forwarding["server"] = server
            
            # 存储转发信息
            forwarding_id = f"remote:{remote_host}:{remote_port}"
            self.forwardings[forwarding_id] = forwarding
            
            # 发送转发状态变化信号
            self.forwarding_status_changed.emit(forwarding, True)
            
            return forwarding
        
        except Exception as e:
            print(f"启动远程转发错误: {str(e)}")
            return None
    
    def start_dynamic_forwarding(self, client, bind_host, bind_port):
        """
        启动动态端口转发(SOCKS代理)
        
        Args:
            client (paramiko.SSHClient): SSH客户端对象
            bind_host (str): 本地绑定地址
            bind_port (int): 本地绑定端口
            
        Returns:
            dict: 转发信息，失败返回None
        """
        if not client:
            return None
        
        try:
            # 创建转发信息
            forwarding = {
                "type": "dynamic",
                "client": client,
                "transport": client.get_transport(),
                "bind_host": bind_host,
                "bind_port": bind_port,
                "active": True,
                "thread": None
            }
            
            # 启动转发线程
            thread = threading.Thread(
                target=self._dynamic_forwarding_thread,
                args=(forwarding,),
                daemon=True
            )
            forwarding["thread"] = thread
            thread.start()
            
            # 存储转发信息
            forwarding_id = f"dynamic:{bind_host}:{bind_port}"
            self.forwardings[forwarding_id] = forwarding
            
            # 发送转发状态变化信号
            self.forwarding_status_changed.emit(forwarding, True)
            
            return forwarding
        
        except Exception as e:
            print(f"启动动态转发错误: {str(e)}")
            return None
    
    def stop_forwarding(self, forwarding):
        """
        停止端口转发
        
        Args:
            forwarding (dict): 转发信息
        """
        if not forwarding:
            return
        
        try:
            forwarding_type = forwarding.get("type")
            
            if forwarding_type == "local":
                # 停止本地转发
                forwarding["active"] = False
                # 线程会自行退出
                
                # 从存储中移除
                forwarding_id = f"local:{forwarding['local_host']}:{forwarding['local_port']}"
                if forwarding_id in self.forwardings:
                    del self.forwardings[forwarding_id]
            
            elif forwarding_type == "remote":
                # 停止远程转发
                transport = forwarding.get("transport")
                if transport:
                    transport.cancel_port_forward(
                        forwarding.get("remote_host", ""),
                        forwarding.get("remote_port", 0)
                    )
                
                forwarding["active"] = False
                
                # 从存储中移除
                forwarding_id = f"remote:{forwarding['remote_host']}:{forwarding['remote_port']}"
                if forwarding_id in self.forwardings:
                    del self.forwardings[forwarding_id]
            
            elif forwarding_type == "dynamic":
                # 停止动态转发
                forwarding["active"] = False
                # 线程会自行退出
                
                # 从存储中移除
                forwarding_id = f"dynamic:{forwarding['bind_host']}:{forwarding['bind_port']}"
                if forwarding_id in self.forwardings:
                    del self.forwardings[forwarding_id]
            
            # 发送转发状态变化信号
            self.forwarding_status_changed.emit(forwarding, False)
        
        except Exception as e:
            print(f"停止转发错误: {str(e)}")
    
    def _local_forwarding_thread(self, forwarding):
        """
        本地转发线程
        
        Args:
            forwarding (dict): 转发信息
        """
        try:
            transport = forwarding.get("transport")
            local_host = forwarding.get("local_host", "")
            local_port = forwarding.get("local_port", 0)
            remote_host = forwarding.get("remote_host", "")
            remote_port = forwarding.get("remote_port", 0)
            
            # 创建本地服务器套接字
            server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server_socket.bind((local_host, local_port))
            server_socket.listen(5)
            
            # 设置非阻塞模式
            server_socket.setblocking(False)
            
            # 处理连接
            while forwarding.get("active", False):
                try:
                    readable, _, _ = select.select([server_socket], [], [], 1)
                    
                    if server_socket in readable:
                        client_socket, addr = server_socket.accept()
                        
                        # 为每个连接创建一个线程
                        t = threading.Thread(
                            target=self._handle_local_connection,
                            args=(client_socket, transport, remote_host, remote_port),
                            daemon=True
                        )
                        t.start()
                
                except (socket.error, select.error) as e:
                    if not forwarding.get("active", False):
                        break
                    print(f"本地转发错误: {str(e)}")
                    continue
            
            # 关闭服务器套接字
            server_socket.close()
        
        except Exception as e:
            print(f"本地转发线程错误: {str(e)}")
            forwarding["active"] = False
    
    def _handle_local_connection(self, client_socket, transport, remote_host, remote_port):
        """
        处理本地转发连接
        
        Args:
            client_socket (socket.socket): 客户端套接字
            transport (paramiko.Transport): SSH传输对象
            remote_host (str): 远程目标地址
            remote_port (int): 远程目标端口
        """
        try:
            # 创建SSH通道
            channel = transport.open_channel(
                "direct-tcpip",
                (remote_host, remote_port),
                client_socket.getpeername()
            )
            
            if channel is None:
                client_socket.close()
                return
            
            # 双向转发数据
            self._forward_data(client_socket, channel)
        
        except Exception as e:
            print(f"处理本地连接错误: {str(e)}")
            client_socket.close()
    
    def _remote_forwarding_handler(self, channel, src_addr, dst_addr, local_host, local_port, forwarding):
        """
        远程转发处理函数
        
        Args:
            channel (paramiko.Channel): SSH通道
            src_addr (tuple): 源地址
            dst_addr (tuple): 目标地址
            local_host (str): 本地目标地址
            local_port (int): 本地目标端口
            forwarding (dict): 转发信息
        """
        try:
            if not forwarding.get("active", False):
                channel.close()
                return
            
            # 连接到本地目标
            local_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            local_socket.connect((local_host, local_port))
            
            # 双向转发数据
            self._forward_data(local_socket, channel)
        
        except Exception as e:
            print(f"远程转发处理错误: {str(e)}")
            channel.close()
    
    def _dynamic_forwarding_thread(self, forwarding):
        """
        动态转发线程(SOCKS代理)
        
        Args:
            forwarding (dict): 转发信息
        """
        try:
            transport = forwarding.get("transport")
            bind_host = forwarding.get("bind_host", "")
            bind_port = forwarding.get("bind_port", 0)
            
            # 创建本地服务器套接字
            server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server_socket.bind((bind_host, bind_port))
            server_socket.listen(5)
            
            # 设置非阻塞模式
            server_socket.setblocking(False)
            
            # 处理连接
            while forwarding.get("active", False):
                try:
                    readable, _, _ = select.select([server_socket], [], [], 1)
                    
                    if server_socket in readable:
                        client_socket, addr = server_socket.accept()
                        
                        # 为每个连接创建一个线程
                        t = threading.Thread(
                            target=self._handle_socks_connection,
                            args=(client_socket, transport),
                            daemon=True
                        )
                        t.start()
                
                except (socket.error, select.error) as e:
                    if not forwarding.get("active", False):
                        break
                    print(f"动态转发错误: {str(e)}")
                    continue
            
            # 关闭服务器套接字
            server_socket.close()
        
        except Exception as e:
            print(f"动态转发线程错误: {str(e)}")
            forwarding["active"] = False
    
    def _handle_socks_connection(self, client_socket, transport):
        """
        处理SOCKS代理连接
        
        Args:
            client_socket (socket.socket): 客户端套接字
            transport (paramiko.Transport): SSH传输对象
        """
        try:
            # 读取SOCKS请求
            # 这里只实现了SOCKS5协议的基本功能
            
            # 读取版本和认证方法数量
            data = client_socket.recv(2)
            if not data or len(data) < 2:
                client_socket.close()
                return
            
            version, nmethods = data[0], data[1]
            
            # 只支持SOCKS5
            if version != 5:
                client_socket.close()
                return
            
            # 读取认证方法
            methods = client_socket.recv(nmethods)
            
            # 回复使用无认证方法
            client_socket.sendall(b"\x05\x00")
            
            # 读取请求
            data = client_socket.recv(4)
            if not data or len(data) < 4:
                client_socket.close()
                return
            
            version, cmd, rsv, atyp = data[0], data[1], data[2], data[3]
            
            # 只支持CONNECT命令
            if cmd != 1:
                client_socket.sendall(b"\x05\x07\x00\x01\x00\x00\x00\x00\x00\x00")
                client_socket.close()
                return
            
            # 解析目标地址
            if atyp == 1:  # IPv4
                addr_bytes = client_socket.recv(4)
                addr = socket.inet_ntoa(addr_bytes)
            elif atyp == 3:  # 域名
                addr_len = client_socket.recv(1)[0]
                addr = client_socket.recv(addr_len).decode("utf-8")
            elif atyp == 4:  # IPv6
                addr_bytes = client_socket.recv(16)
                addr = socket.inet_ntop(socket.AF_INET6, addr_bytes)
            else:
                client_socket.sendall(b"\x05\x08\x00\x01\x00\x00\x00\x00\x00\x00")
                client_socket.close()
                return
            
            # 读取端口
            port_bytes = client_socket.recv(2)
            port = (port_bytes[0] << 8) + port_bytes[1]
            
            # 创建SSH通道
            channel = transport.open_channel(
                "direct-tcpip",
                (addr, port),
                client_socket.getpeername()
            )
            
            if channel is None:
                client_socket.sendall(b"\x05\x04\x00\x01\x00\x00\x00\x00\x00\x00")
                client_socket.close()
                return
            
            # 回复成功
            client_socket.sendall(b"\x05\x00\x00\x01\x00\x00\x00\x00\x00\x00")
            
            # 双向转发数据
            self._forward_data(client_socket, channel)
        
        except Exception as e:
            print(f"处理SOCKS连接错误: {str(e)}")
            client_socket.close()
    
    def _forward_data(self, socket_obj, channel):
        """
        双向转发数据
        
        Args:
            socket_obj (socket.socket): 套接字对象
            channel (paramiko.Channel): SSH通道
        """
        try:
            # 设置非阻塞模式
            socket_obj.setblocking(False)
            channel.setblocking(False)
            
            # 双向转发数据
            while True:
                # 等待可读取的对象
                r, w, x = select.select([socket_obj, channel], [], [], 1)
                
                if socket_obj in r:
                    data = socket_obj.recv(4096)
                    if len(data) == 0:
                        break
                    channel.sendall(data)
                
                if channel in r:
                    data = channel.recv(4096)
                    if len(data) == 0:
                        break
                    socket_obj.sendall(data)
                
                # 检查通道是否关闭
                if channel.closed:
                    break
        
        except Exception as e:
            print(f"转发数据错误: {str(e)}")
        
        finally:
            # 关闭连接
            try:
                socket_obj.close()
            except:
                pass
            
            try:
                channel.close()
            except:
                pass