// PWA Service Worker Registration
if ('serviceWorker' in navigator) {
    window.addEventListener('load', () => {
        navigator.serviceWorker.register('/static/sw.js')
            .then(registration => {
                console.log('✅ PWA Service Worker registered:', registration.scope);

                // Check for updates
                registration.addEventListener('updatefound', () => {
                    const newWorker = registration.installing;
                    newWorker.addEventListener('statechange', () => {
                        if (newWorker.state === 'installed' && navigator.serviceWorker.controller) {
                            // New content available, refresh page
                            if (confirm('New version available! Refresh to update?')) {
                                window.location.reload();
                            }
                        }
                    });
                });
            })
            .catch(error => {
                console.log('❌ PWA Service Worker registration failed:', error);
            });
    });
}

// PWA Install Prompt
let deferredPrompt;
window.addEventListener('beforeinstallprompt', (e) => {
    console.log('💾 PWA install prompt available');
    e.preventDefault();
    deferredPrompt = e;

    // Show custom install button/banner if desired
    showInstallButton();
});

// PWA Install Function
function installPWA() {
    if (deferredPrompt) {
        deferredPrompt.prompt();
        deferredPrompt.userChoice.then((choiceResult) => {
            if (choiceResult.outcome === 'accepted') {
                console.log('✅ User accepted PWA install');
            } else {
                console.log('❌ User dismissed PWA install');
            }
            deferredPrompt = null;
        });
    }
}

// Show install button
function showInstallButton() {
    const installBtn = document.getElementById('installPWA');
    if (installBtn) {
        installBtn.style.display = 'inline-block';
    }
    console.log('📱 PWA can be installed - install button shown');
}

// Fullscreen toggle function
function toggleFullscreen() {
    if (!document.fullscreenElement && !document.webkitFullscreenElement && !document.msFullscreenElement) {
        enterFullscreen();
    } else {
        if (document.exitFullscreen) {
            document.exitFullscreen();
        } else if (document.webkitExitFullscreen) {
            document.webkitExitFullscreen();
        } else if (document.msExitFullscreen) {
            document.msExitFullscreen();
        }
    }
}

// Update fullscreen button icon
document.addEventListener('fullscreenchange', updateFullscreenIcon);
document.addEventListener('webkitfullscreenchange', updateFullscreenIcon);
document.addEventListener('msfullscreenchange', updateFullscreenIcon);

function updateFullscreenIcon() {
    const fullscreenBtn = document.getElementById('fullscreenToggle');
    if (fullscreenBtn) {
        const icon = fullscreenBtn.querySelector('i');
        if (document.fullscreenElement || document.webkitFullscreenElement || document.msFullscreenElement) {
            icon.className = 'codicon codicon-screen-normal';
            fullscreenBtn.title = 'Exit Fullscreen (F11)';
        } else {
            icon.className = 'codicon codicon-screen-full';
            fullscreenBtn.title = 'Enter Fullscreen (F11)';
        }
    }
}

// Fullscreen API for desktop app experience
function enterFullscreen() {
    const elem = document.documentElement;
    if (elem.requestFullscreen) {
        elem.requestFullscreen();
    } else if (elem.webkitRequestFullscreen) {
        elem.webkitRequestFullscreen();
    } else if (elem.msRequestFullscreen) {
        elem.msRequestFullscreen();
    }
}

// Keyboard shortcut for fullscreen (F11 alternative)
document.addEventListener('keydown', (e) => {
    if (e.key === 'F11' || (e.ctrlKey && e.shiftKey && e.key === 'F')) {
        e.preventDefault();
        if (!document.fullscreenElement) {
            enterFullscreen();
        } else {
            document.exitFullscreen();
        }
    }
});

// Tab switching
document.querySelectorAll('.tab').forEach(tab => {
    tab.addEventListener('click', () => {
        const targetTab = tab.dataset.tab;

        // Update tab active state
        document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
        tab.classList.add('active');

        // Update content active state
        document.querySelectorAll('.tab-content').forEach(content => {
            content.classList.remove('active');
        });
        document.getElementById(`${targetTab}-content`).classList.add('active');

        // Auto-show assessment panel when switching to Talk Experts tab
        // This will be enhanced after AssessmentPanel class is initialized
        if (targetTab === 'experts') {
            // Try to use the AssessmentPanel class if available
            if (window.assessmentPanelInstance) {
                window.assessmentPanelInstance.show();
            } else {
                // Fallback for early execution
                const panel = document.getElementById('assessmentPanel');
                if (panel && !panel.classList.contains('active')) {
                    panel.classList.add('active');
                }
            }
        }
    });
});

// Sidebar toggle functionality
const sidebar = document.querySelector('.sidebar');
let currentActivePanel = 'explorer';
let sidebarVisible = true;

// Activity bar switching with sidebar toggle
document.querySelectorAll('.activity-item').forEach(item => {
    item.addEventListener('click', () => {
        const panel = item.dataset.panel;

        if (currentActivePanel === panel && sidebarVisible) {
            // Clicking the same active panel - hide sidebar
            hideSidebar();
        } else {
            // Show sidebar and switch to new panel
            showSidebar();
            switchToPanel(panel);
        }

        // Update active states
        document.querySelectorAll('.activity-item').forEach(i => i.classList.remove('active'));
        if (sidebarVisible) {
            item.classList.add('active');
            currentActivePanel = panel;
        }
    });
});

function showSidebar() {
    sidebar.classList.remove('collapsed');
    sidebarVisible = true;
    console.log('📱 Sidebar opened');
}

function hideSidebar() {
    sidebar.classList.add('collapsed');
    sidebarVisible = false;
    currentActivePanel = null;
    document.querySelectorAll('.activity-item').forEach(i => i.classList.remove('active'));
    console.log('📱 Sidebar closed');
}

function switchToPanel(panel) {
    // Update sidebar header and content based on panel
    const sidebarHeader = document.querySelector('.sidebar-header h3');
    const panelConfigs = {
        'profile': {
            title: '<i class="codicon codicon-person"></i> USER PROFILE',
            contentId: 'profile-content'
        },
        'lessons': {
            title: '<i class="codicon codicon-book"></i> LESSON GENERATOR',
            contentId: 'lessons-content'
        },
        'progress': {
            title: '<i class="codicon codicon-graph-line"></i> PROGRESS',
            contentId: 'progress-content'
        },
        'resources': {
            title: '<i class="codicon codicon-cloud-download"></i> RESOURCES',
            contentId: 'resources-content'
        },
        'settings': {
            title: '<i class="codicon codicon-settings-gear"></i> SETTINGS',
            contentId: 'settings-content'
        }
    };

    const config = panelConfigs[panel];
    if (config && sidebarHeader) {
        // Update header
        sidebarHeader.innerHTML = config.title;

        // Hide all sidebar content sections
        document.querySelectorAll('.sidebar-content').forEach(content => {
            content.style.display = 'none';
        });

        // Show the selected content
        const targetContent = document.getElementById(config.contentId);
        if (targetContent) {
            targetContent.style.display = 'block';
        }

        console.log(`📱 Switched to ${panel} panel`);
    }
}

// Initialize sidebar state
function initializeSidebar() {
    // Start with explorer panel active and sidebar visible
    const explorerItem = document.querySelector('.activity-item[data-panel="explorer"]');
    if (explorerItem) {
        explorerItem.classList.add('active');
    }

    // Ensure profile content is visible by default
    switchToPanel('explorer');
    console.log('📱 Sidebar initialized');
}

// Keyboard shortcuts for sidebar
document.addEventListener('keydown', (e) => {
    // Ctrl/Cmd + B to toggle sidebar
    if ((e.ctrlKey || e.metaKey) && e.key === 'b') {
        e.preventDefault();
        if (sidebarVisible) {
            hideSidebar();
        } else {
            showSidebar();
            // Restore last active panel or default to explorer
            const lastActive = currentActivePanel || 'explorer';
            switchToPanel(lastActive);
            document.querySelector(`[data-panel="${lastActive}"]`)?.classList.add('active');
            currentActivePanel = lastActive;
        }
    }

    // Quick panel switching with Ctrl/Cmd + number keys
    if ((e.ctrlKey || e.metaKey) && e.key >= '1' && e.key <= '5') {
        e.preventDefault();
        const panels = ['explorer', 'search', 'git', 'extensions', 'settings'];
        const panelIndex = parseInt(e.key) - 1;
        const panel = panels[panelIndex];

        if (panel) {
            showSidebar();
            switchToPanel(panel);
            document.querySelectorAll('.activity-item').forEach(i => i.classList.remove('active'));
            document.querySelector(`[data-panel="${panel}"]`)?.classList.add('active');
            currentActivePanel = panel;
        }
    }
});

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', initializeSidebar);

// User profile loading
const userIdInput = document.getElementById('user_id');
const profileStatus = document.getElementById('profile_status');
const ancestrySelect = document.getElementById('ancestry');
const mbtiSelect = document.getElementById('mbti');
const targetLanguageSelect = document.getElementById('target_language');
const currentUserSpan = document.getElementById('current_user');
const currentLanguageSpan = document.getElementById('current_language');

userIdInput.addEventListener('blur', async () => {
    const userId = userIdInput.value.trim();
    if (!userId) {
        profileStatus.textContent = 'Enter your name to load saved settings';
        currentUserSpan.textContent = 'Not logged in';
        return;
    }

    try {
        const response = await fetch(`/load_profile?user_id=${encodeURIComponent(userId)}`);
        const data = await response.json();

        if (data.profile) {
            ancestrySelect.value = data.profile.ancestry || 'EAS';
            mbtiSelect.value = data.profile.mbti || 'INTJ';
            targetLanguageSelect.value = data.profile.target_language || 'japanese';

            profileStatus.textContent = `✅ Profile loaded for ${userId}`;
            currentUserSpan.textContent = userId;
            updateLanguageDisplay();
        } else {
            profileStatus.textContent = `New profile for ${userId}`;
            currentUserSpan.textContent = userId;
        }
    } catch (error) {
        console.error('Error loading profile:', error);
        profileStatus.textContent = 'Error loading profile';
    }
});

// Update language display
targetLanguageSelect.addEventListener('change', updateLanguageDisplay);

function updateLanguageDisplay() {
    const langMap = {
        'japanese': 'Japanese',
        'dutch': 'Dutch',
        'chinese': 'Chinese'
    };
    currentLanguageSpan.textContent = langMap[targetLanguageSelect.value] || targetLanguageSelect.value;
}

// Status message helper
function setStatus(message, isError = false) {
    const statusMessage = document.getElementById('status_message');
    const icon = isError ?
        '<i class="codicon codicon-error"></i>' :
        '<i class="codicon codicon-circle-filled"></i>';
    statusMessage.innerHTML = `${icon} ${message}`;
}

