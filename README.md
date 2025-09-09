# 定投计算工具

自动化定投计算工具，根据预设的投资配比和市场行情，自动计算每周各标的的购买金额，并提供智能加仓建议。

## 功能特性

- 📊 **实时行情获取**：自动获取美股和加密货币的最新价格
- 💰 **智能定投计算**：根据目标配比自动分配每周投资资金
- 🚨 **大跌检测**：检测市场大跌并提供加仓建议
- 📋 **购买清单生成**：生成详细的购买操作清单
- 📈 **历史记录管理**：记录和分析投资历史数据
- 🎯 **配比再平衡**：自动检测配比偏离并调整

## 投资配置

### 目标配比
- **美股 (60%)**
  - QQQ: 35%
  - VOO: 20% 
  - GLDM: 5%

- **加密货币 (40%)**
  - BTC: 45%
  - BNB: 25%
  - SOL: 20%
  - ETH: 10%

### 投资限制
- 每周USD上限: 2000
- 每周TAO上限: 10
- 定投时间: 周二或周三

## 安装和设置

### 1. 安装依赖
```bash
pip install -r requirements.txt
```

### 2. 配置设置
编辑 `config.json` 文件，可以调整：
- 投资配比
- 资金限制
- 大跌检测阈值
- API密钥（可选）

### 3. 运行工具
```bash
# 查看当前价格
python invest_tool.py prices

# 计算本周定投金额
python invest_tool.py calc

# 检查大跌加仓机会
python invest_tool.py crash-check

# 生成购买清单
python invest_tool.py generate-list

# 查看历史记录
python invest_tool.py history
```

## 使用说明

### 查看当前价格
```bash
python invest_tool.py prices
```
显示所有标的的当前市场价格，包括美股、加密货币和TAO。

### 计算定投金额
```bash
python invest_tool.py calc
```
根据配置的目标配比和资金限制，计算本周各标的的投资金额。

### 大跌检测
```bash
python invest_tool.py crash-check
```
检测各标的是否出现显著下跌，并提供对应的加仓建议：
- 🟡 一级加仓：跌幅10-15%，投资金额×1.5
- 🟠 二级加仓：跌幅15-25%，投资金额×2.0  
- 🔴 三级加仓：跌幅>25%，投资金额×3.0

### 生成购买清单
```bash
python invest_tool.py generate-list
```
生成详细的购买清单，分为：
- 🏦 IBKR美股清单：精确到股数
- 🪙 Binance加密货币清单：精确到小数点后6位

### 历史记录查看
```bash
python invest_tool.py history
```
查看最近的投资记录，包括购买日期、标的、数量、价格等信息。

## 数据文件

工具会创建以下文件：
- `investment_history.json`: 投资历史记录
- `prices_cache.json`: 价格数据缓存
- `backups/`: 数据备份目录

## 高级功能

### 配比再平衡
当某标的实际配比偏离目标±5%时，系统会自动优先分配资金进行再平衡。

### 历史数据分析
- 计算平均成本
- 投资收益率统计
- 投资频率分析
- 数据导出到CSV

### 数据备份
```python
from history_manager import HistoryManager
manager = HistoryManager()
manager.backup_data()  # 创建数据备份
manager.export_to_csv('my_investments.csv')  # 导出到CSV
```

## 注意事项

1. **价格数据**：默认使用免费API获取价格，如果获取失败会使用模拟数据
2. **TAO价格**：需要确认TAO代币的准确价格源
3. **网络连接**：需要互联网连接获取实时价格
4. **数据备份**：建议定期备份 `investment_history.json` 文件

## 自定义配置

可以通过修改 `config.json` 来调整：

```json
{
  "portfolio": {
    "stock_allocation": {
      "QQQ": 0.35,
      "VOO": 0.20,
      "GLDM": 0.05
    },
    "crypto_allocation": {
      "BTC": 0.45,
      "BNB": 0.25,
      "SOL": 0.20,
      "ETH": 0.10
    }
  },
  "limits": {
    "weekly_usd_limit": 2000,
    "weekly_tao_limit": 10
  }
}
```

## 故障排除

### 价格获取失败
- 检查网络连接
- 确认API服务可用
- 查看是否达到API调用限制

### 配置错误
运行配置验证：
```python
from utils import validate_config
import json

with open('config.json') as f:
    config = json.load(f)
    
errors = validate_config(config)
if errors:
    for error in errors:
        print(f"配置错误: {error}")
```

### 历史数据问题
如果历史数据文件损坏，删除 `investment_history.json` 文件，系统会自动创建新的记录。

## 贡献

欢迎提交Issue和Pull Request来改进这个工具！

## 免责声明

这个工具仅用于投资计算辅助，不构成投资建议。投资有风险，请根据自己的风险承受能力谨慎投资。