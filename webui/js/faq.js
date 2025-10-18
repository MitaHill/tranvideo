// 切换FAQ答案显示/隐藏
function toggleAnswer(element) {
    const faqItem = element.parentElement;
    const isActive = faqItem.classList.contains('active');

    // 关闭其他打开的项目（可选：单一展开模式）
    // document.querySelectorAll('.faq-item.active').forEach(item => {
    //     if (item !== faqItem) {
    //         item.classList.remove('active');
    //     }
    // });

    // 切换当前项目
    faqItem.classList.toggle('active');

    // 平滑滚动到问题位置
    if (!isActive) {
        setTimeout(() => {
            element.scrollIntoView({
                behavior: 'smooth',
                block: 'nearest'
            });
        }, 150);
    }
}

// 搜索功能
function searchFAQ() {
    const searchTerm = document.getElementById('searchInput').value.toLowerCase().trim();
    const faqItems = document.querySelectorAll('.faq-item');
    const categories = document.querySelectorAll('.category');

    // 清除之前的高亮
    document.querySelectorAll('.highlight').forEach(element => {
        element.outerHTML = element.innerHTML;
    });

    if (searchTerm === '') {
        // 显示所有项目
        faqItems.forEach(item => item.classList.remove('hidden'));
        categories.forEach(category => category.classList.remove('hidden'));
        return;
    }

    let hasVisibleItems = false;

    categories.forEach(category => {
        let categoryHasVisible = false;
        const categoryItems = category.querySelectorAll('.faq-item');

        categoryItems.forEach(item => {
            const keywords = item.dataset.keywords || '';
            const question = item.querySelector('.faq-question span').textContent;
            const answer = item.querySelector('.faq-answer').textContent;
            const content = (keywords + ' ' + question + ' ' + answer).toLowerCase();

            if (content.includes(searchTerm)) {
                item.classList.remove('hidden');
                categoryHasVisible = true;
                hasVisibleItems = true;

                // 高亮关键词
                highlightText(item, searchTerm);
            } else {
                item.classList.add('hidden');
            }
        });

        // 隐藏/显示分类
        if (categoryHasVisible) {
            category.classList.remove('hidden');
        } else {
            category.classList.add('hidden');
        }
    });

    // 显示搜索结果提示
    showSearchResults(hasVisibleItems, searchTerm);
}

// 高亮搜索关键词
function highlightText(element, searchTerm) {
    const walker = document.createTreeWalker(
        element,
        NodeFilter.SHOW_TEXT,
        null,
        false
    );

    const textNodes = [];
    let node;

    while (node = walker.nextNode()) {
        textNodes.push(node);
    }

    textNodes.forEach(textNode => {
        const text = textNode.textContent;
        const regex = new RegExp(`(${searchTerm})`, 'gi');

        if (regex.test(text)) {
            const highlightedText = text.replace(regex, '<span class="highlight">$1</span>');
            const span = document.createElement('span');
            span.innerHTML = highlightedText;
            textNode.parentNode.replaceChild(span, textNode);
        }
    });
}

// 显示搜索结果
function showSearchResults(hasResults, searchTerm) {
    let resultDiv = document.getElementById('searchResults');

    if (!resultDiv) {
        resultDiv = document.createElement('div');
        resultDiv.id = 'searchResults';
        resultDiv.className = 'search-results';
        document.querySelector('.search-section').appendChild(resultDiv);
    }

    if (searchTerm === '') {
        resultDiv.style.display = 'none';
        return;
    }

    resultDiv.style.display = 'block';

    if (hasResults) {
        const visibleCount = document.querySelectorAll('.faq-item:not(.hidden)').length;
        resultDiv.innerHTML = `<p class="search-info">找到 ${visibleCount} 个相关问题</p>`;
    } else {
        resultDiv.innerHTML = `<p class="search-info no-results">未找到包含 "${searchTerm}" 的问题</p>`;
    }
}

// 展开所有匹配的项目
function expandAllVisible() {
    document.querySelectorAll('.faq-item:not(.hidden)').forEach(item => {
        item.classList.add('active');
    });
}

// 收起所有项目
function collapseAll() {
    document.querySelectorAll('.faq-item.active').forEach(item => {
        item.classList.remove('active');
    });
}

// 滚动到分类
function scrollToCategory(categoryId) {
    const category = document.querySelector(`[data-category="${categoryId}"]`);
    if (category) {
        category.scrollIntoView({
            behavior: 'smooth',
            block: 'start'
        });
    }
}

// 页面初始化
document.addEventListener('DOMContentLoaded', function() {
    const searchInput = document.getElementById('searchInput');

    // 搜索输入事件
    let searchTimeout;
    searchInput.addEventListener('input', function() {
        clearTimeout(searchTimeout);
        searchTimeout = setTimeout(searchFAQ, 300); // 防抖
    });

    // 回车键搜索
    searchInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            e.preventDefault();
            clearTimeout(searchTimeout);
            searchFAQ();
        }
    });

    // 添加搜索结果样式
    if (!document.getElementById('searchResultsStyle')) {
        const style = document.createElement('style');
        style.id = 'searchResultsStyle';
        style.textContent = `
            .search-results {
                margin-top: 15px;
            }
            .search-info {
                padding: 10px;
                background: #e3f2fd;
                border-radius: 6px;
                margin: 0;
                color: #1565c0;
                font-size: 14px;
            }
            .search-info.no-results {
                background: #fff3e0;
                color: #e65100;
            }
        `;
        document.head.appendChild(style);
    }

    // 处理URL锚点
    if (window.location.hash) {
        const targetId = window.location.hash.substring(1);
        setTimeout(() => {
            const targetElement = document.getElementById(targetId);
            if (targetElement && targetElement.classList.contains('faq-item')) {
                targetElement.classList.add('active');
                targetElement.scrollIntoView({
                    behavior: 'smooth',
                    block: 'center'
                });
            }
        }, 500);
    }
});

// 键盘快捷键
document.addEventListener('keydown', function(e) {
    // Ctrl/Cmd + F 聚焦搜索框
    if ((e.ctrlKey || e.metaKey) && e.key === 'f') {
        e.preventDefault();
        document.getElementById('searchInput').focus();
    }

    // ESC 清除搜索
    if (e.key === 'Escape') {
        const searchInput = document.getElementById('searchInput');
        if (searchInput.value) {
            searchInput.value = '';
            searchFAQ();
        }
    }
});