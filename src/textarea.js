/**
 * GeneLingua - Markdown Editor JavaScript (textarea.js)
 * Handles markdown editing, preview, and toolbar functionality
 */

class MarkdownEditor {
    constructor() {
        this.textarea = null;
        this.previewContainer = null;
        this.previewContent = null;
        this.editorContainer = null;
        this.saveIndicator = null;
        this.wordCountEl = null;
        this.isPreviewMode = false;
        this.autoSaveTimeout = null;
        this.undoStack = [];
        this.redoStack = [];
        this.maxUndoStack = 50;
    }

    init() {
        this.textarea = document.getElementById('markdown-textarea');
        this.previewContainer = document.getElementById('preview-container');
        this.previewContent = document.getElementById('preview-content');
        this.editorContainer = document.getElementById('editor-container');
        this.saveIndicator = document.getElementById('save-indicator');

        if (!this.textarea || !this.previewContainer || !this.previewContent) {
            console.error('Markdown editor elements not found');
            return;
        }

        this.loadContent();
        this.setupToolbar();
        this.setupEventListeners();
        this.setupKeyboardShortcuts();
        this.updateWordCount();
    }

    /**
     * Setup Toolbar Buttons
     */
    setupToolbar() {
        // Mode toggle buttons
        const editBtn = document.getElementById('edit-btn');
        const previewBtn = document.getElementById('preview-btn');

        if (editBtn) {
            editBtn.addEventListener('click', () => this.switchMode('edit'));
        }

        if (previewBtn) {
            previewBtn.addEventListener('click', () => this.switchMode('preview'));
        }

        // Save and Clear buttons
        const saveBtn = document.getElementById('save-btn');
        const clearBtn = document.getElementById('clear-btn');

        if (saveBtn) {
            saveBtn.addEventListener('click', () => this.saveContent(true));
        }

        if (clearBtn) {
            clearBtn.addEventListener('click', () => this.clearContent());
        }

        // Create toolbar buttons
        this.createToolbarButtons();
    }

    /**
     * Create Toolbar Button Groups
     */
    createToolbarButtons() {
        const toolbar = document.querySelector('.editor-toolbar');
        if (!toolbar) return;

        // Find the save button to insert before it
        const saveBtn = document.getElementById('save-btn');

        // Create button groups
        const groups = [
            {
                buttons: [
                    { icon: '↶', title: 'Undo (Ctrl+Z)', action: () => this.undo() },
                    { icon: '↷', title: 'Redo (Ctrl+Y)', action: () => this.redo() }
                ]
            },
            {
                buttons: [
                    { icon: 'B', title: 'Bold (Ctrl+B)', action: () => this.formatText('**', '**'), style: 'font-weight: bold' },
                    { icon: 'I', title: 'Italic (Ctrl+I)', action: () => this.formatText('*', '*'), style: 'font-style: italic' },
                    { icon: 'S', title: 'Strikethrough', action: () => this.formatText('~~', '~~'), style: 'text-decoration: line-through' },
                    { icon: '`', title: 'Code (Ctrl+`)', action: () => this.formatText('`', '`'), style: 'font-family: monospace' }
                ]
            },
            {
                buttons: [
                    { icon: 'H1', title: 'Heading 1', action: () => this.insertHeading(1) },
                    { icon: 'H2', title: 'Heading 2', action: () => this.insertHeading(2) },
                    { icon: 'H3', title: 'Heading 3', action: () => this.insertHeading(3) }
                ]
            },
            {
                buttons: [
                    { icon: '•', title: 'Bullet List', action: () => this.insertList('unordered') },
                    { icon: '1.', title: 'Numbered List', action: () => this.insertList('ordered') },
                    { icon: '☑', title: 'Task List', action: () => this.insertList('task') }
                ]
            },
            {
                buttons: [
                    { icon: '🔗', title: 'Insert Link (Ctrl+K)', action: () => this.insertLink() },
                    { icon: '🖼️', title: 'Insert Image', action: () => this.insertImage() },
                    { icon: '📋', title: 'Code Block', action: () => this.insertCodeBlock() },
                    { icon: '❝', title: 'Blockquote', action: () => this.insertBlockquote() }
                ]
            },
            {
                buttons: [
                    { icon: '📊', title: 'Insert Table', action: () => this.insertTable() },
                    { icon: '—', title: 'Horizontal Rule', action: () => this.insertHorizontalRule() }
                ]
            }
        ];

        // Insert groups before save button
        groups.forEach(group => {
            const groupEl = document.createElement('div');
            groupEl.className = 'toolbar-group';

            group.buttons.forEach(btn => {
                const button = document.createElement('button');
                button.className = 'toolbar-btn';
                button.innerHTML = btn.icon;
                button.title = btn.title;
                if (btn.style) {
                    button.style.cssText = btn.style;
                }
                button.addEventListener('click', (e) => {
                    e.preventDefault();
                    btn.action();
                });
                groupEl.appendChild(button);
            });

            toolbar.insertBefore(groupEl, saveBtn.parentElement);
        });

        // Add word count
        const wordCountEl = document.createElement('span');
        wordCountEl.className = 'word-count';
        wordCountEl.id = 'word-count';
        wordCountEl.textContent = '0 words';
        toolbar.insertBefore(wordCountEl, saveBtn.parentElement);
        this.wordCountEl = wordCountEl;
    }

