# ETH余额监控工具

一个功能强大的以太坊代币余额监控系统，支持多地址、多代币的实时监控和智能报警。

## 🚀 主要功能

- **多地址监控**: 同时监控多个以太坊地址
- **多代币支持**: 每个地址可监控多个ERC20代币
- **智能阈值**: 支持绝对值阈值和变化百分比阈值
- **声音报警**: 可配置的声音提醒系统
- **模块化架构**: 清晰的代码结构，易于维护和扩展
- **内存存储**: 轻量级，不依赖外部数据库
- **跨平台**: 支持Windows、macOS和Linux

## 📋 监控配置


## 🛠️ 安装和配置

### 1. 环境要求

- Python 3.8+
- pip

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 配置设置

#### 3.1 获取以太坊节点API密钥

您需要获取一个以太坊节点提供商的API密钥：

- [Alchemy](https://www.alchemy.com/) (推荐)
- [Infura](https://infura.io/)
- [QuickNode](https://www.quicknode.com/)

#### 3.2 修改配置文件

编辑 `config.yaml` 文件：

```yaml
rpc_settings:
  provider_url: "https://eth-mainnet.g.alchemy.com/v2/YOUR_API_KEY"  # 替换为您的API密钥
```

#### 3.3 自定义监控参数

根据需要调整以下参数：

- `check_interval_seconds`: 检查间隔（秒）
- 阈值设置：`min_balance`, `max_balance`, `change_percentage_up`, `change_percentage_down`
- 报警设置：`sound_repeat_count`, `alert_cooldown_minutes`

## 🚀 使用方法

### 启动监控

```bash
python main.py
```

### 测试模式

```bash
python main.py --test
```

### 指定配置文件

```bash
python main.py --config my_config.yaml
```

### 查看帮助

```bash
python main.py --help
```

## 📊 监控界面

启动后，您将看到：

1. **初始化信息**: 系统组件加载状态
2. **余额快照**: 当前所有监控地址的余额
3. **实时监控**: 定期检查和报警信息
4. **统计信息**: 停止时显示监控统计

## 🚨 报警系统

### 报警触发条件

1. **最小余额报警**: 余额低于设定的最小值
2. **最大余额报警**: 余额超过设定的最大值
3. **上涨报警**: 相比上次检查，余额上涨超过设定百分比
4. **下跌报警**: 相比上次检查，余额下跌超过设定百分比

### 报警方式

- **控制台输出**: 详细的报警信息
- **声音提醒**: 系统声音或自定义音频文件
- **日志记录**: 可选的日志文件记录

### 冷却机制

- 同一类型的报警在冷却期内不会重复触发
- 默认冷却期：5分钟（可配置）

## 🏗️ 架构说明

### 模块化设计

```
src/
├── config/          # 配置管理模块
│   ├── __init__.py
│   └── config_manager.py
├── blockchain/      # 区块链交互模块
│   ├── __init__.py
│   ├── web3_client.py
│   └── token_service.py
├── monitor/         # 监控引擎模块
│   ├── __init__.py
│   ├── balance_monitor.py
│   └── threshold_checker.py
├── alert/           # 报警系统模块
│   ├── __init__.py
│   ├── alert_manager.py
│   └── sound_player.py
└── __init__.py
```

### 核心组件

1. **ConfigManager**: 配置文件加载和验证
2. **Web3Client**: 以太坊网络连接和交互
3. **TokenService**: ERC20代币相关操作
4. **BalanceMonitor**: 余额监控和阈值检查
5. **AlertManager**: 报警管理和通知
6. **SoundPlayer**: 跨平台声音播放

## 🔧 高级配置

### 自定义声音文件

1. 将音频文件放置在项目目录
2. 修改配置文件中的 `sound_file_path`
3. 支持格式：WAV, MP3（取决于系统）

### 调整监控频率

- 生产环境建议：60-300秒
- 测试环境可设置：10-30秒
- 注意：频率过高可能触发API限制

### 扩展通知方式

可以通过添加自定义通知处理器来扩展报警方式：

```python
def custom_notification(alert_info, alert_message):
    # 自定义通知逻辑
    # 如：发送邮件、Webhook、微信消息等
    pass

alert_manager.add_notification_handler(custom_notification)
```

## 🔍 故障排除

### 常见问题

1. **连接失败**
   - 检查API密钥是否正确
   - 确认网络连接正常
   - 验证RPC URL格式

2. **代币余额获取失败**
   - 验证代币合约地址
   - 检查地址格式是否正确
   - 确认代币是否为标准ERC20

3. **声音播放失败**
   - 检查音频文件是否存在
   - 确认系统音频设备正常
   - 尝试使用系统默认提示音

### 日志调试

启用详细日志：

```yaml
logging:
  level: "DEBUG"
```

## 📝 更新日志

### v1.0.0 (当前版本)

- ✅ 基础监控功能
- ✅ 多地址、多代币支持
- ✅ 阈值报警系统
- ✅ 声音提醒功能
- ✅ 模块化架构
- ✅ 跨平台支持

## 🤝 支持和反馈

如有问题或建议，请通过以下方式联系：

- 查看日志文件获取详细错误信息
- 检查配置文件格式是否正确
- 确认所有依赖包已正确安装

## ⚠️ 注意事项

1. **API限制**: 请注意以太坊节点提供商的API调用限制
2. **网络稳定性**: 确保网络连接稳定，避免误报
3. **私钥安全**: 本工具仅读取余额，不需要私钥
4. **资源消耗**: 监控频率过高可能影响系统性能

## 📄 许可证

本项目采用MIT许可证，请查看LICENSE文件了解详情。
