document.addEventListener('DOMContentLoaded', function() {
    // Sidebar toggle
    const sidebar = document.getElementById('sidebar');
    const menuToggle = document.getElementById('menuToggle');
    
    if (menuToggle && sidebar) {
        menuToggle.addEventListener('click', function() {
            sidebar.classList.toggle('expanded');
        });
    }
    
    // User dropdown
    const userBtn = document.getElementById('userBtn');
    const dropdownMenu = document.getElementById('dropdownMenu');
    
    if (userBtn && dropdownMenu) {
        userBtn.addEventListener('click', function(e) {
            e.stopPropagation();
            dropdownMenu.classList.toggle('active');
        });
        
        document.addEventListener('click', function(e) {
            if (!userBtn.contains(e.target) && !dropdownMenu.contains(e.target)) {
                dropdownMenu.classList.remove('active');
            }
        });
    }
    
    // News modal
    const viewAllBtn = document.getElementById('viewAllNewsBtn');
    const newsModal = document.getElementById('newsModal');
    const closeModalBtn = document.getElementById('closeNewsModal');
    const modalOverlay = document.getElementById('newsModalOverlay');
    
    if (viewAllBtn) {
        viewAllBtn.addEventListener('click', function() {
            newsModal.style.display = 'flex';
            loadAllNews();
        });
    }
    
    if (closeModalBtn) {
        closeModalBtn.addEventListener('click', function() {
            newsModal.style.display = 'none';
        });
    }
    
    if (modalOverlay) {
        modalOverlay.addEventListener('click', function() {
            newsModal.style.display = 'none';
        });
    }
    
    // Load trending news on page load
    loadTrendingNews();
    
    // Refresh every 5 minutes
    setInterval(loadTrendingNews, 300000);
});

async function loadTrendingNews() {
    try {
        const response = await fetch('/auth/trending/api/news/?limit=10');
        const data = await response.json();
        
        if (data.success && data.news.length > 0) {
            displayTrendingNews(data.news);
        } else {
            console.log('No trending news available');
        }
    } catch (error) {
        console.error('Error loading trending news:', error);
    }
}

function displayTrendingNews(newsItems) {
    const newsList = document.querySelector('.news-list');
    if (!newsList) return;
    
    // Clear existing news (except the "View All" button)
    const viewAllBtn = newsList.querySelector('.list-row:last-child');
    newsList.innerHTML = '';
    
    // Display top news items
    newsItems.slice(0, 3).forEach((news, index) => {
        const newsItem = createNewsItem(news, index + 1);
        newsList.appendChild(newsItem);
    });
    
    // Re-add "View All" button
    if (viewAllBtn) {
        newsList.appendChild(viewAllBtn);
    }
}

function createNewsItem(news, rank) {
    const newsItem = document.createElement('div');
    newsItem.className = 'news-item';
    newsItem.setAttribute('data-news-id', news.id);
    
    // Determine status badge
    let statusBadge = '';
    if (news.is_fact_checked) {
        const statusColors = {
            'verified': '#4caf50',
            'false': '#f44336',
            'misleading': '#ff9800',
            'unverified': '#9e9e9e'
        };
        const color = statusColors[news.fact_check_status] || '#9e9e9e';
        statusBadge = `<span style="font-size:10px; padding:2px 6px; background:${color}; border-radius:3px; margin-left:8px;">${news.fact_check_status.toUpperCase()}</span>`;
    }
    
    newsItem.innerHTML = `
        <div class="news-rank">${rank}</div>
        <div class="news-content">
            <div class="news-title">${escapeHtml(news.title)}${statusBadge}</div>
            <div class="news-author">By ${escapeHtml(news.author)} • ${news.time_ago}</div>
            <div class="news-actions">
                <button class="action-btn like-btn" onclick="voteNews('${news.id}', 'like', this)">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M14 9V5a3 3 0 0 0-3-3l-4 9v11h11.28a2 2 0 0 0 2-1.7l1.38-9a2 2 0 0 0-2-2.3zM7 22H4a2 2 0 0 1-2-2v-7a2 2 0 0 1 2-2h3"></path>
                    </svg>
                    <span>${news.likes}</span>
                </button>
                <button class="action-btn dislike-btn" onclick="voteNews('${news.id}', 'dislike', this)">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M10 15v4a3 3 0 0 0 3 3l4-9V2H5.72a2 2 0 0 0-2 1.7l-1.38 9a2 2 0 0 0 2 2.3zm7-13h2.67A2.31 2.31 0 0 1 22 4v7a2.31 2.31 0 0 1-2.33 2H17"></path>
                    </svg>
                    <span>${news.dislikes}</span>
                </button>
            </div>
        </div>
    `;
    
    return newsItem;
}

