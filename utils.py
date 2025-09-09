"""
工具函数模块
包含格式化、打印表格等通用功能
"""

from typing import List, Dict, Any
import os


def format_currency(amount: float, currency: str = 'USD') -> str:
    """格式化货币显示"""
    if currency == 'USD':
        return f"${amount:,.2f}"
    elif currency == 'TAO':
        return f"{amount:.4f} TAO"
    else:
        return f"{amount:,.2f} {currency}"


def format_percentage(value: float, decimal_places: int = 2) -> str:
    """格式化百分比显示"""
    return f"{value:.{decimal_places}f}%"


def format_quantity(quantity: float, asset_type: str = 'stock') -> str:
    """格式化数量显示"""
    if asset_type == 'stock':
        return f"{int(quantity)}"
    else:
        return f"{quantity:.6f}"


def print_table(data: List[Dict[str, Any]], headers: List[str] = None, title: str = None):
    """打印表格
    
    Args:
        data: 表格数据，每行是一个字典
        headers: 表头列表，如果为None则使用第一行的键
        title: 表格标题
    """
    
    if not data:
        print("无数据显示")
        return
    
    # 确定表头
    if headers is None:
        headers = list(data[0].keys())
    
    # 计算每列的最大宽度
    col_widths = {}
    for header in headers:
        col_widths[header] = len(str(header))
    
    for row in data:
        for header in headers:
            value = str(row.get(header, ''))
            col_widths[header] = max(col_widths[header], len(value))
    
    # 打印标题
    if title:
        print(f"\n{title}")
        print("=" * len(title))
    
    # 打印表头
    header_line = " | ".join(str(header).ljust(col_widths[header]) for header in headers)
    print(header_line)
    print("-" * len(header_line))
    
    # 打印数据行
    for row in data:
        data_line = " | ".join(str(row.get(header, '')).ljust(col_widths[header]) for header in headers)
        print(data_line)


def print_summary_box(title: str, items: Dict[str, str], width: int = 50):
    """打印摘要框
    
    Args:
        title: 标题
        items: 要显示的项目 {标签: 值}
        width: 框的宽度
    """
    
    print("=" * width)
    print(f"{title:^{width}}")
    print("=" * width)
    
    for label, value in items.items():
        print(f"{label:<20} : {value}")
    
    print("=" * width)


def print_portfolio_allocation(allocation: Dict[str, float], title: str = "投资配比"):
    """打印投资组合配比"""
    print(f"\n📊 {title}")
    print("-" * 30)
    
    total = sum(allocation.values())
    
    for asset, amount in sorted(allocation.items(), key=lambda x: x[1], reverse=True):
        percentage = (amount / total * 100) if total > 0 else 0
        bar_length = int(percentage / 2)  # 每2%一个字符
        bar = "█" * bar_length + "░" * (50 - bar_length)
        
        print(f"{asset:>6} │{bar}│ {percentage:5.1f}% (${amount:>8.2f})")
    
    print("-" * 30)
    print(f"{'Total':>6} │{'█' * 50}│ 100.0% (${total:>8.2f})")


def print_crash_alerts(opportunities: Dict[str, Any]):
    """打印大跌警报"""
    if not opportunities:
        print("✅ 当前没有检测到大跌机会")
        return
    
    print("🚨 大跌加仓机会")
    print("=" * 60)
    
    for symbol, data in opportunities.items():
        level = data['crash_level']
        level_emoji = "🟡" if level == 1 else "🟠" if level == 2 else "🔴"
        
        print(f"\n{level_emoji} {symbol} - {level}级加仓机会")
        print(f"  当前价格: {format_currency(data['current_price'])}")
        print(f"  平均成本: {format_currency(data['avg_price'])}")
        print(f"  跌幅: {format_percentage(data['drop_percent'])}")
        print(f"  建议倍数: ×{data['multiplier']}")
        print(f"  建议金额: {format_currency(data['suggested_amount'])}")


def create_progress_bar(current: float, total: float, width: int = 30, 
                       label: str = "") -> str:
    """创建进度条"""
    if total == 0:
        percentage = 0
    else:
        percentage = min(100, (current / total) * 100)
    
    filled_width = int(width * percentage / 100)
    bar = "█" * filled_width + "░" * (width - filled_width)
    
    return f"{label} [{bar}] {percentage:5.1f}%"


def calculate_color_code(value: float, thresholds: List[float] = [-10, -5, 0, 5, 10]) -> str:
    """根据数值计算颜色代码（用于收益率显示）"""
    if value <= thresholds[0]:
        return "🔴"  # 深红
    elif value <= thresholds[1]:
        return "🟠"  # 橙色
    elif value <= thresholds[2]:
        return "🟡"  # 黄色
    elif value <= thresholds[3]:
        return "🟢"  # 绿色
    else:
        return "💚"  # 深绿


