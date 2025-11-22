// lessons.js - Duolingo-Style Practice System
// Gamified language learning with multiple exercise types

(function () {
    const STORAGE_KEY = 'genelingua_progress';
    const XP_PER_EXERCISE = 10;
    const STREAK_BONUS = 5;

    // Game State
    let gameState = {
        currentExerciseIndex: 0,
        lives: 3,
        maxLives: 3,
        xp: 0,
        streak: 0,
        correctAnswers: 0,
        totalAnswers: 0,
        exercises: [],
        startTime: null,
        hintsUsed: 0,
        language: 'dutch'  // Default language
    };

    // Utility Functions
    function shuffleArray(array) {
        const arr = [...array];
        for (let i = arr.length - 1; i > 0; i--) {
            const j = Math.floor(Math.random() * (i + 1));
            [arr[i], arr[j]] = [arr[j], arr[i]];
        }
        return arr;
    }

    // Ensure the 'Next' button advances exercises; add listener once
    function ensureNextListener() {
        const nextBtn = document.getElementById('next-btn');
        if (!nextBtn || nextBtn.dataset.wired) return;
        nextBtn.addEventListener('click', () => {
            const container = document.querySelector('.practice-exercise-container');
            if (!container) return;
            if (gameState.currentExerciseIndex < gameState.exercises.length - 1) {
                gameState.currentExerciseIndex += 1;
                renderExerciseUI(container, gameState.exercises[gameState.currentExerciseIndex], gameState.currentExerciseIndex);
            } else {
                container.innerHTML = `
                    <div style="text-align: center; padding: 20px;">
                        <div style="font-size: 48px; margin-bottom: 16px;">🎉</div>
                        <h2>Lesson Complete!</h2>
                        <p>Great job! You've finished all exercises.</p>
                        <div style="margin: 16px 0; padding: 12px; background: var(--vscode-input-bg); border-radius: 6px;">
                            <strong>Your Score:</strong> ${gameState.correctAnswers}/${gameState.totalAnswers} 
                            (${Math.round((gameState.correctAnswers / gameState.totalAnswers) * 100) || 0}%)
                        </div>
                    </div>
                `;
            }
            updateGameStats();
        });
        nextBtn.dataset.wired = '1';
    }

    function levenshtein(a, b) {
        if (a === b) return 0;
        const al = a.length, bl = b.length;
        if (al === 0) return bl;
        if (bl === 0) return al;
        const v0 = new Array(bl + 1).fill(0);
        const v1 = new Array(bl + 1).fill(0);
        for (let j = 0; j <= bl; j++) v0[j] = j;
        for (let i = 0; i < al; i++) {
            v1[0] = i + 1;
            for (let j = 0; j < bl; j++) {
                const cost = a[i] === b[j] ? 0 : 1;
                v1[j + 1] = Math.min(v1[j] + 1, v0[j + 1] + 1, v0[j] + cost);
            }
            for (let j = 0; j <= bl; j++) v0[j] = v1[j];
        }
        return v1[bl];
    }

    function calculateAccuracy(expected, got) {
        const dist = levenshtein(expected.toLowerCase().trim(), got.toLowerCase().trim());
        const maxLen = Math.max(expected.length, 1);
        return Math.max(0, Math.round((1 - dist / maxLen) * 100));
    }

    function escapeHtml(str) {
        return String(str)
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#39;');
    }

    function playCorrectSound() {
        // Simple audio feedback
        const audioCtx = new (window.AudioContext || window.webkitAudioContext)();
        const oscillator = audioCtx.createOscillator();
        const gainNode = audioCtx.createGain();
        oscillator.connect(gainNode);
        gainNode.connect(audioCtx.destination);
        oscillator.frequency.value = 523.25; // C5
        oscillator.type = 'sine';
        gainNode.gain.setValueAtTime(0.3, audioCtx.currentTime);
        gainNode.gain.exponentialRampToValueAtTime(0.01, audioCtx.currentTime + 0.3);
        oscillator.start(audioCtx.currentTime);
        oscillator.stop(audioCtx.currentTime + 0.3);
    }

    function playIncorrectSound() {
        const audioCtx = new (window.AudioContext || window.webkitAudioContext)();
        const oscillator = audioCtx.createOscillator();
        const gainNode = audioCtx.createGain();
        oscillator.connect(gainNode);
        gainNode.connect(audioCtx.destination);
        oscillator.frequency.value = 196; // G3
        oscillator.type = 'sine';
        gainNode.gain.setValueAtTime(0.3, audioCtx.currentTime);
        gainNode.gain.exponentialRampToValueAtTime(0.01, audioCtx.currentTime + 0.3);
        oscillator.start(audioCtx.currentTime);
        oscillator.stop(audioCtx.currentTime + 0.3);
    }

    // Voice model mapping for Azure Text-to-Speech
    const VOICE_MODELS = {
        "dutch": "nl-NL-ColetteNeural",      // Female Dutch voice
        "japanese": "ja-JP-NanamiNeural",    // Female Japanese voice
        "chinese": "zh-CN-XiaoxiaoNeural",   // Female Chinese voice
        "english": "en-US-JennyNeural"       // Female English voice
    };

    function speakText(text, lang = 'dutch') {
        // Normalize language code
        const langKey = lang.toLowerCase().split('-')[0];
        const voiceModel = VOICE_MODELS[langKey] || VOICE_MODELS['dutch'];

        // Try backend Azure TTS first (higher quality)
        generateSpeechWithAzure(text, voiceModel, langKey)
            .catch(error => {
                console.warn('Azure TTS failed, falling back to Web Speech API:', error);
                // Fallback to Web Speech API
                fallbackToWebSpeech(text, lang);
            });
    }

    async function generateSpeechWithAzure(text, voice, language) {
        try {
            const response = await fetch('/api/generate_speech', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    text: text,
                    voice: voice,
                    language: language
                })
            });

            if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);

            const data = await response.json();

            if (data.success && data.audio_data) {
                // Convert hex string to binary data
                const hexString = data.audio_data;
                const bytes = new Uint8Array(hexString.length / 2);
                for (let i = 0; i < hexString.length; i += 2) {
                    bytes[i / 2] = parseInt(hexString.substr(i, 2), 16);
                }

                // Create blob from binary data
                const audioBlob = new Blob([bytes], { type: 'audio/mpeg' });
                const audioUrl = URL.createObjectURL(audioBlob);
                const audio = new Audio(audioUrl);
                audio.play();
            } else {
                throw new Error('Invalid response from speech generation');
            }
        } catch (error) {
            console.error('Error generating speech:', error);
            throw error;
        }
    }

    function fallbackToWebSpeech(text, lang) {
        if ('speechSynthesis' in window) {
            const utterance = new SpeechSynthesisUtterance(text);
            utterance.lang = lang;
            utterance.rate = 0.9;
            speechSynthesis.speak(utterance);
        }
    }

    function saveProgress(userId, lessonId) {
        const progress = JSON.parse(localStorage.getItem(STORAGE_KEY) || '{}');
        if (!progress[userId]) progress[userId] = {};
        progress[userId][lessonId] = {
            xp: gameState.xp,
            streak: gameState.streak,
            correctAnswers: gameState.correctAnswers,
            totalAnswers: gameState.totalAnswers,
            completedAt: new Date().toISOString(),
            accuracy: Math.round((gameState.correctAnswers / gameState.totalAnswers) * 100) || 0
        };
        localStorage.setItem(STORAGE_KEY, JSON.stringify(progress));
    }

    // UI Components
    function createGameHeader() {
        const header = document.createElement('div');
        header.className = 'game-header';
        header.innerHTML = `
            <div class="progress-bar-container">
                <div class="progress-bar" id="lesson-progress"></div>
            </div>
            <div class="game-stats">
                <div class="stat-item">
                    <span class="stat-icon">❤️</span>
                    <span id="lives-count">${gameState.lives}</span>
                </div>
                <div class="stat-item">
                    <span class="stat-icon">⭐</span>
                    <span id="xp-count">${gameState.xp}</span>
                </div>
                <div class="stat-item">
                    <span class="stat-icon">🔥</span>
                    <span id="streak-count">${gameState.streak}</span>
                </div>
            </div>
        `;
        return header;
    }

    function updateGameStats() {
        const livesEl = document.getElementById('lives-count');
        const xpEl = document.getElementById('xp-count');
        const streakEl = document.getElementById('streak-count');
        const progressEl = document.getElementById('lesson-progress');

        if (livesEl) livesEl.textContent = gameState.lives;
        if (xpEl) xpEl.textContent = gameState.xp;
        if (streakEl) streakEl.textContent = gameState.streak;

        if (progressEl) {
            const progress = (gameState.currentExerciseIndex / gameState.exercises.length) * 100;
            progressEl.style.width = `${progress}%`;
        }
    }

    function showFeedback(correct, explanation) {
        const feedbackEl = document.getElementById('exercise-feedback');
        if (!feedbackEl) return;

        feedbackEl.className = `feedback ${correct ? 'correct' : 'incorrect'}`;
        feedbackEl.innerHTML = `
            <div class="feedback-icon">${correct ? '✓' : '✗'}</div>
            <div class="feedback-text">
                <strong>${correct ? 'Correct!' : 'Not quite right'}</strong>
                <p>${explanation || ''}</p>
            </div>
        `;
        feedbackEl.style.display = 'block';

        if (correct) {
            playCorrectSound();
            createConfetti();
        } else {
            playIncorrectSound();
        }
    }

    function createConfetti() {
        const container = document.getElementById('confetti-container');
        if (!container) return;

        for (let i = 0; i < 20; i++) {
            const confetti = document.createElement('div');
            confetti.className = 'confetti';
            confetti.style.left = Math.random() * 100 + '%';
            confetti.style.backgroundColor = ['#FFD700', '#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4'][Math.floor(Math.random() * 5)];
            confetti.style.animationDelay = Math.random() * 0.3 + 's';
            container.appendChild(confetti);

            setTimeout(() => confetti.remove(), 2000);
        }
    }

    // Exercise Type Renderers
    function renderTypingExercise(exercise, container) {
        container.innerHTML = `
            <div class="exercise-container">
                <div class="exercise-question">
                    <h3>Type this sentence:</h3>
                    <p class="target-sentence">${exercise.correct_answer || exercise.question}</p>
                    ${exercise.audio_text ? `<button class="btn-icon" id="speak-btn" title="Listen">🔊</button>` : ''}
                </div>
                <textarea id="typing-input" class="exercise-input" placeholder="Type your answer here..." rows="3"></textarea>
                <div class="exercise-hints" id="hints-area"></div>
                <div id="exercise-feedback" class="feedback" style="display: none;"></div>
                <div class="exercise-actions">
                    <button class="btn-secondary" id="hint-btn">💡 Hint</button>
                    <button class="btn-primary" id="check-btn">Check</button>
                    <button class="btn-flashcard" id="next-btn" disabled><i class="codicon codicon-arrow-right"></i> Next</button>
                </div>
            </div>
        `;

        setupExerciseHandlers(exercise, 'typing-input');
    }

    function renderFillBlankExercise(exercise, container) {
        const options = exercise.options || [];
        container.innerHTML = `
            <div class="exercise-container">
                <div class="exercise-question">
                    <h3>Fill in the blank:</h3>
                    <p class="target-sentence">${exercise.question}</p>
                    ${exercise.audio_text ? `<button class="btn-icon" id="speak-btn" title="Listen">🔊</button>` : ''}
                </div>
                <div class="options-grid" id="options-container">
                    ${options.map((opt, i) => `
                        <button class="option-btn" data-value="${opt}">${opt}</button>
                    `).join('')}
                </div>
                <div class="selected-answer" id="selected-answer" style="display: none;">
                    <span>Your answer: </span><strong id="selected-value"></strong>
                </div>
                <div class="exercise-hints" id="hints-area"></div>
                <div id="exercise-feedback" class="feedback" style="display: none;"></div>
                <div class="exercise-actions">
                    <button class="btn-secondary" id="hint-btn">💡 Hint</button>
                    <button class="btn-primary" id="check-btn" disabled>Check</button>
                    <button class="btn-flashcard" id="next-btn" disabled><i class="codicon codicon-arrow-right"></i> Next</button>
                </div>
            </div>
        `;

        setupFillBlankHandlers(exercise);
    }

    function renderWordOrderExercise(exercise, container) {
        const words = shuffleArray(exercise.options || exercise.correct_answer.split(' '));
        container.innerHTML = `
            <div class="exercise-container">
                <div class="exercise-question">
                    <h3>Arrange the words in correct order:</h3>
                    <p>${exercise.question || 'Put these words in the right order'}</p>
                    ${exercise.audio_text ? `<button class="btn-icon" id="speak-btn" title="Listen to correct order">🔊</button>` : ''}
                </div>
                <div class="word-order-area">
                    <div class="answer-zone" id="answer-zone">
                        <span class="placeholder-text">Drop words here</span>
                    </div>
                    <div class="words-bank" id="words-bank">
                        ${words.map((word, i) => `
                            <button class="word-chip" data-word="${word}" draggable="true">${word}</button>
                        `).join('')}
                    </div>
                </div>
                <div class="exercise-hints" id="hints-area"></div>
                <div id="exercise-feedback" class="feedback" style="display: none;"></div>
                <div class="exercise-actions">
                    <button class="btn-secondary" id="reset-btn">↺ Reset</button>
                    <button class="btn-secondary" id="hint-btn">💡 Hint</button>
                    <button class="btn-primary" id="check-btn" disabled>Check</button>
                    <button class="btn-flashcard" id="next-btn" disabled><i class="codicon codicon-arrow-right"></i> Next</button>
                </div>
            </div>
        `;

        setupWordOrderHandlers(exercise);
    }

    function renderMatchingExercise(exercise, container) {
        // Parse matching pairs from correct_answer (format: "word1=trans1,word2=trans2")
        const pairs = exercise.correct_answer.split(',').map(p => {
            const [left, right] = p.split('=');
            return { left: left.trim(), right: right.trim() };
        });

        const leftItems = pairs.map(p => p.left);
        const rightItems = shuffleArray(pairs.map(p => p.right));

        container.innerHTML = `
            <div class="exercise-container">
                <div class="exercise-question">
                    <h3>Match the pairs:</h3>
                    <p>${exercise.question || 'Connect matching items'}</p>
                </div>
                <div class="matching-area">
                    <div class="matching-column">
                        ${leftItems.map((item, i) => `
                            <button class="match-btn left" data-value="${item}" data-index="${i}">
                                ${item}
                            </button>
                        `).join('')}
                    </div>
                    <div class="matching-column">
                        ${rightItems.map((item, i) => `
                            <button class="match-btn right" data-value="${item}">
                                ${item}
                            </button>
                        `).join('')}
                    </div>
                </div>
                <div class="matches-display" id="matches-display"></div>
                <div class="exercise-hints" id="hints-area"></div>
                <div id="exercise-feedback" class="feedback" style="display: none;"></div>
                <div class="exercise-actions">
                    <button class="btn-secondary" id="reset-btn">↺ Reset</button>
                    <button class="btn-secondary" id="hint-btn">💡 Hint</button>
                    <button class="btn-primary" id="check-btn" disabled>Check</button>
                    <button class="btn-flashcard" id="next-btn" disabled><i class="codicon codicon-arrow-right"></i> Next</button>
                </div>
            </div>
        `;

        setupMatchingHandlers(exercise, pairs);
    }

    function setupExerciseHandlers(exercise, inputId) {
        const input = document.getElementById(inputId);
        const checkBtn = document.getElementById('check-btn');
        const hintBtn = document.getElementById('hint-btn');
        const speakBtn = document.getElementById('speak-btn');

        if (speakBtn && exercise.audio_text) {
            speakBtn.addEventListener('click', () => speakText(exercise.audio_text, gameState.language));
        }

        if (hintBtn && exercise.hints) {
            hintBtn.addEventListener('click', () => showHint(exercise.hints));
        }

        if (input) {
            input.addEventListener('input', () => {
                checkBtn.disabled = !input.value.trim();
            });
        }

        checkBtn.addEventListener('click', () => {
            const userAnswer = input.value.trim();
            const correct = (exercise.correct_answer || '').trim();
            const accuracy = calculateAccuracy(correct, userAnswer);
            const isCorrect = accuracy >= 85 || (correct.length === 0 && userAnswer.length > 0);

            handleAnswer(isCorrect, exercise.explanation);

            // enable next button on correct
            const nextBtn = document.getElementById('next-btn');

            if (!isCorrect) {
                showFeedback(false, `Expected: "${correct}". ${exercise.explanation || ''}`);
            } else {
                showFeedback(true, exercise.explanation);
                if (nextBtn) {
                    nextBtn.disabled = false;
                }
                if (checkBtn) checkBtn.disabled = true;
            }
        });

        // Wire next button to advance exercises when present
        const nextBtn = document.getElementById('next-btn');
        if (nextBtn) {
            nextBtn.addEventListener('click', () => {
                const container = document.querySelector('.practice-exercise-container');
                if (!container) return;
                if (gameState.currentExerciseIndex < gameState.exercises.length - 1) {
                    gameState.currentExerciseIndex += 1;
                    renderExerciseUI(container, gameState.exercises[gameState.currentExerciseIndex], gameState.currentExerciseIndex);
                } else {
                    // End of lesson UI
                    container.innerHTML = `\n                        <div style="text-align: center; padding: 20px;">\n                            <div style="font-size: 48px; margin-bottom: 16px;">🎉</div>\n                            <h2>Lesson Complete!</h2>\n                            <p>Great job! You've finished all exercises.</p>\n                            <div style="margin: 16px 0; padding: 12px; background: var(--vscode-input-bg); border-radius: 6px;">\n                                <strong>Your Score:</strong> ${gameState.correctAnswers}/${gameState.totalAnswers} \n                                (${Math.round((gameState.correctAnswers / gameState.totalAnswers) * 100) || 0}%)\n                            </div>\n                        </div>\n                    `;
                }
                updateGameStats();
            });
        }
    }

    function setupFillBlankHandlers(exercise) {
        const options = document.querySelectorAll('.option-btn');
        const checkBtn = document.getElementById('check-btn');
        const selectedAnswer = document.getElementById('selected-answer');
        const selectedValue = document.getElementById('selected-value');
        const hintBtn = document.getElementById('hint-btn');
        const speakBtn = document.getElementById('speak-btn');

        let selected = null;

        if (speakBtn && exercise.audio_text) {
            speakBtn.addEventListener('click', () => speakText(exercise.audio_text, gameState.language));
        }

        if (hintBtn && exercise.hints) {
            hintBtn.addEventListener('click', () => showHint(exercise.hints));
        }

        options.forEach(btn => {
            btn.addEventListener('click', () => {
                options.forEach(b => b.classList.remove('selected'));
                btn.classList.add('selected');
                selected = btn.dataset.value;
                selectedValue.textContent = selected;
                selectedAnswer.style.display = 'block';
                checkBtn.disabled = false;
            });
        });

        checkBtn.addEventListener('click', () => {
            const isCorrect = selected === exercise.correct_answer;
            handleAnswer(isCorrect, exercise.explanation);

            options.forEach(btn => {
                if (btn.dataset.value === exercise.correct_answer) {
                    btn.classList.add('correct-answer');
                } else if (btn.dataset.value === selected && !isCorrect) {
                    btn.classList.add('wrong-answer');
                }
            });
            if (isCorrect) {
                const nextBtn = document.getElementById('next-btn');
                if (nextBtn) {
                    nextBtn.disabled = false;
                    ensureNextListener();
                    if (checkBtn) checkBtn.disabled = true;
                }
            }
        });
    }

    function setupWordOrderHandlers(exercise) {
        const answerZone = document.getElementById('answer-zone');
        const wordsBank = document.getElementById('words-bank');
        const checkBtn = document.getElementById('check-btn');
        const resetBtn = document.getElementById('reset-btn');
        const hintBtn = document.getElementById('hint-btn');
        const speakBtn = document.getElementById('speak-btn');

        let selectedWords = [];

        if (speakBtn && exercise.audio_text) {
            speakBtn.addEventListener('click', () => speakText(exercise.audio_text, gameState.language));
        }

        if (hintBtn && exercise.hints) {
            hintBtn.addEventListener('click', () => showHint(exercise.hints));
        }

        function updateAnswerZone() {
            if (selectedWords.length === 0) {
                answerZone.innerHTML = '<span class="placeholder-text">Drop words here</span>';
            } else {
                answerZone.innerHTML = selectedWords.map((word, i) => `
                    <button class="word-chip selected" data-index="${i}">${word}</button>
                `).join('');

                // Add click handlers to remove words
                answerZone.querySelectorAll('.word-chip').forEach(chip => {
                    chip.addEventListener('click', () => {
                        const index = parseInt(chip.dataset.index);
                        const word = selectedWords[index];
                        selectedWords.splice(index, 1);
                        updateAnswerZone();

                        // Add word back to bank
                        const wordBtn = document.createElement('button');
                        wordBtn.className = 'word-chip';
                        wordBtn.dataset.word = word;
                        wordBtn.textContent = word;
                        wordBtn.addEventListener('click', () => addWord(word, wordBtn));
                        wordsBank.appendChild(wordBtn);
                    });
                });
            }
            checkBtn.disabled = selectedWords.length === 0;
        }

        function addWord(word, btn) {
            selectedWords.push(word);
            btn.remove();
            updateAnswerZone();
        }

        wordsBank.querySelectorAll('.word-chip').forEach(btn => {
            btn.addEventListener('click', () => {
                addWord(btn.dataset.word, btn);
            });
        });

        resetBtn.addEventListener('click', () => {
            selectedWords = [];
            updateAnswerZone();
            // Restore all words to bank
            wordsBank.innerHTML = '';
            const words = shuffleArray(exercise.options || exercise.correct_answer.split(' '));
            words.forEach(word => {
                const btn = document.createElement('button');
                btn.className = 'word-chip';
                btn.dataset.word = word;
                btn.textContent = word;
                btn.addEventListener('click', () => addWord(word, btn));
                wordsBank.appendChild(btn);
            });
        });

        checkBtn.addEventListener('click', () => {
            const userAnswer = selectedWords.join(' ');
            const isCorrect = userAnswer === exercise.correct_answer;
            handleAnswer(isCorrect, exercise.explanation);

            if (!isCorrect) {
                showFeedback(false, `Expected: "${exercise.correct_answer}". ${exercise.explanation || ''}`);
            } else {
                showFeedback(true, exercise.explanation);
                const nextBtn = document.getElementById('next-btn');
                if (nextBtn) {
                    nextBtn.disabled = false;
                    ensureNextListener();
                    if (checkBtn) checkBtn.disabled = true;
                }
            }
        });
    }

    function setupMatchingHandlers(exercise, correctPairs) {
        const leftBtns = document.querySelectorAll('.match-btn.left');
        const rightBtns = document.querySelectorAll('.match-btn.right');
        const checkBtn = document.getElementById('check-btn');
        const resetBtn = document.getElementById('reset-btn');
        const hintBtn = document.getElementById('hint-btn');
        const matchesDisplay = document.getElementById('matches-display');

        let selectedLeft = null;
        let matches = [];

        if (hintBtn && exercise.hints) {
            hintBtn.addEventListener('click', () => showHint(exercise.hints));
        }

        function updateDisplay() {
            matchesDisplay.innerHTML = matches.map((m, i) => `
                <div class="match-pair">
                    <span>${m.left}</span> ↔ <span>${m.right}</span>
                    <button class="btn-icon-small" data-index="${i}">×</button>
                </div>
            `).join('');

            matchesDisplay.querySelectorAll('.btn-icon-small').forEach(btn => {
                btn.addEventListener('click', () => {
                    const index = parseInt(btn.dataset.index);
                    const match = matches[index];
                    matches.splice(index, 1);

                    // Re-enable buttons
                    leftBtns.forEach(b => {
                        if (b.dataset.value === match.left) b.disabled = false;
                    });
                    rightBtns.forEach(b => {
                        if (b.dataset.value === match.right) b.disabled = false;
                    });

                    updateDisplay();
                });
            });

            checkBtn.disabled = matches.length === 0;
        }

        leftBtns.forEach(btn => {
            btn.addEventListener('click', () => {
                if (selectedLeft) {
                    leftBtns.forEach(b => b.classList.remove('selected'));
                }
                selectedLeft = btn.dataset.value;
                btn.classList.add('selected');
            });
        });

        rightBtns.forEach(btn => {
            btn.addEventListener('click', () => {
                if (!selectedLeft) return;

                matches.push({ left: selectedLeft, right: btn.dataset.value });

                // Disable matched buttons
                leftBtns.forEach(b => {
                    if (b.dataset.value === selectedLeft) {
                        b.disabled = true;
                        b.classList.remove('selected');
                    }
                });
                btn.disabled = true;

                selectedLeft = null;
                updateDisplay();
            });
        });

        resetBtn.addEventListener('click', () => {
            matches = [];
            selectedLeft = null;
            leftBtns.forEach(b => {
                b.disabled = false;
                b.classList.remove('selected');
            });
            rightBtns.forEach(b => b.disabled = false);
            updateDisplay();
        });

        checkBtn.addEventListener('click', () => {
            let correctCount = 0;
            matches.forEach(match => {
                const isCorrect = correctPairs.some(p =>
                    p.left === match.left && p.right === match.right
                );
                if (isCorrect) correctCount++;
            });

            const allCorrect = correctCount === correctPairs.length && matches.length === correctPairs.length;
            handleAnswer(allCorrect, exercise.explanation);

            if (!allCorrect) {
                showFeedback(false, `You got ${correctCount}/${correctPairs.length} correct. ${exercise.explanation || ''}`);
            } else {
                showFeedback(true, exercise.explanation);
                const nextBtn = document.getElementById('next-btn');
                if (nextBtn) {
                    nextBtn.disabled = false;
                    ensureNextListener();
                    if (checkBtn) checkBtn.disabled = true;
                }
            }
        });
    }

    function showHint(hints) {
        if (!hints || !hints.length) return;

        const hintsArea = document.getElementById('hints-area');
        const hintIndex = gameState.hintsUsed % hints.length;

        hintsArea.innerHTML = `
            <div class="hint-box">
                💡 ${hints[hintIndex]}
            </div>
        `;
        hintsArea.style.display = 'block';
        gameState.hintsUsed++;
    }

    function handleAnswer(correct, explanation) {
        gameState.totalAnswers++;

        if (correct) {
            gameState.correctAnswers++;
            gameState.streak++;
            gameState.xp += XP_PER_EXERCISE + (gameState.streak >= 3 ? STREAK_BONUS : 0);
        } else {
            gameState.lives--;
            gameState.streak = 0;

            if (gameState.lives <= 0) {
                showGameOver();
                return;
            }
        }

        updateGameStats();
        showFeedback(correct, explanation);
        // Removed auto-advance: user should press Next to continue.
    }

    function renderCurrentExercise() {
        const container = document.getElementById('exercise-area');
        if (!container) return;

        const exercise = gameState.exercises[gameState.currentExerciseIndex];

        container.innerHTML = '';

        switch (exercise.type) {
            case 'typing':
                renderTypingExercise(exercise, container);
                break;
            case 'fill_blank':
                renderFillBlankExercise(exercise, container);
                break;
            case 'word_order':
                renderWordOrderExercise(exercise, container);
                break;
            case 'matching':
                renderMatchingExercise(exercise, container);
                break;
            default:
                renderTypingExercise(exercise, container);
        }

        updateGameStats();
    }

    function showLessonComplete() {
        const container = document.getElementById('exercise-area') || document.getElementById('practice-modal-content');
        if (!container) return;

        const accuracy = Math.round((gameState.correctAnswers / gameState.totalAnswers) * 100);
        const timeElapsed = Math.round((Date.now() - (gameState.startTime || Date.now())) / 1000);

        container.innerHTML = `
            <div class="lesson-complete">
                <div class="complete-header">
                    <div class="trophy-icon">🏆</div>
                    <h2>Lesson Complete!</h2>
                </div>
                <div class="stats-grid">
                    <div class="stat-card">
                        <div class="stat-value">${gameState.xp}</div>
                        <div class="stat-label">XP Earned</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value">${accuracy}%</div>
                        <div class="stat-label">Accuracy</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value">${gameState.correctAnswers}/${gameState.totalAnswers}</div>
                        <div class="stat-label">Correct</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value">${timeElapsed}s</div>
                        <div class="stat-label">Time</div>
                    </div>
                </div>
                <div class="complete-message">
                    ${accuracy >= 90 ? '🌟 Outstanding work!' : accuracy >= 70 ? '👏 Great job!' : '💪 Keep practicing!'}
                </div>
                <div class="complete-actions">
                    <button class="btn-primary" id="close-lesson-btn">Close</button>
                    <button class="btn-secondary" id="review-btn">Review Mistakes</button>
                </div>
            </div>
        `;

        createConfetti();

        const closeBtn = document.getElementById('close-lesson-btn');
        if (closeBtn) closeBtn.addEventListener('click', () => {
            container.innerHTML = '';
            updateGameStats();
        });

        const reviewBtn = document.getElementById('review-btn');
        if (reviewBtn) reviewBtn.addEventListener('click', () => {
            gameState.currentExerciseIndex = 0;
            gameState.lives = gameState.maxLives;
            gameState.xp = 0;
            gameState.streak = 0;
            gameState.correctAnswers = 0;
            gameState.totalAnswers = 0;
            renderCurrentExercise();
        });
    }

    function showGameOver() {
        const container = document.getElementById('exercise-area') || document.getElementById('practice-modal-content');
        if (!container) return;

        container.innerHTML = `
            <div class="game-over">
                <div class="game-over-icon">💔</div>
                <h2>Out of Lives!</h2>
                <p>Don't worry, mistakes help you learn!</p>
                <div class="stats-summary">
                    <p><strong>${gameState.correctAnswers}</strong> correct out of <strong>${gameState.totalAnswers}</strong></p>
                    <p>Earned <strong>${gameState.xp} XP</strong></p>
                </div>
                <div class="complete-actions">
                    <button class="btn-primary" id="retry-btn">Try Again</button>
                    <button class="btn-secondary" id="close-btn">Close</button>
                </div>
            </div>
        `;

        const retryBtn = document.getElementById('retry-btn');
        if (retryBtn) retryBtn.addEventListener('click', () => {
            gameState.currentExerciseIndex = 0;
            gameState.lives = gameState.maxLives;
            gameState.xp = 0;
            gameState.streak = 0;
            gameState.correctAnswers = 0;
            gameState.totalAnswers = 0;
            renderCurrentExercise();
        });

        const closeBtn = document.getElementById('close-btn');
        if (closeBtn) closeBtn.addEventListener('click', () => {
            container.innerHTML = '';
            updateGameStats();
        });
    }

    // renderPracticeInterface was modal-specific and is no longer used; exercise rendering
    // is handled by `startLessonPractice` and `renderCurrentExercise` which render into
    // the page's `#exercise-area`.

    // Modal Management
    // Modal Management with Dragging and Resizing
    // Modal creation and modal-specific helpers were removed. Practice rendering
    // now targets the page `#exercise-area` directly via `startLessonPractice`.

    // Public API: `startLessonPractice` (tab-based) is defined later and used for in-page practice rendering.

    // Add CSS Styles
    // Comprehensive lesson styles using VSCode theme variables from vscode.css
    const styles = document.createElement('style');
    styles.id = 'lessons-styles';
    styles.textContent = `
        /* Practice area container */
        .lesson-practice { padding: 0; }
        #practice-header { margin-bottom: 20px; }
        
        /* Game stats header */
        .game-header { margin-bottom: 24px; padding: 12px 0; border-bottom: 1px solid var(--vscode-border); }
        .progress-bar-container { width: 100%; height: 6px; background: var(--vscode-input-bg); border-radius: 3px; overflow: hidden; margin-bottom: 16px; }
        .progress-bar { height: 100%; background: linear-gradient(90deg, var(--vscode-accent), #45B7D1); width: 0%; transition: width 0.4s ease; border-radius: 3px; }
        .game-stats { display: flex; gap: 32px; justify-content: center; margin: 0; }
        .stat-item { display: flex; align-items: center; gap: 8px; font-size: 14px; font-weight: 600; color: var(--vscode-text); }
        .stat-icon { font-size: 20px; }
        
        /* Exercise area */
        #exercise-area { min-height: 320px; }
        .exercise-container { 
            background: var(--vscode-sidebar-bg); 
            border: 1px solid var(--vscode-border); 
            border-radius: 6px; 
            padding: 20px; 
            margin-bottom: 12px;
            animation: slideIn 0.3s ease;
        }
        @keyframes slideIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
        
        /* Exercise question section */
        .exercise-question { margin-bottom: 20px; position: relative; }
        .exercise-question h3 { 
            color: var(--vscode-text); 
            margin: 0 0 12px 0; 
            font-size: 16px; 
            font-weight: 600;
        }
        .target-sentence { 
            font-size: 16px; 
            color: var(--vscode-accent); 
            padding: 14px; 
            background: var(--vscode-input-bg); 
            border: 1px solid var(--vscode-input-border);
            border-radius: 4px; 
            margin: 8px 0;
            line-height: 1.5;
        }
        .btn-icon {
            position: absolute;
            top: 0;
            right: 0;
            background: var(--vscode-button-secondary-bg);
            border: 1px solid var(--vscode-border);
            color: var(--vscode-button-secondary-fg);
            padding: 6px 10px;
            border-radius: 4px;
            cursor: pointer;
            font-size: 16px;
            transition: all 0.2s;
        }
        .btn-icon:hover { background: var(--vscode-button-secondary-hover-bg); }
        
        /* Input field */
        .exercise-input {
            width: 100%;
            padding: 10px 12px;
            font-size: 14px;
            background: var(--vscode-input-bg);
            border: 1px solid var(--vscode-input-border);
            border-radius: 4px;
            color: var(--vscode-text);
            font-family: inherit;
            resize: vertical;
            margin-bottom: 14px;
            transition: border-color 0.2s;
        }
        .exercise-input:focus { outline: none; border-color: var(--vscode-accent); }
        
        /* Options grid */
        .options-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
            gap: 10px;
            margin-bottom: 14px;
        }
        .option-btn {
            padding: 10px 14px;
            background: var(--vscode-button-secondary-bg);
            border: 1px solid var(--vscode-border);
            border-radius: 4px;
            color: var(--vscode-text);
            font-size: 13px;
            cursor: pointer;
            transition: all 0.2s;
        }
        .option-btn:hover { background: var(--vscode-hover); }
        .option-btn.selected { background: var(--vscode-accent); border-color: var(--vscode-accent); color: #fff; }
        .option-btn.correct-answer { background: #28a745; border-color: #28a745; color: #fff; }
        .option-btn.wrong-answer { background: #dc3545; border-color: #dc3545; color: #fff; }
        
        /* Word order */
        .answer-zone {
            min-height: 70px;
            padding: 12px;
            background: var(--vscode-input-bg);
            border: 2px dashed var(--vscode-border);
            border-radius: 4px;
            margin-bottom: 12px;
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            align-items: center;
        }
        .placeholder-text { color: var(--vscode-text-secondary); font-style: italic; font-size: 13px; }
        .words-bank {
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            padding: 12px;
            background: var(--vscode-input-bg);
            border: 1px solid var(--vscode-border);
            border-radius: 4px;
            margin-bottom: 12px;
        }
        .word-chip {
            padding: 8px 12px;
            background: var(--vscode-button-secondary-bg);
            border: 1px solid var(--vscode-border);
            border-radius: 16px;
            color: var(--vscode-text);
            font-size: 13px;
            cursor: pointer;
            transition: all 0.2s;
            user-select: none;
        }
        .word-chip:hover { background: var(--vscode-hover); }
        .word-chip.selected { background: var(--vscode-accent); border-color: var(--vscode-accent); color: #fff; }
        
        /* Multiple choice list */
        .options-list {
            display: flex;
            flex-direction: column;
            gap: 10px;
            margin-bottom: 14px;
        }
        .choice-btn {
            display: flex;
            align-items: center;
            gap: 12px;
            padding: 12px;
            background: var(--vscode-button-secondary-bg);
            border: 1px solid var(--vscode-border);
            border-radius: 4px;
            color: var(--vscode-text);
            font-size: 14px;
            cursor: pointer;
            transition: all 0.2s;
            text-align: left;
        }
        .choice-btn:hover { background: var(--vscode-hover); }
        .choice-btn.selected { background: var(--vscode-accent); border-color: var(--vscode-accent); color: #fff; }
        .choice-btn.correct-answer { background: #28a745; border-color: #28a745; color: #fff; }
        .choice-btn.wrong-answer { background: #dc3545; border-color: #dc3545; color: #fff; }
        .choice-letter {
            display: flex;
            align-items: center;
            justify-content: center;
            width: 28px;
            height: 28px;
            background: var(--vscode-input-bg);
            border-radius: 50%;
            font-weight: 600;
            font-size: 12px;
            flex-shrink: 0;
        }
        
        /* Matching */
        .matching-area { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 14px; }
        .matching-column { display: flex; flex-direction: column; gap: 8px; }
        .match-btn {
            padding: 10px;
            background: var(--vscode-button-secondary-bg);
            border: 1px solid var(--vscode-border);
            border-radius: 4px;
            color: var(--vscode-text);
            font-size: 13px;
            cursor: pointer;
            transition: all 0.2s;
            text-align: center;
        }
        .match-btn:hover:not(:disabled) { background: var(--vscode-hover); }
        .match-btn.selected { background: var(--vscode-accent); border-color: var(--vscode-accent); color: #fff; }
        .match-btn:disabled { opacity: 0.4; cursor: not-allowed; }
        .matches-display {
            padding: 12px;
            background: var(--vscode-input-bg);
            border: 1px solid var(--vscode-border);
            border-radius: 4px;
            min-height: 50px;
            margin-bottom: 12px;
        }
        .match-pair {
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 8px;
            background: var(--vscode-sidebar-bg);
            border-radius: 4px;
            margin-bottom: 6px;
            font-size: 13px;
        }
        .btn-icon-small {
            background: none;
            border: none;
            color: var(--vscode-text-secondary);
            cursor: pointer;
            font-size: 14px;
            padding: 2px 6px;
            border-radius: 4px;
            transition: all 0.2s;
        }
        .btn-icon-small:hover { background: var(--vscode-hover); color: var(--vscode-text); }
        
        /* Hints section */
        .exercise-hints { margin-bottom: 12px; display: none; }
        .hint-box { 
            padding: 10px 12px; 
            background: rgba(255,193,7,0.1); 
            border-left: 3px solid #fbc02d; 
            color: var(--vscode-text);
            border-radius: 3px; 
            font-size: 13px;
        }
        
        /* Feedback messages */
        .feedback {
            display: flex;
            align-items: flex-start;
            gap: 10px;
            padding: 10px 12px;
            border-radius: 4px;
            margin-bottom: 12px;
            font-size: 13px;
            animation: slideIn 0.3s ease;
        }
        .feedback.correct { 
            background: rgba(40,167,69,0.1); 
            border-left: 3px solid #28a745; 
            color: #28a745;
        }
        .feedback.incorrect { 
            background: rgba(220,53,69,0.1); 
            border-left: 3px solid #dc3545; 
            color: #dc3545;
        }
        .feedback-icon { font-size: 16px; font-weight: bold; margin-top: 2px; }
        .feedback-text { flex: 1; }
        .feedback-text strong { display: block; margin-bottom: 2px; }
        .feedback-text p { margin: 0; font-size: 12px; }
        
        /* Selected answer display */
        .selected-answer { 
            padding: 10px 12px; 
            background: var(--vscode-input-bg); 
            border-radius: 4px; 
            margin-bottom: 12px; 
            font-size: 13px;
        }
        .selected-answer strong { color: var(--vscode-accent); }
        
        /* Action buttons */
        .exercise-actions {
            display: flex;
            gap: 10px;
            justify-content: flex-end;
            margin-top: 16px;
        }
        .btn-primary, .btn-secondary, .btn-flashcard {
            padding: 8px 16px;
            border: none;
            border-radius: 4px;
            font-size: 13px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s;
        }
        .btn-primary {
            background: var(--vscode-button-bg);
            color: white;
        }
        .btn-primary:hover:not(:disabled) { background: var(--vscode-button-hover); }
        .btn-primary:disabled { opacity: 0.5; cursor: not-allowed; }
        .btn-secondary {
            background: var(--vscode-button-secondary-bg);
            border: 1px solid var(--vscode-border);
            color: var(--vscode-button-secondary-fg);
        }
        .btn-secondary:hover { background: var(--vscode-button-secondary-hover-bg); }
        .btn-flashcard {
            background: transparent;
            border: 1px solid var(--vscode-border);
            color: var(--vscode-text);
        }
        .btn-flashcard:hover { background: var(--vscode-hover); }
        .btn-flashcard:disabled { opacity: 0.4; cursor: not-allowed; }
        .btn-flashcard i { margin-right: 4px; }
        
        /* Completion screens */
        .lesson-complete, .game-over {
            text-align: center;
            padding: 24px;
            background: var(--vscode-sidebar-bg);
            border: 1px solid var(--vscode-border);
            border-radius: 6px;
        }
        .complete-header { margin-bottom: 20px; }
        .trophy-icon { font-size: 60px; margin-bottom: 12px; }
        .lesson-complete h2, .game-over h2 { 
            color: var(--vscode-text); 
            margin: 0 0 8px 0; 
            font-size: 20px; 
        }
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
            gap: 12px;
            margin-bottom: 16px;
        }
        .stat-card {
            background: var(--vscode-input-bg);
            padding: 12px;
            border-radius: 4px;
            border: 1px solid var(--vscode-border);
        }
        .stat-value { font-size: 24px; font-weight: bold; color: var(--vscode-accent); margin-bottom: 4px; }
        .stat-label { color: var(--vscode-text-secondary); font-size: 12px; }
        .complete-message { font-size: 16px; color: var(--vscode-text); margin-bottom: 16px; }
        .complete-actions { display: flex; gap: 12px; justify-content: center; }
        .game-over-icon { font-size: 60px; margin-bottom: 12px; }
        .stats-summary { margin: 16px 0; color: var(--vscode-text-secondary); }
        .stats-summary p { margin: 4px 0; font-size: 13px; }
        
        /* Confetti animation */
        .confetti-container {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            pointer-events: none;
            z-index: 9999;
        }
        .confetti {
            position: absolute;
            width: 10px;
            height: 10px;
            top: -10px;
            animation: confetti-fall 2s linear forwards;
        }
        @keyframes confetti-fall {
            to { transform: translateY(100vh) rotate(360deg); opacity: 0; }
        }
        
        /* Debug section */
        .exercise-debug { margin-top: 12px; color: var(--vscode-text-secondary); }
        .exercise-debug summary { cursor: pointer; color: var(--vscode-text); font-size: 12px; }
        .exercise-debug pre { 
            white-space: pre-wrap; 
            font-size: 11px; 
            background: var(--vscode-input-bg);
            padding: 8px;
            border-radius: 4px;
            border: 1px solid var(--vscode-border);
        }
        
        /* Responsive */
        @media (max-width: 768px) {
            .matching-area { grid-template-columns: 1fr; }
            .stats-grid { grid-template-columns: repeat(2, 1fr); }
            .exercise-container { padding: 14px; }
            .game-stats { gap: 16px; }
        }
    `;
    document.head.appendChild(styles);

    // Auto-initialize if lesson data exists in DOM
    document.addEventListener('DOMContentLoaded', () => {
        console.log('Duolingo-style practice system loaded ✓');
    });

    // Modal helpers removed. Practice now renders into the in-page lesson area.

    function renderExerciseUI(container, exercise, index) {
        console.log('🎯 renderExerciseUI called with exercise:', exercise);
        container.innerHTML = '';
        container.className = 'practice-exercise-container';

        const title = document.createElement('h3');
        title.textContent = `${index + 1}. ${exercise.type || 'Exercise'}`;
        container.appendChild(title);

        // Use the specific exercise renderer based on type
        switch (exercise.type) {
            case 'typing':
                renderTypingExercise(exercise, container);
                break;
            case 'vocabulary':
                renderVocabularyExercise(exercise, container);
                break;
            case 'fill_blank':
                renderFillBlankExercise(exercise, container);
                break;
            case 'sentence':
                renderSentenceExercise(exercise, container);
                break;
            case 'word_order':
                renderWordOrderExercise(exercise, container);
                break;
            case 'pronunciation':
                renderPronunciationExercise(exercise, container);
                break;
            case 'matching':
                renderMatchingExercise(exercise, container);
                break;
            case 'listening':
                renderListeningExercise(exercise, container);
                break;
            default:
                // Fallback for unknown exercise types
                const prompt = document.createElement('div');
                prompt.className = 'practice-exercise-prompt';
                prompt.textContent = exercise.question || '';
                container.appendChild(prompt);

                const input = document.createElement('textarea');
                input.className = 'practice-exercise-input';
                input.rows = 3;
                input.placeholder = 'Type your answer here...';
                container.appendChild(input);

                const controls = document.createElement('div');
                controls.className = 'practice-exercise-controls';
                const checkBtn = document.createElement('button');
                checkBtn.className = 'btn-small';
                checkBtn.innerHTML = '<i class="codicon codicon-check"></i> Check Answer';
                const nextBtn = document.createElement('button');
                nextBtn.className = 'btn-flashcard';
                nextBtn.innerHTML = '<i class="codicon codicon-arrow-right"></i> Next';
                nextBtn.disabled = true;
                controls.appendChild(checkBtn);
                controls.appendChild(nextBtn);
                container.appendChild(controls);

                const feedback = document.createElement('div');
                feedback.className = 'practice-feedback';
                container.appendChild(feedback);

                checkBtn.addEventListener('click', () => {
                    const expected = (exercise.correct_answer || exercise.question || '').toString();
                    const got = input.value.trim();
                    if (!got) {
                        feedback.className = 'practice-feedback incorrect';
                        feedback.style.display = 'block';
                        feedback.innerHTML = '<i class="codicon codicon-warning"></i> Please enter an answer first';
                        return;
                    }

                    const accuracy = calculateAccuracy(expected, got);
                    gameState.totalAnswers += 1;
                    const passed = accuracy >= 70 || expected.trim().length === 0;

                    feedback.style.display = 'block';
                    if (passed) {
                        gameState.correctAnswers += 1;
                        gameState.xp += XP_PER_EXERCISE;
                        gameState.streak += 1;
                        playCorrectSound();
                        feedback.className = 'practice-feedback correct';
                        feedback.innerHTML = `<i class="codicon codicon-check"></i> Correct! Accuracy: ${accuracy}%`;
                        nextBtn.disabled = false;
                        checkBtn.disabled = true;
                    } else {
                        gameState.lives = Math.max(0, gameState.lives - 1);
                        gameState.streak = 0;
                        playIncorrectSound();
                        feedback.className = 'practice-feedback incorrect';
                        feedback.innerHTML = `<i class="codicon codicon-error"></i> Try again - Accuracy: ${accuracy}%`;
                    }
                    updateGameStats();
                });

                nextBtn.addEventListener('click', () => {
                    if (gameState.currentExerciseIndex < gameState.exercises.length - 1) {
                        gameState.currentExerciseIndex += 1;
                        renderExerciseUI(container, gameState.exercises[gameState.currentExerciseIndex], gameState.currentExerciseIndex);
                    } else {
                        // End of lesson
                        container.innerHTML = `
                            <div style="text-align: center; padding: 20px;">
                                <div style="font-size: 48px; margin-bottom: 16px;">🎉</div>
                                <h2>Lesson Complete!</h2>
                                <p>Great job! You've finished all exercises.</p>
                                <div style="margin: 16px 0; padding: 12px; background: var(--vscode-input-bg); border-radius: 6px;">
                                    <strong>Your Score:</strong> ${gameState.correctAnswers}/${gameState.totalAnswers} 
                                    (${Math.round((gameState.correctAnswers / gameState.totalAnswers) * 100) || 0}%)
                                </div>
                            </div>
                        `;
                    }
                });
                break;
        }
    }

    // Modal-based openPracticeModal removed; practice is rendered in the Today's Lesson tab.

    // Start practice directly in Today's Lesson tab (no modal)
    window.startLessonPractice = function (lesson, userId) {
        console.log('✓ startLessonPractice called with:', lesson);
        if (!lesson || !lesson.exercises) {
            console.warn('startLessonPractice: no lesson/exercises', lesson);
            return;
        }

        // Initialize game state
        gameState.exercises = lesson.exercises || [];
        gameState.currentExerciseIndex = 0;
        gameState.lives = 3;
        gameState.xp = 0;
        gameState.streak = 0;
        gameState.correctAnswers = 0;
        gameState.totalAnswers = 0;
        gameState.hintsUsed = 0;
        gameState.language = lesson.metadata?.language || lesson.language || 'dutch';

        // Render header and first exercise into lesson tab
        const headerContainer = document.getElementById('practice-header');
        const exerciseContainer = document.getElementById('exercise-area');
        if (!exerciseContainer) {
            console.error('startLessonPractice: no #exercise-area in DOM');
            return;
        }

        if (headerContainer) {
            headerContainer.innerHTML = '';
            headerContainer.appendChild(createGameHeader());
        }

        // Render first exercise
        renderExerciseUI(exerciseContainer, gameState.exercises[0], 0);
        updateGameStats();
    };

})();