async function loadAllNews() {
    try {
        const response = await fetch('/auth/trending/api/news/?limit=50');
        const data = await response.json();
        
        if (data.success && data.news.length > 0) {
            displayAllNews(data.news);
        }
    } catch (error) {
        console.error('Error loading all news:', error);
    }
}

function displayAllNews(newsItems) {
    const newsGrid = document.querySelector('.news-grid');
    if (!newsGrid) return;
    
    newsGrid.innerHTML = '';
    
    newsItems.forEach((news, index) => {
        const newsCard = createNewsCard(news, index + 1);
        newsGrid.appendChild(newsCard);
    });
}

function createNewsCard(news, rank) {
    const newsCard = document.createElement('div');
    newsCard.className = 'news-card';
    newsCard.setAttribute('data-news-id', news.id);
    
    // Truncate content for excerpt
    const excerpt = news.content.length > 150 
        ? news.content.substring(0, 150) + '...' 
        : news.content;
    
    // Status badge
    let statusBadge = '';
    if (news.is_fact_checked) {
        const statusColors = {
            'verified': '#4caf50',
            'false': '#f44336',
            'misleading': '#ff9800',
            'unverified': '#9e9e9e'
        };
        const color = statusColors[news.fact_check_status] || '#9e9e9e';
        statusBadge = `<span style="font-size:11px; padding:3px 8px; background:${color}; border-radius:4px; margin-left:10px; display:inline-block; margin-top:5px;">${news.fact_check_status.toUpperCase()}</span>`;
    }
    
    newsCard.innerHTML = `
        <div class="news-card-rank">${rank}</div>
        <h3 class="news-card-title">${escapeHtml(news.title)}</h3>
        ${statusBadge}
        <p class="news-card-author">By ${escapeHtml(news.author)} • ${news.time_ago}</p>
        <p class="news-card-excerpt">${escapeHtml(excerpt)}</p>
        <div class="news-card-actions">
            <button class="action-btn like-btn" onclick="voteNews('${news.id}', 'like', this)">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M14 9V5a3 3 0 0 0-3-3l-4 9v11h11.28a2 2 0 0 0 2-1.7l1.38-9a2 2 0 0 0-2-2.3zM7 22H4a2 2 0 0 1-2-2v-7a2 2 0 0 1 2-2h3"></path>
                </svg>
                <span>${news.likes}</span>
            </button>
            <button class="action-btn dislike-btn" onclick="voteNews('${news.id}', 'dislike', this)">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M10 15v4a3 3 0 0 0 3 3l4-9V2H5.72a2 2 0 0 0-2 1.7l-1.38 9a2 2 0 0 0 2 2.3zm7-13h2.67A2.31 2.31 0 0 1 22 4v7a2.31 2.31 0 0 1-2.33 2H17"></path>
                </svg>
                <span>${news.dislikes}</span>
            </button>
        </div>
    `;
    
    return newsCard;
}

async function voteNews(newsId, voteType, buttonElement) {
    try {
        const response = await fetch(`/auth/trending/api/news/${newsId}/vote/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify({ vote_type: voteType })
        });
        
        const data = await response.json();
        
        if (data.success) {
            // Update the counts in the UI
            const newsItem = buttonElement.closest('[data-news-id]');
            if (newsItem) {
                const likeBtn = newsItem.querySelector('.like-btn span');
                const dislikeBtn = newsItem.querySelector('.dislike-btn span');
                
                if (likeBtn) likeBtn.textContent = data.likes;
                if (dislikeBtn) dislikeBtn.textContent = data.dislikes;
            }
            
            // Visual feedback
            buttonElement.style.transform = 'scale(1.2)';
            setTimeout(() => {
                buttonElement.style.transform = 'scale(1)';
            }, 200);
        }
    } catch (error) {
        console.error('Error voting:', error);
    }
}

function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