    /**
     * Setup Event Listeners
     */
    setupEventListeners() {
        // Auto-save on input
        this.textarea.addEventListener('input', () => {
            this.showUnsavedIndicator();
            this.updateWordCount();
            this.scheduleAutoSave();
        });

        // Update preview in real-time if in preview mode
        this.textarea.addEventListener('input', () => {
            if (this.isPreviewMode) {
                this.updatePreview();
            }
        });

        // Handle tab key for indentation
        this.textarea.addEventListener('keydown', (e) => {
            if (e.key === 'Tab') {
                e.preventDefault();
                this.insertTab();
            }
        });
    }

    /**
     * Keyboard Shortcuts
     */
    setupKeyboardShortcuts() {
        this.textarea.addEventListener('keydown', (e) => {
            // Ctrl/Cmd + B: Bold
            if ((e.ctrlKey || e.metaKey) && e.key === 'b') {
                e.preventDefault();
                this.formatText('**', '**');
            }

            // Ctrl/Cmd + I: Italic
            if ((e.ctrlKey || e.metaKey) && e.key === 'i') {
                e.preventDefault();
                this.formatText('*', '*');
            }

            // Ctrl/Cmd + K: Link
            if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
                e.preventDefault();
                this.insertLink();
            }

            // Ctrl/Cmd + `: Code
            if ((e.ctrlKey || e.metaKey) && e.key === '`') {
                e.preventDefault();
                this.formatText('`', '`');
            }

            // Ctrl/Cmd + Z: Undo
            if ((e.ctrlKey || e.metaKey) && e.key === 'z' && !e.shiftKey) {
                e.preventDefault();
                this.undo();
            }

            // Ctrl/Cmd + Y or Ctrl/Cmd + Shift + Z: Redo
            if ((e.ctrlKey || e.metaKey) && (e.key === 'y' || (e.key === 'z' && e.shiftKey))) {
                e.preventDefault();
                this.redo();
            }

            // Ctrl/Cmd + S: Save
            if ((e.ctrlKey || e.metaKey) && e.key === 's') {
                e.preventDefault();
                this.saveContent(true);
            }
        });
    }

    /**
     * Switch between Edit and Preview modes
     */
    switchMode(mode) {
        const editBtn = document.getElementById('edit-btn');
        const previewBtn = document.getElementById('preview-btn');

        if (mode === 'preview') {
            this.isPreviewMode = true;
            this.editorContainer.classList.add('hidden');
            this.previewContainer.classList.add('show');
            editBtn.classList.remove('active');
            previewBtn.classList.add('active');
            this.updatePreview();
        } else {
            this.isPreviewMode = false;
            this.editorContainer.classList.remove('hidden');
            this.previewContainer.classList.remove('show');
            editBtn.classList.add('active');
            previewBtn.classList.remove('active');
            this.textarea.focus();
        }
    }

    /**
     * Update Preview with Markdown Rendering
     */
    updatePreview() {
        const markdown = this.textarea.value;
        const html = this.parseMarkdown(markdown);
        this.previewContent.innerHTML = html;
    }

    /**
     * Simple Markdown Parser
     */
    parseMarkdown(text) {
        let html = text;

        // Escape HTML
        html = html.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');

        // Headers
        html = html.replace(/^### (.*$)/gim, '<h3>$1</h3>');
        html = html.replace(/^## (.*$)/gim, '<h2>$1</h2>');
        html = html.replace(/^# (.*$)/gim, '<h1>$1</h1>');

        // Bold
        html = html.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
        html = html.replace(/__(.+?)__/g, '<strong>$1</strong>');

        // Italic
        html = html.replace(/\*(.+?)\*/g, '<em>$1</em>');
        html = html.replace(/_(.+?)_/g, '<em>$1</em>');

        // Strikethrough
        html = html.replace(/~~(.+?)~~/g, '<del>$1</del>');

        // Code
        html = html.replace(/`(.+?)`/g, '<code>$1</code>');

        // Links
        html = html.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2">$1</a>');

        // Images
        html = html.replace(/!\[([^\]]*)\]\(([^)]+)\)/g, '<img src="$2" alt="$1">');

        // Horizontal Rule
        html = html.replace(/^---$/gim, '<hr>');
        html = html.replace(/^\*\*\*$/gim, '<hr>');

        // Line breaks
        html = html.replace(/\n\n/g, '</p><p>');
        html = html.replace(/\n/g, '<br>');

        // Wrap in paragraphs
        html = '<p>' + html + '</p>';

        // Clean up empty paragraphs
        html = html.replace(/<p><\/p>/g, '');
        html = html.replace(/<p><h/g, '<h');
        html = html.replace(/<\/h([1-6])><\/p>/g, '</h$1>');
        html = html.replace(/<p><hr><\/p>/g, '<hr>');

        return html;
    }

    /**
     * Format selected text
     */
    formatText(before, after) {
        const start = this.textarea.selectionStart;
        const end = this.textarea.selectionEnd;
        const selectedText = this.textarea.value.substring(start, end);
        const beforeText = this.textarea.value.substring(0, start);
        const afterText = this.textarea.value.substring(end);

        if (selectedText) {
            // Wrap selected text
            this.textarea.value = beforeText + before + selectedText + after + afterText;
            this.textarea.selectionStart = start + before.length;
            this.textarea.selectionEnd = end + before.length;
        } else {
            // Insert format markers
            const placeholder = 'text';
            this.textarea.value = beforeText + before + placeholder + after + afterText;
            this.textarea.selectionStart = start + before.length;
            this.textarea.selectionEnd = start + before.length + placeholder.length;
        }

        this.textarea.focus();
        this.saveToUndoStack();
        this.showUnsavedIndicator();
    }

    /**
     * Insert Heading
     */
    insertHeading(level) {
        const start = this.textarea.selectionStart;
        const beforeText = this.textarea.value.substring(0, start);
        const afterText = this.textarea.value.substring(start);
        const prefix = '#'.repeat(level) + ' ';

        this.textarea.value = beforeText + prefix + 'Heading' + '\n' + afterText;
        this.textarea.selectionStart = start + prefix.length;
        this.textarea.selectionEnd = start + prefix.length + 7; // "Heading" length
        this.textarea.focus();
        this.saveToUndoStack();
        this.showUnsavedIndicator();
    }

    /**
     * Insert List
     */
    insertList(type) {
        const start = this.textarea.selectionStart;
        const beforeText = this.textarea.value.substring(0, start);
        const afterText = this.textarea.value.substring(start);

        let listText = '';
        if (type === 'unordered') {
            listText = '- Item 1\n- Item 2\n- Item 3\n';
        } else if (type === 'ordered') {
            listText = '1. Item 1\n2. Item 2\n3. Item 3\n';
        } else if (type === 'task') {
            listText = '- [ ] Task 1\n- [ ] Task 2\n- [x] Task 3 (completed)\n';
        }

        this.textarea.value = beforeText + listText + afterText;
        this.textarea.selectionStart = start;
        this.textarea.selectionEnd = start + listText.length;
        this.textarea.focus();
        this.saveToUndoStack();
        this.showUnsavedIndicator();
    }

    /**
     * Insert Link
     */
    insertLink() {
        const url = prompt('Enter URL:', 'https://');
        if (!url) return;

        const start = this.textarea.selectionStart;
        const end = this.textarea.selectionEnd;
        const selectedText = this.textarea.value.substring(start, end);
        const beforeText = this.textarea.value.substring(0, start);
        const afterText = this.textarea.value.substring(end);

        const linkText = selectedText || 'link text';
        const markdown = `[${linkText}](${url})`;

        this.textarea.value = beforeText + markdown + afterText;
        this.textarea.selectionStart = start + 1;
        this.textarea.selectionEnd = start + 1 + linkText.length;
        this.textarea.focus();
        this.saveToUndoStack();
        this.showUnsavedIndicator();
    }

    /**
     * Insert Image
     */
    insertImage() {
        const url = prompt('Enter image URL:', 'https://');
        if (!url) return;

        const alt = prompt('Enter image description (alt text):', 'image');
        const start = this.textarea.selectionStart;
        const beforeText = this.textarea.value.substring(0, start);
        const afterText = this.textarea.value.substring(start);

        const markdown = `![${alt}](${url})`;

        this.textarea.value = beforeText + markdown + '\n' + afterText;
        this.textarea.selectionStart = start + markdown.length;
        this.textarea.focus();
        this.saveToUndoStack();
        this.showUnsavedIndicator();
    }

    /**
     * Insert Code Block
     */
    insertCodeBlock() {
        const language = prompt('Enter language (optional):', 'javascript');
        const start = this.textarea.selectionStart;
        const beforeText = this.textarea.value.substring(0, start);
        const afterText = this.textarea.value.substring(start);

        const codeBlock = '```' + (language || '') + '\n// Your code here\n```\n';

        this.textarea.value = beforeText + codeBlock + afterText;
        this.textarea.selectionStart = start + 4 + (language ? language.length : 0) + 1;
        this.textarea.focus();
        this.saveToUndoStack();
        this.showUnsavedIndicator();
    }

    /**
     * Insert Blockquote
     */
    insertBlockquote() {
        const start = this.textarea.selectionStart;
        const end = this.textarea.selectionEnd;
        const selectedText = this.textarea.value.substring(start, end);
        const beforeText = this.textarea.value.substring(0, start);
        const afterText = this.textarea.value.substring(end);

        const quote = selectedText || 'Your quote here';
        const markdown = `> ${quote}\n`;

        this.textarea.value = beforeText + markdown + afterText;
        this.textarea.selectionStart = start + 2;
        this.textarea.selectionEnd = start + 2 + quote.length;
        this.textarea.focus();
        this.saveToUndoStack();
        this.showUnsavedIndicator();
    }

    /**
     * Insert Table
     */
    insertTable() {
        const start = this.textarea.selectionStart;
        const beforeText = this.textarea.value.substring(0, start);
        const afterText = this.textarea.value.substring(start);

        const table = '| Header 1 | Header 2 | Header 3 |\n' +
            '|----------|----------|----------|\n' +
            '| Cell 1   | Cell 2   | Cell 3   |\n' +
            '| Cell 4   | Cell 5   | Cell 6   |\n';

        this.textarea.value = beforeText + table + afterText;
        this.textarea.focus();
        this.saveToUndoStack();
        this.showUnsavedIndicator();
    }

    /**
     * Insert Horizontal Rule
     */
    insertHorizontalRule() {
        const start = this.textarea.selectionStart;
        const beforeText = this.textarea.value.substring(0, start);
        const afterText = this.textarea.value.substring(start);

        this.textarea.value = beforeText + '\n---\n' + afterText;
        this.textarea.focus();
        this.saveToUndoStack();
        this.showUnsavedIndicator();
    }

    /**
     * Insert Tab (indentation)
     */
    insertTab() {
        const start = this.textarea.selectionStart;
        const beforeText = this.textarea.value.substring(0, start);
        const afterText = this.textarea.value.substring(start);

        this.textarea.value = beforeText + '  ' + afterText;
        this.textarea.selectionStart = start + 2;
        this.textarea.selectionEnd = start + 2;
    }

    /**
     * Undo/Redo functionality
     */
    saveToUndoStack() {
        this.undoStack.push(this.textarea.value);
        if (this.undoStack.length > this.maxUndoStack) {
            this.undoStack.shift();
        }
        this.redoStack = [];
    }

    undo() {
        if (this.undoStack.length > 0) {
            this.redoStack.push(this.textarea.value);
            this.textarea.value = this.undoStack.pop();
            this.showUnsavedIndicator();
        }
    }

    redo() {
        if (this.redoStack.length > 0) {
            this.undoStack.push(this.textarea.value);
            this.textarea.value = this.redoStack.pop();
            this.showUnsavedIndicator();
        }
    }

    /**
     * Word Count
     */
    updateWordCount() {
        const text = this.textarea.value.trim();
        const words = text ? text.split(/\s+/).length : 0;
        const chars = text.length;

        if (this.wordCountEl) {
            this.wordCountEl.textContent = `${words} words • ${chars} chars`;
        }
    }

    /**
     * Save/Load Content
     */
    saveContent(showIndicator = false) {
        const content = this.textarea.value;
        localStorage.setItem('markdown-content', content);
        localStorage.setItem('markdown-last-saved', new Date().toISOString());

        if (showIndicator) {
            this.showSavedIndicator();
        }

        console.log('Content saved');
    }

    loadContent() {
        const content = localStorage.getItem('markdown-content');
        if (content) {
            this.textarea.value = content;
            this.updateWordCount();
            console.log('Content loaded');
        }
    }

    clearContent() {
        if (confirm('Are you sure you want to clear all content? This cannot be undone.')) {
            this.textarea.value = '';
            this.saveContent();
            this.updateWordCount();
            this.textarea.focus();
        }
    }

    /**
     * Auto-save
     */
    scheduleAutoSave() {
        clearTimeout(this.autoSaveTimeout);
        this.autoSaveTimeout = setTimeout(() => {
            this.saveContent();
            this.showSavedIndicator();
        }, 2000); // Auto-save after 2 seconds of inactivity
    }

    /**
     * Save Indicator
     */
    showSavedIndicator() {
        if (!this.saveIndicator) return;

        this.saveIndicator.textContent = '✓ Saved';
        this.saveIndicator.classList.remove('unsaved');
        this.saveIndicator.classList.add('show');

        setTimeout(() => {
            this.saveIndicator.classList.remove('show');
        }, 2000);
    }

    showUnsavedIndicator() {
        if (!this.saveIndicator) return;

        this.saveIndicator.textContent = '● Unsaved';
        this.saveIndicator.classList.add('unsaved', 'show');
    }
}

// Make it available globally
window.MarkdownEditor = MarkdownEditor;