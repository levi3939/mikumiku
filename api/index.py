from flask import Flask, request, jsonify, render_template, send_file
import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.utils.baidu_api import BaiduMapAPI
from backend.utils.excel_handler import ExcelHandler
from werkzeug.utils import secure_filename
import logging
from datetime import datetime
import io

app = Flask(__name__, 
    template_folder='../frontend/templates',
    static_folder='../frontend/static',
    static_url_path='/static'
)

baidu_api = BaiduMapAPI()
excel_handler = ExcelHandler()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/calculate', methods=['POST'])
def calculate_commute_time():
    if 'file' not in request.files:
        return jsonify({'error': '请上传文件'}), 400
        
    file = request.files['file']
    target_address = request.form.get('target_address')
    
    if not target_address:
        return jsonify({'error': '请输入目标地址'}), 400
        
    if not file or not file.filename:
        return jsonify({'error': '未选择文件'}), 400
        
    try:
        # 读取Excel文件
        df = excel_handler.read_excel(file)
        
        # 计算每个地址的通勤信息
        results = []
        for index, row in df.iterrows():
            try:
                commute_info = baidu_api.get_commute_info(
                    row['地址'], 
                    target_address
                )
                results.append(commute_info)
            except Exception as e:
                results.append({
                    'start_location': {'lng': 0, 'lat': 0},
                    'end_location': {'lng': 0, 'lat': 0},
                    'distance': 0,
                    'commute_time': 0,
                    'transport_mode': 'error'
                })
        
        # 创建结果文件在内存中
        output = io.BytesIO()
        excel_handler.create_result_file_in_memory(df, results, output)
        output.seek(0)
        
        # 生成唯一的文件名
        filename = f"commute_result_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=filename
        )
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/sample')
def download_sample():
    """下载示例文件"""
    try:
        sample_file = os.path.join(app.static_folder, 'sample.xlsx')
        return send_file(
            sample_file,
            as_attachment=True,
            download_name='示例文件.xlsx'
        )
    except Exception as e:
        return jsonify({'error': str(e)}), 404

app = app.wsgi_app 