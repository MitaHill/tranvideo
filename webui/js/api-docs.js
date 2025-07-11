// 显示指定的API文档部分
function showSection(sectionId) {
    // 隐藏所有部分
    document.querySelectorAll('.api-section').forEach(section => {
        section.classList.remove('active');
    });

    // 移除所有导航链接的激活状态
    document.querySelectorAll('.nav-menu a').forEach(link => {
        link.classList.remove('active');
    });

    // 显示目标部分
    const targetSection = document.getElementById(sectionId);
    if (targetSection) {
        targetSection.classList.add('active');
    }

    // 激活对应的导航链接
    const activeLink = document.querySelector(`a[href="#${sectionId}"]`);
    if (activeLink) {
        activeLink.classList.add('active');
    }

    // 平滑滚动到顶部
    document.querySelector('.content').scrollTop = 0;
}

// 复制代码到剪贴板
function copyCode(button) {
    const codeBlock = button.nextElementSibling.querySelector('code');
    const text = codeBlock.textContent;

    navigator.clipboard.writeText(text).then(() => {
        const originalText = button.textContent;
        button.textContent = '已复制!';
        button.style.background = '#28a745';

        setTimeout(() => {
            button.textContent = originalText;
            button.style.background = '';
        }, 2000);
    }).catch(() => {
        // 备用复制方法
        const textArea = document.createElement('textarea');
        textArea.value = text;
        document.body.appendChild(textArea);
        textArea.select();
        document.execCommand('copy');
        document.body.removeChild(textArea);

        button.textContent = '已复制!';
        setTimeout(() => {
            button.textContent = '复制';
        }, 2000);
    });
}

// 搜索功能
function searchAPI() {
    const searchTerm = document.getElementById('searchInput').value.toLowerCase();
    const sections = document.querySelectorAll('.api-section');

    sections.forEach(section => {
        const content = section.textContent.toLowerCase();
        const navLink = document.querySelector(`a[href="#${section.id}"]`);

        if (content.includes(searchTerm) || searchTerm === '') {
            section.style.display = 'block';
            if (navLink) navLink.style.display = 'block';
        } else {
            section.style.display = 'none';
            if (navLink) navLink.style.display = 'none';
        }
    });
}

// 页面初始化
document.addEventListener('DOMContentLoaded', function() {
    // 默认显示第一个部分
    showSection('invitation');

    // 为代码块添加复制按钮
    document.querySelectorAll('.code-block').forEach(block => {
        const copyBtn = document.createElement('button');
        copyBtn.textContent = '复制';
        copyBtn.className = 'copy-btn';
        copyBtn.onclick = () => copyCode(copyBtn);

        block.style.position = 'relative';
        block.appendChild(copyBtn);
    });

    // 处理锚点链接
    if (window.location.hash) {
        const sectionId = window.location.hash.substring(1);
        showSection(sectionId);
    }

    // 监听hashchange事件
    window.addEventListener('hashchange', () => {
        if (window.location.hash) {
            const sectionId = window.location.hash.substring(1);
            showSection(sectionId);
        }
    });
});

// 响应式导航切换（移动端）
function toggleMobileNav() {
    const sidebar = document.querySelector('.sidebar');
    sidebar.classList.toggle('mobile-open');
}

// 添加移动端导航按钮（如果需要）
if (window.innerWidth <= 768) {
    const header = document.querySelector('.header');
    const menuBtn = document.createElement('button');
    menuBtn.innerHTML = '☰';
    menuBtn.className = 'mobile-menu-btn';
    menuBtn.onclick = toggleMobileNav;
    header.appendChild(menuBtn);
}