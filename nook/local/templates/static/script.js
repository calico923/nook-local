// テーマ切り替え機能
document.addEventListener('DOMContentLoaded', function() {
    // テーマ設定の初期化
    const savedTheme = localStorage.getItem('theme') || 'light';
    document.documentElement.setAttribute('data-theme', savedTheme);
    updateThemeToggleIcon(savedTheme);

    // テーマ切り替えボタンのイベントリスナー
    const themeToggle = document.getElementById('theme-toggle');
    if (themeToggle) {
        themeToggle.addEventListener('click', function() {
            const currentTheme = document.documentElement.getAttribute('data-theme');
            const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
            
            document.documentElement.setAttribute('data-theme', newTheme);
            localStorage.setItem('theme', newTheme);
            updateThemeToggleIcon(newTheme);
        });
    }

    // 日付選択のイベントリスナー
    const dateSelector = document.getElementById('date-selector');
    if (dateSelector) {
        dateSelector.addEventListener('change', function() {
            window.location.href = `/?date=${this.value}`;
        });
    }

    // 記事アイテムのクリックイベント
    setupArticleItemListeners();

    // カテゴリナビゲーションのイベントリスナー
    setupCategoryNavListeners();

    // チャット機能の初期化
    initializeChat();
});

// テーマアイコンの更新
function updateThemeToggleIcon(theme) {
    const themeIcon = document.querySelector('.theme-toggle-icon');
    if (themeIcon) {
        themeIcon.textContent = theme === 'dark' ? '🌙' : '☀️';
    }
    
    const themeText = document.querySelector('.theme-toggle-text');
    if (themeText) {
        themeText.textContent = theme === 'dark' ? 'ダークモード' : 'ライトモード';
    }
}

// 記事アイテムのクリックイベントを設定
function setupArticleItemListeners() {
    // カテゴリ名のクリックイベント
    const categoryNames = document.querySelectorAll('.category-name');
    categoryNames.forEach(category => {
        category.addEventListener('click', function() {
            const articleCategory = this.closest('.article-category');
            const appName = articleCategory.getAttribute('data-app');
            
            // アクティブ状態の切り替え
            document.querySelectorAll('.article-category').forEach(cat => {
                cat.classList.remove('active');
            });
            articleCategory.classList.add('active');
            
            // カテゴリナビゲーションの更新
            updateCategoryNav(appName);
            
            // 記事コンテンツの読み込み
            loadArticleContent(appName);
        });
    });
    
    // 見出しのクリックイベント
    const headings = document.querySelectorAll('.article-heading');
    headings.forEach(heading => {
        heading.addEventListener('click', function() {
            const appName = this.getAttribute('data-app');
            const headingText = this.getAttribute('data-heading');
            
            // アクティブ状態の切り替え
            document.querySelectorAll('.article-heading').forEach(h => {
                h.classList.remove('active');
            });
            this.classList.add('active');
            
            // カテゴリナビゲーションの更新
            updateCategoryNav(appName);
            
            // 記事コンテンツの読み込みと特定の見出しへのスクロール
            loadArticleContent(appName, headingText);
        });
    });
    
    // 初期表示（最初のカテゴリを表示）
    const firstCategory = document.querySelector('.category-name');
    if (firstCategory) {
        firstCategory.click();
    }
}

// カテゴリナビゲーションの更新
function updateCategoryNav(activeApp) {
    const navLinks = document.querySelectorAll('.nav-category .nav-link');
    
    navLinks.forEach(link => {
        const appName = link.getAttribute('data-app');
        if (appName === activeApp) {
            link.classList.add('active');
        } else {
            link.classList.remove('active');
        }
    });
}

// カテゴリナビゲーションのイベントリスナー設定
function setupCategoryNavListeners() {
    const navLinks = document.querySelectorAll('.nav-category .nav-link');
    
    navLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            
            // アクティブクラスの切り替え
            navLinks.forEach(l => l.classList.remove('active'));
            this.classList.add('active');
            
            // 記事リストの更新
            const appName = this.getAttribute('data-app');
            updateArticleList(appName);
            
            // 最初の記事を表示
            const firstArticle = document.querySelector(`.article-item[data-app="${appName}"]`);
            if (firstArticle) {
                firstArticle.click();
            }
        });
    });
}

