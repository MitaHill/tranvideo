let selectedFile = null;
let selectedBatchFiles = [];
let currentInviteCode = null;
let queryRefreshInterval = null;  // 查询刷新定时器
let currentQueryTaskId = null;    // 当前查询的任务ID
let lastCreatedTaskId = null;     // 最新创建的任务ID

function switchTab(tab) {
    document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
    document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
    event.target.classList.add('active');
    document.getElementById(tab + '-tab').classList.add('active');
}

async function verifyInviteCode() {
    const code = document.getElementById('inviteCode').value.trim();
    if (!code) {
        showStatus('请输入邀请码', 'error');
        return;
    }

    try {
        const response = await fetch(`/api/invitation/check/${code}`);
        const data = await response.json();

        if (data.valid && data.available_minutes > 0) {
            currentInviteCode = code;
            showStatus(`验证成功，可用时长: ${data.available_minutes} 分钟`, 'success');
            
            // 延迟执行动画序列
            setTimeout(() => {
                // 第一步：淡出邀请码验证区域
                const authSection = document.getElementById('authSection');
                authSection.classList.add('fade-out');
                
                // 第二步：显示页面标题（带延迟）
                setTimeout(() => {
                    authSection.style.display = 'none';
                    const pageHeader = document.getElementById('pageHeader');
                    pageHeader.classList.remove('hidden');
                    pageHeader.classList.add('fade-in');
                    
                    // 第三步：显示主要内容（带延迟）
                    setTimeout(() => {
                        const mainContent = document.getElementById('mainContent');
                        mainContent.classList.remove('hidden');
                        mainContent.classList.add('fade-in');
                    }, 300);
                }, 300);
            }, 1000); // 让用户先看到成功消息
        } else {
            showStatus('邀请码无效或已过期', 'error');
        }
    } catch (error) {
        showStatus('验证失败，请重试', 'error');
    }
}

function showStatus(message, type) {
    document.getElementById('inviteStatus').innerHTML =
        `<div class="status status-${type}">${message}</div>`;
}

function handleSingleFile(input) {
    selectedFile = input.files[0];
    document.getElementById('fileName').textContent = selectedFile.name;
    document.getElementById('processBtn').disabled = false;
}

function handleBatchFiles(input) {
    selectedBatchFiles = Array.from(input.files);
    document.getElementById('batchList').innerHTML =
        selectedBatchFiles.map(f => `<div class="file-item">${f.name}</div>`).join('');
    document.getElementById('batchProcessBtn').disabled = false;
}

async function processVideo() {
    if (!selectedFile || !currentInviteCode) return;

    const formData = new FormData();
    formData.append('file', selectedFile);
    const mode = document.querySelector('input[name="mode"]:checked').value;

    document.getElementById('processBtn').disabled = true;

    try {
        const response = await fetch(`/api/process/${mode}/${currentInviteCode}`, {
            method: 'POST',
            body: formData
        });
        const data = await response.json();

        if (response.ok) {
            lastCreatedTaskId = data.task_id;
            showTaskResult(`任务已提交，ID: ${data.task_id}<br>视频时长: ${data.duration.toFixed(1)} 分钟`, 'success', 'single');
            showCopyButton(data.task_id);
            pollStatus(data.task_id, 'task', mode);
        } else {
            showTaskResult(data.error || '处理失败', 'error', 'single');
            document.getElementById('processBtn').disabled = false;
        }
    } catch (error) {
        showTaskResult('网络错误', 'error', 'single');
        document.getElementById('processBtn').disabled = false;
    }
}

async function processBatch() {
    if (!selectedBatchFiles.length || !currentInviteCode) return;

    const formData = new FormData();
    selectedBatchFiles.forEach(f => formData.append('files', f));
    formData.append('mode', document.querySelector('input[name="batch_mode"]:checked').value);

    document.getElementById('batchProcessBtn').disabled = true;

    try {
        const response = await fetch(`/api/batch/process/${currentInviteCode}`, {
            method: 'POST',
            body: formData
        });
        const data = await response.json();

        if (response.ok) {
            lastCreatedTaskId = data.batch_id;
            showTaskResult(`批量任务已提交，ID: ${data.batch_id}<br>文件数: ${data.file_count}`, 'success', 'batch');
            showCopyButton(data.batch_id);
            pollStatus(data.batch_id, 'batch');
        } else {
            showTaskResult(data.error || '处理失败', 'error', 'batch');
            document.getElementById('batchProcessBtn').disabled = false;
        }
    } catch (error) {
        showTaskResult('网络错误', 'error', 'batch');
        document.getElementById('batchProcessBtn').disabled = false;
    }
}