// DNA Analysis Button - REMOVED
// DNA analysis feature has been removed from the application

// Lesson Generation Button
document.addEventListener('DOMContentLoaded', () => {
    const generateLessonBtn = document.getElementById('generateLessonBtn');
    if (generateLessonBtn) {
        generateLessonBtn.addEventListener('click', async () => {
            const userId = userIdInput.value.trim() || 'unknown';
            const targetLanguage = targetLanguageSelect.value;
            const logText = document.getElementById('log_text').value;

            // Disable button and show loading
            generateLessonBtn.disabled = true;
            generateLessonBtn.innerHTML = '<i class="codicon codicon-loading codicon-modifier-spin"></i> Generating...';
            setStatus('Generating today\'s lesson...');

            try {
                // Prepare form data
                const formData = new FormData();
                formData.append('user_id', userId);
                formData.append('target_language', targetLanguage);
                formData.append('log_text', logText);

                // Send request to new lesson generation endpoint
                const response = await fetch('/api/generate-lesson', {
                    method: 'POST',
                    body: formData
                });

                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }

                const result = await response.json();

                // Update lesson content
                if (result.words) {
                    const wordsOutputEl = document.getElementById('words_output');
                    if (wordsOutputEl) wordsOutputEl.innerHTML = formatList(result.words);
                    const wordsDetailEl = document.getElementById('words_detail');
                    if (wordsDetailEl) wordsDetailEl.innerHTML = formatList(result.words);
                }

                if (result.sentences) {
                    const sentencesOutputEl = document.getElementById('sentences_output');
                    if (sentencesOutputEl) sentencesOutputEl.innerHTML = formatList(result.sentences);
                    const sentencesDetailEl = document.getElementById('sentences_detail');
                    if (sentencesDetailEl) sentencesDetailEl.innerHTML = formatList(result.sentences);
                }

                // Update Resources Tab
                updateResourcesTab(result.user_id || userId);

                // Handle audio
                if (result.audio_path) {
                    document.getElementById('audio_output').innerHTML =
                        `<audio controls style="width: 100%;">
                            <source src="/download/audio/${userId}" type="audio/mpeg">
                            Your browser does not support the audio element.
                        </audio>
                        <p class="output-text" style="margin-top: 12px;">Listen to native pronunciation</p>`;
                }

                // Handle Anki flashcards
                if (result.anki_path) {
                    loadFlashcards(`/download/anki/${userId}`);
                }

                setStatus('Lesson generated successfully!');

                // Switch to overview tab to show results
                document.querySelector('.tab[data-tab="overview"]').click();

            } catch (error) {
                console.error('Error:', error);
                setStatus('Error generating lesson', true);
                alert('An error occurred while generating the lesson. Please try again.');
            } finally {
                // Re-enable button
                generateLessonBtn.disabled = false;
                generateLessonBtn.innerHTML = '<i class="codicon codicon-mortar-board"></i> Generate Today\'s Lesson';
            }
        });
    }
});

// Theme switching: apply CSS variable sets for dark/light/auto and persist selection
(function () {
    const themeSelect = document.getElementById('theme_select');
    if (!themeSelect) return;

    const themes = {
        dark: {
            '--vscode-bg': '#1e1e1e',
            '--vscode-sidebar-bg': '#1e1e1e',
            '--vscode-editor-bg': '#1e1e1e',
            '--vscode-activitybar-bg': '#1e1e1e',
            '--vscode-statusbar-bg': '#007acc',
            '--vscode-border': '#1e1e1e',
            '--vscode-text': '#cccccc',
            '--vscode-text-secondary': '#969696',
            '--vscode-accent': '#007acc',
            '--vscode-hover': '#2a2d2e',
            '--vscode-active': '#37373d',
            '--vscode-input-bg': '#3c3c3c',
            '--vscode-button-bg': '#0e639c',
            '--vscode-button-hover': '#1177bb'
        },
        light: {
            '--vscode-bg': '#ffffff',
            '--vscode-sidebar-bg': '#f3f3f3',
            '--vscode-editor-bg': '#ffffff',
            '--vscode-activitybar-bg': '#f3f3f3',
            '--vscode-statusbar-bg': '#007acc',
            '--vscode-border': '#e5e5e5',
            '--vscode-text': '#333333',
            '--vscode-text-secondary': '#666666',
            '--vscode-accent': '#007acc',
            '--vscode-hover': '#e5e5e5',
            '--vscode-active': '#d6d6d6',
            '--vscode-input-bg': '#ffffff',
            '--vscode-button-bg': '#0e639c',
            '--vscode-button-hover': '#1177bb'
        }
    };

    function applyTheme(name) {
        let resolved = name;
        if (name === 'auto') {
            resolved = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
        }

        const vars = themes[resolved];
        if (!vars) return;

        Object.keys(vars).forEach(k => {
            document.documentElement.style.setProperty(k, vars[k]);
        });

        // mark dataset for possible CSS hooks
        document.documentElement.dataset.theme = resolved;
    }

    // load saved theme
    const saved = localStorage.getItem('app_theme') || 'auto';
    themeSelect.value = saved;
    applyTheme(saved);

    themeSelect.addEventListener('change', (e) => {
        const val = e.target.value;
        localStorage.setItem('app_theme', val);
        applyTheme(val);
    });

    // react to system changes when in auto
    if (window.matchMedia) {
        const mq = window.matchMedia('(prefers-color-scheme: dark)');
        mq.addEventListener && mq.addEventListener('change', () => {
            const current = localStorage.getItem('app_theme') || 'auto';
            if (current === 'auto') applyTheme('auto');
        });
    }
})();

// DNA-related functions have been removed

// Check for existing resources on page load
async function checkExistingResources() {
    // Get user ID from input field or current user display
    let userId = document.getElementById('user_id').value || document.getElementById('current_user').textContent;

    // Default to 'yusup' if no user is specified (since files exist for this user)
    if (!userId || userId === 'Not logged in') {
        userId = 'yusup';
    }

    if (userId) {
        console.log('🔍 Checking existing resources for user:', userId);

        // Check if files exist by trying to access them
        const resourceTypes = ['pdf', 'anki', 'audio'];
        const existingResources = [];

        for (const type of resourceTypes) {
            try {
                const response = await fetch(`/download/${type}/${userId}`);
                if (response.ok) {
                    existingResources.push(type);
                }
            } catch (error) {
                console.log(`${type} file not found for ${userId}`);
            }
        }

        if (existingResources.length > 0) {
            console.log('📁 Found existing resources:', existingResources);
            updateResourcesTab(userId);
        } else {
            console.log('📁 No existing resources found, showing empty message');
            showEmptyResourcesMessage();
        }
    }
}

// Show message when no resources are available
function showEmptyResourcesMessage() {
    const sections = [
        { id: 'pdf_output', message: 'Generate your learning plan to create a comprehensive PDF report' },
        { id: 'anki_output', message: 'Generate your learning plan to create Anki flashcard decks' },
        { id: 'audio_output', message: 'Generate your learning plan to create pronunciation audio guides' }
    ];

    sections.forEach(section => {
        const element = document.getElementById(section.id);
        if (element) {
            element.innerHTML = `<p class="output-text">${section.message}</p>`;
        }
    });
}

// Update Resources Tab with download links
function updateResourcesTab(userId) {
    console.log('📁 Updating resources tab for user:', userId);

    // Update PDF section
    const pdfOutput = document.getElementById('pdf_output');
    if (pdfOutput) {
        pdfOutput.innerHTML = `
            <div class="resource-item">
                <button class="btn btn-download" onclick="downloadResource('pdf', '${userId}')">
                    <i class="codicon codicon-file-pdf"></i> Download PDF Report
                </button>
                <p class="resource-desc">Complete learning analysis and personalized plan</p>
            </div>
        `;
    }

    // Update Anki section
    const ankiOutput = document.getElementById('anki_output');
    if (ankiOutput) {
        ankiOutput.innerHTML = `
            <div class="resource-item">
                <button class="btn btn-download" onclick="downloadResource('anki', '${userId}')">
                    <i class="codicon codicon-library"></i> Download Anki Deck CSV
                </button>
                <p class="resource-desc">Flashcard deck for spaced repetition learning</p>
            </div>
        `;
    }

    // Update Audio section
    const audioOutput = document.getElementById('audio_output');
    if (audioOutput) {
        audioOutput.innerHTML = `
            <div class="resource-item">
                <button class="btn btn-download" onclick="downloadResource('audio', '${userId}')">
                    <i class="codicon codicon-cloud-download"></i> Download Audio Guide
                </button>
                <button class="btn btn-play" onclick="playAudioGuide('${userId}')">
                    <i class="codicon codicon-play"></i> Play Audio Guide
                </button>
                <p class="resource-desc">Pronunciation guide for your vocabulary</p>
                <audio id="audioPlayer" controls style="display: none; width: 100%; margin-top: 10px;">
                    Your browser does not support the audio element.
                </audio>
            </div>
        `;
    }
}

// Download resource function
async function downloadResource(type, userId) {
    try {
        console.log(`⬇️ Downloading ${type} for user ${userId}`);
        const response = await fetch(`/download/${type}/${userId}`);

        if (response.ok) {
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.style.display = 'none';
            a.href = url;

            // Set filename based on type
            const fileExtensions = { pdf: 'pdf', anki: 'csv', audio: 'mp3' };
            a.download = `GeneLingua_${type}_${userId}.${fileExtensions[type]}`;

            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);

            console.log(`✅ ${type} downloaded successfully`);
        } else {
            throw new Error(`Failed to download ${type}`);
        }
    } catch (error) {
        console.error(`❌ Download failed:`, error);
        alert(`Failed to download ${type}. Please try again.`);
    }
}

// Play audio guide function
async function playAudioGuide(userId) {
    try {
        console.log(`🔊 Playing audio guide for user ${userId}`);
        const audioPlayer = document.getElementById('audioPlayer');
        const audioUrl = `/download/audio/${userId}`;

        audioPlayer.src = audioUrl;
        audioPlayer.style.display = 'block';
        await audioPlayer.play();

        console.log('✅ Audio guide playing');
    } catch (error) {
        console.error('❌ Audio playback failed:', error);
        alert('Failed to play audio guide. Please try downloading it instead.');
    }
}

// Helper functions - v1.1 - Fixed formatMarkdown and speech debug
function formatMarkdown(text) {
    // Guard against non-string input
    if (typeof text !== 'string') {
        console.warn('formatMarkdown received non-string:', typeof text, text);
        return String(text || '');
    }
    // Simple markdown formatting
    return text
        .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
        .replace(/\*(.+?)\*/g, '<em>$1</em>')
        .replace(/\n/g, '<br>')
        .replace(/^- (.+)$/gm, '<li>$1</li>')
        .replace(/(<li>.*<\/li>)/s, '<ul>$1</ul>');
}