// 記事リストの更新
function updateArticleList(appName) {
    const articleItems = document.querySelectorAll('.article-item');
    
    articleItems.forEach(item => {
        if (item.getAttribute('data-app') === appName) {
            item.style.display = 'block';
        } else {
            item.style.display = 'none';
        }
    });
}

// 記事コンテンツの読み込み
function loadArticleContent(appName, headingText = null) {
    const date = document.getElementById('date-selector').value;
    const contentContainer = document.querySelector('.article-content');
    
    if (contentContainer) {
        // ローディング表示
        contentContainer.innerHTML = '<div class="text-center"><div class="spinner-border" role="status"><span class="visually-hidden">Loading...</span></div></div>';
        
        // 記事データの取得
        fetch(`/fetch_markdown?app_name=${appName}&date=${date}`)
            .then(response => response.json())
            .then(data => {
                if (data.content) {
                    // マークダウンの変換と表示
                    const converter = new showdown.Converter();
                    const html = converter.makeHtml(data.content);
                    
                    // タイトルと本文を分離
                    const titleMatch = html.match(/<h1>(.*?)<\/h1>/);
                    const title = titleMatch ? titleMatch[1] : appName;
                    
                    // タイトルを設定
                    const titleElement = document.querySelector('.article-title');
                    if (titleElement) {
                        titleElement.innerHTML = title + '<span class="chat-button" onclick="toggleChat()"><i class="bi bi-chat-dots"></i> チャット</span>';
                    }
                    
                    // 本文を設定
                    contentContainer.innerHTML = html.replace(/<h1>.*?<\/h1>/, '');
                    
                    // 特定の見出しが指定されている場合、その位置にスクロール
                    if (headingText) {
                        setTimeout(() => {
                            const headingElement = Array.from(contentContainer.querySelectorAll('h2')).find(
                                h2 => h2.textContent.trim() === headingText
                            );
                            if (headingElement) {
                                headingElement.scrollIntoView({ behavior: 'smooth', block: 'start' });
                                // 見出しをハイライト
                                headingElement.classList.add('highlight');
                                setTimeout(() => {
                                    headingElement.classList.remove('highlight');
                                }, 2000);
                            }
                        }, 100);
                    }
                } else {
                    contentContainer.innerHTML = '<div class="alert alert-info">この日付のデータはありません。</div>';
                }
            })
            .catch(error => {
                console.error('Error fetching content:', error);
                contentContainer.innerHTML = '<div class="alert alert-danger">コンテンツの読み込み中にエラーが発生しました。</div>';
            });
    }
}

// チャット機能の初期化
function initializeChat() {
    // チャットトグルボタンのイベントリスナー
    document.querySelectorAll('.chat-button').forEach(button => {
        button.addEventListener('click', toggleChat);
    });
    
    // チャット閉じるボタンのイベントリスナー
    const closeChat = document.querySelector('.close-chat');
    if (closeChat) {
        closeChat.addEventListener('click', toggleChat);
    }
    
    // チャットフォームのイベントリスナー
    const chatForm = document.getElementById('chat-form');
    if (chatForm) {
        chatForm.addEventListener('submit', function(e) {
            e.preventDefault();
            const messageInput = document.getElementById('message-input');
            const message = messageInput.value.trim();
            
            if (message) {
                addMessage(message, 'user');
                messageInput.value = '';
                
                // ボットの応答をシミュレート
                setTimeout(() => {
                    const botResponse = "申し訳ありませんが、現在チャット機能は開発中です。もう少々お待ちください。";
                    addMessage(botResponse, 'bot');
                }, 1000);
            }
        });
    }
}

// チャットの表示/非表示を切り替え
function toggleChat() {
    const chatContainer = document.querySelector('.chat-container');
    if (chatContainer) {
        const isVisible = chatContainer.style.display === 'flex';
        chatContainer.style.display = isVisible ? 'none' : 'flex';
        
        if (!isVisible) {
            const messageInput = document.getElementById('message-input');
            if (messageInput) {
                messageInput.focus();
            }
        }
    }
}

// メッセージを追加
function addMessage(text, sender) {
    const chatBody = document.querySelector('.chat-body');
    if (chatBody) {
        const messageElement = document.createElement('div');
        messageElement.classList.add('message', `${sender}-message`);
        messageElement.textContent = text;
        chatBody.appendChild(messageElement);
        chatBody.scrollTop = chatBody.scrollHeight;
    }
} 