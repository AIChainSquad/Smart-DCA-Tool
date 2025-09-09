"""
价格数据获取模块
从各种API获取美股和加密货币的实时价格
"""

import requests
import json
import time
from datetime import datetime, timedelta
from typing import Dict, Optional


class PriceFetcher:
    """价格数据获取器"""
    
    def __init__(self):
        self.cache = {}
        self.cache_expiry = {}
        self.cache_duration = 3600  # 缓存1小时
        
    def _is_cache_valid(self, key: str) -> bool:
        """检查缓存是否有效"""
        if key not in self.cache_expiry:
            return False
        return datetime.now() < self.cache_expiry[key]
    
    def _set_cache(self, key: str, data: any):
        """设置缓存"""
        self.cache[key] = data
        self.cache_expiry[key] = datetime.now() + timedelta(seconds=self.cache_duration)
    
    def get_stock_prices(self) -> Dict[str, float]:
        """获取美股价格 (QQQ, VOO, GLDM)"""
        cache_key = 'stock_prices'
        
        if self._is_cache_valid(cache_key):
            return self.cache[cache_key]
        
        symbols = ['QQQ', 'VOO', 'GLDM']
        prices = {}
        
        try:
            # 使用Yahoo Finance API
            for symbol in symbols:
                price = self._fetch_yahoo_price(symbol)
                if price:
                    prices[symbol] = price
                time.sleep(0.1)  # 避免请求过于频繁
            
            if len(prices) == len(symbols):
                self._set_cache(cache_key, prices)
                print(f"✅ 成功获取美股价格")
                return prices
            else:
                print(f"⚠️  美股价格获取不完整，获取到 {len(prices)}/{len(symbols)} 个")
                
        except Exception as e:
            print(f"❌ 获取美股价格失败: {e}")
            
        # 返回模拟数据用于测试
        fallback_prices = {
            'QQQ': 350.25,
            'VOO': 420.80,
            'GLDM': 35.90
        }
        print("⚠️  使用模拟价格数据")
        return fallback_prices
    
    def get_crypto_prices(self) -> Dict[str, float]:
        """获取加密货币价格 (BTC, BNB, SOL, ETH)"""
        cache_key = 'crypto_prices'
        
        if self._is_cache_valid(cache_key):
            return self.cache[cache_key]
        
        try:
            # 使用币安API获取价格
            symbols = ['BTCUSDT', 'BNBUSDT', 'SOLUSDT', 'ETHUSDT']
            prices = {}
            
            for symbol in symbols:
                try:
                    url = f"https://api.binance.com/api/v3/ticker/price?symbol={symbol}"
                    response = requests.get(url, timeout=10)
                    response.raise_for_status()
                    data = response.json()
                    
                    # 映射币安交易对到我们的符号
                    symbol_map = {
                        'BTCUSDT': 'BTC',
                        'BNBUSDT': 'BNB', 
                        'SOLUSDT': 'SOL',
                        'ETHUSDT': 'ETH'
                    }
                    
                    if symbol in symbol_map:
                        prices[symbol_map[symbol]] = float(data['price'])
                    
                    time.sleep(0.1)  # 避免请求过于频繁
                    
                except Exception as e:
                    print(f"获取 {symbol} 价格失败: {e}")
                    continue
            
            if len(prices) == 4:  # 成功获取所有价格
                self._set_cache(cache_key, prices)
                print(f"✅ 成功获取加密货币价格 (币安)")
                return prices
            else:
                print(f"⚠️  加密货币价格获取不完整，获取到 {len(prices)}/4 个")
                
        except Exception as e:
            print(f"❌ 获取加密货币价格失败: {e}")
            
        # 返回模拟数据用于测试
        fallback_prices = {
            'BTC': 45000.0,
            'BNB': 280.0,
            'SOL': 98.0,
            'ETH': 2800.0
        }
        print("⚠️  使用模拟加密货币价格数据")
        return fallback_prices
    
    def get_tao_price(self) -> Optional[float]:
        """获取TAO代币价格"""
        cache_key = 'tao_price'
        
        if self._is_cache_valid(cache_key):
            return self.cache[cache_key]
        
        try:
            # 尝试从币安获取TAO价格 (如果币安有TAO交易对)
            tao_symbols = ['TAOUSDT', 'TAOUSD']  # 尝试不同的交易对
            
            for symbol in tao_symbols:
                try:
                    url = f"https://api.binance.com/api/v3/ticker/price?symbol={symbol}"
                    response = requests.get(url, timeout=10)
                    response.raise_for_status()
                    data = response.json()
                    
                    price = float(data['price'])
                    self._set_cache(cache_key, price)
                    print(f"✅ 成功获取TAO价格 (币安): ${price}")
                    return price
                    
                except Exception as e:
                    # 这个交易对不存在，尝试下一个
                    continue
            
            # 如果币安没有，尝试其他交易所API (如Gate.io, OKX等)
            try:
                # 尝试Gate.io API
                url = "https://api.gateio.ws/api/v4/spot/tickers?currency_pair=TAO_USDT"
                response = requests.get(url, timeout=10)
                response.raise_for_status()
                data = response.json()
                
                if data and len(data) > 0:
                    price = float(data[0]['last'])
                    self._set_cache(cache_key, price)
                    print(f"✅ 成功获取TAO价格 (Gate.io): ${price}")
                    return price
                    
            except Exception as e:
                print(f"Gate.io API失败: {e}")
            
        except Exception as e:
            print(f"⚠️  获取TAO价格失败: {e}")
        
        # 如果所有方法都失败，返回固定价格
        fallback_price = 318.21  # 使用你刚才看到的价格作为默认值
        print(f"⚠️  使用默认TAO价格: ${fallback_price}")
        return fallback_price
    
    def _fetch_yahoo_price(self, symbol: str) -> Optional[float]:
        """从Yahoo Finance获取单个股票价格"""
        try:
            # Yahoo Finance查询URL
            url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if 'chart' in data and 'result' in data['chart']:
                result = data['chart']['result'][0]
                if 'meta' in result and 'regularMarketPrice' in result['meta']:
                    return float(result['meta']['regularMarketPrice'])
                    
        except Exception as e:
            print(f"获取 {symbol} 价格失败: {e}")
            
        return None
    
    def get_historical_prices(self, symbol: str, days: int) -> Dict[str, float]:
        """获取历史价格数据用于计算平均价格"""
        cache_key = f'historical_{symbol}_{days}'
        
        if self._is_cache_valid(cache_key):
            return self.cache[cache_key]
        
        try:
            if symbol in ['QQQ', 'VOO', 'GLDM']:
                # 美股历史数据
                prices = self._fetch_stock_historical(symbol, days)
            else:
                # 加密货币历史数据
                prices = self._fetch_crypto_historical(symbol, days)
            
            if prices:
                self._set_cache(cache_key, prices)
                return prices
                
        except Exception as e:
            print(f"获取 {symbol} 历史价格失败: {e}")
        
        return {}
    
    def _fetch_stock_historical(self, symbol: str, days: int) -> Dict[str, float]:
        """获取美股历史价格"""
        # 这里可以实现调用Alpha Vantage或其他API获取历史数据
        # 为简化，返回模拟数据
        return {}
    
    def _fetch_crypto_historical(self, symbol: str, days: int) -> Dict[str, float]:
        """获取加密货币历史价格"""
        try:
            # 使用币安K线数据获取历史价格
            symbol_map = {
                'BTC': 'BTCUSDT',
                'BNB': 'BNBUSDT', 
                'SOL': 'SOLUSDT',
                'ETH': 'ETHUSDT'
            }
            
            if symbol not in symbol_map:
                return {}
            
            binance_symbol = symbol_map[symbol]
            
            # 计算开始时间 (毫秒时间戳)
            end_time = int(datetime.now().timestamp() * 1000)
            start_time = end_time - (days * 24 * 60 * 60 * 1000)
            
            url = f"https://api.binance.com/api/v3/klines?symbol={binance_symbol}&interval=1d&startTime={start_time}&endTime={end_time}"
            
            response = requests.get(url, timeout=15)
            response.raise_for_status()
            
            data = response.json()
            
            prices = {}
            for kline in data:
                # kline format: [timestamp, open, high, low, close, volume, ...]
                timestamp = int(kline[0])
                close_price = float(kline[4])  # 收盘价
                date_str = datetime.fromtimestamp(timestamp/1000).strftime('%Y-%m-%d')
                prices[date_str] = close_price
            
            return prices
                
        except Exception as e:
            print(f"获取 {symbol} 历史价格失败: {e}")
        
        return {}
    
    def update_all_prices(self) -> Dict[str, any]:
        """更新所有价格数据"""
        print("🔄 更新所有价格数据...")
        
        stock_prices = self.get_stock_prices()
        crypto_prices = self.get_crypto_prices()
        tao_price = self.get_tao_price()
        
        all_prices = {
            'stocks': stock_prices,
            'cryptos': crypto_prices,
            'tao': tao_price,
            'timestamp': datetime.now().isoformat()
        }
        
        # 保存到本地文件
        try:
            with open('prices_cache.json', 'w', encoding='utf-8') as f:
                json.dump(all_prices, f, indent=2, ensure_ascii=False)
            print("💾 价格数据已保存到本地")
        except Exception as e:
            print(f"保存价格数据失败: {e}")
        
        return all_prices


if __name__ == '__main__':
    # 测试价格获取功能
    fetcher = PriceFetcher()
    
    print("测试价格获取功能...")
    
    stocks = fetcher.get_stock_prices()
    print(f"美股价格: {stocks}")
    
    cryptos = fetcher.get_crypto_prices()
    print(f"加密货币价格: {cryptos}")
    
    tao = fetcher.get_tao_price()
    print(f"TAO价格: ${tao}")
    
    # 更新所有价格
    all_prices = fetcher.update_all_prices()
    print("所有价格数据更新完成")