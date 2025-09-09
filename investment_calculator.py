"""
定投计算模块
实现核心的投资计算逻辑，包括定投分配、配比调整、大跌检测等
"""

from typing import Dict, Optional, Any
from datetime import datetime, timedelta
import statistics
import math


class InvestmentCalculator:
    """投资计算器"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.portfolio = config['portfolio']
        self.limits = config['limits']
        self.crash_config = config['crash_detection']
        
    def calculate_weekly_investment(self, stock_prices: Dict[str, float], 
                                  crypto_prices: Dict[str, float], 
                                  tao_price: float) -> Dict[str, Any]:
        """计算本周定投金额分配"""
        
        # 资金分配规则：
        # 1. 计算总预算：美股上限 + TAO上限的USD等值
        # 2. 按6:4比例分配美股:加密货币
        # 3. 美股内部按配比分配，但不超过USD上限
        # 4. 加密货币内部按配比分配，但不超过TAO上限
        
        weekly_usd_limit = self.limits['weekly_usd_limit']  # 2000 USD 美股基准
        weekly_tao_limit = self.limits['weekly_tao_limit']   # TAO上限
        
        # 第1步：先计算美股投资（基于基准金额）
        stock_investments = self._calculate_stock_allocation(weekly_usd_limit, stock_prices)
        actual_stock_cost = sum(data['amount'] for data in stock_investments.values())
        
        # 第2步：根据美股实际花费，按6:4比例计算加密货币预算
        stock_weight = self.portfolio['stock_weight']  # 0.6
        crypto_weight = self.portfolio['crypto_weight']  # 0.4
        
        # 美股:加密 = 6:4，所以加密预算 = 美股实际花费 * (4/6)
        target_crypto_budget = actual_stock_cost * (crypto_weight / stock_weight)
        
        # 确保不超过TAO上限
        tao_usd_value = weekly_tao_limit * tao_price
        actual_crypto_budget = min(target_crypto_budget, tao_usd_value)
        
        # 第3步：计算加密货币分配
        crypto_investments = self._calculate_crypto_allocation(actual_crypto_budget, crypto_prices)
        
        return {
            'stock_total': actual_stock_cost,
            'crypto_total': actual_crypto_budget,
            'crypto_tao_amount': actual_crypto_budget / tao_price,
            'stocks': stock_investments,
            'cryptos': crypto_investments,
            'total_budget': actual_stock_cost + actual_crypto_budget
        }
    
    def _calculate_stock_allocation(self, budget: float, prices: Dict[str, float]) -> Dict[str, Any]:
        """计算美股分配（整股交易，允许超过预算50%）"""
        allocations = self.portfolio['stock_allocation']
        investments = {}
        
        # 先按配比计算理论股数，然后取整
        total_allocation = sum(allocations.values())
        max_budget = budget * 1.5  # 允许超过50%
        
        # 第一轮：按配比分配并取整
        for symbol, ratio in allocations.items():
            if symbol in prices:
                # 按配比分配金额
                target_amount = budget * (ratio / total_allocation)
                target_shares = target_amount / prices[symbol]
                
                # 取整股数（向上取整确保至少买1股）
                shares = max(1, round(target_shares))
                actual_amount = shares * prices[symbol]
                
                investments[symbol] = {
                    'amount': actual_amount,
                    'ratio': ratio,
                    'price': prices[symbol],
                    'shares': shares
                }
        
        # 检查总成本是否超过最大限额
        total_cost = sum(data['amount'] for data in investments.values())
        
        # 如果超过最大限额，优先减少贵的股票
        while total_cost > max_budget:
            # 找到单价最高且股数>1的标的
            max_price_symbol = None
            max_price = 0
            
            for symbol, data in investments.items():
                if data['shares'] > 1 and data['price'] > max_price:
                    max_price = data['price']
                    max_price_symbol = symbol
            
            if max_price_symbol:
                investments[max_price_symbol]['shares'] -= 1
                investments[max_price_symbol]['amount'] = (
                    investments[max_price_symbol]['shares'] * 
                    investments[max_price_symbol]['price']
                )
                total_cost = sum(data['amount'] for data in investments.values())
            else:
                break  # 所有标的都只有1股，无法再减少
        
        return investments
    
    def _calculate_crypto_allocation(self, budget: float, prices: Dict[str, float]) -> Dict[str, Any]:
        """计算加密货币分配"""
        allocations = self.portfolio['crypto_allocation']
        investments = {}
        
        for symbol, ratio in allocations.items():
            if symbol in prices:
                amount = budget * ratio
                investments[symbol] = {
                    'amount': amount,
                    'ratio': ratio,
                    'price': prices[symbol],
                    'quantity': amount / prices[symbol]
                }
        
        return investments
    
    def calculate_rebalancing_adjustment(self, current_portfolio: Dict[str, float], 
                                       target_allocation: Dict[str, float],
                                       weekly_budget: float) -> Dict[str, float]:
        """计算再平衡调整
        
        Args:
            current_portfolio: 当前持仓价值 {symbol: value}
            target_allocation: 目标配比 {symbol: ratio}
            weekly_budget: 本周投资预算
            
        Returns:
            调整后的投资分配 {symbol: amount}
        """
        
        total_portfolio_value = sum(current_portfolio.values()) + weekly_budget
        adjustments = {}
        
        for symbol, target_ratio in target_allocation.items():
            target_value = total_portfolio_value * target_ratio
            current_value = current_portfolio.get(symbol, 0)
            
            # 计算偏离程度
            if total_portfolio_value > 0:
                current_ratio = current_value / (total_portfolio_value - weekly_budget)
                deviation = abs(current_ratio - target_ratio)
                
                # 如果偏离超过5%，进行调整
                if deviation > 0.05:
                    needed_adjustment = target_value - current_value
                    # 限制单次调整不超过本周预算的50%
                    max_adjustment = weekly_budget * 0.5
                    adjustment = min(max_adjustment, max(0, needed_adjustment))
                    adjustments[symbol] = adjustment
        
        # 如果有调整，重新分配剩余预算
        if adjustments:
            total_adjustments = sum(adjustments.values())
            remaining_budget = weekly_budget - total_adjustments
            
            # 将剩余预算按原始配比分配
            if remaining_budget > 0:
                for symbol, target_ratio in target_allocation.items():
                    base_amount = remaining_budget * target_ratio
                    adjustments[symbol] = adjustments.get(symbol, 0) + base_amount
        else:
            # 没有需要调整的，按正常配比分配
            for symbol, target_ratio in target_allocation.items():
                adjustments[symbol] = weekly_budget * target_ratio
        
        return adjustments
    
    def detect_crash_opportunities(self, current_prices: Dict[str, float], 
                                 history_manager) -> Dict[str, Any]:
        """检测大跌加仓机会
        
        Args:
            current_prices: 当前价格 {symbol: price}
            history_manager: 历史数据管理器
            
        Returns:
            加仓机会 {symbol: opportunity_data}
        """
        
        opportunities = {}
        
        for symbol, current_price in current_prices.items():
            # 获取历史平均价格
            if symbol in ['QQQ', 'VOO', 'GLDM']:
                lookback_days = self.crash_config['stock_lookback_days']
            else:
                lookback_days = self.crash_config['crypto_lookback_days']
            
            avg_price = self._get_average_price(symbol, current_price, history_manager, lookback_days)
            
            if avg_price and avg_price > 0:
                # 计算跌幅
                drop_percent = (avg_price - current_price) / avg_price
                
                # 确定加仓等级
                crash_level, multiplier = self._determine_crash_level(drop_percent)
                
                if crash_level > 0:
                    # 计算建议投资金额
                    base_allocation = self._get_base_allocation(symbol)
                    weekly_budget = self._get_weekly_budget(symbol)
                    
                    base_amount = weekly_budget * base_allocation
                    suggested_amount = base_amount * multiplier
                    
                    opportunities[symbol] = {
                        'current_price': current_price,
                        'avg_price': avg_price,
                        'drop_percent': drop_percent * 100,
                        'crash_level': crash_level,
                        'multiplier': multiplier,
                        'base_amount': base_amount,
                        'suggested_amount': suggested_amount
                    }
        
        return opportunities
    
    def _get_average_price(self, symbol: str, current_price: float, 
                          history_manager, days: int) -> Optional[float]:
        """获取平均价格
        
        优先使用历史数据，如果没有则使用当前价格作为基准
        """
        try:
            # 尝试从历史记录获取平均成本
            avg_cost = history_manager.get_average_cost(symbol)
            if avg_cost and avg_cost > 0:
                return avg_cost
            
            # 如果没有历史记录，使用当前价格的一个倍数作为"高点"
            # 这里假设当前已经下跌了一些
            return current_price * 1.15  # 假设高点比当前价格高15%
            
        except Exception as e:
            print(f"获取 {symbol} 平均价格失败: {e}")
            return None
    
    def _determine_crash_level(self, drop_percent: float) -> tuple:
        """确定大跌等级和加仓倍数"""
        
        if drop_percent >= self.crash_config['level3_threshold']:
            return 3, self.crash_config['level3_multiplier']
        elif drop_percent >= self.crash_config['level2_threshold']:
            return 2, self.crash_config['level2_multiplier']
        elif drop_percent >= self.crash_config['level1_threshold']:
            return 1, self.crash_config['level1_multiplier']
        else:
            return 0, 1.0
    
    def _get_base_allocation(self, symbol: str) -> float:
        """获取标的基础配比"""
        if symbol in self.portfolio['stock_allocation']:
            return self.portfolio['stock_allocation'][symbol] * self.portfolio['stock_weight']
        elif symbol in self.portfolio['crypto_allocation']:
            return self.portfolio['crypto_allocation'][symbol] * self.portfolio['crypto_weight']
        else:
            return 0.0
    
    def _get_weekly_budget(self, symbol: str) -> float:
        """获取标的对应的周预算"""
        if symbol in ['QQQ', 'VOO', 'GLDM']:
            return self.limits['weekly_usd_limit']
        else:
            # 对于加密货币，需要转换TAO为USD
            # 这里简化处理，返回固定值
            return self.limits['weekly_tao_limit'] * 500  # 假设TAO价格500
    
    def calculate_optimal_purchase_units(self, amount: float, price: float, 
                                       asset_type: str = 'stock') -> Dict[str, Any]:
        """计算最优购买单位
        
        Args:
            amount: 投资金额
            price: 单价
            asset_type: 资产类型 ('stock' or 'crypto')
            
        Returns:
            购买信息
        """
        
        if asset_type == 'stock':
            # 美股按股数购买
            shares = int(amount / price)
            actual_cost = shares * price
            remainder = amount - actual_cost
            
            return {
                'units': shares,
                'unit_type': 'shares',
                'actual_cost': actual_cost,
                'remainder': remainder,
                'efficiency': actual_cost / amount if amount > 0 else 0
            }
        
        else:
            # 加密货币可以买小数
            quantity = amount / price
            
            return {
                'units': round(quantity, 6),
                'unit_type': 'coins',
                'actual_cost': amount,
                'remainder': 0,
                'efficiency': 1.0
            }
    
    def simulate_investment_outcome(self, investment_plan: Dict[str, Any], 
                                  price_changes: Dict[str, float]) -> Dict[str, Any]:
        """模拟投资结果
        
        Args:
            investment_plan: 投资计划
            price_changes: 价格变化百分比 {symbol: change_percent}
            
        Returns:
            模拟结果
        """
        
        results = {
            'initial_value': 0,
            'final_value': 0,
            'total_return': 0,
            'return_percent': 0,
            'asset_performance': {}
        }
        
        # 计算股票部分
        for symbol, data in investment_plan.get('stocks', {}).items():
            initial_value = data['amount']
            price_change = price_changes.get(symbol, 0)
            final_value = initial_value * (1 + price_change)
            
            results['initial_value'] += initial_value
            results['final_value'] += final_value
            
            results['asset_performance'][symbol] = {
                'initial_value': initial_value,
                'final_value': final_value,
                'return': final_value - initial_value,
                'return_percent': price_change * 100
            }
        
        # 计算加密货币部分
        for symbol, data in investment_plan.get('cryptos', {}).items():
            initial_value = data['amount']
            price_change = price_changes.get(symbol, 0)
            final_value = initial_value * (1 + price_change)
            
            results['initial_value'] += initial_value
            results['final_value'] += final_value
            
            results['asset_performance'][symbol] = {
                'initial_value': initial_value,
                'final_value': final_value,
                'return': final_value - initial_value,
                'return_percent': price_change * 100
            }
        
        # 计算总体收益
        results['total_return'] = results['final_value'] - results['initial_value']
        if results['initial_value'] > 0:
            results['return_percent'] = (results['total_return'] / results['initial_value']) * 100
        
        return results


if __name__ == '__main__':
    # 测试投资计算功能
    import json
    
    with open('config.json', 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    calculator = InvestmentCalculator(config)
    
    # 模拟价格数据
    stock_prices = {'QQQ': 350.0, 'VOO': 420.0, 'GLDM': 36.0}
    crypto_prices = {'BTC': 45000.0, 'BNB': 280.0, 'SOL': 98.0, 'ETH': 2800.0}
    tao_price = 500.0
    
    # 测试定投计算
    investment_plan = calculator.calculate_weekly_investment(
        stock_prices, crypto_prices, tao_price
    )
    
    print("定投计算结果:")
    print(json.dumps(investment_plan, indent=2, ensure_ascii=False))