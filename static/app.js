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
    });
});

// Activity bar switching (optional - for future enhancements)
document.querySelectorAll('.activity-item').forEach(item => {
    item.addEventListener('click', () => {
        document.querySelectorAll('.activity-item').forEach(i => i.classList.remove('active'));
        item.classList.add('active');
    });
});

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
        const response = await fetch(`/api/load_profile?user_id=${encodeURIComponent(userId)}`);
        const data = await response.json();

        if (data.profile) {
            ancestrySelect.value = data.profile.ancestry || 'EAS';
            mbtiSelect.value = data.profile.mbti || 'INTJ';
            targetLanguageSelect.value = data.profile.target_language || 'japanese';

            let statusMsg = `✅ Profile loaded for ${userId}`;
            if (data.dna_exists) {
                statusMsg += '\n📁 DNA file found - no need to re-upload';
            } else {
                statusMsg += '\n⚠️ Please upload your DNA file';
            }
            profileStatus.textContent = statusMsg;
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
        '<i class="fas fa-exclamation-circle"></i>' :
        '<i class="fas fa-circle"></i>';
    statusMessage.innerHTML = `${icon} ${message}`;
}

// Generate Learning Plan
const generateBtn = document.getElementById('generateBtn');
generateBtn.addEventListener('click', async () => {
    const userId = userIdInput.value.trim() || 'unknown';
    const ancestry = ancestrySelect.value;
    const mbti = mbtiSelect.value;
    const targetLanguage = targetLanguageSelect.value;
    const logText = document.getElementById('log_text').value;
    const dnaFile = document.getElementById('dna_file').files[0];

    // Disable button and show loading
    generateBtn.disabled = true;
    generateBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Generating...';
    setStatus('Processing your request...');

    try {
        // Prepare form data
        const formData = new FormData();
        formData.append('user_id', userId);
        formData.append('ancestry', ancestry);
        formData.append('mbti', mbti);
        formData.append('target_language', targetLanguage);
        formData.append('log_text', logText);

        if (dnaFile) {
            formData.append('dna_file', dnaFile);
        }

        // Send request
        const response = await fetch('/api/process', {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const result = await response.json();

        // Update all outputs
        if (result.dna_report) {
            document.getElementById('dna_output').textContent = result.dna_report;
            document.getElementById('dna_detail').textContent = result.dna_report;
        }

        if (result.method) {
            document.getElementById('method_output').innerHTML = formatMarkdown(result.method);
        }

        if (result.words) {
            document.getElementById('words_output').innerHTML = formatList(result.words);
            document.getElementById('words_detail').innerHTML = formatList(result.words);
        }

        if (result.sentences) {
            document.getElementById('sentences_output').innerHTML = formatList(result.sentences);
            document.getElementById('sentences_detail').innerHTML = formatList(result.sentences);
        }

        // DNA Plot
        if (result.dna_plot_path) {
            const dnaPlot = document.getElementById('dna_plot');
            dnaPlot.src = result.dna_plot_path;
            dnaPlot.style.display = 'block';
            document.getElementById('dna_plot_placeholder').style.display = 'none';
        }

        // Progress Plot
        if (result.progress_plot_path) {
            const progressPlot = document.getElementById('progress_plot');
            progressPlot.src = result.progress_plot_path;
            progressPlot.style.display = 'block';
            document.getElementById('progress_plot_placeholder').style.display = 'none';
        }

        // PDF Download
        if (result.pdf_path) {
            document.getElementById('pdf_output').innerHTML =
                `<a href="${result.pdf_path}" class="download-link" download>
                    <i class="fas fa-download"></i> Download PDF Report
                </a>
                <p class="output-text" style="margin-top: 12px;">Complete personalized learning report</p>`;
        }

        // Anki Download
        if (result.anki_path) {
            document.getElementById('anki_output').innerHTML =
                `<a href="${result.anki_path}" class="download-link" download>
                    <i class="fas fa-download"></i> Download Anki Deck
                </a>
                <p class="output-text" style="margin-top: 12px;">Import this into Anki for spaced repetition</p>`;

            // Load flashcards for the Anki tab
            loadFlashcards(result.anki_path);
        } else {
            loadFlashcards(null);
        }

        // Audio - Always show player or error message
        if (result.audio_path) {
            document.getElementById('audio_output').innerHTML =
                `<audio controls style="width: 100%;">
                    <source src="${result.audio_path}" type="audio/mpeg">
                    Your browser does not support the audio element.
                </audio>
                <p class="output-text" style="margin-top: 12px;">Listen to native pronunciation</p>`;
        } else {
            document.getElementById('audio_output').innerHTML =
                `<div class="output-text">
                    <p style="color: #e74c3c;"><i class="fas fa-exclamation-triangle"></i> Audio generation failed or is still processing.</p>
                    <p style="margin-top: 8px; color: var(--vscode-text-secondary);">You can still see your sentences in the lesson tab.</p>
                </div>`;
        }

        setStatus('Learning plan generated successfully!');

        // Switch to overview tab to show results
        document.querySelector('.tab[data-tab="overview"]').click();

    } catch (error) {
        console.error('Error:', error);
        setStatus('Error generating learning plan', true);
        alert('An error occurred while generating your learning plan. Please try again.');
    } finally {
        // Re-enable button
        generateBtn.disabled = false;
        generateBtn.innerHTML = '<i class="fas fa-rocket"></i> Generate Learning Plan';
    }
});

// Helper functions
function formatMarkdown(text) {
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

