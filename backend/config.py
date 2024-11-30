import os
from dotenv import load_dotenv

load_dotenv()

# 获取当前文件所在目录
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# 百度地图API配置
BAIDU_API_KEYS = os.getenv('BAIDU_API_KEYS', '').split(',')

# 文件上传配置
ALLOWED_EXTENSIONS = {'xlsx', 'xls'}
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'temp')

# 距离阈值配置（单位：公里）
CYCLING_DISTANCE_THRESHOLD = 5 