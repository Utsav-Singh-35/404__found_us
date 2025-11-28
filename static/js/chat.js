document.addEventListener('DOMContentLoaded', function() {
    const chatForm = document.getElementById('chatForm');
    const messageInput = document.getElementById('messageInput');
    const welcomeScreen = document.getElementById('welcomeScreen');
    const messagesArea = document.getElementById('messagesArea');
    const chatArea = document.getElementById('chatArea');
    const userBtn = document.getElementById('userBtn');
    const dropdownMenu = document.getElementById('dropdownMenu');
    const bgVideo = document.getElementById('bgVideo');
    const fileInput = document.getElementById('fileInput');
    
    // Current conversation ID
    let currentConversationId = null;
    
    // Check if we're loading an existing conversation
    const pathParts = window.location.pathname.split('/');
    if (pathParts.length >= 4 && pathParts[2] === 'chat' && pathParts[3]) {
        currentConversationId = pathParts[3];
        // Load conversation history
        loadConversationHistory(currentConversationId);
    }
    
    // Handle file selection
    const fileNamesDisplay = document.getElementById('fileNames');
    if (fileInput && fileNamesDisplay) {
        fileInput.addEventListener('change', function(e) {
            const files = e.target.files;
            if (files.length > 0) {
                // Display file names
                if (files.length === 1) {
                    fileNamesDisplay.textContent = files[0].name;
                } else {
                    fileNamesDisplay.textContent = `${files.length} files selected`;
                }
            } else {
                fileNamesDisplay.textContent = '';
            }
        });
    }
    
    // Ensure video plays
    if (bgVideo) {
        bgVideo.play().catch(function(error) {
            // Video autoplay failed
        });
    }
    
    // Sidebar toggle
    const sidebar = document.getElementById('sidebar');
    const menuToggle = document.getElementById('menuToggle');
    
    if (menuToggle && sidebar) {
        menuToggle.addEventListener('click', function() {
            sidebar.classList.toggle('expanded');
        });
    }
    
    // New Chat button
    const newChatBtn = document.getElementById('newChatBtn');
    if (newChatBtn) {
        newChatBtn.addEventListener('click', async function() {
            try {
                // Create new conversation
                const response = await fetch('/auth/chat/api/conversations/create/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': getCookie('csrftoken')
                    },
                    body: JSON.stringify({
                        title: 'New Chat'
                    })
                });
                
                const data = await response.json();
                if (data.success) {
                    // Redirect to new conversation
                    window.location.href = `/auth/chat/${data.conversation.id}/`;
                } else {
                    alert('Failed to create new chat. Please try again.');
                }
            } catch (error) {
                alert('Error creating new chat. Please try again.');
            }
        });
    }
    
    // Current Chat button
    const currentChatBtn = document.getElementById('currentChatBtn');
    if (currentChatBtn) {
        currentChatBtn.addEventListener('click', function() {
            // Hide history list
            if (historyList) {
                historyList.style.display = 'none';
            }
            
            // Update active state
            document.querySelectorAll('.sidebar-item').forEach(item => {
                item.classList.remove('active');
            });
            currentChatBtn.classList.add('active');
            
            // If we have a current conversation, stay on it
            // Otherwise, show welcome screen
            if (!currentConversationId) {
                if (welcomeScreen) welcomeScreen.style.display = 'flex';
                if (messagesArea) messagesArea.style.display = 'none';
            }
        });
    }
    
    // History button
    const historyBtn = document.getElementById('historyBtn');
    const historyView = document.getElementById('historyView');
    const historySearchInput = document.getElementById('historySearchInput');
    let allConversations = [];
    
    if (historyBtn && historyView) {
        historyBtn.addEventListener('click', async function() {
            // Update active state
            document.querySelectorAll('.sidebar-item').forEach(item => {
                item.classList.remove('active');
            });
            historyBtn.classList.add('active');
            
            // Show history view
            historyView.style.display = 'flex';
            
            // Hide other views
            if (welcomeScreen) welcomeScreen.style.display = 'none';
            if (messagesArea) messagesArea.style.display = 'none';
            
            // Load conversations
            await loadConversationsTable();
        });
    }
    
    // Search functionality
    if (historySearchInput) {
        historySearchInput.addEventListener('input', function(e) {
            const searchTerm = e.target.value.toLowerCase();
            filterConversations(searchTerm);
        });
    }
    
    async function loadConversationsTable() {
        try {
            const response = await fetch('/auth/chat/api/conversations/');
            const data = await response.json();
            
            if (data.success) {
                allConversations = data.conversations;
                displayConversationsTable(allConversations);
            } else {
                const tbody = document.getElementById('historyTableBody');
                tbody.innerHTML = '<tr><td colspan="5" class="loading-row">No conversations yet</td></tr>';
            }
        } catch (error) {
            const tbody = document.getElementById('historyTableBody');
            tbody.innerHTML = '<tr><td colspan="5" class="loading-row">Error loading conversations</td></tr>';
        }
    }
    
    function displayConversationsTable(conversations) {
        const tbody = document.getElementById('historyTableBody');
        
        if (conversations.length === 0) {
            tbody.innerHTML = '<tr><td colspan="5" class="loading-row">No conversations found</td></tr>';
            return;
        }
        
        tbody.innerHTML = '';
        
        conversations.forEach((conv, index) => {
            const convId = conv.id || conv._id;
            
            if (!convId || convId === 'undefined') {
                return;
            }
            
            const date = new Date(conv.updated_at);
            const dateStr = formatDate(date);
            
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${index + 1}</td>
                <td>
                    <div class="chat-name-cell">
                        <span class="chat-name-text">${escapeHtml(conv.title)}</span>
                        <button class="edit-name-btn" onclick="openEditModal('${convId}', '${escapeHtml(conv.title)}')">
                            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path>
                                <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path>
                            </svg>
                        </button>
                    </div>
                </td>
                <td>${conv.message_count || 0}</td>
                <td>${dateStr}</td>
                <td>
                    <div class="action-buttons">
                        <button class="action-btn" onclick="viewConversation('${convId}')">
                            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path>
                                <circle cx="12" cy="12" r="3"></circle>
                            </svg>
                            View
                        </button>
                        <button class="action-btn delete-btn" onclick="deleteConversation('${convId}')">
                            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <polyline points="3 6 5 6 21 6"></polyline>
                                <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
                            </svg>
                            Delete
                        </button>
                    </div>
                </td>
            `;
            
            tbody.appendChild(row);
        });
    }
    
    function filterConversations(searchTerm) {
        if (!searchTerm) {
            displayConversationsTable(allConversations);
            return;
        }
        
        const filtered = allConversations.filter(conv => 
            conv.title.toLowerCase().includes(searchTerm)
        );
        
        displayConversationsTable(filtered);
    }
    
    function formatDate(date) {
        const now = new Date();
        const diff = now - date;
        const days = Math.floor(diff / (1000 * 60 * 60 * 24));
        
        if (days === 0) {
            return 'Today';
        } else if (days === 1) {
            return 'Yesterday';
        } else if (days < 7) {
            return `${days} days ago`;
        } else {
            return date.toLocaleDateString();
        }
    }
    
    // User dropdown toggle
    if (userBtn && dropdownMenu) {
        userBtn.addEventListener('click', function(e) {
            e.stopPropagation();
            dropdownMenu.classList.toggle('active');
        });
        
        // Close dropdown when clicking outside
        document.addEventListener('click', function(e) {
            if (!userBtn.contains(e.target) && !dropdownMenu.contains(e.target)) {
                dropdownMenu.classList.remove('active');
            }
        });
    }
    
    // Handle suggestion cards
    const suggestionCards = document.querySelectorAll('.suggestion-card');
    suggestionCards.forEach(card => {
        card.addEventListener('click', function() {
            const prompt = this.getAttribute('data-prompt');
            messageInput.value = prompt;
            messageInput.focus();
        });
    });
    
    // Handle welcome screen form submission
    chatForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const message = messageInput.value.trim();
        const files = fileInput ? fileInput.files : [];
        
        if (!message && files.length === 0) return;
        
        // Create conversation if first message
        if (!currentConversationId) {
            await createConversation();
        }
        
        // Activate chat mode
        activateChatMode();
        
        // Add user message to UI
        addMessage(message, 'user');
        
        // Send message to backend BEFORE clearing files
        await sendMessage(message, files);
        
        // Clear input and files AFTER sending
        messageInput.value = '';
        if (fileInput) {
            fileInput.value = '';
        }
        if (fileNamesDisplay) {
            fileNamesDisplay.textContent = '';
        }
    });
    
    // Handle chat mode form submission
    const chatFormActive = document.getElementById('chatFormActive');
    const messageInputActive = document.getElementById('messageInputActive');
    const fileInputActive = document.getElementById('fileInputActive');
    const chatFileNames = document.getElementById('chatFileNames');
    const chatAttachBtn = document.getElementById('chatAttachBtn');
    
    if (chatFormActive) {
        chatFormActive.addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const message = messageInputActive.value.trim();
            const files = fileInputActive ? fileInputActive.files : [];
            
            if (!message && files.length === 0) return;
            
            // Create conversation if first message
            if (!currentConversationId) {
                await createConversation();
            }
            
            // Add user message to UI
            addMessage(message, 'user');
            
            // Send message to backend BEFORE clearing
            await sendMessage(message, files);
            
            // Clear input and files AFTER sending
            messageInputActive.value = '';
            if (fileInputActive) {
                fileInputActive.value = '';
            }
            if (chatFileNames) {
                chatFileNames.textContent = '';
            }
        });
    }
    
    // Handle attach button in chat mode
    if (chatAttachBtn && fileInputActive) {
        chatAttachBtn.addEventListener('click', function() {
            fileInputActive.click();
        });
        
        fileInputActive.addEventListener('change', function(e) {
            const files = e.target.files;
            
            if (files.length > 0 && chatFileNames) {
                if (files.length === 1) {
                    chatFileNames.textContent = files[0].name;
                } else {
                    chatFileNames.textContent = `${files.length} files selected`;
                }
            } else if (chatFileNames) {
                chatFileNames.textContent = '';
            }
        });
    }
    
    async function createConversation() {
        try {
            const response = await fetch('/auth/chat/api/conversations/create/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken')
                },
                body: JSON.stringify({
                    title: 'New Chat'
                })
            });
            
            const data = await response.json();
            if (data.success) {
                currentConversationId = data.conversation.id;
                
                // Update chat header with conversation title
                const chatName = document.querySelector('.chat-name');
                if (chatName) {
                    chatName.textContent = data.conversation.title;
                }
            } else {
                addMessage(`Error: ${data.error || 'Failed to create conversation'}`, 'bot');
            }
        } catch (error) {
            addMessage('Error: Could not connect to server. Please check your connection.', 'bot');
        }
    }
    
    async function sendMessage(message, files) {
        try {
            if (!currentConversationId) {
                addMessage('Error: No conversation ID. Please refresh the page.', 'bot');
                return;
            }
            
            const formData = new FormData();
            formData.append('message', message);
            
            // Add files if any
            for (let i = 0; i < files.length; i++) {
                formData.append('files', files[i]);
            }
            
            const response = await fetch(`/auth/chat/api/${currentConversationId}/messages/send/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': getCookie('csrftoken')
                },
                body: formData
            });
            
            const data = await response.json();
            if (data.success) {
                // Display all messages from server (including bot response)
                data.messages.forEach(msg => {
                    if (msg.sender === 'bot') {
                        // Add bot response with slight delay for better UX
                        setTimeout(() => {
                            addMessage(msg.content, 'bot');
                        }, 500);
                    }
                    // User message already displayed, skip it
                });
            } else {
                addMessage(`Error: ${data.error || 'Failed to send message'}`, 'bot');
            }
        } catch (error) {
            addMessage('Error: Could not send message. Please check if MongoDB is configured.', 'bot');
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
    
    function activateChatMode() {
        // Hide welcome screen
        if (welcomeScreen) {
            welcomeScreen.style.display = 'none';
        }
        
        // Show messages area
        if (messagesArea) {
            messagesArea.style.display = 'flex';
        }
        
        // Add blur effect to background
        const mainContent = document.querySelector('.main-content');
        if (mainContent) {
            mainContent.classList.add('chat-active');
        }
    }
    
    function addMessage(text, type) {
        const messagesContainer = document.getElementById('messagesContainer');
        if (!messagesContainer) return;
        
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${type}-message`;
        
        if (type === 'bot') {
            messageDiv.innerHTML = `
                <div class="message-avatar">
                    <img src="/static/assects/images/Aurora.png" alt="SatyaMatrix">
                </div>
                <div class="message-content">
                    <p class="message-text">${escapeHtml(text)}</p>
                </div>
            `;
        } else {
            messageDiv.innerHTML = `
                <div class="message-content">
                    <p class="message-text">${escapeHtml(text)}</p>
                </div>
            `;
        }
        
        messagesContainer.appendChild(messageDiv);
        
        // Scroll to bottom smoothly
        setTimeout(() => {
            messagesContainer.scrollTo({
                top: messagesContainer.scrollHeight,
                behavior: 'smooth'
            });
        }, 100);
    }
    
    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
    
    async function loadConversationHistory(conversationId) {
        try {
            const response = await fetch(`/auth/chat/api/${conversationId}/messages/`);
            const data = await response.json();
            
            if (data.success && data.messages.length > 0) {
                // Activate chat mode
                activateChatMode();
                
                // Display all messages
                data.messages.forEach(msg => {
                    addMessage(msg.content, msg.sender);
                });
            }
        } catch (error) {
            // Error loading conversation history
        }
    }
    
    // Focus input on load
    if (messageInput) {
        messageInput.focus();
    }
    
    // Edit Modal functionality
    const editChatModal = document.getElementById('editChatModal');
    const closeEditModal = document.getElementById('closeEditModal');
    const cancelEditBtn = document.getElementById('cancelEditBtn');
    const saveEditBtn = document.getElementById('saveEditBtn');
    const editChatNameInput = document.getElementById('editChatNameInput');
    const editChatId = document.getElementById('editChatId');
    
    if (closeEditModal) {
        closeEditModal.addEventListener('click', function() {
            editChatModal.style.display = 'none';
        });
    }
    
    if (cancelEditBtn) {
        cancelEditBtn.addEventListener('click', function() {
            editChatModal.style.display = 'none';
        });
    }
    
    if (saveEditBtn) {
        saveEditBtn.addEventListener('click', async function() {
            const newName = editChatNameInput.value.trim();
            const chatId = editChatId.value;
            
            if (!newName) {
                alert('Please enter a chat name');
                return;
            }
            
            try {
                const response = await fetch(`/auth/chat/api/conversations/${chatId}/update/`, {
                    method: 'PUT',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': getCookie('csrftoken')
                    },
                    body: JSON.stringify({ title: newName })
                });
                
                const data = await response.json();
                if (data.success) {
                    editChatModal.style.display = 'none';
                    await loadConversationsTable();
                } else {
                    alert('Failed to update chat name');
                }
            } catch (error) {
                alert('Error updating chat name');
            }
        });
    }
    
    // Make functions global for onclick handlers
    window.openEditModal = function(chatId, currentName) {
        editChatId.value = chatId;
        editChatNameInput.value = currentName;
        editChatModal.style.display = 'flex';
        editChatNameInput.focus();
    };
    
    window.viewConversation = function(chatId) {
        window.location.href = `/auth/chat/${chatId}/`;
    };
    
    window.deleteConversation = async function(chatId) {
        if (!confirm('Are you sure you want to delete this conversation? This action cannot be undone.')) {
            return;
        }
        
        try {
            const response = await fetch(`/auth/chat/api/conversations/${chatId}/delete/`, {
                method: 'DELETE',
                headers: {
                    'X-CSRFToken': getCookie('csrftoken')
                }
            });
            
            const data = await response.json();
            if (data.success) {
                await loadConversationsTable();
                
                // If deleted current conversation, redirect to chat home
                if (chatId === currentConversationId) {
                    window.location.href = '/auth/chat/';
                }
            } else {
                alert('Failed to delete conversation');
            }
        } catch (error) {
            alert('Error deleting conversation');
        }
    };
});
