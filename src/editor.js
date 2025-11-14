/**
 * GeneLingua Editor - Main JavaScript
 * Handles UI interactions for the video editor interface
 */

class EditorApp {
    constructor() {
        this.isLeftPanelVisible = true;
        this.init();
    }

    init() {
        this.setupSidebarNavigation();
        this.setupHeaderButtons();
        this.setupTabs();
        this.setupSummaryTabs();
        this.setupTranscriptInteractions();
        this.setupResizablePanel();
    }

    /**
     * Sidebar Navigation
     */
    setupSidebarNavigation() {
        const sidebarIcons = document.querySelectorAll('.sidebar-icon');

        sidebarIcons.forEach((icon, index) => {
            icon.addEventListener('click', () => {
                // Remove active class from all icons
                sidebarIcons.forEach(i => i.classList.remove('active'));

                // Add active class to clicked icon
                icon.classList.add('active');

                // Show left panel when any sidebar icon is clicked
                this.showLeftPanel();

                // Switch content based on sidebar icon
                const sections = ['Text', 'Analytics', 'Video', 'Files', 'Settings'];
                this.switchMainContent(sections[index]);

                console.log(`Navigated to: ${sections[index]}`);
            });
        });
    }

    /**
     * Switch main content based on section
     */
    switchMainContent(section) {
        const leftPanel = document.querySelector('.left-panel');
        if (!leftPanel) return;

        let contentHTML = '';

        switch (section) {
            case 'Text':
                contentHTML = this.getTextEditorHTML();
                break;
            case 'Analytics':
                contentHTML = this.getAnalyticsContentHTML();
                break;
            case 'Video':
                contentHTML = this.getVideoContentHTML();
                break;
            case 'Files':
                contentHTML = this.getFilesContentHTML();
                break;
            case 'Settings':
                contentHTML = this.getSettingsContentHTML();
                break;
        }

        leftPanel.innerHTML = contentHTML;

        // Re-setup interactions after content change
        this.setupTabs();
        this.setupTranscriptInteractions();

        // Initialize markdown editor if Text section is loaded
        if (section === 'Text' && typeof MarkdownEditor !== 'undefined') {
            setTimeout(() => {
                if (!this.markdownEditor) {
                    this.markdownEditor = new MarkdownEditor();
                }
                this.markdownEditor.init();
            }, 100);
        }
    }

    /**
     * Header Buttons
     */
    setupHeaderButtons() {
        const backBtn = document.querySelector('.back-btn');
        const upgradeBtn = document.querySelector('.btn-secondary');
        const newBtn = document.querySelector('.btn-primary');

        if (backBtn) {
            backBtn.addEventListener('click', () => {
                console.log('Back button clicked');
                // Hide left panel when back is clicked
                this.hideLeftPanel();
            });
        }

        if (upgradeBtn) {
            upgradeBtn.addEventListener('click', () => {
                console.log('Upgrade button clicked');
                // Implement upgrade modal or navigation
                this.showUpgradeModal();
            });
        }

        if (newBtn) {
            newBtn.addEventListener('click', () => {
                console.log('New button clicked');
                // Implement create new document logic
                this.createNewDocument();
            });
        }
    }

    /**
     * Main Content Tabs (Transcript, Subtitles, Chapter)
     */
    setupTabs() {
        const tabs = document.querySelectorAll('.tab');

        tabs.forEach((tab, index) => {
            tab.addEventListener('click', () => {
                // Remove active class from all tabs
                tabs.forEach(t => t.classList.remove('active'));

                // Add active class to clicked tab
                tab.classList.add('active');

                // Switch content based on tab
                const tabName = tab.textContent.trim();
                this.switchTabContent(tabName);
            });
        });
    }

    switchTabContent(tabName) {
        console.log(`Switched to tab: ${tabName}`);

        // Here you would implement actual content switching logic
        // For now, we'll just update the transcript container
        const transcriptContainer = document.querySelector('.transcript-container');

        switch (tabName) {
            case 'Transcript':
                // Show transcript content (already visible)
                if (transcriptContainer) {
                    transcriptContainer.style.display = 'block';
                }
                break;
            case 'Subtitles':
                // Load/show subtitle content
                console.log('Loading subtitles...');
                // You can replace content here
                break;
            case 'Chapter':
                // Load/show chapter content
                console.log('Loading chapters...');
                // You can replace content here
                break;
        }
    }