function formatList(items) {
    if (typeof items === 'string') {
        items = items.split('\n').filter(item => item.trim());
    }
    if (!Array.isArray(items) || items.length === 0) {
        return '<p class="output-text">No items available</p>';
    }
    return '<ul>' + items.map(item => `<li>${item}</li>`).join('') + '</ul>';
}

// Initialize language display
updateLanguageDisplay();

// Initial status
setStatus('Ready');

// ==================== FLASHCARD FUNCTIONALITY ====================
let flashcards = [];
let currentCardIndex = 0;

const flashcardElement = document.getElementById('flashcard');
const flashcardFront = document.querySelector('.flashcard-front .output-text');
const flashcardBack = document.querySelector('.flashcard-back .output-text');
const flipButton = document.getElementById('flipCard');
const prevButton = document.getElementById('prevCard');
const nextButton = document.getElementById('nextCard');
const cardCounter = document.getElementById('cardCounter');

// Flip card
flipButton.addEventListener('click', () => {
    flashcardElement.classList.toggle('flipped');
});

flashcardElement.addEventListener('click', () => {
    flashcardElement.classList.toggle('flipped');
});

// Previous card
prevButton.addEventListener('click', () => {
    if (currentCardIndex > 0) {
        currentCardIndex--;
        updateFlashcard();
    }
});

// Next card
nextButton.addEventListener('click', () => {
    if (currentCardIndex < flashcards.length - 1) {
        currentCardIndex++;
        updateFlashcard();
    }
});

function loadFlashcards(ankiPath) {
    if (!ankiPath) {
        flashcards = [];
        updateFlashcardUI();
        return;
    }

    // Fetch and parse the Anki CSV
    fetch(ankiPath)
        .then(response => response.text())
        .then(csv => {
            const lines = csv.trim().split('\n');
            flashcards = lines.map(line => {
                const [front, back] = line.split(',').map(s => s.trim().replace(/^"|"$/g, ''));
                return { front, back };
            });
            currentCardIndex = 0;
            updateFlashcard();
        })
        .catch(error => {
            console.error('Error loading flashcards:', error);
            flashcards = [];
            updateFlashcardUI();
        });
}

function updateFlashcard() {
    if (flashcards.length === 0) {
        flashcardFront.textContent = 'No flashcards available';
        flashcardBack.textContent = 'Generate your learning plan first';
        prevButton.disabled = true;
        nextButton.disabled = true;
        cardCounter.textContent = '0 / 0';
        return;
    }

    const card = flashcards[currentCardIndex];
    flashcardFront.textContent = card.front;
    flashcardBack.textContent = card.back;

    // Remove flipped class when changing cards
    flashcardElement.classList.remove('flipped');

    // Update navigation
    prevButton.disabled = currentCardIndex === 0;
    nextButton.disabled = currentCardIndex === flashcards.length - 1;
    cardCounter.textContent = `${currentCardIndex + 1} / ${flashcards.length}`;
}

function updateFlashcardUI() {
    updateFlashcard();
}

// Keyboard navigation for flashcards
document.addEventListener('keydown', (e) => {
    const ankiTab = document.getElementById('anki-content');
    if (!ankiTab.classList.contains('active')) return;

    if (e.key === 'ArrowLeft') {
        prevButton.click();
    } else if (e.key === 'ArrowRight') {
        nextButton.click();
    } else if (e.key === ' ' || e.key === 'Enter') {
        e.preventDefault();
        flipButton.click();
    }
});

// ==================== MARKDOWN EDITOR FUNCTIONALITY ====================
const markdownInput = document.getElementById('markdownInput');
const markdownPreview = document.getElementById('markdownPreview');
const clearMarkdownBtn = document.getElementById('clearMarkdown');

// Update preview on input
markdownInput.addEventListener('input', () => {
    updateMarkdownPreview();
});

// Clear button
clearMarkdownBtn.addEventListener('click', () => {
    if (confirm('Are you sure you want to clear the editor?')) {
        markdownInput.value = '';
        updateMarkdownPreview();
    }
});

function updateMarkdownPreview() {
    const markdown = markdownInput.value;
    const html = convertMarkdownToHTML(markdown);
    markdownPreview.innerHTML = html || '<p class="output-text">Start typing in the editor to see the preview here...</p>';
}

function convertMarkdownToHTML(markdown) {
    if (!markdown.trim()) return '';

    let html = markdown;

    // Headers
    html = html.replace(/^### (.*$)/gim, '<h3>$1</h3>');
    html = html.replace(/^## (.*$)/gim, '<h2>$1</h2>');
    html = html.replace(/^# (.*$)/gim, '<h1>$1</h1>');

    // Bold and Italic
    html = html.replace(/\*\*\*(.+?)\*\*\*/g, '<strong><em>$1</em></strong>');
    html = html.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
    html = html.replace(/\*(.+?)\*/g, '<em>$1</em>');
    html = html.replace(/___(.+?)___/g, '<strong><em>$1</em></strong>');
    html = html.replace(/__(.+?)__/g, '<strong>$1</strong>');
    html = html.replace(/_(.+?)_/g, '<em>$1</em>');

    // Inline code
    html = html.replace(/`([^`]+)`/g, '<code>$1</code>');

    // Code blocks
    html = html.replace(/```([\\s\\S]*?)```/g, '<pre><code>$1</code></pre>');

    // Links
    html = html.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2">$1</a>');

    // Images
    html = html.replace(/!\[([^\]]*)\]\(([^)]+)\)/g, '<img src="$2" alt="$1">');

    // Blockquotes
    html = html.replace(/^> (.+)$/gim, '<blockquote>$1</blockquote>');

    // Horizontal rule
    html = html.replace(/^---$/gim, '<hr>');
    html = html.replace(/^\*\*\*$/gim, '<hr>');

    // Lists
    // Unordered lists
    html = html.replace(/^\* (.+)$/gim, '<li>$1</li>');
    html = html.replace(/^- (.+)$/gim, '<li>$1</li>');
    html = html.replace(/^\\+ (.+)$/gim, '<li>$1</li>');

    // Ordered lists
    html = html.replace(/^\\d+\\. (.+)$/gim, '<li>$1</li>');

    // Wrap consecutive <li> in <ul>
    html = html.replace(/(<li>.*<\/li>)/s, (match) => {
        return '<ul>' + match + '</ul>';
    });

    // Line breaks
    html = html.replace(/\n\n/g, '</p><p>');
    html = html.replace(/\n/g, '<br>');

    // Wrap in paragraphs if not already wrapped
    if (!html.startsWith('<')) {
        html = '<p>' + html + '</p>';
    }

    return html;
}

// Save markdown to localStorage
markdownInput.addEventListener('input', () => {
    localStorage.setItem('genelingua_markdown', markdownInput.value);
});

// Load markdown from localStorage on page load
const savedMarkdown = localStorage.getItem('genelingua_markdown');
if (savedMarkdown) {
    markdownInput.value = savedMarkdown;
    updateMarkdownPreview();
}

// Chat functionality
const chatMessages = document.getElementById('chatMessages');
const chatInput = document.getElementById('chatInput');
const sendButton = document.getElementById('sendButton');
const voiceButton = document.getElementById('voiceButton');
const expertSelect = document.getElementById('expertSelect');

let isRecording = false;
let recognition = null;
let currentExpert = 'healthcare';
let conversationHistory = [];

// Initialize speech recognition if available
if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
    recognition = new (window.SpeechRecognition || window.webkitSpeechRecognition)();
    recognition.continuous = false;
    recognition.interimResults = false;
    recognition.lang = 'en-US'; // Default, will be updated based on conversation

    recognition.onstart = () => {
        isRecording = true;
        voiceButton.classList.add('recording');
        voiceButton.innerHTML = '<i class="codicon codicon-debug-stop"></i>';
    };

    recognition.onresult = (event) => {
        const transcript = event.results[0][0].transcript;
        chatInput.value = transcript;
        autoResizeTextarea(chatInput);
    };

    recognition.onend = () => {
        isRecording = false;
        voiceButton.classList.remove('recording');
        voiceButton.innerHTML = '<i class="codicon codicon-mic"></i>';
    };

    recognition.onerror = (event) => {
        console.error('Speech recognition error:', event.error);
        isRecording = false;
        voiceButton.classList.remove('recording');
        voiceButton.innerHTML = '<i class="codicon codicon-mic"></i>';
    };
} else {
    // Hide voice button if speech recognition is not supported
    voiceButton.style.display = 'none';
}

// Expert selection
expertSelect.addEventListener('change', (e) => {
    currentExpert = e.target.value;

    // Reset conversation history when switching experts
    conversationHistory = [];

    // Update assessment panel context
    const userId = document.getElementById('user_id')?.value.trim() || 'anonymous';
    assessmentPanel.updateContext(userId, currentExpert, conversationHistory);

    addWelcomeMessage();
});

// Chat input handlers
chatInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
    }
});

chatInput.addEventListener('input', () => {
    autoResizeTextarea(chatInput);
    sendButton.disabled = !chatInput.value.trim();
});

sendButton.addEventListener('click', sendMessage);

voiceButton.addEventListener('click', () => {
    if (!recognition) return;

    if (isRecording) {
        recognition.stop();
    } else {
        // Update recognition language based on recent messages
        updateRecognitionLanguage();
        recognition.start();
    }
});

function updateRecognitionLanguage() {
    if (!recognition) return;

    // Get the last few messages to detect conversation language
    const messages = chatMessages.querySelectorAll('.message.expert .message-text');
    if (messages.length > 0) {
        const recentText = Array.from(messages)
            .slice(-3) // Last 3 expert messages
            .map(msg => msg.textContent)
            .join(' ');

        const detectedLang = detectLanguage(recentText);
        const voiceConfig = getVoiceForLanguage(detectedLang);

        // Update recognition language
        recognition.lang = voiceConfig.lang;
        console.log(`🎤 Updated speech recognition to: ${voiceConfig.lang} (detected: ${detectedLang})`);
    }
}

function autoResizeTextarea(textarea) {
    textarea.style.height = 'auto';
    textarea.style.height = Math.min(textarea.scrollHeight, 120) + 'px';
}

function addMessage(content, isUser = false, speakText = false) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${isUser ? 'user' : 'expert'}`;

    const time = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

    messageDiv.innerHTML = `
        <div class="message-avatar">
            <i class="codicon ${isUser ? 'codicon-person' : getExpertIcon()}"></i>
        </div>
        <div class="message-content">
            <div class="message-text">${content}</div>
            <div class="message-time">${time}</div>
            ${!isUser && speakText ? `
                <div class="message-actions">
                    <button class="btn-message-action" onclick="speakMessage('${content.replace(/'/g, '\\\\').replace(/"/g, '&quot;')}')" title="Listen to response (High Quality)">
                        <i class="codicon codicon-unmute"></i>
                    </button>
                </div>
            ` : ''}
        </div>
    `;

    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;

    // Speak the message if requested and speech synthesis is available
    if (speakText && 'speechSynthesis' in window) {
        speakMessage(content);
    }
}