async function pollStatus(id, type, mode) {
    try {
        const response = await fetch(`/api/${type}/${id}`);
        const data = await response.json();

        if (!response.ok) {
            setTimeout(() => pollStatus(id, type, mode), 2000);
            return;
        }

        if (type === 'batch') {
            const completed = data.task_ids.filter(tid =>
                data.tasks[tid].status === 'completed').length;
            document.getElementById('status').textContent =
                `进度: ${completed}/${data.task_ids.length}`;

            if (data.status === 'completed') {
                showTaskResult(`<a href="/api/batch/download/${id}" class="btn btn-success">下载全部文件</a>`, 'success', 'batch');
                document.getElementById('batchProcessBtn').disabled = false;
            } else {
                setTimeout(() => pollStatus(id, type), 2000);
            }
        } else {
            if (data.status === 'processing') {
                const progressText = data.progress || '处理中...';
                const progressBar = data.progress_percentage !== undefined ?
                    `<div class="progress-bar"><div class="progress-fill" style="width: ${data.progress_percentage}%"></div><span>${data.progress_percentage}%</span></div>` :
                    '';
                showTaskResult(`${progressText} ${progressBar}`, 'info', 'single');
                setTimeout(() => pollStatus(id, type, mode), 2000);
            } else if (data.status === 'completed') {
                const url = mode === 'srt' ?
                    `/api/download/srt/${data.filename}` :
                    `/api/download/video/${data.filename}`;
                showTaskResult(`<a href="${url}" class="btn btn-success">下载文件</a>`, 'success', 'single');
                document.getElementById('processBtn').disabled = false;
            } else if (data.status === 'failed') {
                showTaskResult(`处理失败: ${data.error}`, 'error', 'single');
                document.getElementById('processBtn').disabled = false;
            } else {
                setTimeout(() => pollStatus(id, type, mode), 1000);
            }
        }
    } catch (error) {
        setTimeout(() => pollStatus(id, type, mode), 2000);
    }
}

async function checkStatus() {
    try {
        const response = await fetch('/api/status');
        const data = await response.json();
        showResult(`系统状态: ${data.busy ? '忙碌' : '空闲'} | 队列: ${data.queue_length}`, 'success');
    } catch (error) {
        showResult('查询失败', 'error');
    }
}

async function queryTask() {
    const id = document.getElementById('taskIdInput').value.trim();
    if (!id) {
        showResult('请输入任务ID', 'warning');
        return;
    }

    // 清除之前的定时器
    if (queryRefreshInterval) {
        clearInterval(queryRefreshInterval);
        queryRefreshInterval = null;
    }

    currentQueryTaskId = id;
    await performTaskQuery(id);
}

