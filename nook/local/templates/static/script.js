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

    // カテゴリナビゲーションのイベントリスナー
    setupCategoryNavListeners();

    // チャット機能の初期化
    initializeChat();
    
    // 初期表示（最初のカテゴリを表示）
    const firstCategoryLink = document.querySelector('.nav-category .nav-link');
    if (firstCategoryLink) {
        firstCategoryLink.click();
    }
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

// カテゴリナビゲーションのイベントリスナー設定
function setupCategoryNavListeners() {
    const navLinks = document.querySelectorAll('.nav-category .nav-link');
    
    navLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            
            // アクティブクラスの切り替え
            navLinks.forEach(l => l.classList.remove('active'));
            this.classList.add('active');
            
            // 選択されたカテゴリ名を取得
            const appName = this.getAttribute('data-app');
            
            // 記事コンテンツの読み込み
            loadArticleContent(appName);
            
            // 左メニューの見出しを更新
            updateHeadingsInLeftMenu(appName);
        });
    });
}

// 左メニューの見出しを更新する関数
function updateHeadingsInLeftMenu(appName) {
    const headingsContainer = document.getElementById('headings-container');
    if (!headingsContainer) return;
    
    // 日付を取得
    const date = document.getElementById('date-selector').value;
    
    // 選択されたカテゴリの見出しを取得
    fetch(`/fetch_markdown?app_name=${appName}&date=${date}`)
        .then(response => response.json())
        .then(data => {
            if (data.content) {
                // マークダウンから見出しを抽出
                const headings = extractHeadingsFromMarkdown(data.content);
                
                if (headings.length > 0) {
                    // 見出しリストを生成
                    let headingsHTML = '';
                    headings.forEach(heading => {
                        headingsHTML += `<div class="article-heading" data-app="${appName}" data-heading="${heading}">${heading}</div>`;
                    });
                    headingsContainer.innerHTML = headingsHTML;
                    
                    // 見出しのクリックイベントを設定
                    setupHeadingClickEvents();
                } else {
                    headingsContainer.innerHTML = '<div class="no-headings">見出しがありません</div>';
                }
            } else {
                headingsContainer.innerHTML = '<div class="no-headings">データがありません</div>';
            }
        })
        .catch(error => {
            console.error('Error fetching headings:', error);
            headingsContainer.innerHTML = '<div class="no-headings">エラーが発生しました</div>';
        });
}

// マークダウンから見出しを抽出する関数
function extractHeadingsFromMarkdown(markdown) {
    const headings = [];
    const lines = markdown.split('\n');
    
    // h2見出し（## で始まる行）を検出
    const h2Pattern = /^## (.+)$/;
    
    lines.forEach(line => {
        const match = line.match(h2Pattern);
        if (match) {
            headings.push(match[1].trim());
        }
    });
    
    // 見出しがない場合は「サマリー」を追加
    if (headings.length === 0 && markdown.trim()) {
        headings.push('サマリー');
    }
    
    return headings;
}

// 見出しのクリックイベントを設定
function setupHeadingClickEvents() {
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
            
            // 記事コンテンツの読み込みと特定の見出しへのスクロール
            loadArticleContent(appName, headingText);
        });
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
        chatContainer.classList.toggle('active');
    }
}

// チャットメッセージを追加
function addMessage(message, sender) {
    const chatBody = document.querySelector('.chat-body');
    if (chatBody) {
        const messageElement = document.createElement('div');
        messageElement.classList.add('message', `${sender}-message`);
        messageElement.textContent = message;
        chatBody.appendChild(messageElement);
        
        // 最新のメッセージが見えるようにスクロール
        chatBody.scrollTop = chatBody.scrollHeight;
    }
} 