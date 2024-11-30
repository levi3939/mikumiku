import pandas as pd
from typing import List, Dict, Optional
import os
from datetime import datetime
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import UPLOAD_FOLDER

class ExcelHandler:
    def __init__(self):
        # 确保上传文件夹存在
        os.makedirs(UPLOAD_FOLDER, exist_ok=True)
            
    def read_excel(self, file) -> pd.DataFrame:
        """
        读取上传的Excel文件
        参数:
            file: 文件对象
        返回:
            DataFrame对象
        """
        try:
            df = pd.read_excel(file)
            
            # 验证必要的列是否存在
            if '地址' not in df.columns:
                raise ValueError("Excel文件必须包含'地址'列")
                
            # 删除空行
            df = df.dropna(subset=['地址'])
            
            return df
            
        except Exception as e:
            raise Exception(f"Excel文件读取失败: {str(e)}")
            
    def create_result_file(self, original_df: pd.DataFrame, 
                          results: List[Dict]) -> str:
        """
        创建结果Excel文件
        参数:
            original_df: 原始DataFrame
            results: 计算结果列表
        返回:
            结果文件名
        """
        try:
            # 创建新的DataFrame
            result_df = original_df.copy()
            
            # 添加新列
            result_df['经度'] = [r['start_location']['lng'] for r in results]
            result_df['纬度'] = [r['start_location']['lat'] for r in results]
            result_df['直线距离(公里)'] = [round(r['distance'], 2) for r in results]
            result_df['通勤时间(分钟)'] = [round(r['commute_time'] / 60) for r in results]
            result_df['交通方式'] = [
                '骑行' if r['transport_mode'] == 'riding' else '公交' 
                for r in results
            ]
            
            # 生成文件名
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'commute_result_{timestamp}.xlsx'
            filepath = os.path.join(UPLOAD_FOLDER, filename)
            
            # 保存文件
            result_df.to_excel(filepath, index=False)
            
            return filename
            
        except Exception as e:
            raise Exception(f"结果文件创建失败: {str(e)}")
            
    def get_result_file_path(self, filename: str) -> str:
        """
        获取结果文件的完整路径
        """
        return os.path.join(UPLOAD_FOLDER, filename)
        
    def clean_old_files(self, max_age_hours: int = 24):
        """清理旧文件"""
        try:
            current_time = datetime.now()
            cleaned_count = 0
            error_count = 0
            
            for filename in os.listdir(UPLOAD_FOLDER):
                try:
                    filepath = os.path.join(UPLOAD_FOLDER, filename)
                    file_time = datetime.fromtimestamp(os.path.getctime(filepath))
                    
                    if (current_time - file_time).total_seconds() > max_age_hours * 3600:
                        os.remove(filepath)
                        cleaned_count += 1
                except Exception as e:
                    error_count += 1
                    print(f"清理文件 {filename} 失败: {str(e)}")
            
            print(f"清理完成: 成功 {cleaned_count} 个, 失败 {error_count} 个")
            
        except Exception as e:
            print(f"清理过程出错: {str(e)}")
            
    def validate_file_extension(self, filename: str) -> bool:
        """
        验证文件扩展名
        """
        return filename.lower().endswith(('.xlsx', '.xls'))
        
    def get_total_rows(self, df: pd.DataFrame) -> int:
        """
        获取需要处理的总行数（不包含表头）
        """
        return len(df) 