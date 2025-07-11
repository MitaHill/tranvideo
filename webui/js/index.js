let selectedFile = null;
let selectedBatchFiles = [];
let currentInviteCode = null;

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
            document.getElementById('mainContent').classList.remove('hidden');
            document.getElementById('querySection').style.display = 'block';
            document.getElementById('helpSection').style.display = 'block';
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

    showProgress(true);
    document.getElementById('processBtn').disabled = true;

    try {
        const response = await fetch(`/api/process/${mode}/${currentInviteCode}`, {
            method: 'POST',
            body: formData
        });
        const data = await response.json();

        if (response.ok) {
            showResult(`任务已提交，ID: ${data.task_id}<br>视频时长: ${data.duration.toFixed(1)} 分钟`, 'success');
            pollStatus(data.task_id, 'task', mode);
        } else {
            showResult(data.error || '处理失败', 'error');
            showProgress(false);
            document.getElementById('processBtn').disabled = false;
        }
    } catch (error) {
        showResult('网络错误', 'error');
        showProgress(false);
        document.getElementById('processBtn').disabled = false;
    }
}

async function processBatch() {
    if (!selectedBatchFiles.length || !currentInviteCode) return;

    const formData = new FormData();
    selectedBatchFiles.forEach(f => formData.append('files', f));
    formData.append('mode', document.querySelector('input[name="batch_mode"]:checked').value);

    showProgress(true);
    document.getElementById('batchProcessBtn').disabled = true;

    try {
        const response = await fetch(`/api/batch/process/${currentInviteCode}`, {
            method: 'POST',
            body: formData
        });
        const data = await response.json();

        if (response.ok) {
            showResult(`批量任务已提交，ID: ${data.batch_id}<br>文件数: ${data.file_count}`, 'success');
            pollStatus(data.batch_id, 'batch');
        } else {
            showResult(data.error || '处理失败', 'error');
            showProgress(false);
            document.getElementById('batchProcessBtn').disabled = false;
        }
    } catch (error) {
        showResult('网络错误', 'error');
        showProgress(false);
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
                showResult(`<a href="/api/batch/download/${id}" class="btn btn-success">下载全部文件</a>`, 'success');
                showProgress(false);
                document.getElementById('batchProcessBtn').disabled = false;
            } else {
                setTimeout(() => pollStatus(id, type), 2000);
            }
        } else {
            if (data.status === 'processing') {
                document.getElementById('status').textContent = data.progress || '处理中...';
                setTimeout(() => pollStatus(id, type, mode), 2000);
            } else if (data.status === 'completed') {
                const url = mode === 'srt' ?
                    `/api/download/srt/${data.filename}` :
                    `/api/download/video/${data.filename}`;
                showResult(`<a href="${url}" class="btn btn-success">下载文件</a>`, 'success');
                showProgress(false);
                document.getElementById('processBtn').disabled = false;
            } else if (data.status === 'failed') {
                showResult(`处理失败: ${data.error}`, 'error');
                showProgress(false);
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

    try {
        let response = await fetch(`/api/batch/${id}`);
        if (response.ok) {
            const data = await response.json();
            const completed = data.task_ids.filter(tid =>
                data.tasks[tid].status === 'completed').length;
            const status = data.status === 'completed' ?
                `<a href="/api/batch/download/${id}" class="btn btn-success">下载</a>` :
                `进度: ${completed}/${data.task_ids.length}`;
            showResult(`批量任务: ${status}`, 'success');
            return;
        }

        response = await fetch(`/api/task/${id}`);
        if (response.ok) {
            const data = await response.json();
            let status = '';
            if (data.status === 'completed') {
                const url = data.mode === 'srt' ?
                    `/api/download/srt/${data.filename}` :
                    `/api/download/video/${data.filename}`;
                status = `已完成 <a href="${url}" class="btn btn-success">下载</a>`;
            } else {
                status = data.status === 'failed' ? `失败: ${data.error}` : data.status;
            }
            showResult(`任务状态: ${status}`, 'success');
        } else {
            showResult('任务不存在', 'error');
        }
    } catch (error) {
        showResult('查询失败', 'error');
    }
}

function showProgress(show) {
    document.getElementById('progress').style.display = show ? 'block' : 'none';
}

function showResult(message, type) {
    document.getElementById('result').innerHTML =
        `<div class="status status-${type}">${message}</div>`;
}

// 回车键支持
document.getElementById('inviteCode').addEventListener('keypress', (e) => {
    if (e.key === 'Enter') verifyInviteCode();
});

document.getElementById('taskIdInput').addEventListener('keypress', (e) => {
    if (e.key === 'Enter') queryTask();
});

// 确保页面加载完成后再添加事件监听器
document.addEventListener('DOMContentLoaded', function() {
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