#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
端口转发管理器模块
"""

import threading
import socket
import select
import time
from PyQt5.QtCore import QObject, pyqtSignal

class PortForwarder(QObject):
    """端口转发管理器类"""
    
    # 信号定义
    forwarding_status_changed = pyqtSignal(dict, bool)  # 转发状态变化信号
    forwarding_traffic = pyqtSignal(dict, int, int)  # 转发流量信号
    
    def __init__(self):
        super().__init__()
        self.forwardings = {}  # 存储转发信息
        self.lock = threading.Lock()  # 线程锁
    
    def add_forwarding(self, forwarding_type, forwarding_config):
        """
        添加端口转发
        
        Args:
            forwarding_type (str): 转发类型，可选值: "local", "remote", "dynamic", "internal"
            forwarding_config (dict): 转发配置
            
        Returns:
            str: 转发ID，失败返回None
        """
        try:
            # 生成转发ID
            if forwarding_type == "local":
                forwarding_id = f"local:{forwarding_config.get('local_host')}:{forwarding_config.get('local_port')}"
            elif forwarding_type == "remote":
                forwarding_id = f"remote:{forwarding_config.get('remote_host')}:{forwarding_config.get('remote_port')}"
            elif forwarding_type == "dynamic":
                forwarding_id = f"dynamic:{forwarding_config.get('bind_host')}:{forwarding_config.get('bind_port')}"
            elif forwarding_type == "internal":
                forwarding_id = f"internal:{forwarding_config.get('internal_host')}:{forwarding_config.get('internal_port')}"
            else:
                return None
            
            # 检查是否已存在
            with self.lock:
                if forwarding_id in self.forwardings:
                    return None
                
                # 添加转发信息
                forwarding_info = {
                    "id": forwarding_id,
                    "type": forwarding_type,
                    "config": forwarding_config,
                    "active": False,
                    "thread": None,
                    "server_socket": None,
                    "connections": [],
                    "bytes_sent": 0,
                    "bytes_received": 0,
                    "start_time": 0,
                    "error": None
                }
                
                self.forwardings[forwarding_id] = forwarding_info
            
            return forwarding_id
        
        except Exception as e:
            print(f"添加转发错误: {str(e)}")
            return None
    
    def start_forwarding(self, forwarding_id):
        """
        启动端口转发
        
        Args:
            forwarding_id (str): 转发ID
            
        Returns:
            bool: 是否成功启动
        """
        try:
            with self.lock:
                if forwarding_id not in self.forwardings:
                    return False
                
                forwarding = self.forwardings[forwarding_id]
                
                # 如果已经启动，直接返回
                if forwarding.get("active", False):
                    return True
                
                # 根据转发类型启动
                forwarding_type = forwarding.get("type")
                
                if forwarding_type == "local":
                    return self._start_local_forwarding(forwarding)
                elif forwarding_type == "remote":
                    return self._start_remote_forwarding(forwarding)
                elif forwarding_type == "dynamic":
                    return self._start_dynamic_forwarding(forwarding)
                elif forwarding_type == "internal":
                    return self._start_internal_forwarding(forwarding)
                
                return False
        
        except Exception as e:
            print(f"启动转发错误: {str(e)}")
            return False
    
    def stop_forwarding(self, forwarding_id):
        """
        停止端口转发
        
        Args:
            forwarding_id (str): 转发ID
            
        Returns:
            bool: 是否成功停止
        """
        try:
            with self.lock:
                if forwarding_id not in self.forwardings:
                    return False
                
                forwarding = self.forwardings[forwarding_id]
                
                # 如果已经停止，直接返回
                if not forwarding.get("active", False):
                    return True
                
                # 标记为非活动
                forwarding["active"] = False
                
                # 关闭服务器套接字
                server_socket = forwarding.get("server_socket")
                if server_socket:
                    try:
                        server_socket.close()
                    except:
                        pass
                
                # 关闭所有连接
                connections = forwarding.get("connections", [])
                for conn in connections:
                    try:
                        if "socket" in conn:
                            conn["socket"].close()
                        if "channel" in conn:
                            conn["channel"].close()
                    except:
                        pass
                
                # 清空连接列表
                forwarding["connections"] = []
                
                # 发送状态变化信号
                self.forwarding_status_changed.emit(forwarding, False)
                
                return True
        
        except Exception as e:
            print(f"停止转发错误: {str(e)}")
            return False
    
    def remove_forwarding(self, forwarding_id):
        """
        移除端口转发
        
        Args:
            forwarding_id (str): 转发ID
            
        Returns:
            bool: 是否成功移除
        """
        try:
            # 先停止转发
            self.stop_forwarding(forwarding_id)
            
            # 从列表中移除
            with self.lock:
                if forwarding_id in self.forwardings:
                    del self.forwardings[forwarding_id]
            
            return True
        
        except Exception as e:
            print(f"移除转发错误: {str(e)}")
            return False
    
    def get_forwarding_status(self, forwarding_id):
        """
        获取转发状态
        
        Args:
            forwarding_id (str): 转发ID
            
        Returns:
            dict: 转发状态信息，不存在返回None
        """
        with self.lock:
            if forwarding_id not in self.forwardings:
                return None
            
            forwarding = self.forwardings[forwarding_id]
            
            # 构建状态信息
            status = {
                "id": forwarding.get("id"),
                "type": forwarding.get("type"),
                "active": forwarding.get("active", False),
                "connections": len(forwarding.get("connections", [])),
                "bytes_sent": forwarding.get("bytes_sent", 0),
                "bytes_received": forwarding.get("bytes_received", 0),
                "uptime": time.time() - forwarding.get("start_time", time.time()) if forwarding.get("active", False) else 0,
                "error": forwarding.get("error")
            }
            
            return status
    
    def get_all_forwardings(self):
        """
        获取所有转发信息
        
        Returns:
            list: 转发信息列表
        """
        with self.lock:
            return list(self.forwardings.values())
    
    def _start_local_forwarding(self, forwarding):
        """
        启动本地端口转发
        
        Args:
            forwarding (dict): 转发信息
            
        Returns:
            bool: 是否成功启动
        """
        try:
            config = forwarding.get("config", {})
            local_host = config.get("local_host", "127.0.0.1")
            local_port = config.get("local_port", 0)
            
            # 创建服务器套接字
            server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server_socket.bind((local_host, local_port))
            server_socket.listen(5)
            
            # 更新转发信息
            forwarding["server_socket"] = server_socket
            forwarding["active"] = True
            forwarding["start_time"] = time.time()
            forwarding["error"] = None
            
            # 创建监听线程
            thread = threading.Thread(
                target=self._local_forwarding_thread,
                args=(forwarding,),
                daemon=True
            )
            forwarding["thread"] = thread
            thread.start()
            
            # 发送状态变化信号
            self.forwarding_status_changed.emit(forwarding, True)
            
            return True
        
        except Exception as e:
            forwarding["error"] = str(e)
            print(f"启动本地转发错误: {str(e)}")
            return False
    
    def _start_remote_forwarding(self, forwarding):
        """
        启动远程端口转发
        
        Args:
            forwarding (dict): 转发信息
            
        Returns:
            bool: 是否成功启动
        """
        try:
            config = forwarding.get("config", {})
            ssh_client = config.get("ssh_client")
            
            if not ssh_client:
                forwarding["error"] = "SSH客户端未提供"
                return False
            
            remote_host = config.get("remote_host", "127.0.0.1")
            remote_port = config.get("remote_port", 0)
            local_host = config.get("local_host", "127.0.0.1")
            local_port = config.get("local_port", 0)
            
            # 获取传输对象
            transport = ssh_client.get_transport()
            
            # 请求端口转发
            transport.request_port_forward(
                remote_host,
                remote_port,
                handler=lambda channel, src_addr, dst_addr: self._handle_remote_connection(
                    forwarding, channel, src_addr, dst_addr, local_host, local_port
                )
            )
            
            # 更新转发信息
            forwarding["active"] = True
            forwarding["start_time"] = time.time()
            forwarding["error"] = None
            
            # 发送状态变化信号
            self.forwarding_status_changed.emit(forwarding, True)
            
            return True
        
        except Exception as e:
            forwarding["error"] = str(e)
            print(f"启动远程转发错误: {str(e)}")
            return False
    
    def _start_dynamic_forwarding(self, forwarding):
        """
        启动动态端口转发
        
        Args:
            forwarding (dict): 转发信息
            
        Returns:
            bool: 是否成功启动
        """
        try:
            config = forwarding.get("config", {})
            bind_host = config.get("bind_host", "127.0.0.1")
            bind_port = config.get("bind_port", 0)
            
            # 创建服务器套接字
            server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server_socket.bind((bind_host, bind_port))
            server_socket.listen(5)
            
            # 更新转发信息
            forwarding["server_socket"] = server_socket
            forwarding["active"] = True
            forwarding["start_time"] = time.time()
            forwarding["error"] = None
            
            # 创建监听线程
            thread = threading.Thread(
                target=self._dynamic_forwarding_thread,
                args=(forwarding,),
                daemon=True
            )
            forwarding["thread"] = thread
            thread.start()
            
            # 发送状态变化信号
            self.forwarding_status_changed.emit(forwarding, True)
            
            return True
        
        except Exception as e:
            forwarding["error"] = str(e)
            print(f"启动动态转发错误: {str(e)}")
            return False
            
    def _start_internal_forwarding(self, forwarding):
        """
        启动内部网络端口转发
        
        Args:
            forwarding (dict): 转发信息
            
        Returns:
            bool: 是否成功启动
        """
        try:
            config = forwarding.get("config", {})
            internal_host = config.get("internal_host")
            internal_port = config.get("internal_port")
            local_host = config.get("local_host", "127.0.0.1")
            local_port = config.get("local_port")
            
            if not internal_host or not internal_port or not local_port:
                raise ValueError("缺少必要的转发配置参数")
            
            # 创建服务器套接字
            server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server_socket.bind((local_host, local_port))
            server_socket.listen(5)
            
            # 更新转发信息
            forwarding["server_socket"] = server_socket
            forwarding["active"] = True
            forwarding["start_time"] = time.time()
            forwarding["error"] = None
            
            # 创建监听线程
            thread = threading.Thread(
                target=self._internal_forwarding_thread,
                args=(forwarding,),
                daemon=True
            )
            forwarding["thread"] = thread
            thread.start()
            
            # 发送状态变化信号
            self.forwarding_status_changed.emit(forwarding, True)
            
            return True
        
        except Exception as e:
            forwarding["error"] = str(e)
            print(f"启动内部转发错误: {str(e)}")
            return False
    
    def _local_forwarding_thread(self, forwarding):
        """
        本地转发线程
        
        Args:
            forwarding (dict): 转发信息
        """
        try:
            server_socket = forwarding.get("server_socket")
            config = forwarding.get("config", {})
            ssh_client = config.get("ssh_client")
            remote_host = config.get("remote_host", "localhost")
            remote_port = config.get("remote_port", 0)
            
            # 设置非阻塞模式
            server_socket.setblocking(False)
            
            while forwarding.get("active", False):
                try:
                    # 等待连接
                    readable, _, _ = select.select([server_socket], [], [], 1)
                    
                    if server_socket in readable:
                        client_socket, addr = server_socket.accept()
                        
                        # 创建SSH通道
                        transport = ssh_client.get_transport()
                        channel = transport.open_channel(
                            "direct-tcpip",
                            (remote_host, remote_port),
                            client_socket.getpeername()
                        )
                        
                        if channel is None:
                            client_socket.close()
                            continue
                        
                        # 记录连接
                        connection = {
                            "socket": client_socket,
                            "channel": channel,
                            "addr": addr,
                            "start_time": time.time(),
                            "bytes_sent": 0,
                            "bytes_received": 0
                        }
                        
                        with self.lock:
                            forwarding["connections"].append(connection)
                        
                        # 创建转发线程
                        t = threading.Thread(
                            target=self._handle_forwarding,
                            args=(forwarding, connection),
                            daemon=True
                        )
                        t.start()
                
                except (socket.error, select.error) as e:
                    if not forwarding.get("active", False):
                        break
                    print(f"本地转发错误: {str(e)}")
                    continue
            
            # 关闭服务器套接字
            try:
                server_socket.close()
            except:
                pass
        
        except Exception as e:
            forwarding["error"] = str(e)
            print(f"本地转发线程错误: {str(e)}")
            
            # 标记为非活动
            with self.lock:
                forwarding["active"] = False
            
            # 发送状态变化信号
            self.forwarding_status_changed.emit(forwarding, False)
    
    def _handle_remote_connection(self, forwarding, channel, src_addr, dst_addr, local_host, local_port):
        """
        处理远程转发连接
        
        Args:
            forwarding (dict): 转发信息
            channel (paramiko.Channel): SSH通道
            src_addr (tuple): 源地址
            dst_addr (tuple): 目标地址
            local_host (str): 本地目标地址
            local_port (int): 本地目标端口
        """
        try:
            # 连接到本地目标
            local_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            local_socket.connect((local_host, local_port))
            
            # 记录连接
            connection = {
                "socket": local_socket,
                "channel": channel,
                "addr": src_addr,
                "start_time": time.time(),
                "bytes_sent": 0,
                "bytes_received": 0
            }
            
            with self.lock:
                forwarding["connections"].append(connection)
            
            # 处理转发
            self._handle_forwarding(forwarding, connection)
        
        except Exception as e:
            print(f"处理远程连接错误: {str(e)}")
            channel.close()
    
    def _dynamic_forwarding_thread(self, forwarding):
        """
        动态转发线程
        
        Args:
            forwarding (dict): 转发信息
        """
        try:
            server_socket = forwarding.get("server_socket")
            config = forwarding.get("config", {})
            ssh_client = config.get("ssh_client")
            
            # 设置非阻塞模式
            server_socket.setblocking(False)
            
            while forwarding.get("active", False):
                try:
                    # 等待连接
                    readable, _, _ = select.select([server_socket], [], [], 1)
                    
                    if server_socket in readable:
                        client_socket, addr = server_socket.accept()
                        
                        # 创建处理线程
                        t = threading.Thread(
                            target=self._handle_socks_connection,
                            args=(forwarding, client_socket, addr, ssh_client),
                            daemon=True
                        )
                        t.start()
                
                except (socket.error, select.error) as e:
                    if not forwarding.get("active", False):
                        break
                    print(f"动态转发错误: {str(e)}")
                    continue
            
            # 关闭服务器套接字
            try:
                server_socket.close()
            except:
                pass
        
        except Exception as e:
            forwarding["error"] = str(e)
            print(f"动态转发线程错误: {str(e)}")
            
            # 标记为非活动
            with self.lock:
                forwarding["active"] = False
            
            # 发送状态变化信号
            self.forwarding_status_changed.emit(forwarding, False)
            
    def _internal_forwarding_thread(self, forwarding):
        """
        内部转发线程
        
        Args:
            forwarding (dict): 转发信息
        """
        try:
            server_socket = forwarding.get("server_socket")
            config = forwarding.get("config", {})
            ssh_client = config.get("ssh_client")
            internal_host = config.get("internal_host")
            internal_port = config.get("internal_port")
            
            # 设置非阻塞模式
            server_socket.setblocking(False)
            
            while forwarding.get("active", False):
                try:
                    # 等待连接
                    readable, _, _ = select.select([server_socket], [], [], 1)
                    
                    if server_socket in readable:
                        client_socket, addr = server_socket.accept()
                        
                        # 创建处理线程
                        t = threading.Thread(
                            target=self._handle_internal_connection,
                            args=(forwarding, client_socket, addr, internal_host, internal_port),
                            daemon=True
                        )
                        t.start()
                
                except (socket.error, select.error) as e:
                    if not forwarding.get("active", False):
                        break
                    print(f"内部转发错误: {str(e)}")
                    continue
            
            # 关闭服务器套接字
            try:
                server_socket.close()
            except:
                pass
        
        except Exception as e:
            forwarding["error"] = str(e)
            print(f"内部转发线程错误: {str(e)}")
            
            # 标记为非活动
            with self.lock:
                forwarding["active"] = False
            
            # 发送状态变化信号
            self.forwarding_status_changed.emit(forwarding, False)
    
    def _handle_socks_connection(self, forwarding, client_socket, addr, ssh_client):
        """
        处理SOCKS代理连接
        
        Args:
            forwarding (dict): 转发信息
            client_socket (socket.socket): 客户端套接字
            addr (tuple): 客户端地址
            ssh_client (paramiko.SSHClient): SSH客户端
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
                client_socket.close()
                return
            
            # 处理地址类型
            if atyp == 1:  # IPv4
                data = client_socket.recv(4)
                if not data or len(data) < 4:
                    client_socket.close()
                    return
                
                dst_addr = socket.inet_ntoa(data)
                
                # 读取端口
                data = client_socket.recv(2)
                if not data or len(data) < 2:
                    client_socket.close()
                    return
                
                dst_port = int.from_bytes(data, byteorder='big')
                
                # 创建SSH通道
                transport = ssh_client.get_transport()
                channel = transport.open_channel(
                    "direct-tcpip",
                    (dst_addr, dst_port),
                    addr
                )
                
                # 回复成功
                client_socket.sendall(b"\x05\x00\x00\x01" + socket.inet_aton("0.0.0.0") + b"\x00\x00")
                
                # 处理转发
                self._handle_forwarding(forwarding, {
                    "socket": client_socket,
                    "channel": channel,
                    "addr": addr,
                    "start_time": time.time(),
                    "bytes_sent": 0,
                    "bytes_received": 0
                })
                
            else:
                client_socket.close()
                return
                
        except Exception as e:
            print(f"处理SOCKS连接错误: {str(e)}")
            try:
                client_socket.close()
            except:
                pass
                
    def _handle_internal_connection(self, forwarding, client_socket, addr, internal_host, internal_port):
        """
        处理内部转发连接
        
        Args:
            forwarding (dict): 转发信息
            client_socket (socket.socket): 客户端套接字
            addr (tuple): 客户端地址
            internal_host (str): 内部目标主机
            internal_port (int): 内部目标端口
        """
        try:
            # 获取SSH客户端
            ssh_client = forwarding.get("config", {}).get("ssh_client")
            
            # 创建SSH通道
            transport = ssh_client.get_transport()
            channel = transport.open_channel(
                "direct-tcpip",
                (internal_host, internal_port),
                addr
            )
            
            # 记录连接
            connection = {
                "socket": client_socket,
                "channel": channel,
                "addr": addr,
                "start_time": time.time(),
                "bytes_sent": 0,
                "bytes_received": 0
            }
            
            with self.lock:
                forwarding["connections"].append(connection)
            
            # 处理转发
            self._handle_forwarding(forwarding, connection)
            
        except Exception as e:
            print(f"处理内部连接错误: {str(e)}")
            try:
                client_socket.close()
            except:
                pass
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
            transport = ssh_client.get_transport()
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
            
            # 记录连接
            connection = {
                "socket": client_socket,
                "channel": channel,
                "addr": addr,
                "start_time": time.time(),
                "bytes_sent": 0,
                "bytes_received": 0
            }
            
            with self.lock:
                forwarding["connections"].append(connection)
            
            # 处理转发
            self._handle_forwarding(forwarding, connection)
        
        except Exception as e:
            print(f"处理SOCKS连接错误: {str(e)}")
            client_socket.close()
    
    def _handle_forwarding(self, forwarding, connection):
        """
        处理数据转发
        
        Args:
            forwarding (dict): 转发信息
            connection (dict): 连接信息
        """
        try:
            socket_obj = connection.get("socket")
            channel = connection.get("channel")
            
            # 设置非阻塞模式
            socket_obj.setblocking(False)
            channel.setblocking(False)
            
            # 双向转发数据
            while forwarding.get("active", False):
                # 等待可读取的对象
                r, w, x = select.select([socket_obj, channel], [], [], 1)
                
                if socket_obj in r:
                    data = socket_obj.recv(4096)
                    if len(data) == 0:
                        break
                    
                    channel.sendall(data)
                    
                    # 更新统计信息
                    with self.lock:
                        connection["bytes_sent"] += len(data)
                        forwarding["bytes_sent"] += len(data)
                    
                    # 发送流量信号
                    self.forwarding_traffic.emit(forwarding, len(data), 0)
                
                if channel in r:
                    data = channel.recv(4096)
                    if len(data) == 0:
                        break
                    
                    socket_obj.sendall(data)
                    
                    # 更新统计信息
                    with self.lock:
                        connection["bytes_received"] += len(data)
                        forwarding["bytes_received"] += len(data)
                    
                    # 发送流量信号
                    self.forwarding_traffic.emit(forwarding, 0, len(data))
                
                # 检查通道是否关闭
                if channel.closed:
                    break
        
        except Exception as e:
            print(f"处理转发错误: {str(e)}")
        
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
            
            # 从连接列表中移除
            with self.lock:
                if connection in forwarding["connections"]:
                    forwarding["connections"].remove(connection)