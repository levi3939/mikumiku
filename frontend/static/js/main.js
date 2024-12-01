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
        this.calculateBtn.addEventListener('click', () => this.startCalculation());
        this.downloadBtn.addEventListener('click', () => this.downloadResult());
        
        // 添加输入验证
        this.targetAddressInput.addEventListener('input', () => this.validateInputs());
        this.fileInput.addEventListener('change', () => this.validateInputs());
    }
    
    validateInputs() {
        const isValid = this.targetAddressInput.value && this.fileInput.files.length > 0;
        this.calculateBtn.disabled = !isValid;
    }
    
    async startCalculation() {
        try {
            // 禁用按钮，显示进度条
            this.calculateBtn.disabled = true;
            this.progressSection.style.display = 'block';
            this.resultSection.style.display = 'none';
            this.progressBar.set(0);
            
            const formData = new FormData();
            formData.append('file', this.fileInput.files[0]);
            formData.append('target_address', this.targetAddressInput.value);
            
            const response = await fetch('/api/calculate', {
                method: 'POST',
                body: formData
            });
            
            const data = await response.json();
            
            if (!response.ok) {
                throw new Error(data.error || '计算失败');
            }
            
            // 计算成功，显示下载按钮
            this.progressBar.animate(1.0);
            this.resultSection.style.display = 'block';
            this.downloadBtn.setAttribute('data-filename', data.filename);
            
            // 显示成功提示
            this.showMessage('计算完成！', 'success');
            
        } catch (error) {
            this.showMessage(error.message, 'error');
            this.progressSection.style.display = 'none';
        } finally {
            this.calculateBtn.disabled = false;
        }
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