function getExpertIcon() {
    const icons = {
        healthcare: 'codicon-pulse',
        interview: 'codicon-briefcase',
        language: 'codicon-mortar-board',
        podcast: 'codicon-broadcast'
    };
    return icons[currentExpert] || 'codicon-robot';
}

function addWelcomeMessage() {
    chatMessages.innerHTML = '';
    const welcomeMessages = {
        healthcare: "Hallo! Ik ben je Nederlandse zorgexpert. Ik help je graag met medische vragen terwijl we samen je Nederlands verbeteren. Waar kan ik je mee helpen?",
        interview: "Hoi! Ik ben je Nederlandse IT-sollicitatiecoach. Ik help je graag met technische gesprekken in het Netherlands en IT-vocabulaire. Waar wil je aan werken?",
        language: "Welkom! Ik ben je Nederlandse taalcoach. Ik help je graag met grammatica, uitspraak, Nederlandse cultuur en natuurlijke gesprekken. Wat wil je vandaag leren?",
        podcast: "🎙️ Welkom bij de Nederlandse Podcast met Emma & Daan! Geef ons een onderwerp waar je over wilt praten en we beginnen meteen een interactief gesprek. Je kunt op elk moment onderbreken met vragen!"
    };

    setTimeout(() => {
        // Don't auto-speak for podcast as it will start speaking when user gives topic
        const shouldSpeak = currentExpert !== 'podcast';
        const welcomeMessage = welcomeMessages[currentExpert] || "Hallo! Hoe kan ik je helpen met Nederlands leren?";
        console.log(`👋 Adding welcome message for ${currentExpert}: ${welcomeMessage.substring(0, 50)}...`);
        addMessage(welcomeMessage, false, shouldSpeak);
    }, 500);
}

function addTypingIndicator() {
    const typingDiv = document.createElement('div');
    typingDiv.className = 'message expert';
    typingDiv.id = 'typing-indicator';

    typingDiv.innerHTML = `
        <div class="message-avatar">
            <i class="codicon ${getExpertIcon()}"></i>
        </div>
        <div class="typing-indicator">
            <div class="typing-dots">
                <div class="typing-dot"></div>
                <div class="typing-dot"></div>
                <div class="typing-dot"></div>
            </div>
        </div>
    `;

    chatMessages.appendChild(typingDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function removeTypingIndicator() {
    const typingIndicator = document.getElementById('typing-indicator');
    if (typingIndicator) {
        typingIndicator.remove();
    }
}

async function sendMessage() {
    const message = chatInput.value.trim();
    if (!message) return;

    // Add user message
    addMessage(message, true);

    // Update conversation history for assessment
    conversationHistory.push({ role: 'user', content: message });

    // Clear input
    chatInput.value = '';
    autoResizeTextarea(chatInput);
    sendButton.disabled = true;

    // Show typing indicator
    addTypingIndicator();

    try {
        // Get user ID from profile
        const userId = document.getElementById('user_id')?.value.trim() || 'anonymous';

        // Send to backend
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                message: message,
                expert: currentExpert,
                user_id: userId
            })
        });

        if (!response.ok) {
            throw new Error('Network response was not ok');
        }

        const data = await response.json();

        // Remove typing indicator
        removeTypingIndicator();

        // Handle podcast responses differently
        if (currentExpert === 'podcast') {
            handlePodcastResponse(data);

            // Start continuous podcast flow after user interaction and current audio finishes
            const waitAndStart = () => {
                if (isPlayingAudio || audioQueue.length > 0) {
                    setTimeout(waitAndStart, 500);
                } else {
                    setTimeout(() => {
                        startContinuousPodcast();
                    }, 2000); // 2 seconds after audio finishes
                }
            };
            waitAndStart();
        } else {
            // Regular expert response
            addMessage(data.response, false, true);

            // Update conversation history
            conversationHistory.push({ role: 'assistant', content: data.response });

            // Keep conversation history manageable
            if (conversationHistory.length > 20) {
                conversationHistory = conversationHistory.slice(-20);
            }

            // Update assessment panel context
            assessmentPanel.updateContext(userId, currentExpert, conversationHistory);

            // Always trigger assessment update for every user message (real-time analysis)
            await assessmentPanel.updateAssessment(message);
        }
    } catch (error) {
        console.error('Error sending message:', error);
        removeTypingIndicator();
        addMessage("I'm sorry, I'm having trouble connecting right now. Please try again.", false);
    }
}

function detectLanguage(text) {
    // Enhanced language detection focusing on the main content language
    const patterns = {
        'dutch': /\b(nederlands|spreek|spreken|kun|kunt|moet|kunnen|willen|zeggen|doen|maken|gaan|komen|worden|zijn|hebben|krijgen|houden|laten|staan|liggen|zitten|lopen|rijden|werken|spelen|eten|drinken|slapen|praten|luisteren|kijken|lezen|schrijven|leren|begrijpen|weten|denken|voelen|horen|zien|ruiken|proeven|aanraken|het|van|een|te|zijn|op|met|voor|als|aan|door|over|om|niet|maar|zo|ook|wel|nog|bij|tot|onder|naar|waar|wat|wie|hoe|waarom|wanneer|omdat|hoewel|toen|terwijl|indien|tenzij|hallo|dag|goedemorgen|goedemiddag|goedenavond|goedenacht|dankjewel|bedankt|alsjeblieft|sorry|excuses|pardon|ja|nee|misschien|wellicht|natuurlijk|zeker|absoluut|precies|inderdaad|werkelijk|echt|heel|erg|zeer|nogal|vrij|tamelijk|redelijk|behoorlijk|enigszins|ietwat|lichtelijk|gisteren|vandaag|morgen|overmorgen|maandag|dinsdag|woensdag|donderdag|vrijdag|zaterdag|zondag|januari|februari|maart|april|mei|juni|juli|augustus|september|oktober|november|december|de)\b/gi,
        'english': /\b(the|and|is|that|to|of|in|it|you|for|with|on|as|be|at|by|this|have|from|or|one|had|but|word|not|what|all|were|they|we|when|your|can|said|there|each|which|she|do|how|their|if|will|up|other|about|out|many|then|them|these|so|some|her|would|make|like|into|him|has|two|more|go|no|way|could|my|than|first|water|been|call|who|its|now|find|long|down|day|did|get|come|made|may|part|over|new|sound|take|only|little|work|know|place|year|live|me|back|give|most|very|after|thing|our|just|name|good|sentence|man|think|say|great|where|help|through|much|before|line|right|too|mean|old|any|same|tell|boy|follow|came|want|show|also|around|form|three|small|set|put|end|why|again|turn|here|move|well|asked|went|men|read|need|land|different|home|us|picture|try|kind|hand|head|high|every|near|add|food|between|own|below|country|plant|last|school|father|keep|tree|never|start|city|earth|eye|light|thought|open|example|begin|life|always|those|both|paper|together|got|group|often|run|important|until)\b/gi,
        'german': /\b(der|die|das|und|ist|zu|den|in|von|mit|auf|für|als|an|werden|aus|er|hat|dass|sie|nach|ein|dem|nicht|war|es|sich|auch|are|einer|bei|des|um|im|am|sind|noch|wie|einem|über|einen|so|zum|kann|habe|seine|mark|ihre|dann|unter|wir|sollte|nur|vor|zur|bis|seine|durch|jahre|mehr|wo|viel|kommen|schon|ihm|weil|ihre|würde|machen|wenn|hier|kann|alle|will|sollen|andere|eines|können|unser|along|gegen|vom|geht|sehr|her|zeit|jedoch|wieder|keine|zwei|ohne|samt|einmal)\b/gi,
        'french': /\b(le|de|et|est|il|être|et|en|avoir|que|pour|dans|ce|son|une|sur|avec|ne|se|pas|tout|plus|par|grand|ou|si|les|du|un|à|nous|vous|ma|ta|sa|mes|tes|ses|notre|votre|leur|nos|vos|leurs|moi|toi|lui|elle|nous|vous|eux|elles|mon|ton|son|ma|ta|sa|mes|tes|ses|ce|cet|cette|ces|qui|que|quoi|dont|où|quand|comment|pourquoi|parce|car|mais|ou|et|donc|or|ni|cependant|néanmoins|toutefois|pourtant|en|effet|bien|sûr|évidemment|naturellement|certainement|probablement|peut-être|sans|doute|hier|aujourd|demain|maintenant|bientôt|toujours|jamais|souvent|parfois|rarement|déjà|encore|enfin)\b/gi,
        'spanish': /\b(el|la|de|que|y|a|en|un|es|se|no|te|lo|le|da|su|por|son|con|para|al|una|del|los|las|me|él|todo|ella|uno|ser|su|hay|había|esta|han|la|si|más|lo|pero|sus|le|ya|o|este|sí|porque|qué|sólo|han|así|cómo|e|cuando|muy|sin|sobre|también|me|hasta|donde|quien|desde|todos|durante|todos|mucho|antes|ser|estar|tener|hacer|poder|decir|todo|cada|gran|otro|mismo|gobierno|mientras|vida|días|tiempo|hombre|estado|país|forma|caso|mano|lugar|parte|parecer|llegar|creer|hablar|llevar|dejar|seguir|encontrar|llamar|venir|pensar|salir|volver|tomar|conocer|vivir|sentir|tratar|mirar|contar|empezar|esperar|buscar|existir|entrar|trabajar|escribir|perder|producir|ocurrir|entender|pedir|recibir|recordar|terminar|permitir|aparecer|conseguir|comenzar|servir|sacar)\b/gi,
        'japanese': /[ひらがなカタカナ漢字]|\b(です|だ|である|します|した|する|すれば|されば|せよ|しろ|しなさい|ください|ます|まし|ました|ません|ませんでした|でしょう|だろう|かもしれません|と思います|と思う|ということ|について|に関して|において|によって|として|から|まで|より|ほど|ばかり|だけ|しか|も|は|が|を|に|へ|で|と|や|の|か|よ|ね|な|ぞ|ぜ|さ|わ|こんにちは|おはよう|こんばんは|ありがとう|すみません|ごめんなさい|はい|いいえ|そうです|違います)\b/gi,
        'chinese': /[\u4e00-\u9fff]|\b(是|的|了|在|我|你|他|她|它|们|这|那|有|没|不|很|也|都|就|会|能|要|可以|应该|必须|如果|因为|所以|但是|然后|或者|而且|虽然|不过|除了|包括|关于|对于|由于|通过|根据|按照|为了|以便|以免|以防|万一|一旦|只要|除非|无论|不管|尽管|即使|哪怕|好像|似乎|大概|可能|也许|肯定|一定|当然|显然|明显|确实|真的|实际|事实|其实|本来|原来|后来|现在|将来|过去|今天|明天|昨天|上午|下午|晚上|早上|中午|深夜|春天|夏天|秋天|冬天|年|月|日|时|分|秒|小时|分钟|秒钟|星期|礼拜|周末)\b/gi
    };

    // Clean text by removing parenthetical explanations which often mix languages
    let cleanText = text.replace(/\([^)]*\)/g, ''); // Remove content in parentheses
    cleanText = cleanText.replace(/\[[^\]]*\]/g, ''); // Remove content in brackets

    let maxMatches = 0;
    let detectedLang = 'english'; // default

    for (const [lang, pattern] of Object.entries(patterns)) {
        const matches = (cleanText.match(pattern) || []).length;
        if (matches > maxMatches) {
            maxMatches = matches;
            detectedLang = lang;
        }
    }

    // Special detection for Dutch responses that might start with common Dutch words
    if (cleanText.toLowerCase().match(/^(ja|nee|hallo|dag|goedemorgen|natuurlijk|zeker|inderdaad|precies)/)) {
        detectedLang = 'dutch';
    }

    console.log(`🔍 Language detection: '${cleanText.substring(0, 50)}...' → ${detectedLang} (${maxMatches} matches)`);
    return detectedLang;
}

