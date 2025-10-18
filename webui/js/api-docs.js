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

    // 初始化所有功能
    if (window.innerWidth <= 768) {
        initMobileMenu();
    }
    
    addScrollEffects();
    enhanceCopyFeature();
    addKeyboardNavigation();
    
    // 延迟添加加载动画以确保页面渲染完成
    setTimeout(addLoadingEffects, 100);

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
    
    // 窗口大小改变时重新初始化移动端菜单
    let resizeTimer;
    window.addEventListener('resize', () => {
        clearTimeout(resizeTimer);
        resizeTimer = setTimeout(() => {
            const existingToggle = document.querySelector('.mobile-menu-toggle');
            const existingOverlay = document.querySelector('.mobile-overlay');
            
            if (window.innerWidth <= 768 && !existingToggle) {
                initMobileMenu();
            } else if (window.innerWidth > 768 && existingToggle) {
                existingToggle.remove();
                existingOverlay.remove();
                document.body.style.overflow = '';
            }
        }, 250);
    });
});

// 移动端菜单功能
function initMobileMenu() {
    // 创建移动端菜单按钮
    const menuToggle = document.createElement('button');
    menuToggle.className = 'mobile-menu-toggle';
    menuToggle.innerHTML = '☰';
    menuToggle.setAttribute('aria-label', '切换菜单');
    
    // 创建遮罩层
    const overlay = document.createElement('div');
    overlay.className = 'mobile-overlay';
    
    document.body.appendChild(menuToggle);
    document.body.appendChild(overlay);
    
    const sidebar = document.querySelector('.sidebar');
    
    // 切换菜单
    function toggleMenu() {
        const isOpen = sidebar.classList.contains('mobile-open');
        
        if (isOpen) {
            sidebar.classList.remove('mobile-open');
            overlay.classList.remove('active');
            menuToggle.innerHTML = '☰';
            document.body.style.overflow = '';
        } else {
            sidebar.classList.add('mobile-open');
            overlay.classList.add('active');
            menuToggle.innerHTML = '✕';
            document.body.style.overflow = 'hidden';
        }
    }
    
    // 事件监听
    menuToggle.addEventListener('click', toggleMenu);
    overlay.addEventListener('click', toggleMenu);
    
    // 点击菜单项后关闭菜单
    sidebar.querySelectorAll('a').forEach(link => {
        link.addEventListener('click', () => {
            if (window.innerWidth <= 768) {
                toggleMenu();
            }
        });
    });
    
    // 窗口大小改变时的处理
    window.addEventListener('resize', () => {
        if (window.innerWidth > 768) {
            sidebar.classList.remove('mobile-open');
            overlay.classList.remove('active');
            menuToggle.innerHTML = '☰';
            document.body.style.overflow = '';
        }
    });
}

// 添加平滑滚动和高亮效果
function addScrollEffects() {
    const links = document.querySelectorAll('.nav-menu a');
    
    links.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            const targetId = this.getAttribute('href').substring(1);
            showSection(targetId);
            
            // 添加点击反馈效果
            this.style.transform = 'scale(0.95)';
            setTimeout(() => {
                this.style.transform = '';
            }, 150);
        });
    });
}

// 添加复制代码功能增强
function enhanceCopyFeature() {
    document.querySelectorAll('.code-block').forEach(block => {
        // 移除已有的复制按钮
        const existingBtn = block.querySelector('.copy-btn');
        if (existingBtn) {
            existingBtn.remove();
        }
        
        const copyBtn = document.createElement('button');
        copyBtn.innerHTML = '📋';
        copyBtn.className = 'copy-btn';
        copyBtn.title = '复制代码';
        
        copyBtn.addEventListener('click', async () => {
            const code = block.querySelector('code');
            const text = code.textContent;
            
            try {
                await navigator.clipboard.writeText(text);
                copyBtn.innerHTML = '✅';
                copyBtn.style.background = '#28a745';
                
                setTimeout(() => {
                    copyBtn.innerHTML = '📋';
                    copyBtn.style.background = '';
                }, 2000);
            } catch (err) {
                // 备用方法
                const textArea = document.createElement('textarea');
                textArea.value = text;
                document.body.appendChild(textArea);
                textArea.select();
                document.execCommand('copy');
                document.body.removeChild(textArea);
                
                copyBtn.innerHTML = '✅';
                setTimeout(() => {
                    copyBtn.innerHTML = '📋';
                }, 2000);
            }
        });
        
        block.appendChild(copyBtn);
    });
}

// 添加键盘导航支持
function addKeyboardNavigation() {
    const sections = ['invitation', 'status', 'single-process', 'batch-process', 'task-query', 'download', 'admin'];
    let currentIndex = 0;
    
    document.addEventListener('keydown', (e) => {
        if (e.ctrlKey || e.metaKey) {
            switch(e.key) {
                case 'ArrowUp':
                    e.preventDefault();
                    currentIndex = Math.max(0, currentIndex - 1);
                    showSection(sections[currentIndex]);
                    break;
                case 'ArrowDown':
                    e.preventDefault();
                    currentIndex = Math.min(sections.length - 1, currentIndex + 1);
                    showSection(sections[currentIndex]);
                    break;
            }
        }
    });
}

// 添加加载动画
function addLoadingEffects() {
    // 为API端点添加加载效果
    document.querySelectorAll('.endpoint').forEach((endpoint, index) => {
        endpoint.style.opacity = '0';
        endpoint.style.transform = 'translateY(20px)';
        
        setTimeout(() => {
            endpoint.style.transition = 'all 0.6s ease';
            endpoint.style.opacity = '1';
            endpoint.style.transform = 'translateY(0)';
        }, index * 100);
    });
}

// 页面初始化增强版