def format_investment_summary(investment_plan: Dict[str, Any], 
                            current_prices: Dict[str, float]) -> str:
    """格式化投资摘要"""
    summary = []
    summary.append("📋 本周投资计划")
    summary.append("=" * 40)
    
    # 美股部分
    if 'stocks' in investment_plan:
        summary.append("\n🏦 美股投资 (IBKR)")
        summary.append("-" * 25)
        stock_total = 0
        
        for symbol, data in investment_plan['stocks'].items():
            price = current_prices.get(symbol, 0)
            shares = int(data['amount'] / price) if price > 0 else 0
            actual_cost = shares * price
            stock_total += actual_cost
            
            summary.append(f"{symbol}: {shares}股 × {format_currency(price)} = {format_currency(actual_cost)}")
        
        summary.append(f"小计: {format_currency(stock_total)}")
    
    # 加密货币部分
    if 'cryptos' in investment_plan:
        summary.append("\n🪙 加密货币投资 (Binance)")
        summary.append("-" * 25)
        crypto_total = 0
        
        for symbol, data in investment_plan['cryptos'].items():
            price = current_prices.get(symbol, 0)
            quantity = data['amount'] / price if price > 0 else 0
            crypto_total += data['amount']
            
            summary.append(f"{symbol}: {quantity:.6f} × {format_currency(price)} = {format_currency(data['amount'])}")
        
        summary.append(f"小计: {format_currency(crypto_total)}")
        
        # TAO等值
        if 'crypto_tao_amount' in investment_plan:
            tao_amount = investment_plan['crypto_tao_amount']
            summary.append(f"TAO等值: {format_currency(tao_amount, 'TAO')}")
    
    # 总计
    total = investment_plan.get('total_budget', 0)
    summary.append(f"\n💰 总投资额: {format_currency(total)}")
    
    return "\n".join(summary)


def validate_config(config: Dict[str, Any]) -> List[str]:
    """验证配置文件的有效性"""
    errors = []
    
    # 检查必要的顶级键
    required_keys = ['portfolio', 'limits', 'crash_detection']
    for key in required_keys:
        if key not in config:
            errors.append(f"缺少配置项: {key}")
    
    # 检查投资组合配置
    if 'portfolio' in config:
        portfolio = config['portfolio']
        
        # 检查股票配比
        if 'stock_allocation' in portfolio:
            stock_total = sum(portfolio['stock_allocation'].values())
            if abs(stock_total - 1.0) > 0.01:
                errors.append(f"股票配比总和应为1.0，当前为{stock_total:.3f}")
        
        # 检查加密货币配比
        if 'crypto_allocation' in portfolio:
            crypto_total = sum(portfolio['crypto_allocation'].values())
            if abs(crypto_total - 1.0) > 0.01:
                errors.append(f"加密货币配比总和应为1.0，当前为{crypto_total:.3f}")
        
        # 检查权重
        if 'stock_weight' in portfolio and 'crypto_weight' in portfolio:
            total_weight = portfolio['stock_weight'] + portfolio['crypto_weight']
            if abs(total_weight - 1.0) > 0.01:
                errors.append(f"股票和加密货币权重总和应为1.0，当前为{total_weight:.3f}")
    
    # 检查限制配置
    if 'limits' in config:
        limits = config['limits']
        if 'weekly_usd_limit' not in limits or limits['weekly_usd_limit'] <= 0:
            errors.append("weekly_usd_limit 必须大于0")
        if 'weekly_tao_limit' not in limits or limits['weekly_tao_limit'] <= 0:
            errors.append("weekly_tao_limit 必须大于0")
    
    return errors


def get_terminal_width() -> int:
    """获取终端宽度"""
    try:
        return os.get_terminal_size().columns
    except OSError:
        return 80  # 默认宽度


if __name__ == '__main__':
    # 测试工具函数
    print("测试格式化函数:")
    print(f"货币: {format_currency(1234.567)}")
    print(f"百分比: {format_percentage(12.345)}")
    print(f"股票数量: {format_quantity(123)}")
    print(f"加密货币数量: {format_quantity(0.123456, 'crypto')}")
    
    # 测试表格打印
    test_data = [
        {'Symbol': 'QQQ', 'Price': 350.25, 'Shares': 5, 'Total': 1751.25},
        {'Symbol': 'BTC', 'Price': 45000.0, 'Shares': 0.01, 'Total': 450.0}
    ]
    
    print_table(test_data, title="测试投资数据")
    
    # 测试配比显示
    test_allocation = {'QQQ': 700, 'VOO': 400, 'GLDM': 100, 'BTC': 450, 'ETH': 350}
    print_portfolio_allocation(test_allocation)
    
    print("\n工具函数测试完成")