function getVoiceForLanguage(language) {
    // Voice mapping that matches the AudioEngine VOICE_MODELS
    const voiceMap = {
        'dutch': { lang: 'nl-NL', name: 'dutch' },
        'english': { lang: 'en-US', name: 'english' },
        'german': { lang: 'de-DE', name: 'german' },
        'french': { lang: 'fr-FR', name: 'french' },
        'spanish': { lang: 'es-ES', name: 'spanish' },
        'japanese': { lang: 'ja-JP', name: 'japanese' },
        'chinese': { lang: 'zh-CN', name: 'chinese' }
    };

    return voiceMap[language] || voiceMap['english'];
}

async function speakMessage(text) {
    try {
        // Clean text by removing speaker labels for speech
        let cleanText = text.replace(/^(Emma|Daan|both):\s*/i, '');

        // Detect language of the cleaned text
        const detectedLang = detectLanguage(cleanText);
        console.log(`🔊 Generating high-quality speech for: ${detectedLang}`);

        // Generate speech using backend edge-tts
        const response = await fetch('/api/generate_speech', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                text: cleanText,
                language: detectedLang,
                user_id: 'anonymous'
            })
        });

        if (response.ok) {
            const data = await response.json();
            console.log('🔍 Speech API response:', data);
            console.log('🔍 data.success:', data.success, 'data.audio_data exists:', !!data.audio_data);
            if (data.success && data.audio_data) {
                // Convert hex string to audio blob
                let audio;
                try {
                    const hexPairs = data.audio_data.match(/.{1,2}/g);
                    if (!hexPairs) {
                        throw new Error('Invalid hex data format');
                    }
                    const audioBytes = new Uint8Array(hexPairs.map(byte => parseInt(byte, 16)));
                    const audioBlob = new Blob([audioBytes], { type: 'audio/mpeg' });
                    const audioUrl = URL.createObjectURL(audioBlob);

                    // Create and play audio element
                    audio = new Audio(audioUrl);
                } catch (conversionError) {
                    console.error('Audio conversion error:', conversionError);
                    throw new Error('Failed to convert audio data');
                }

                audio.volume = 0.8;

                // Add loading state
                const speakButtons = document.querySelectorAll('.btn-message-action');
                speakButtons.forEach(btn => {
                    if (btn.innerHTML.includes('codicon-unmute')) {
                        btn.innerHTML = '<i class="codicon codicon-loading codicon-modifier-spin"></i>';
                        btn.disabled = true;
                    }
                });

                // Handle audio playback with user interaction requirements
                const playAudio = async () => {
                    try {
                        await audio.play();
                        console.log(`✅ Playing high-quality ${detectedLang} audio`);

                        // Reset buttons when audio finishes
                        audio.onended = () => {
                            speakButtons.forEach(btn => {
                                if (btn.innerHTML.includes('codicon-loading')) {
                                    btn.innerHTML = '<i class="codicon codicon-unmute"></i>';
                                    btn.disabled = false;
                                }
                            });
                        };

                    } catch (playError) {
                        if (playError.name === 'NotAllowedError') {
                            console.log('🔊 Audio requires user interaction, showing play button');
                            // Show a play button for user to click
                            speakButtons.forEach(btn => {
                                if (btn.innerHTML.includes('codicon-loading')) {
                                    btn.innerHTML = '<i class="codicon codicon-play"></i>';
                                    btn.disabled = false;
                                    btn.title = 'Click to play audio';
                                    btn.onclick = async () => {
                                        try {
                                            await audio.play();
                                            btn.innerHTML = '<i class="codicon codicon-unmute"></i>';
                                            btn.title = 'Listen to response (High Quality)';
                                            btn.onclick = () => speakMessage(text);
                                        } catch (err) {
                                            console.error('Manual audio play failed:', err);
                                            btn.innerHTML = '<i class="codicon codicon-unmute"></i>';
                                            btn.title = 'Audio playback failed';
                                        }
                                    };
                                }
                            });
                        } else {
                            throw playError;
                        }
                    }
                };

                // Handle audio errors
                audio.onerror = () => {
                    console.error('Audio loading failed');
                    speakButtons.forEach(btn => {
                        if (btn.innerHTML.includes('codicon-loading')) {
                            btn.innerHTML = '<i class="codicon codicon-unmute"></i>';
                            btn.disabled = false;
                        }
                    });
                };

                // Try to play the audio
                await playAudio();

            } else {
                throw new Error('Invalid response from speech generation');
            }
        } else {
            throw new Error('Failed to generate speech');
        }

    } catch (error) {
        console.error('Speech generation failed:', error);
        // Fallback to browser speech synthesis if backend fails
        fallbackSpeechSynthesis(text);
    }
}

function fallbackSpeechSynthesis(text) {
    if ('speechSynthesis' in window) {
        console.log('🔄 Falling back to browser speech synthesis');
        speechSynthesis.cancel();

        const detectedLang = detectLanguage(text);
        const voiceConfig = getVoiceForLanguage(detectedLang);

        const utterance = new SpeechSynthesisUtterance(text);
        utterance.rate = 0.9;
        utterance.pitch = 1;
        utterance.volume = 0.8;
        utterance.lang = voiceConfig.lang;

        const voices = speechSynthesis.getVoices();
        if (voices.length > 0) {
            const preferredVoice = voices.find(voice =>
                voice.lang === voiceConfig.lang || voice.lang.startsWith(voiceConfig.lang.split('-')[0])
            );

            if (preferredVoice) {
                utterance.voice = preferredVoice;
            }
        }

        speechSynthesis.speak(utterance);
    }
}

// Clear chat functionality
function clearChat() {
    chatMessages.innerHTML = '';
    addWelcomeMessage();
}

// Track user interaction for audio playback
let userHasInteracted = false;

// Initialize audio context on first user interaction
function initializeAudioContext() {
    if (!userHasInteracted) {
        userHasInteracted = true;
        console.log('🔊 User interaction detected, audio context ready');
    }
}

// Add event listeners for user interaction
document.addEventListener('click', initializeAudioContext, { once: true });
document.addEventListener('keydown', initializeAudioContext, { once: true });
document.addEventListener('touchstart', initializeAudioContext, { once: true });

// Assessment Panel Management
class AssessmentPanel {
    constructor() {
        this.panel = document.getElementById('assessmentPanel');
        this.isActive = false;
        this.conversationHistory = [];
        this.currentExpert = 'language';
        this.currentUserId = 'unknown';
        this.isDragging = false;
        this.isMinimized = false;
        this._savedHeight = null;
        this.latestAssessment = null;

        this.initializeElements();
        this.setupEventListeners();
        this.setupDragging();
        this.setupResizer();
        // Restore position if saved
        this._restorePanelPosition();
        // Ensure panel is within bounds on window resize
        window.addEventListener('resize', () => this._ensurePositionInBounds());
    } initializeElements() {
        // Get all assessment UI elements
        this.elements = {
            overallScore: document.getElementById('overallScore'),
            performanceLevel: document.getElementById('performanceLevel'),
            grammarScore: document.getElementById('grammarScore'),
            fluencyScore: document.getElementById('fluencyScore'),
            vocabularyLevel: document.getElementById('vocabularyLevel'),
            languageTips: document.getElementById('languageTips'),
            conversationTips: document.getElementById('conversationTips'),
            expertTips: document.getElementById('expertTips'),
            messageCount: document.getElementById('messageCount'),
            engagementLevel: document.getElementById('engagementLevel'),
            learningMomentum: document.getElementById('learningMomentum'),
            closeBtn: document.getElementById('closeAssessment'),
            helpBtn: document.getElementById('getHelpBtn'),
            practiceBtn: document.getElementById('practiceMoreBtn'),
            reviewBtn: document.getElementById('reviewErrorsBtn')
        };

        // Clear initial content
        this.clearAssessmentData();
    }

    _ensurePositionInBounds() {
        try {
            const rect = this.panel.getBoundingClientRect();
            const maxX = window.innerWidth - rect.width;
            const maxY = window.innerHeight - rect.height;
            let left = parseInt(this.panel.style.left || rect.left);
            let top = parseInt(this.panel.style.top || rect.top);
            left = Math.max(0, Math.min(left, maxX));
            top = Math.max(0, Math.min(top, maxY));
            this.panel.style.left = left + 'px';
            this.panel.style.top = top + 'px';
            this.panel.style.right = 'auto';
        } catch (e) {
            // ignore
        }
    }

