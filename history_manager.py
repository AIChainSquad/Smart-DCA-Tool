"""
投资历史记录管理模块
负责存储、查询和分析投资历史数据
"""

import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import statistics


class HistoryManager:
    """投资历史记录管理器"""
    
    def __init__(self, data_file: str = 'investment_history.json'):
        self.data_file = data_file
        self.data = self._load_data()
    
    def _load_data(self) -> Dict[str, Any]:
        """加载历史数据"""
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, FileNotFoundError):
                print(f"⚠️  无法读取历史数据文件，创建新的记录")
        
        # 返回默认结构
        return {
            'investments': [],  # 投资记录列表
            'portfolio_snapshots': [],  # 组合快照
            'metadata': {
                'created_at': datetime.now().isoformat(),
                'version': '1.0'
            }
        }
    
    def _save_data(self):
        """保存数据到文件"""
        try:
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"❌ 保存历史数据失败: {e}")
    
    def record_investment(self, investment_data: Dict[str, Any]) -> bool:
        """记录一次投资
        
        Args:
            investment_data: 投资数据
            {
                'date': '2024-01-01',
                'stocks': [{'symbol': 'QQQ', 'quantity': 5, 'price': 350.0, 'total': 1750.0}],
                'cryptos': [{'symbol': 'BTC', 'quantity': 0.01, 'price': 45000.0, 'total': 450.0}],
                'market_snapshot': {'qqq_price': 350.0, 'btc_price': 45000.0},
                'total_invested': 2200.0,
                'tao_price': 500.0,
                'notes': '正常定投'
            }
        """
        
        try:
            # 添加时间戳
            investment_data['timestamp'] = datetime.now().isoformat()
            investment_data['id'] = len(self.data['investments']) + 1
            
            # 验证必要字段
            required_fields = ['date', 'total_invested']
            for field in required_fields:
                if field not in investment_data:
                    print(f"❌ 缺少必要字段: {field}")
                    return False
            
            # 添加到历史记录
            self.data['investments'].append(investment_data)
            
            # 保存到文件
            self._save_data()
            
            print(f"✅ 投资记录已保存: {investment_data['date']}")
            return True
            
        except Exception as e:
            print(f"❌ 记录投资失败: {e}")
            return False
    
    def get_recent_records(self, limit: int = 10) -> List[Dict[str, Any]]:
        """获取最近的投资记录"""
        investments = sorted(
            self.data['investments'], 
            key=lambda x: x.get('date', ''), 
            reverse=True
        )
        
        return investments[:limit]
    
    def get_records_by_date_range(self, start_date: str, end_date: str) -> List[Dict[str, Any]]:
        """根据日期范围获取记录"""
        records = []
        
        for investment in self.data['investments']:
            inv_date = investment.get('date', '')
            if start_date <= inv_date <= end_date:
                records.append(investment)
        
        return sorted(records, key=lambda x: x.get('date', ''))
    
    def get_average_cost(self, symbol: str) -> Optional[float]:
        """获取某标的的平均成本"""
        total_cost = 0
        total_quantity = 0
        
        for investment in self.data['investments']:
            # 检查股票
            for stock in investment.get('stocks', []):
                if stock.get('symbol') == symbol:
                    total_cost += stock.get('total', 0)
                    total_quantity += stock.get('quantity', 0)
            
            # 检查加密货币
            for crypto in investment.get('cryptos', []):
                if crypto.get('symbol') == symbol:
                    total_cost += crypto.get('total', 0)
                    total_quantity += crypto.get('quantity', 0)
        
        if total_quantity > 0:
            return total_cost / total_quantity
        
        return None
    
    def get_total_invested(self) -> Dict[str, float]:
        """获取总投资金额统计"""
        total_usd = 0
        total_by_asset = {}
        monthly_totals = {}
        
        for investment in self.data['investments']:
            amount = investment.get('total_invested', 0)
            total_usd += amount
            
            # 按日期统计
            date_str = investment.get('date', '')
            if date_str:
                month_key = date_str[:7]  # YYYY-MM
                monthly_totals[month_key] = monthly_totals.get(month_key, 0) + amount
            
            # 按资产统计
            for stock in investment.get('stocks', []):
                symbol = stock.get('symbol', '')
                total_by_asset[symbol] = total_by_asset.get(symbol, 0) + stock.get('total', 0)
            
            for crypto in investment.get('cryptos', []):
                symbol = crypto.get('symbol', '')
                total_by_asset[symbol] = total_by_asset.get(symbol, 0) + crypto.get('total', 0)
        
        return {
            'total_usd': total_usd,
            'by_asset': total_by_asset,
            'by_month': monthly_totals
        }
    
    def get_portfolio_composition(self) -> Dict[str, Any]:
        """获取当前投资组合构成"""
        holdings = {}  # {symbol: {'quantity': x, 'avg_cost': y, 'total_invested': z}}
        
        for investment in self.data['investments']:
            # 处理股票
            for stock in investment.get('stocks', []):
                symbol = stock.get('symbol', '')
                if symbol:
                    if symbol not in holdings:
                        holdings[symbol] = {'quantity': 0, 'total_cost': 0, 'type': 'stock'}
                    
                    holdings[symbol]['quantity'] += stock.get('quantity', 0)
                    holdings[symbol]['total_cost'] += stock.get('total', 0)
            
            # 处理加密货币
            for crypto in investment.get('cryptos', []):
                symbol = crypto.get('symbol', '')
                if symbol:
                    if symbol not in holdings:
                        holdings[symbol] = {'quantity': 0, 'total_cost': 0, 'type': 'crypto'}
                    
                    holdings[symbol]['quantity'] += crypto.get('quantity', 0)
                    holdings[symbol]['total_cost'] += crypto.get('total', 0)
        
        # 计算平均成本
        for symbol, data in holdings.items():
            if data['quantity'] > 0:
                data['avg_cost'] = data['total_cost'] / data['quantity']
            else:
                data['avg_cost'] = 0
        
        return holdings
    
    def calculate_returns(self, current_prices: Dict[str, float]) -> Dict[str, Any]:
        """计算投资收益
        
        Args:
            current_prices: 当前市价 {symbol: price}
        """
        portfolio = self.get_portfolio_composition()
        total_cost = 0
        current_value = 0
        asset_returns = {}
        
        for symbol, holding in portfolio.items():
            cost = holding['total_cost']
            quantity = holding['quantity']
            
            total_cost += cost
            
            if symbol in current_prices and quantity > 0:
                market_value = quantity * current_prices[symbol]
                current_value += market_value
                
                # 单个资产收益
                profit = market_value - cost
                return_percent = (profit / cost * 100) if cost > 0 else 0
                
                asset_returns[symbol] = {
                    'cost': cost,
                    'market_value': market_value,
                    'profit': profit,
                    'return_percent': return_percent,
                    'quantity': quantity,
                    'avg_cost': holding['avg_cost'],
                    'current_price': current_prices[symbol]
                }
        
        # 总体收益
        total_profit = current_value - total_cost
        total_return_percent = (total_profit / total_cost * 100) if total_cost > 0 else 0
        
        return {
            'total_cost': total_cost,
            'current_value': current_value,
            'total_profit': total_profit,
            'total_return_percent': total_return_percent,
            'asset_returns': asset_returns
        }
    
    def get_investment_frequency_stats(self) -> Dict[str, Any]:
        """获取投资频率统计"""
        if not self.data['investments']:
            return {}
        
        dates = [inv.get('date', '') for inv in self.data['investments'] if inv.get('date')]
        dates.sort()
        
        if len(dates) < 2:
            return {'total_investments': len(dates)}
        
        # 计算投资间隔
        intervals = []
        for i in range(1, len(dates)):
            try:
                date1 = datetime.strptime(dates[i-1], '%Y-%m-%d')
                date2 = datetime.strptime(dates[i], '%Y-%m-%d')
                intervals.append((date2 - date1).days)
            except ValueError:
                continue
        
        stats = {
            'total_investments': len(dates),
            'first_investment': dates[0],
            'last_investment': dates[-1],
            'investment_period_days': (datetime.strptime(dates[-1], '%Y-%m-%d') - 
                                     datetime.strptime(dates[0], '%Y-%m-%d')).days
        }
        
        if intervals:
            stats.update({
                'avg_interval_days': statistics.mean(intervals),
                'median_interval_days': statistics.median(intervals),
                'min_interval_days': min(intervals),
                'max_interval_days': max(intervals)
            })
        
        return stats
    
    def export_to_csv(self, filename: str = 'investment_export.csv') -> bool:
        """导出历史数据到CSV"""
        try:
            import csv
            
            with open(filename, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                
                # 写入表头
                headers = ['Date', 'Asset', 'Type', 'Symbol', 'Quantity', 'Price', 'Total', 'Notes']
                writer.writerow(headers)
                
                # 写入数据
                for investment in self.data['investments']:
                    date = investment.get('date', '')
                    notes = investment.get('notes', '')
                    
                    # 股票数据
                    for stock in investment.get('stocks', []):
                        row = [
                            date, 'Stock', stock.get('symbol', ''),
                            stock.get('quantity', 0), stock.get('price', 0),
                            stock.get('total', 0), notes
                        ]
                        writer.writerow(row)
                    
                    # 加密货币数据
                    for crypto in investment.get('cryptos', []):
                        row = [
                            date, 'Crypto', crypto.get('symbol', ''),
                            crypto.get('quantity', 0), crypto.get('price', 0),
                            crypto.get('total', 0), notes
                        ]
                        writer.writerow(row)
            
            print(f"✅ 数据已导出到: {filename}")
            return True
            
        except Exception as e:
            print(f"❌ 导出CSV失败: {e}")
            return False
    
    def backup_data(self, backup_dir: str = 'backups') -> bool:
        """备份历史数据"""
        try:
            os.makedirs(backup_dir, exist_ok=True)
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_file = f"{backup_dir}/investment_backup_{timestamp}.json"
            
            with open(backup_file, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, indent=2, ensure_ascii=False)
            
            print(f"✅ 数据已备份到: {backup_file}")
            return True
            
        except Exception as e:
            print(f"❌ 备份失败: {e}")
            return False


if __name__ == '__main__':
    # 测试历史记录管理功能
    manager = HistoryManager()
    
    # 测试记录投资
    test_investment = {
        'date': '2024-01-15',
        'stocks': [
            {'symbol': 'QQQ', 'quantity': 5, 'price': 350.0, 'total': 1750.0}
        ],
        'cryptos': [
            {'symbol': 'BTC', 'quantity': 0.01, 'price': 45000.0, 'total': 450.0}
        ],
        'total_invested': 2200.0,
        'tao_price': 500.0,
        'notes': '测试投资记录'
    }
    
    manager.record_investment(test_investment)
    
    # 测试查询功能
    recent = manager.get_recent_records(5)
    print(f"最近投资记录: {len(recent)} 条")
    
    # 测试统计功能
    stats = manager.get_total_invested()
    print(f"投资统计: {stats}")
    
    # 测试组合构成
    composition = manager.get_portfolio_composition()
    print(f"组合构成: {composition}")
    
    print("历史记录管理测试完成")