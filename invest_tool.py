#!/usr/bin/env python3
"""
定投计算工具
自动计算每周各标的的购买金额，提供智能加仓建议
"""

import argparse
import json
import sys
import math
from datetime import datetime
from price_fetcher import PriceFetcher
from investment_calculator import InvestmentCalculator
from history_manager import HistoryManager
from utils import format_currency, print_table


def load_config():
    """加载配置文件"""
    try:
        with open('config.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print("错误: 找不到配置文件 config.json")
        sys.exit(1)
    except json.JSONDecodeError:
        print("错误: 配置文件格式不正确")
        sys.exit(1)


def show_current_prices(price_fetcher):
    """显示当前市场价格"""
    print("\n=== 当前市场价格 ===")
    
    # 获取美股价格
    stock_prices = price_fetcher.get_stock_prices()
    if stock_prices:
        print("\n美股:")
        for symbol, price in stock_prices.items():
            print(f"  {symbol}: ${price:.2f}")
    
    # 获取加密货币价格
    crypto_prices = price_fetcher.get_crypto_prices()
    if crypto_prices:
        print("\n加密货币:")
        for symbol, price in crypto_prices.items():
            print(f"  {symbol}: ${price:.2f}")
    
    # 获取TAO价格
    tao_price = price_fetcher.get_tao_price()
    if tao_price:
        print(f"\nTAO: ${tao_price:.2f}")


def calculate_weekly_investment(config):
    """计算本周定投金额"""
    print("\n=== 本周定投计算 ===")
    
    price_fetcher = PriceFetcher()
    calculator = InvestmentCalculator(config)
    
    # 获取当前价格
    stock_prices = price_fetcher.get_stock_prices()
    crypto_prices = price_fetcher.get_crypto_prices()
    tao_price = price_fetcher.get_tao_price()
    
    if not all([stock_prices, crypto_prices, tao_price]):
        print("错误: 无法获取完整的价格数据")
        return
    
    # 计算投资金额
    investment_plan = calculator.calculate_weekly_investment(
        stock_prices, crypto_prices, tao_price
    )
    
    # 显示结果
    print(f"\n总投资预算:")
    print(f"  美股部分: ${investment_plan['stock_total']:.2f}")
    print(f"  加密货币部分: ${investment_plan['crypto_total']:.2f} (TAO: {investment_plan['crypto_total']/tao_price:.4f})")
    
    print(f"\n美股购买计划 (IBKR):")
    for symbol, data in investment_plan['stocks'].items():
        shares = data['shares']  # 使用计算器计算的股数
        actual_cost = data['amount']  # 使用计算器计算的实际成本
        print(f"  {symbol}: {shares}股 × ${stock_prices[symbol]:.2f} = ${actual_cost:.2f}")
    
    print(f"\n加密货币购买计划 (Binance):")
    for symbol, data in investment_plan['cryptos'].items():
        quantity = data['amount'] / crypto_prices[symbol]
        tao_cost = data['amount'] / tao_price
        tao_cost_rounded = math.ceil(tao_cost * 100) / 100  # 向上取整到2位小数
        print(f"  {symbol}: {quantity:.6f} × ${crypto_prices[symbol]:.2f} = {tao_cost_rounded:.2f} TAO")


def check_crash_opportunity(config):
    """检查大跌加仓机会"""
    print("\n=== 大跌检测与加仓建议 ===")
    
    price_fetcher = PriceFetcher()
    calculator = InvestmentCalculator(config)
    history = HistoryManager()
    
    # 获取当前价格和历史数据
    current_prices = {
        **price_fetcher.get_stock_prices(),
        **price_fetcher.get_crypto_prices()
    }
    
    # 检查每个标的的跌幅
    crash_opportunities = calculator.detect_crash_opportunities(current_prices, history)
    
    if not crash_opportunities:
        print("当前没有检测到显著的下跌机会")
        return
    
    print("检测到以下加仓机会:")
    for asset, data in crash_opportunities.items():
        print(f"\n{asset}:")
        print(f"  当前价格: ${data['current_price']:.2f}")
        print(f"  平均成本: ${data['avg_price']:.2f}")
        print(f"  跌幅: {data['drop_percent']:.1f}%")
        print(f"  建议加仓: {data['crash_level']}级 (×{data['multiplier']})")
        print(f"  建议金额: ${data['suggested_amount']:.2f}")


def show_history():
    """显示历史投资记录"""
    print("\n=== 投资历史记录 ===")
    
    history = HistoryManager()
    records = history.get_recent_records(10)
    
    if not records:
        print("暂无投资记录")
        return
    
    print(f"\n最近10次投资记录:")
    for record in records:
        print(f"\n{record['date']}:")
        if record['stocks']:
            print("  美股:")
            for purchase in record['stocks']:
                print(f"    {purchase['symbol']}: {purchase['quantity']}股 × ${purchase['price']:.2f} = ${purchase['total']:.2f}")
        
        if record['cryptos']:
            print("  加密货币:")
            for purchase in record['cryptos']:
                print(f"    {purchase['symbol']}: {purchase['quantity']:.6f} × ${purchase['price']:.2f} = ${purchase['total']:.2f}")


def generate_purchase_list(config):
    """生成购买清单"""
    print("\n=== 生成购买清单 ===")
    
    price_fetcher = PriceFetcher()
    calculator = InvestmentCalculator(config)
    
    # 获取价格数据
    stock_prices = price_fetcher.get_stock_prices()
    crypto_prices = price_fetcher.get_crypto_prices()
    tao_price = price_fetcher.get_tao_price()
    
    if not all([stock_prices, crypto_prices, tao_price]):
        print("错误: 无法获取完整的价格数据")
        return
    
    # 计算投资计划
    investment_plan = calculator.calculate_weekly_investment(
        stock_prices, crypto_prices, tao_price
    )
    
    # 生成购买清单
    today = datetime.now().strftime("%Y-%m-%d")
    
    print(f"\n📋 购买清单 - {today}")
    print("=" * 50)
    
    print("\n🏦 IBKR 美股购买清单:")
    print("-" * 30)
    stock_total = 0
    for symbol, data in investment_plan['stocks'].items():
        shares = data['shares']  # 使用计算器计算的股数
        actual_cost = data['amount']  # 使用计算器计算的实际成本
        stock_total += actual_cost
        print(f"{symbol}: 买入 {shares} 股 @ ${stock_prices[symbol]:.2f} = ${actual_cost:.2f}")
    print(f"小计: ${stock_total:.2f}")
    
    print(f"\n🪙 Binance 加密货币购买清单:")
    print("-" * 30)
    crypto_total_usd = 0
    crypto_total_tao = 0
    for symbol, data in investment_plan['cryptos'].items():
        quantity = data['amount'] / crypto_prices[symbol]
        tao_cost = data['amount'] / tao_price
        tao_cost_rounded = math.ceil(tao_cost * 100) / 100  # 向上取整到2位小数
        crypto_total_usd += data['amount']
        crypto_total_tao += tao_cost_rounded  # 使用向上取整后的值
        print(f"{symbol}: 买入 {quantity:.6f} @ ${crypto_prices[symbol]:.2f} = {tao_cost_rounded:.2f} TAO")
    print(f"小计: {crypto_total_tao:.2f} TAO (约 ${crypto_total_usd:.2f})")
    
    print(f"\n💰 总计: ${stock_total + crypto_total_usd:.2f}")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='定投计算工具')
    parser.add_argument('command', choices=['calc', 'prices', 'history', 'crash-check', 'generate-list'],
                       help='执行的命令')
    
    args = parser.parse_args()
    config = load_config()
    
    print("📈 定投计算工具")
    print("=" * 40)
    
    if args.command == 'prices':
        price_fetcher = PriceFetcher()
        show_current_prices(price_fetcher)
    
    elif args.command == 'calc':
        calculate_weekly_investment(config)
    
    elif args.command == 'crash-check':
        check_crash_opportunity(config)
    
    elif args.command == 'history':
        show_history()
    
    elif args.command == 'generate-list':
        generate_purchase_list(config)


if __name__ == '__main__':
    main()