    /**
     * Summary Panel Tabs (Summary, Mind Map, AI Chat, More)
     */
    setupSummaryTabs() {
        const summaryTabs = document.querySelectorAll('.summary-tab');

        summaryTabs.forEach((tab, index) => {
            tab.addEventListener('click', () => {
                // Remove active class from all summary tabs
                summaryTabs.forEach(t => t.classList.remove('active'));

                // Add active class to clicked tab
                tab.classList.add('active');

                // Switch summary content
                const tabName = tab.textContent.trim();
                this.switchSummaryContent(tabName);
            });
        });
    }

    switchSummaryContent(tabName) {
        console.log(`Switched to summary tab: ${tabName}`);

        const summaryContent = document.querySelector('.summary-content');

        switch (tabName) {
            case 'Summary':
                // Show summary (default content)
                if (summaryContent) {
                    summaryContent.innerHTML = this.getSummaryHTML();
                }
                break;
            case 'Mind Map':
                // Show mind map content
                if (summaryContent) {
                    summaryContent.innerHTML = '<h2>Mind Map</h2><p>Mind map visualization will appear here...</p>';
                }
                break;
            case 'AI Chat':
                // Show AI chat interface
                if (summaryContent) {
                    summaryContent.innerHTML = this.getAIChatHTML();
                }
                break;
            case 'More':
                // Show more options
                if (summaryContent) {
                    summaryContent.innerHTML = '<h2>More Options</h2><p>Additional features coming soon...</p>';
                }
                break;
        }
    }

    /**
     * Show/Hide Left Panel
     */
    showLeftPanel() {
        const leftPanel = document.querySelector('.left-panel');
        const resizeHandle = document.getElementById('resizeHandle');
        const rightPanel = document.querySelector('.right-panel');
        const backBtn = document.querySelector('.back-btn');

        if (leftPanel && resizeHandle && rightPanel) {
            leftPanel.classList.remove('collapsed');
            resizeHandle.classList.remove('collapsed');
            rightPanel.classList.remove('expanded');
            if (backBtn) {
                backBtn.classList.remove('hidden');
            }
            this.isLeftPanelVisible = true;
            console.log('Left panel shown');
        }
    }

    hideLeftPanel() {
        const leftPanel = document.querySelector('.left-panel');
        const resizeHandle = document.getElementById('resizeHandle');
        const rightPanel = document.querySelector('.right-panel');
        const backBtn = document.querySelector('.back-btn');

        if (leftPanel && resizeHandle && rightPanel) {
            leftPanel.classList.add('collapsed');
            resizeHandle.classList.add('collapsed');
            rightPanel.classList.add('expanded');
            if (backBtn) {
                backBtn.classList.add('hidden');
            }
            this.isLeftPanelVisible = false;
            console.log('Left panel hidden');
        }
    }

    /**
     * Resizable Panel Divider
     */
    setupResizablePanel() {
        const resizeHandle = document.getElementById('resizeHandle');
        const leftPanel = document.querySelector('.left-panel');
        const rightPanel = document.querySelector('.right-panel');
        const mainContent = document.querySelector('.main-content');

        if (!resizeHandle || !leftPanel || !rightPanel || !mainContent) return;

        let isResizing = false;
        let startX = 0;
        let startRightWidth = 0;

        resizeHandle.addEventListener('mousedown', (e) => {
            isResizing = true;
            startX = e.clientX;
            startRightWidth = rightPanel.offsetWidth;

            resizeHandle.classList.add('resizing');
            document.body.style.cursor = 'col-resize';
            document.body.style.userSelect = 'none';

            e.preventDefault();
        });

        document.addEventListener('mousemove', (e) => {
            if (!isResizing) return;

            const delta = startX - e.clientX;
            const newRightWidth = startRightWidth + delta;

            // Apply constraints
            const minWidth = 350;
            const maxWidth = 800;
            const mainContentWidth = mainContent.offsetWidth;
            const maxAllowedWidth = mainContentWidth - 400; // Keep at least 400px for left panel

            const constrainedWidth = Math.max(minWidth, Math.min(newRightWidth, maxWidth, maxAllowedWidth));

            rightPanel.style.width = `${constrainedWidth}px`;
        });

        document.addEventListener('mouseup', () => {
            if (isResizing) {
                isResizing = false;
                resizeHandle.classList.remove('resizing');
                document.body.style.cursor = '';
                document.body.style.userSelect = '';
            }
        });

        // Double-click to reset to default width
        resizeHandle.addEventListener('dblclick', () => {
            rightPanel.style.width = '450px';
        });
    }