async function performTaskQuery(id) {
    try {
        let response = await fetch(`/api/batch/${id}`);
        let taskFound = false;
        let isCompleted = false;
        
        if (response.ok) {
            const data = await response.json();
            // 修复：使用实际的API响应格式 sub_tasks
            const subTasks = data.sub_tasks || {};
            const taskIds = Object.keys(subTasks);
            const completed = taskIds.filter(tid => {
                const status = subTasks[tid].status;
                return status === '已完成' || status === '被下载过进入清理倒计时';
            }).length;
            const progressBar = data.progress_percentage !== undefined ?
                `<div class="progress-bar"><div class="progress-fill" style="width: ${data.progress_percentage}%"></div><span>${data.progress_percentage}%</span></div>` :
                '';
            const status = data.status === '已完成' ?
                `<a href="/api/batch/download/${id}" class="btn btn-success">下载</a>` :
                `进度: ${completed}/${taskIds.length} ${progressBar}`;
            showResult(`批量任务: ${status}`, 'success');
            
            taskFound = true;
            isCompleted = (data.status === '已完成');
        } else {
            response = await fetch(`/api/task/${id}`);
            if (response.ok) {
                const data = await response.json();
                let status = '';
                if (data.status === '已完成' || data.status === '清理倒计时') {
                    const url = data.mode === 'srt' ?
                        `/api/download/srt/${data.filename}` :
                        `/api/download/video/${data.filename}`;
                    const statusText = data.status === '已完成' ? '已完成' : '清理倒计时';
                    status = `${statusText} <a href="${url}" class="btn btn-success">下载</a>`;
                    isCompleted = true;
                } else {
                    const progressBar = data.progress_percentage !== undefined ?
                        `<div class="progress-bar"><div class="progress-fill" style="width: ${data.progress_percentage}%"></div><span>${data.progress_percentage}%</span></div>` :
                        '';
                    status = data.status === '处理失败' ? `失败: ${data.error}` : `${data.status} ${progressBar}`;
                    // 判断是否为处理中的状态
                    isCompleted = (data.status === '处理失败');
                }
                showResult(`任务状态: ${status}`, 'success');
                taskFound = true;
            } else {
                showResult('任务不存在。检查任务ID是否拼写正确、或者太多请求，等待一些时间再次请求。', 'error');
            }
        }
        
        // 如果任务存在且未完成，开始自动刷新
        if (taskFound && !isCompleted && !queryRefreshInterval) {
            queryRefreshInterval = setInterval(() => {
                if (currentQueryTaskId === id) {
                    performTaskQuery(id);
                } else {
                    clearInterval(queryRefreshInterval);
                    queryRefreshInterval = null;
                }
            }, 6500); // 6.5秒刷新一次
        }
        
    } catch (error) {
        showResult('查询失败', 'error');
    }
}

// 新函数：显示任务结果
function showTaskResult(message, type, tabType) {
    const targetElement = tabType === 'batch' ? 
        document.getElementById('batchTaskResult') : 
        document.getElementById('singleTaskResult');
    targetElement.innerHTML = `<div class="status status-${type}">${message}</div>`;
}

// 显示复制按钮
function showCopyButton(taskId) {
    document.getElementById('taskIdInput').value = taskId;
    document.getElementById('copyBtn').style.display = 'inline-block';
}

// 复制任务ID到剪贴板
function copyTaskId() {
    const taskId = document.getElementById('taskIdInput').value;
    if (taskId) {
        navigator.clipboard.writeText(taskId).then(() => {
            showResult('任务ID已复制到剪贴板', 'success');
        }).catch(() => {
            // Fallback for older browsers
            const textArea = document.createElement('textarea');
            textArea.value = taskId;
            document.body.appendChild(textArea);
            textArea.select();
            document.execCommand('copy');
            document.body.removeChild(textArea);
            showResult('任务ID已复制到剪贴板', 'success');
        });
    }
}

function showResult(message, type) {
    const resultElement = document.getElementById('result');
    const containerElement = document.getElementById('result-container');
    
    if (message) {
        resultElement.innerHTML = `<div class="status status-${type}">${message}</div>`;
        containerElement.classList.add('show');
    } else {
        resultElement.innerHTML = '';
        containerElement.classList.remove('show');
    }
}

// 回车键支持
document.getElementById('inviteCode').addEventListener('keypress', (e) => {
    if (e.key === 'Enter') verifyInviteCode();
});

document.getElementById('taskIdInput').addEventListener('keypress', (e) => {
    if (e.key === 'Enter') queryTask();
});

// 页面卸载时清理定时器
window.addEventListener('beforeunload', () => {
    if (queryRefreshInterval) {
        clearInterval(queryRefreshInterval);
    }
});

// 确保页面加载完成后再添加事件监听器
document.addEventListener('DOMContentLoaded', function() {
    // 清空结果显示区域并隐藏容器
    document.getElementById('result').innerHTML = '';
    document.getElementById('result-container').classList.remove('show');
    
    // 添加回车键支持
    const inviteCodeInput = document.getElementById('inviteCode');
    const taskIdInput = document.getElementById('taskIdInput');

    if (inviteCodeInput) {
        inviteCodeInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') verifyInviteCode();
        });
    }

    if (taskIdInput) {
        taskIdInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') queryTask();
        });
    }
});