    setupEventListeners() {
        // Close panel
        this.elements.closeBtn?.addEventListener('click', () => {
            this.hide();
        });

        // Toggle button in chat header
        const toggleBtn = document.getElementById('toggleAssessment');
        toggleBtn?.addEventListener('click', () => {
            this.toggle();
            toggleBtn.classList.toggle('active', this.isActive);
        });

        // Minimize button
        const minimizeBtn = document.getElementById('minimizeBtn');
        minimizeBtn?.addEventListener('click', () => {
            this.minimize();
        });

        // Quick action buttons
        this.elements.helpBtn?.addEventListener('click', () => {
            this.showHelp();
        });

        this.elements.practiceBtn?.addEventListener('click', () => {
            this.suggestPractice();
        });

        this.elements.reviewBtn?.addEventListener('click', () => {
            this.reviewErrors();
        });

        // ESC key to close
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && this.isActive) {
                this.hide();
            }
        });
    }

    setupDragging() {
        const header = this.panel?.querySelector('.assessment-header');
        if (!header) return;

        let isDragging = false;
        let dragOffset = { x: 0, y: 0 };

        header.addEventListener('mousedown', (e) => {
            if (e.target.classList.contains('btn-close')) return;

            isDragging = true;
            const rect = this.panel.getBoundingClientRect();
            dragOffset.x = e.clientX - rect.left;
            dragOffset.y = e.clientY - rect.top;

            document.addEventListener('mousemove', handleMouseMove);
            document.addEventListener('mouseup', handleMouseUp);

            this.panel.style.transition = 'none';
            header.style.cursor = 'grabbing';
        });

        // Double click header to center panel
        header.addEventListener('dblclick', (e) => {
            const centerX = Math.max(0, Math.floor((window.innerWidth - this.panel.offsetWidth) / 2));
            const centerY = Math.max(0, Math.floor((window.innerHeight - this.panel.offsetHeight) / 2));
            this.panel.style.left = centerX + 'px';
            this.panel.style.top = centerY + 'px';
            this.panel.style.right = 'auto';
            try {
                localStorage.setItem('assessment_panel_pos', JSON.stringify({ left: centerX, top: centerY }));
            } catch (e) {
                console.log('⚠️ Could not save center panel position', e);
            }
        });

        const handleMouseMove = (e) => {
            if (!isDragging) return;

            const x = e.clientX - dragOffset.x;
            const y = e.clientY - dragOffset.y;

            // Keep panel within viewport bounds
            const maxX = window.innerWidth - this.panel.offsetWidth;
            const maxY = window.innerHeight - this.panel.offsetHeight;

            const boundedX = Math.max(0, Math.min(x, maxX));
            const boundedY = Math.max(0, Math.min(y, maxY));

            this.panel.style.left = `${boundedX}px`;
            this.panel.style.top = `${boundedY}px`;
            this.panel.style.right = 'auto';
        };

        const handleMouseUp = () => {
            isDragging = false;
            document.removeEventListener('mousemove', handleMouseMove);
            document.removeEventListener('mouseup', handleMouseUp);

            this.panel.style.transition = '';
            header.style.cursor = 'move';
            // Save the panel position
            try {
                const left = parseInt(this.panel.style.left || this.panel.getBoundingClientRect().left);
                const top = parseInt(this.panel.style.top || this.panel.getBoundingClientRect().top);
                localStorage.setItem('assessment_panel_pos', JSON.stringify({ left, top }));
            } catch (e) {
                console.log('⚠️ Could not save assessment panel position', e);
            }
        };

        // Touch support
        header.addEventListener('touchstart', (e) => {
            if (e.target.classList.contains('btn-close')) return;
            isDragging = true;
            const touch = e.touches[0];
            const rect = this.panel.getBoundingClientRect();
            dragOffset.x = touch.clientX - rect.left;
            dragOffset.y = touch.clientY - rect.top;
            document.addEventListener('touchmove', handleTouchMove, { passive: false });
            document.addEventListener('touchend', handleTouchEnd, { passive: false });
            this.panel.style.transition = 'none';
            header.style.cursor = 'grabbing';
            e.preventDefault();
        });

        const handleTouchMove = (e) => {
            if (!isDragging) return;
            const touch = e.touches[0];
            const x = touch.clientX - dragOffset.x;
            const y = touch.clientY - dragOffset.y;
            const maxX = window.innerWidth - this.panel.offsetWidth;
            const maxY = window.innerHeight - this.panel.offsetHeight;
            const boundedX = Math.max(0, Math.min(x, maxX));
            const boundedY = Math.max(0, Math.min(y, maxY));
            this.panel.style.left = `${boundedX}px`;
            this.panel.style.top = `${boundedY}px`;
            this.panel.style.right = 'auto';
            e.preventDefault();
        };

        const handleTouchEnd = () => {
            if (!isDragging) return;
            isDragging = false;
            document.removeEventListener('touchmove', handleTouchMove);
            document.removeEventListener('touchend', handleTouchEnd);
            this.panel.style.transition = '';
            header.style.cursor = 'move';
            // Save the final position
            try {
                const left = parseInt(this.panel.style.left || this.panel.getBoundingClientRect().left);
                const top = parseInt(this.panel.style.top || this.panel.getBoundingClientRect().top);
                localStorage.setItem('assessment_panel_pos', JSON.stringify({ left, top }));
            } catch (e) {
                console.log('⚠️ Could not save assessment panel position after touch', e);
            }
        };
    }

    _restorePanelPosition() {
        try {
            const saved = localStorage.getItem('assessment_panel_pos');
            if (saved) {
                const pos = JSON.parse(saved);
                const maxX = window.innerWidth - this.panel.offsetWidth;
                const maxY = window.innerHeight - this.panel.offsetHeight;
                const left = Math.max(0, Math.min(pos.left, maxX));
                const top = Math.max(0, Math.min(pos.top, maxY));
                this.panel.style.left = left + 'px';
                this.panel.style.top = top + 'px';
                this.panel.style.right = 'auto';
            }
        } catch (e) {
            console.log('⚠️ Could not restore assessment panel position', e);
        }
    }

    setupResizer() {
        const resizer = this.panel?.querySelector('.assessment-resizer');
        if (!resizer) return;

        let isResizing = false;
        let startY = 0;
        let startHeight = 0;

        // Apply saved height if present
        try {
            const savedHeight = localStorage.getItem('assessment_panel_height');
            if (savedHeight) {
                this.panel.style.height = savedHeight + 'px';
                this.panel.style.bottom = 'auto';
            }
        } catch (e) {
            console.log('⚠️ Could not read assessment panel height from storage', e);
        }

        const onMouseMove = (e) => {
            if (!isResizing) return;
            const delta = e.clientY - startY; // positive when moving down
            let newHeight = startHeight + delta;
            const minH = 120;
            const maxH = Math.max(220, window.innerHeight - 120);
            newHeight = Math.max(minH, Math.min(newHeight, maxH));

            this.panel.style.height = newHeight + 'px';
            this.panel.style.bottom = 'auto';
        };

        const onMouseUp = (e) => {
            if (!isResizing) return;
            isResizing = false;
            document.body.style.cursor = '';
            document.removeEventListener('mousemove', onMouseMove);
            document.removeEventListener('mouseup', onMouseUp);

            // Save height
            try {
                localStorage.setItem('assessment_panel_height', parseInt(this.panel.style.height || this.panel.offsetHeight));
            } catch (e) {
                console.log('⚠️ Could not save assessment panel height', e);
            }
        };

        resizer.addEventListener('mousedown', (e) => {
            if (this.isMinimized) return;
            isResizing = true;
            startY = e.clientY;
            startHeight = this.panel.offsetHeight;
            document.body.style.cursor = 'ns-resize';
            document.addEventListener('mousemove', onMouseMove);
            document.addEventListener('mouseup', onMouseUp);
            e.preventDefault();
        });
    }

    show() {
        this.panel.classList.add('active');
        this.panel.classList.remove('minimized');
        this.isActive = true;
        this.isMinimized = false;

        // Clear any existing data first
        this.clearAssessmentData();

        // Update toggle button state
        const toggleBtn = document.getElementById('toggleAssessment');
        if (toggleBtn) toggleBtn.classList.add('active');

        console.log('📊 Assessment panel opened at position:', {
            top: this.panel.style.top || 'default',
            right: this.panel.style.right || 'default',
            display: window.getComputedStyle(this.panel).display,
            zIndex: window.getComputedStyle(this.panel).zIndex
        });
    }

    hide() {
        this.panel.classList.remove('active');
        this.panel.classList.remove('minimized');
        this.isActive = false;
        this.isMinimized = false;

        // Update toggle button state
        const toggleBtn = document.getElementById('toggleAssessment');
        if (toggleBtn) toggleBtn.classList.remove('active');

        console.log('📊 Assessment panel closed');
    }

    minimize() {
        if (this.isMinimized) {
            this.panel.classList.remove('minimized');
            this.isMinimized = false;
            // Restore saved height if present
            try {
                const savedHeight = this._savedHeight || localStorage.getItem('assessment_panel_height');
                if (savedHeight) {
                    this.panel.style.height = parseInt(savedHeight) + 'px';
                    this.panel.style.bottom = 'auto';
                } else {
                    this.panel.style.height = '';
                    this.panel.style.bottom = 'auto';
                }
            } catch (e) {
                console.log('⚠️ Could not restore panel height', e);
            }
        } else {
            // Save current height before minimizing
            try {
                this._savedHeight = parseInt(this.panel.style.height || this.panel.offsetHeight);
                localStorage.setItem('assessment_panel_height', this._savedHeight);
            } catch (e) {
                console.log('⚠️ Could not save panel height before minimizing', e);
            }
            this.panel.classList.add('minimized');
            this.isMinimized = true;
        }
        console.log(`📊 Assessment panel ${this.isMinimized ? 'minimized' : 'restored'}`);
    }

    toggle() {
        if (this.isActive) {
            this.hide();
        } else {
            this.show();
        }
    }

    updateContext(userId, expert, conversationHistory) {
        this.currentUserId = userId || 'unknown';
        this.currentExpert = expert || 'language';
        this.conversationHistory = conversationHistory || [];

        // Update basic stats immediately
        this.updateBasicStats();
    }

    updateBasicStats() {
        const userMessages = this.conversationHistory.filter(msg => msg.role === 'user');
        const messageCount = userMessages.length;

        if (this.elements.messageCount) {
            this.elements.messageCount.textContent = messageCount;
        }

        // Simple engagement calculation
        let engagement = 'Low';
        if (messageCount > 5) engagement = 'High';
        else if (messageCount > 2) engagement = 'Medium';

        if (this.elements.engagementLevel) {
            this.elements.engagementLevel.textContent = engagement;
        }

        // Learning momentum
        let momentum = 'Starting';
        if (messageCount > 5) momentum = 'Strong';
        else if (messageCount > 2) momentum = 'Building';

        if (this.elements.learningMomentum) {
            this.elements.learningMomentum.textContent = momentum;
        }
    }

    async updateAssessment(currentMessage) {
        try {
            console.log(`📊 Analyzing message: "${currentMessage.substring(0, 50)}..."`);

            // Show loading state if panel is visible
            if (this.isActive) {
                this.showLoadingState();
            }

            const response = await fetch('/api/assessment', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    user_id: this.currentUserId,
                    expert: this.currentExpert,
                    conversation_history: this.conversationHistory,
                    current_message: currentMessage
                })
            });

            const assessment = await response.json();
            console.log('📊 Raw assessment response:', assessment);

            if (assessment.error) {
                console.warn('Assessment error:', assessment.error);
                // Use fallback assessment if provided
                const dataToDisplay = assessment.fallback_assessment || assessment;
                console.log('📊 Using fallback assessment:', dataToDisplay);

                // Store the latest assessment data
                this.latestAssessment = dataToDisplay;

                // Display immediately if panel is visible
                if (this.isActive) {
                    this.displayAssessment(dataToDisplay);
                }
                return;
            }

            // Store the latest assessment data
            this.latestAssessment = assessment;

            // Display immediately if panel is visible
            if (this.isActive) {
                this.displayAssessment(assessment);
            }

            console.log('📊 Assessment updated successfully');

        } catch (error) {
            console.error('Failed to get assessment:', error);
            // Create a minimal fallback assessment
            const fallbackData = {
                overall_score: { overall_score: 5.0, performance_level: 'developing' },
                language_analysis: { grammar_score: 5, fluency_score: 5, vocabulary_level: 'intermediate' },
                hints: {
                    language_tips: ['Keep practicing Dutch!'],
                    conversation_tips: ['Stay engaged in the conversation'],
                    expert_tips: ['Ask questions to learn more']
                }
            };

            this.latestAssessment = fallbackData;

            if (this.isActive) {
                this.displayAssessment(fallbackData);
            }
        }
    }

    showLoadingState() {
        if (this.elements.performanceLevel) {
            this.elements.performanceLevel.textContent = 'Analyseren...';
        }

        // Show loading in hints
        if (this.elements.languageTips) {
            this.elements.languageTips.innerHTML = '<li>🔄 Analyseren van je Nederlands...</li>';
        }
    }

    show() {
        this.panel.classList.add('active');
        this.panel.classList.remove('minimized');
        this.isActive = true;
        this.isMinimized = false;

        // Show latest assessment if available, otherwise clear
        if (this.latestAssessment) {
            this.displayAssessment(this.latestAssessment);
        } else {
            this.clearAssessmentData();
        }

        // Update toggle button state
        const toggleBtn = document.getElementById('toggleAssessment');
        if (toggleBtn) toggleBtn.classList.add('active');

        console.log('📊 Assessment panel opened');
    }

    displayAssessment(assessment) {
        console.log('📊 Displaying assessment:', assessment);
        console.log('📊 Assessment structure check:', {
            hasOverallScore: !!assessment.overall_score,
            hasLanguageAnalysis: !!assessment.language_analysis,
            hasHints: !!assessment.hints,
            overallScore: assessment.overall_score,
            languageAnalysis: assessment.language_analysis,
            hints: assessment.hints
        });

        // Update overall score
        const overall = assessment.overall_score || {};
        const score = overall.overall_score || 0;
        const level = overall.performance_level || 'developing';

        console.log('📊 Updating overall score:', { score, level });

        if (this.elements.overallScore) {
            const scoreNumber = this.elements.overallScore.querySelector('.score-number');
            if (scoreNumber) {
                scoreNumber.textContent = score.toFixed(1);
                // Add visual feedback for score changes
                scoreNumber.style.animation = 'none';
                setTimeout(() => {
                    scoreNumber.style.animation = 'pulse 0.5s ease-in-out';
                }, 10);
            }
        }

        if (this.elements.performanceLevel) {
            this.elements.performanceLevel.textContent = this.capitalize(level);
            // Color code the performance level
            const colors = {
                'excellent': 'var(--vscode-button-bg)',
                'good': 'var(--vscode-accent)',
                'developing': '#FF9800',
                'beginner': '#F44336'
            };
            this.elements.performanceLevel.style.color = colors[level] || 'var(--vscode-accent)';
        }

        // Update language metrics
        const language = assessment.language_analysis || {};

        if (this.elements.grammarScore && language.grammar_score !== undefined) {
            this.elements.grammarScore.textContent = language.grammar_score;
            this.updateMetricBar('grammar', language.grammar_score);
        }

        if (this.elements.fluencyScore && language.fluency_score !== undefined) {
            this.elements.fluencyScore.textContent = language.fluency_score;
            this.updateMetricBar('fluency', language.fluency_score);
        }

        if (this.elements.vocabularyLevel && language.vocabulary_level) {
            this.elements.vocabularyLevel.textContent = this.capitalize(language.vocabulary_level);
        }

        // Update corrections and improved version
        this.updateCorrections(language);

        // Update hints
        const hints = assessment.hints || {};
        this.updateHints(hints);

        // Update conversation flow stats
        const flow = assessment.conversation_flow || {};
        if (flow.engagement_level && this.elements.engagementLevel) {
            this.elements.engagementLevel.textContent = this.capitalize(flow.engagement_level);
        }

        const progress = assessment.learning_progress || {};
        if (progress.learning_momentum && this.elements.learningMomentum) {
            this.elements.learningMomentum.textContent = this.capitalize(progress.learning_momentum);
        }

        console.log('📊 Assessment updated successfully');
    }

    updateMetricBar(metric, score) {
        const bar = document.querySelector(`[data-metric="${metric}"]`);
        if (bar) {
            const percentage = Math.max(0, Math.min(100, (score / 10) * 100));
            bar.style.width = `${percentage}%`;
        }
    }

    updateHints(hints) {
        const updates = [
            { element: this.elements.languageTips, tips: hints.language_tips },
            { element: this.elements.conversationTips, tips: hints.conversation_tips },
            { element: this.elements.expertTips, tips: hints.expert_tips }
        ];

        updates.forEach(({ element, tips }) => {
            if (element && tips && Array.isArray(tips)) {
                element.innerHTML = tips.map(tip => `<li>${tip}</li>`).join('');
            }
        });
    }

    updateCorrections(languageAnalysis) {
        const correctionsSection = document.getElementById('correctionsSection');
        const errorsList = document.getElementById('errorsList');
        const correctionsList = document.getElementById('correctionsList');
        const improvedText = document.getElementById('improvedText');
        const explanation = document.getElementById('explanation');

        if (!languageAnalysis) return;

        const hasCorrections = (languageAnalysis.errors && languageAnalysis.errors.length > 0) ||
            (languageAnalysis.corrections && languageAnalysis.corrections.length > 0) ||
            languageAnalysis.improved_version;

        if (hasCorrections) {
            // Show the corrections section
            if (correctionsSection) {
                correctionsSection.style.display = 'block';
            }

            // Update errors list
            if (errorsList && languageAnalysis.errors && languageAnalysis.errors.length > 0) {
                errorsList.innerHTML = languageAnalysis.errors.map(error => `<li>${error}</li>`).join('');
            } else if (errorsList) {
                errorsList.innerHTML = '<li>Geen specifieke fouten gevonden</li>';
            }

            // Update corrections list
            if (correctionsList && languageAnalysis.corrections && languageAnalysis.corrections.length > 0) {
                correctionsList.innerHTML = languageAnalysis.corrections.map(correction => `<li>${correction}</li>`).join('');
            } else if (correctionsList) {
                correctionsList.innerHTML = '<li>Geen specifieke correcties</li>';
            }

            // Update improved version
            if (improvedText && languageAnalysis.improved_version) {
                improvedText.textContent = languageAnalysis.improved_version;
            }

            // Update explanation
            if (explanation && languageAnalysis.explanation) {
                explanation.textContent = languageAnalysis.explanation;
            }

            console.log('📝 Grammar corrections updated');
        } else {
            // Hide the corrections section if no corrections needed
            if (correctionsSection) {
                correctionsSection.style.display = 'none';
            }
        }
    }

    showFallbackAssessment(fallback) {
        const level = fallback?.overall_score?.performance_level || 'developing';
        const suggestions = fallback?.hints?.quick_suggestions || ['Keep practicing!'];

        if (this.elements.performanceLevel) {
            this.elements.performanceLevel.textContent = this.capitalize(level);
        }

        if (this.elements.languageTips) {
            this.elements.languageTips.innerHTML = suggestions.map(tip => `<li>${tip}</li>`).join('');
        }
    }

    capitalize(str) {
        return str.charAt(0).toUpperCase() + str.slice(1);
    }

    clearAssessmentData() {
        // Clear all assessment displays
        if (this.elements.performanceLevel) {
            this.elements.performanceLevel.textContent = 'Begin een gesprek voor beoordeling';
        }

        const scoreNumber = this.elements.overallScore?.querySelector('.score-number');
        if (scoreNumber) scoreNumber.textContent = '-';

        if (this.elements.grammarScore) this.elements.grammarScore.textContent = '-';
        if (this.elements.fluencyScore) this.elements.fluencyScore.textContent = '-';
        if (this.elements.vocabularyLevel) this.elements.vocabularyLevel.textContent = '-';

        // Clear metric bars
        this.updateMetricBar('grammar', 0);
        this.updateMetricBar('fluency', 0);

        // Clear hints - conversation focused
        if (this.elements.languageTips) {
            this.elements.languageTips.innerHTML = '<li>Start een gesprek met een expert</li>';
        }
        if (this.elements.conversationTips) {
            this.elements.conversationTips.innerHTML = '<li>Praat Nederlands met de expert</li>';
        }
        if (this.elements.expertTips) {
            this.elements.expertTips.innerHTML = '<li>Realtime feedback tijdens gesprek</li>';
        }
    }



    // Quick action handlers
    showHelp() {
        const helpMessage = `Assessment Help:\n\n• Grammar/Fluency scores (0-10)\n• Vocabulary levels: Beginner → Advanced\n• Real-time tips based on your conversation\n• Progress tracking per session\n\nTip: Keep chatting to get better feedback!`;
        alert(helpMessage);
    }

    suggestPractice() {
        const practices = [
            'Try asking follow-up questions',
            'Use more complex sentence structures',
            'Practice with technical vocabulary',
            'Focus on pronunciation',
            'Engage in longer conversations'
        ];

        const suggestion = practices[Math.floor(Math.random() * practices.length)];
        alert(`Practice Suggestion:\n\n${suggestion}\n\nKeep up the great work!`);
    }

    reviewErrors() {
        // This could show a summary of common errors
        alert('Error Review:\n\nBased on your conversation:\n• Grammar improvements available\n• Vocabulary expansion opportunities\n• Pronunciation practice recommended\n\nCheck the hints panel for specific tips!');
    }
}

