from flask import Flask, request, jsonify, render_template, send_file
from utils.baidu_api import BaiduMapAPI
from utils.excel_handler import ExcelHandler
import os
from werkzeug.utils import secure_filename
from flask_socketio import SocketIO, emit
from datetime import datetime
import logging
import config

app = Flask(__name__, 
    template_folder='../frontend/templates',
    static_folder='../frontend/static',
    static_url_path='/static'
)
socketio = SocketIO(app)

baidu_api = BaiduMapAPI()
excel_handler = ExcelHandler()

# 配置日志
logging.basicConfig(
    filename='app.log',
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

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
        
    if not excel_handler.validate_file_extension(file.filename):
        return jsonify({'error': '仅支持.xlsx和.xls格式的文件'}), 400
        
    try:
        logger.info(f"开始处理文件: {file.filename}")
        # 读取Excel文件
        df = excel_handler.read_excel(file)
        total_rows = excel_handler.get_total_rows(df)
        
        # 发送初始进度
        socketio.emit('progress_update', {'progress': 0})
        
        # 计算每个地址的通勤信息
        results = []
        for index, row in df.iterrows():
            try:
                commute_info = baidu_api.get_commute_info(
                    row['地址'], 
                    target_address
                )
                results.append(commute_info)
                
                # 更新进度
                progress = int((index + 1) / total_rows * 100)
                socketio.emit('progress_update', {'progress': progress})
                socketio.sleep(0)  # 让出控制权，确保进度更新能发送出去
                
            except Exception as e:
                print(f"处理第{index+1}行时出错: {str(e)}")
                results.append({
                    'start_location': {'lng': 0, 'lat': 0},
                    'end_location': {'lng': 0, 'lat': 0},
                    'distance': 0,
                    'commute_time': 0,
                    'transport_mode': 'error'
                })
        
        # 创建结果文件
        result_filename = excel_handler.create_result_file(df, results)
        
        # 发送完成进度
        socketio.emit('progress_update', {'progress': 100})
        
        logger.info(f"处理完成: {total_rows}行数据")
        
        return jsonify({
            'status': 'success',
            'filename': result_filename,
            'total_processed': total_rows
        })
        
    except Exception as e:
        logger.error(f"处理失败: {str(e)}")
        raise

@app.route('/api/download/<filename>')
def download_result(filename):
    try:
        file_path = excel_handler.get_result_file_path(filename)
        return send_file(
            file_path,
            as_attachment=True,
            download_name=filename
        )
    except Exception as e:
        return jsonify({'error': str(e)}), 404

# 定期清理旧文件
@app.before_first_request
def setup():
    # 确保上传目录存在
    os.makedirs(config.UPLOAD_FOLDER, exist_ok=True)
    excel_handler.clean_old_files()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/health')
def health_check():
    """健康检查接口"""
    return jsonify({
        'status': 'healthy',
        'api_keys_available': len(config.BAIDU_API_KEYS),
        'timestamp': datetime.now().isoformat()
    })

@app.route('/sample')
def download_sample():
    """下载示例文件"""
    sample_file = os.path.join(app.static_folder, 'sample.xlsx')
    return send_file(
        sample_file,
        as_attachment=True,
        download_name='示例文件.xlsx'
    )

if __name__ == '__main__':
    socketio.run(app, debug=True) 