    /**
     * Transcript Item Interactions
     */
    setupTranscriptInteractions() {
        const transcriptItems = document.querySelectorAll('.transcript-item');

        transcriptItems.forEach(item => {
            // Click to jump to timestamp (if video is present)
            item.addEventListener('click', () => {
                const timestamp = item.querySelector('.timestamp');
                if (timestamp) {
                    const time = timestamp.textContent.trim();
                    this.jumpToTimestamp(time);
                }
            });

            // Hover effect
            item.addEventListener('mouseenter', () => {
                item.style.backgroundColor = '#f0f0f0';
            });

            item.addEventListener('mouseleave', () => {
                item.style.backgroundColor = '#f9f9f9';
            });
        });
    }

    jumpToTimestamp(timeString) {
        console.log(`Jumping to timestamp: ${timeString}`);

        // Convert timestamp string to seconds (e.g., "01:15" -> 75 seconds)
        const parts = timeString.split(':');
        const seconds = parseInt(parts[0]) * 60 + parseInt(parts[1]);

        // If you have an actual video element, you would seek to this time
        const video = document.querySelector('video');
        if (video) {
            video.currentTime = seconds;
            video.play();
        }
    }

    /**
     * Modal/Dialog helpers
     */
    showUpgradeModal() {
        alert('Upgrade modal - This would show pricing/upgrade options');
        // Replace with actual modal implementation
    }

    createNewDocument() {
        if (confirm('Create a new document? Any unsaved changes will be lost.')) {
            console.log('Creating new document...');
            // Implement new document creation logic
        }
    }

    /**
     * Content Templates
     */
    getSummaryHTML() {
        return `
            <h2>Summary</h2>
            <div class="content-placeholder"></div>
            <div class="content-placeholder"></div>
            <div class="content-placeholder medium"></div>
            <br>

            <div class="summary-section">
                <h3>Key Themes and Insights</h3>
                <ul>
                    <li>
                        <div class="content-placeholder"></div>
                        <div class="content-placeholder short"></div>
                    </li>
                    <li>
                        <div class="content-placeholder"></div>
                        <div class="content-placeholder medium"></div>
                    </li>
                    <li>
                        <div class="content-placeholder"></div>
                    </li>
                </ul>
            </div>

            <div class="summary-section">
                <h3>Additional Points</h3>
                <ul>
                    <li>
                        <div class="content-placeholder"></div>
                        <div class="content-placeholder short"></div>
                    </li>
                    <li>
                        <div class="content-placeholder"></div>
                    </li>
                </ul>
            </div>
        `;
    }

    getAIChatHTML() {
        return `
            <h2>AI Chat</h2>
            <div class="chat-container">
                <div class="chat-messages">
                    <p>Start a conversation about your video...</p>
                </div>
                <div class="chat-input-container">
                    <input type="text" placeholder="Type your message..." class="input">
                    <button class="btn btn-primary">Send</button>
                </div>
            </div>
        `;
    }

    /**
     * Section Content Templates
     */
    getTextEditorHTML() {
        return `
            <div class="markdown-editor-container">
                <div class="editor-toolbar">
                    <div class="mode-toggle">
                        <button id="edit-btn" class="mode-btn active">Edit</button>
                        <button id="preview-btn" class="mode-btn">Preview</button>
                    </div>
                    <!-- Toolbar button groups will be inserted here by MarkdownEditor.createToolbarButtons() -->
                    <div class="toolbar-spacer"></div>
                    <div class="toolbar-actions">
                        <button id="save-btn" class="btn btn-success">💾 Save</button>
                        <button id="clear-btn" class="btn btn-error">🗑️ Clear</button>
                        <span id="save-indicator">Saved</span>
                    </div>
                    <div id="word-count" class="word-count"></div>
                </div>
                
                <div id="editor-container">
                    <textarea id="markdown-textarea" 
                              placeholder="Start writing your markdown here..."></textarea>
                </div>
                
                <div id="preview-container">
                    <div id="preview-content"></div>
                </div>
            </div>
        `;
    }