// Initialize assessment panel
const assessmentPanel = new AssessmentPanel();
// Make it globally accessible for tab switching
window.assessmentPanelInstance = assessmentPanel;

// Setup assessment panel for Talk Experts tab
function setupAssessmentForExperts() {
    // Add assessment toggle button in status bar
    const testBtn = document.getElementById('testAssessment');
    if (testBtn) {
        testBtn.addEventListener('click', () => {
            console.log('📊 Toggling assessment panel');
            assessmentPanel.toggle();
        });
    }

    // Hide assessment panel when switching away from experts
    document.querySelectorAll('.tab:not([data-tab="experts"])').forEach(tab => {
        tab.addEventListener('click', () => {
            if (assessmentPanel.isActive) {
                assessmentPanel.hide();
            }
        });
    });
}// Initialize chat with welcome message
document.addEventListener('DOMContentLoaded', () => {
    // Add welcome message after a short delay
    setTimeout(() => {
        console.log('🚀 Initial page load - adding welcome message');
        addWelcomeMessage();
        setupAssessmentForExperts();
        checkExistingResources();

        // Auto-show assessment panel on page load since Talk Experts is default tab
        // Use the AssessmentPanel class method instead of directly manipulating DOM
        assessmentPanel.show();

        // Debug: Test panel visibility
        const panel = document.getElementById('assessmentPanel');
        console.log('🔍 Assessment panel element:', panel);
        console.log('🔍 Panel computed styles:', panel ? {
            display: window.getComputedStyle(panel).display,
            position: window.getComputedStyle(panel).position,
            zIndex: window.getComputedStyle(panel).zIndex,
            right: window.getComputedStyle(panel).right,
            top: window.getComputedStyle(panel).top
        } : 'NOT FOUND');
        console.log('🔍 Toggle button element:', document.getElementById('toggleAssessment'));
        console.log('🔍 Test button element:', document.getElementById('testAssessment'));

        // Assessment panel is ready for real conversations
        console.log('📊 Assessment panel ready for conversations');
    }, 1000);
});


