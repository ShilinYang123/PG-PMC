# CREOSON安装配置指南

## 概述

CREOSON是一个开源的Creo Parametric自动化工具，为Creo 10提供现代化的JSON API接口，支持HTTP请求进行CAD自动化操作。

## 系统要求

### 软件环境
- **Creo Parametric**: 10.0（推荐）或 9.0
- **操作系统**: Windows 10/11
- **Java**: JRE 8或更高版本
- **网络**: 本地HTTP服务支持

### 硬件要求
- **内存**: 最少8GB，推荐16GB
- **存储**: 至少500MB可用空间
- **网络**: 本地端口9056可用

## 安装步骤

### 1. 下载CREOSON

```bash
# 官方下载地址
https://github.com/SimplifiedLogic/creoson/releases

# 推荐版本
CREOSON 2.9.0 (支持Creo 10)
```

### 2. 安装目录结构

```
C:\CREOSON\
├── CreosonServer.exe          # 服务器主程序
├── creoson.jar               # Java库文件
├── lib\                      # 依赖库目录
│   ├── jackson-*.jar
│   └── other-libs.jar
├── config\                   # 配置文件目录
│   └── creoson.properties
└── logs\                     # 日志目录
```

### 3. 配置CREOSON

#### 3.1 创建配置文件

创建 `C:\CREOSON\config\creoson.properties`：

```properties
# CREOSON服务器配置
server.port=9056
server.host=localhost

# Creo连接配置
creo.start_dir=C:\\PTC\\Creo 10.0\\Parametric\\bin
creo.start_command=parametric.exe

# 日志配置
logging.level=INFO
logging.file=logs/creoson.log

# 安全配置
security.allow_localhost=true
security.cors_enabled=true
```

#### 3.2 环境变量设置

```batch
# 添加到系统环境变量
CREOSON_HOME=C:\CREOSON
PATH=%PATH%;%CREOSON_HOME%

# Java环境（如果未设置）
JAVA_HOME=C:\Program Files\Java\jre1.8.0_XXX
PATH=%PATH%;%JAVA_HOME%\bin
```

### 4. 启动CREOSON服务器

#### 4.1 手动启动

```batch
# 命令行启动
cd C:\CREOSON
CreosonServer.exe

# 或使用Java直接启动
java -jar creoson.jar
```

#### 4.2 自动启动脚本

创建 `start_creoson.bat`：

```batch
@echo off
echo 启动CREOSON服务器...
cd /d C:\CREOSON
start "CREOSON Server" CreosonServer.exe
echo CREOSON服务器已启动
echo 服务地址: http://localhost:9056
pause
```

### 5. 验证安装

#### 5.1 检查服务器状态

```bash
# 浏览器访问
http://localhost:9056/status

# 或使用curl
curl http://localhost:9056/status
```

#### 5.2 测试连接

```python
import requests

# 测试CREOSON连接
response = requests.post(
    "http://localhost:9056/creoson",
    json={
        "command": "creo",
        "function": "connect"
    }
)

print(f"连接状态: {response.json()}")
```

## 集成配置

### 1. Python环境配置

```bash
# 安装依赖
pip install requests
pip install creopyson  # 可选的Python包装器
```

### 2. 项目集成

更新 `s:\PG-Dev\project\src\creo\creoson_connector.py` 中的路径：

```python
# 更新CREOSON路径
creoson_path = "C:\\CREOSON\\CreosonServer.exe"

# 更新服务器URL
server_url = "http://localhost:9056"
```

### 3. Creo配置

在Creo中启用J-Link支持：

1. 启动Creo Parametric 10.0
2. 进入 **工具** → **选项** → **配置编辑器**
3. 添加配置选项：
   ```
   j_link_java_command java
   web_browser_homepage http://localhost:9056
   ```

## 使用示例

### 1. 基本连接测试

```python
from src.creo.creoson_connector import CreosonConnector

# 创建连接器
connector = CreosonConnector()

# 连接到Creo
if connector.connect():
    print("✅ CREOSON连接成功")
    
    # 创建零件
    connector.create_part("test_part")
    
    # 断开连接
    connector.disconnect()
else:
    print("❌ CREOSON连接失败")
```

### 2. 圆柱体创建

```python
from src.examples.create_cylinder_creoson import CreosonCylinderGenerator

# 创建生成器
generator = CreosonCylinderGenerator()

# 生成圆柱体
success = generator.create_steel_cylinder(
    diameter_cm=3.0,
    height_cm=10.0,
    material="不锈钢"
)
```

## 故障排除

### 常见问题

#### 1. 服务器启动失败

**问题**: `CreosonServer.exe` 无法启动

**解决方案**:
```bash
# 检查Java环境
java -version

# 检查端口占用
netstat -an | findstr 9056

# 手动启动并查看错误
java -jar creoson.jar
```

#### 2. Creo连接失败

**问题**: 无法连接到Creo Parametric

**解决方案**:
1. 确保Creo正在运行
2. 检查J-Link配置
3. 验证Creo版本兼容性

#### 3. 权限问题

**问题**: 访问被拒绝

**解决方案**:
```batch
# 以管理员身份运行
runas /user:Administrator "C:\CREOSON\CreosonServer.exe"
```

### 日志分析

```bash
# 查看CREOSON日志
type C:\CREOSON\logs\creoson.log

# 查看Creo日志
type %USERPROFILE%\AppData\Local\PTC\Creo\std.out
```

## 性能优化

### 1. 内存配置

```batch
# 增加Java堆内存
java -Xmx2G -jar creoson.jar
```

### 2. 网络优化

```properties
# creoson.properties
server.connection_timeout=30000
server.read_timeout=60000
```

### 3. 并发配置

```properties
# 最大并发连接数
server.max_connections=10
server.thread_pool_size=5
```

## 安全考虑

### 1. 网络安全

```properties
# 限制访问IP
security.allowed_hosts=localhost,127.0.0.1

# 启用认证（可选）
security.auth_enabled=false
```

### 2. 文件权限

```batch
# 设置适当的文件权限
icacls C:\CREOSON /grant Users:F
```

## 维护和更新

### 1. 定期更新

```bash
# 检查新版本
https://github.com/SimplifiedLogic/creoson/releases

# 备份配置
copy C:\CREOSON\config\* C:\CREOSON\backup\
```

### 2. 监控和日志

```python
# 自动监控脚本
import requests
import time

def monitor_creoson():
    while True:
        try:
            response = requests.get("http://localhost:9056/status", timeout=5)
            if response.status_code == 200:
                print("✅ CREOSON运行正常")
            else:
                print("⚠️ CREOSON状态异常")
        except:
            print("❌ CREOSON连接失败")
        
        time.sleep(60)  # 每分钟检查一次
```

## 总结

CREOSON为Creo 10提供了现代化的自动化接口，通过JSON API实现高效的CAD操作。正确安装和配置CREOSON后，可以显著提升AI辅助设计的自动化水平。

### 优势
- ✅ 现代化JSON API接口
- ✅ 跨语言支持
- ✅ 丰富的功能集
- ✅ 活跃的社区支持
- ✅ 开源免费

### 注意事项
- 🔄 需要Creo 10或更早版本
- 🔧 需要正确的Java环境
- 📋 需要适当的系统权限
- 🔍 需要定期维护和更新

---
*技术负责人: 雨俊*  
*创建时间: 2025-07-12*  
*版本: 1.0*