class CommuteCalculator {
    constructor() {
        this.targetAddressInput = document.getElementById('target-address');
        this.fileInput = document.getElementById('file-upload');
        this.calculateBtn = document.getElementById('calculate-btn');
        this.downloadBtn = document.getElementById('download-btn');
        this.progressSection = document.querySelector('.progress-section');
        this.resultSection = document.querySelector('.result-section');
        
        // 初始化进度条
        this.progressBar = new ProgressBar.Line('#progress-bar', {
            strokeWidth: 4,
            easing: 'easeInOut',
            duration: 200,
            color: '#007bff',
            trailColor: '#eee',
            trailWidth: 1,
            svgStyle: {width: '100%', height: '100%'},
            step: (state, bar) => {
                document.getElementById('progress-text').textContent = 
                    Math.round(bar.value() * 100) + '%';
            }
        });
        
        // 初始化WebSocket连接
        this.socket = io();
        
        // 监听进度更新
        this.socket.on('progress_update', (data) => {
            this.progressBar.animate(data.progress / 100);
        });
        
        this.bindEvents();
    }
    
    bindEvents() {
        this.calculateBtn.addEventListener('click', async () => {
            const formData = new FormData();
            formData.append('file', this.fileInput.files[0]);
            formData.append('target_address', this.targetAddressInput.value);
            
            this.calculateBtn.disabled = true;
            this.progressSection.style.display = 'block';
            
            try {
                const response = await fetch('/api/calculate', {
                    method: 'POST',
                    body: formData
                });
                
                if (!response.ok) {
                    throw new Error('计算失败');
                }
                
                // 获取文件blob
                const blob = await response.blob();
                
                // 创建下载链接
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = response.headers.get('content-disposition')?.split('filename=')[1] || 'result.xlsx';
                document.body.appendChild(a);
                a.click();
                window.URL.revokeObjectURL(url);
                document.body.removeChild(a);
                
            } catch (error) {
                console.error('Error:', error);
                alert('计算过程出错，请重试');
            } finally {
                this.calculateBtn.disabled = false;
                this.progressSection.style.display = 'none';
            }
        });
        this.downloadBtn.addEventListener('click', () => this.downloadResult());
        
        // 添加输入验证
        this.targetAddressInput.addEventListener('input', () => this.validateInputs());
        this.fileInput.addEventListener('change', () => this.validateInputs());
    }
    
    validateInputs() {
        const isValid = this.targetAddressInput.value && this.fileInput.files.length > 0;
        this.calculateBtn.disabled = !isValid;
    }
    
    async downloadResult() {
        const filename = this.downloadBtn.getAttribute('data-filename');
        if (!filename) {
            this.showMessage('找不到结果文件', 'error');
            return;
        }
        
        try {
            window.location.href = `/api/download/${filename}`;
        } catch (error) {
            this.showMessage('下载失败', 'error');
        }
    }
    
    showMessage(message, type = 'info') {
        // 创建消息元素
        const messageDiv = document.createElement('div');
        messageDiv.className = `alert alert-${type}`;
        messageDiv.textContent = message;
        
        // 添加到页面
        const container = document.querySelector('.container');
        container.insertBefore(messageDiv, container.firstChild);
        
        // 3秒后自动消失
        setTimeout(() => {
            messageDiv.remove();
        }, 3000);
    }
}

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', () => {
    new CommuteCalculator();
}); 