// === Podcast Functionality ===

let podcastTimeout = null;
let isPodcastActive = false;
let currentAudio = null;
let audioQueue = [];
let isPlayingAudio = false;

function handlePodcastResponse(data) {
    const speaker = data.speaker || 'Host';
    const message = data.response || '';
    const speakerKey = data.speaker_key || 'host1';
    const voice = data.voice || 'nl-NL-ColetteNeural';

    console.log(`🎙️ Podcast response from ${speaker}: ${message.substring(0, 50)}...`);
    console.log(`🔊 Voice for ${speaker}: ${voice}`);

    // Add speaker label to message for clarity
    const displayMessage = `**${speaker}**: ${message}`;

    // Add to chat with special podcast styling
    addPodcastMessage(displayMessage, speaker, speakerKey, voice);

    // Mark podcast as active
    isPodcastActive = true;
}

function addPodcastMessage(content, speaker, speakerKey, voice) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message expert podcast-message`;
    messageDiv.dataset.speaker = speakerKey;

    const time = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

    // Different avatars for each host
    const avatarIcon = speakerKey === 'host1' ? 'codicon-person' : 'codicon-account';
    const avatarColor = speakerKey === 'host1' ? '#e74c3c' : '#3498db';

    messageDiv.innerHTML = `
        <div class="message-avatar" style="background-color: ${avatarColor}">
            <i class="codicon ${avatarIcon}"></i>
        </div>
        <div class="message-content">
            <div class="message-text">${content}</div>
            <div class="message-time">${time}</div>
            <div class="message-actions">
                <button class="btn-message-action" onclick="speakPodcastMessage('${content.replace(/'/g, '\\\\').replace(/"/g, '&quot;')}', '${voice}')" title="Listen to ${speaker}">
                    <i class="codicon codicon-unmute"></i>
                </button>
                <button class="btn-message-action" onclick="interruptPodcast()" title="Interrupt podcast">
                    <i class="codicon codicon-debug-pause"></i>
                </button>
            </div>
        </div>
    `;

    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;

    // Auto-play the message
    speakPodcastMessage(content, voice);
}

async function speakPodcastMessage(text, voice) {
    // Add to audio queue to prevent overlaps
    audioQueue.push({ text, voice });
    await processAudioQueue();
}

async function processAudioQueue() {
    if (isPlayingAudio || audioQueue.length === 0) {
        return;
    }

    isPlayingAudio = true;
    const { text, voice } = audioQueue.shift();

    try {
        // Stop any currently playing audio
        if (currentAudio) {
            currentAudio.pause();
            currentAudio = null;
        }

        // Remove markdown formatting AND speaker labels for speech
        let cleanText = text.replace(/\*\*(.*?)\*\*/g, '$1').replace(/\*(.*?)\*/g, '$1');

        // Remove speaker labels like "Emma:", "Daan:", "both:" at the beginning
        cleanText = cleanText.replace(/^(Emma|Daan|both):\s*/i, '');

        console.log(`🔊 Playing podcast audio with voice: ${voice}`);
        console.log(`🎙️ Original text: "${text.substring(0, 50)}..."`);
        console.log(`🎙️ Cleaned text: "${cleanText.substring(0, 50)}..."`);
        console.log(`🎙️ Sending request with cleaned text and voice: ${voice}`);

        // Generate speech using backend with specific voice
        const response = await fetch('/api/generate_speech', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                text: cleanText,
                language: 'dutch',
                voice: voice  // Pass specific voice
            })
        });

        if (response.ok) {
            const data = await response.json();
            if (data.success && data.audio_data) {
                // Convert hex string to audio blob
                const hexPairs = data.audio_data.match(/.{1,2}/g);
                if (hexPairs) {
                    const audioBytes = new Uint8Array(hexPairs.map(byte => parseInt(byte, 16)));
                    const audioBlob = new Blob([audioBytes], { type: 'audio/mpeg' });
                    const audioUrl = URL.createObjectURL(audioBlob);

                    // Create and play audio element
                    currentAudio = new Audio(audioUrl);
                    currentAudio.volume = 0.8;

                    // Wait for audio to finish before processing next in queue
                    await new Promise((resolve, reject) => {
                        currentAudio.onended = () => {
                            console.log(`✅ Finished playing ${voice} audio`);
                            currentAudio = null;
                            resolve();
                        };

                        currentAudio.onerror = (error) => {
                            console.error('Audio playback error:', error);
                            currentAudio = null;
                            reject(error);
                        };

                        currentAudio.play().catch(reject);
                    });
                }
            }
        }

    } catch (error) {
        console.error('Podcast speech error:', error);
    } finally {
        isPlayingAudio = false;
        // Process next item in queue
        if (audioQueue.length > 0) {
            setTimeout(() => processAudioQueue(), 200); // Small delay between audio clips
        }
    }
}

async function startContinuousPodcast() {
    if (!isPodcastActive || currentExpert !== 'podcast') {
        return;
    }

    console.log('🎙️ Starting continuous podcast flow...');

    // Clear any existing timeout
    if (podcastTimeout) {
        clearTimeout(podcastTimeout);
    }

    // Set up continuous conversation with faster timing
    podcastTimeout = setTimeout(async () => {
        await getContinuousPodcastResponse();
    }, 2000); // 2 seconds between responses for faster flow
}

async function getContinuousPodcastResponse() {
    if (!isPodcastActive || currentExpert !== 'podcast') {
        return;
    }

    try {
        const response = await fetch('/api/podcast/continue', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            }
        });

        if (response.ok) {
            const data = await response.json();

            if (data.type === 'podcast_message') {
                handlePodcastResponse(data);

                // Wait for current audio to finish, then schedule next response
                const waitForAudio = () => {
                    if (isPlayingAudio || audioQueue.length > 0) {
                        // Check again in 500ms
                        setTimeout(waitForAudio, 500);
                    } else {
                        // Audio finished, schedule next response faster
                        podcastTimeout = setTimeout(async () => {
                            await getContinuousPodcastResponse();
                        }, 1000); // 1 second pause after audio finishes
                    }
                };
                waitForAudio();
            } else if (data.type === 'podcast_inactive') {
                console.log('🎙️ Podcast ended naturally');
                isPodcastActive = false;
            }
        }
    } catch (error) {
        console.error('Error getting continuous podcast response:', error);
        // Retry after longer delay
        podcastTimeout = setTimeout(async () => {
            await getContinuousPodcastResponse();
        }, 10000);
    }
}

function interruptPodcast() {
    console.log('🛑 Podcast interrupted by user');

    // Clear continuous flow
    if (podcastTimeout) {
        clearTimeout(podcastTimeout);
        podcastTimeout = null;
    }

    // Focus on chat input
    chatInput.focus();
    chatInput.placeholder = "Onderbreek de podcast - typ je vraag of opmerking...";

    // Reset placeholder after a few seconds
    setTimeout(() => {
        if (chatInput.placeholder.includes('Onderbreek')) {
            chatInput.placeholder = "Type your message here...";
        }
    }, 5000);
}

function stopPodcast() {
    console.log('🛑 Stopping podcast');

    isPodcastActive = false;

    if (podcastTimeout) {
        clearTimeout(podcastTimeout);
        podcastTimeout = null;
    }

    // Send stop message to backend
    chatInput.value = 'stop podcast';
    sendMessage();
}

// Add podcast control when expert changes
const originalExpertChange = expertSelect.addEventListener;
expertSelect.addEventListener('change', (e) => {
    // Stop podcast when switching away
    if (currentExpert === 'podcast' && e.target.value !== 'podcast') {
        isPodcastActive = false;
        if (podcastTimeout) {
            clearTimeout(podcastTimeout);
            podcastTimeout = null;
        }

        // Clear audio queue and stop current audio
        audioQueue = [];
        if (currentAudio) {
            currentAudio.pause();
            currentAudio = null;
        }
        isPlayingAudio = false;
    }

    currentExpert = e.target.value;

    // Reset conversation history when switching experts
    conversationHistory = [];

    // Update assessment panel context (skip for podcast)
    if (currentExpert !== 'podcast') {
        const userId = document.getElementById('user_id')?.value.trim() || 'anonymous';
        assessmentPanel.updateContext(userId, currentExpert, conversationHistory);
    }

    // Only add welcome message if this is an actual user change (not initial load)
    if (chatMessages.children.length > 0) {
        console.log(`🔄 Expert changed to: ${currentExpert} - adding welcome message`);
        addWelcomeMessage();
    } else {
        console.log(`🔄 Expert changed to: ${currentExpert} - skipping welcome (initial load)`);
    }
});