    getAnalyticsContentHTML() {
        return `
            <div class="section-content">
                <h2>📊 Analytics</h2>
                <div class="content-placeholder" style="height: 200px;"></div>
                <p>Analytics data, charts, and statistics will appear here.</p>
            </div>
        `;
    }

    getVideoContentHTML() {
        return `
            <div class="video-container">
                <div class="video-placeholder">Video Placeholder</div>
            </div>

            <div class="tabs">
                <button class="tab active">Transcript</button>
                <button class="tab">Subtitles</button>
                <button class="tab">Chapter</button>
            </div>

            <div class="transcript-container">
                <div class="transcript-item">
                    <div class="timestamp">00:00</div>
                    <div class="transcript-text">
                        <div class="content-placeholder"></div>
                        <div class="content-placeholder"></div>
                        <div class="content-placeholder short"></div>
                    </div>
                </div>

                <div class="transcript-item">
                    <div class="timestamp">00:27</div>
                    <div class="transcript-text">
                        <div class="content-placeholder"></div>
                        <div class="content-placeholder medium"></div>
                    </div>
                </div>

                <div class="transcript-item">
                    <div class="timestamp">01:15</div>
                    <div class="transcript-text">
                        <div class="content-placeholder"></div>
                        <div class="content-placeholder"></div>
                        <div class="content-placeholder short"></div>
                    </div>
                </div>
            </div>
        `;
    }

    getFilesContentHTML() {
        return `
            <div class="section-content">
                <h2>📁 Files</h2>
                <div class="file-list">
                    <div class="file-item">
                        <span class="file-icon">📄</span>
                        <div>
                            <div class="file-name">Document 1.pdf</div>
                            <div class="file-meta">2.5 MB • Modified 2 days ago</div>
                        </div>
                    </div>
                    <div class="file-item">
                        <span class="file-icon">🎥</span>
                        <div>
                            <div class="file-name">Video Presentation.mp4</div>
                            <div class="file-meta">15.8 MB • Modified yesterday</div>
                        </div>
                    </div>
                    <div class="file-item">
                        <span class="file-icon">📊</span>
                        <div>
                            <div class="file-name">Report.xlsx</div>
                            <div class="file-meta">1.2 MB • Modified last week</div>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    getSettingsContentHTML() {
        return `
            <div class="section-content">
                <h2>⚙️ Settings</h2>
                <div class="settings-group">
                    <h3>General</h3>
                    <div class="settings-option">
                        <label>
                            <input type="checkbox" checked>
                            <span>Enable notifications</span>
                        </label>
                    </div>
                </div>
                <div class="settings-group">
                    <h3>Appearance</h3>
                    <div class="settings-option">
                        <label>
                            <input type="checkbox">
                            <span>Dark mode</span>
                        </label>
                    </div>
                </div>
                <div class="settings-group">
                    <h3>Privacy</h3>
                    <div class="settings-option">
                        <label>
                            <input type="checkbox" checked>
                            <span>Share analytics data</span>
                        </label>
                    </div>
                </div>
            </div>
        `;
    }
}

// Initialize the app when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    console.log('GeneLingua Editor initialized');
    new EditorApp();
});

// Optional: Add keyboard shortcuts
document.addEventListener('keydown', (e) => {
    // Example: Press 'Escape' to go back
    if (e.key === 'Escape') {
        const backBtn = document.querySelector('.back-btn');
        if (backBtn) backBtn.click();
    }

    // Example: Ctrl/Cmd + N for new document
    if ((e.ctrlKey || e.metaKey) && e.key === 'n') {
        e.preventDefault();
        const newBtn = document.querySelector('.btn-primary');
        if (newBtn) newBtn.click();
    }
});
