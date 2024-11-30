import requests
import time
from typing import Dict, Tuple, Optional
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import BAIDU_API_KEYS

class BaiduMapAPI:
    def __init__(self):
        self.api_keys = BAIDU_API_KEYS
        self.current_key_index = 0
        self.key_usage = {key: 0 for key in self.api_keys}
        self.max_daily_usage = 5000  # 设置每个密钥的每日配额
        self.base_url = "http://api.map.baidu.com"
        
    def _get_available_key(self):
        """获取可用的API密钥"""
        for _ in range(len(self.api_keys)):
            current_key = self.api_keys[self.current_key_index]
            if self.key_usage[current_key] < self.max_daily_usage:
                return current_key
            self._switch_to_next_key()
        raise Exception("所有API密钥已达到使用限制")
        
    def _update_key_usage(self, key):
        """更新密钥使用次数"""
        self.key_usage[key] += 1
    
    def _switch_to_next_key(self) -> None:
        """切换到下一个API密钥"""
        self.current_key_index = (self.current_key_index + 1) % len(self.api_keys)
    
    def _handle_api_response(self, response: requests.Response) -> Dict:
        """处理API响应"""
        if response.status_code != 200:
            raise Exception(f"API请求失败: {response.status_code}")
            
        data = response.json()
        if data.get('status') != 0:
            # 如果是配额超限，切换到下一个密钥
            if data.get('status') == 302:
                self._switch_to_next_key()
                raise Exception("API配额超限，已切换密钥")
            raise Exception(f"API返回错误: {data.get('message')}")
            
        return data
    
    def geocode(self, address: str) -> Tuple[float, float]:
        """
        地理编码：将地址转换为经纬度
        返回: (经度, 纬度)
        """
        url = f"{self.base_url}/geocoding/v3/"
        params = {
            'address': address,
            'output': 'json',
            'city': '上海市',  # 限定在上海市范围内搜索
            'ak': self._get_available_key()
        }
        
        try:
            response = requests.get(url, params=params)
            data = self._handle_api_response(response)
            
            location = data['result']['location']
            return location['lng'], location['lat']
            
        except Exception as e:
            raise Exception(f"地理编码失败: {str(e)}")
    
    def calculate_route(self, origin: Tuple[float, float], 
                       destination: Tuple[float, float], 
                       mode: str = 'transit') -> Dict:
        """
        计算路线
        mode: transit(公交) 或 riding(骑行)
        返回: 路线信息字典
        """
        if mode == 'transit':
            url = f"{self.base_url}/direction/v2/transit"
        elif mode == 'riding':
            url = f"{self.base_url}/direction/v2/riding"
        else:
            raise ValueError("不支持的交通方式")
            
        params = {
            'origin': f"{origin[1]},{origin[0]}",  # 纬度,经度
            'destination': f"{destination[1]},{destination[0]}",
            'region': '上海',  # 限定在上海市范围内
            'ak': self._get_available_key()
        }
        
        try:
            response = requests.get(url, params=params)
            data = self._handle_api_response(response)
            
            if mode == 'transit':
                # 获取最快的公交路线
                route = min(data['result']['routes'], 
                          key=lambda x: x['duration'])
                return {
                    'duration': route['duration'],
                    'distance': route['distance'] / 1000,  # 转换为公里
                    'mode': 'transit'
                }
            else:
                # 骑行路线
                return {
                    'duration': data['result']['duration'],
                    'distance': data['result']['distance'] / 1000,  # 转换为公里
                    'mode': 'riding'
                }
                
        except Exception as e:
            raise Exception(f"路线计算失败: {str(e)}")
    
    def get_commute_info(self, start_address: str, 
                        end_address: str) -> Dict:
        """
        获取两个地址之间的通勤信息
        """
        try:
            # 获取起点和终点的经纬度
            start_lng, start_lat = self.geocode(start_address)
            end_lng, end_lat = self.geocode(end_address)
            
            # 计算路线距离和时间
            route_info = self.calculate_route(
                (start_lng, start_lat),
                (end_lng, end_lat),
                'transit' if abs(end_lng - start_lng) > 0.045 or 
                            abs(end_lat - start_lat) > 0.045 
                else 'riding'
            )
            
            return {
                'start_location': {'lng': start_lng, 'lat': start_lat},
                'end_location': {'lng': end_lng, 'lat': end_lat},
                'distance': route_info['distance'],
                'commute_time': route_info['duration'],
                'transport_mode': route_info['mode']
            }
            
        except Exception as e:
            raise Exception(f"获取通勤信息失败: {str(e)}") 