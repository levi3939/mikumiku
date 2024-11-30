import os

def create_result_file(self, df, results):
    # 确保临时目录存在
    temp_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'backend', 'temp')
    os.makedirs(temp_dir, exist_ok=True)
    
    # 继续处理文件的其他逻辑
    # ... 