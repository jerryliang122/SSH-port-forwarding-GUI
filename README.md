# Linux SSH 端口转发工具

一个基于PyQt的图形化工具，用于管理SSH连接和端口转发，方便访问内部网络资源。

![应用截图](resources/screenshots/main_window.png)

## 功能特点

- 图形化界面管理SSH连接
- 支持本地端口转发(Local Forwarding)
- 支持远程端口转发(Remote Forwarding)
- 支持动态端口转发(Dynamic Forwarding)
- 保存和管理多个连接配置
- 连接状态实时监控
- 支持密码和密钥认证方式
- 加密存储敏感信息
- 跨平台支持(Windows/Linux/macOS)

## 系统要求

- Python 3.7+
- PyQt5/PyQt6
- Paramiko
- cryptography

## 安装方法

### Windows

1. 克隆仓库
```
git clone https://github.com/yourusername/linux-ssh-port-forwarding.git
cd linux-ssh-port-forwarding
```

2. 安装依赖
```
pip install -r requirements.txt
```

3. 运行程序
```
python src/main.py
```

或者直接双击`start.bat`文件

### Linux/macOS

1. 克隆仓库
```
git clone https://github.com/yourusername/linux-ssh-port-forwarding.git
cd linux-ssh-port-forwarding
```

2. 安装依赖
```
pip3 install -r requirements.txt
```

3. 运行程序
```
chmod +x start.sh
./start.sh
```

## 使用说明

### 添加SSH连接

1. 点击"添加连接"按钮
2. 填写连接信息(名称、主机、端口、用户名)
3. 选择认证方式(密码/密钥)
4. 点击"确定"保存

### 管理端口转发

1. 选择已连接的SSH服务器
2. 点击"端口转发"按钮
3. 选择转发类型(本地/远程/动态)
4. 填写转发规则
5. 点击"启动"按钮开始转发

### 保存和加载配置

- 所有连接配置和转发规则会自动保存
- 下次启动时会自动加载
- 支持导入/导出配置

## 开发

### 运行测试
```
python -m unittest discover tests
```

### 打包应用
```
python setup.py sdist bdist_wheel
```

## 许可证

MIT

## 贡献指南

欢迎提交问题和功能请求。如果您想贡献代码，请先开issue讨论您想要更改的内容。

1. Fork仓库
2. 创建您的特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交您的更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开Pull Request