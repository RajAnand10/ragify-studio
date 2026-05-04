const toolBtns = document.querySelectorAll('.tool-btn');
const chatModeTitle = document.getElementById('chatModeTitle');
const chatModeDesc = document.getElementById('chatModeDesc');
const promptInput = document.getElementById('promptInput');
const sendBtn = document.getElementById('sendBtn');
const chatMessages = document.getElementById('chatMessages');
const clearChatBtn = document.getElementById('clearChatBtn');

// Auth Guard
const currentUser = localStorage.getItem('currentUser');
if (!currentUser) window.location.href = '/';

const historyList = document.getElementById('historyList');
const historyCount = document.querySelector('.history-count');
const mainAudioPlayer = document.getElementById('mainAudioPlayer');
const playerTitle = document.getElementById('playerTitle');
const downloadBtn = document.getElementById('downloadBtn');
const micBtn = document.getElementById('micBtn');

// Custom Player Elements
const customPlayPauseBtn = document.getElementById('customPlayPauseBtn');
const progressBarFill = document.getElementById('progressBarFill');
const progressBarContainer = document.getElementById('progressBarContainer');
const currentTimeDisplay = document.getElementById('currentTimeDisplay');
const durationDisplay = document.getElementById('durationDisplay');
const volumeSlider = document.getElementById('volumeSlider');
const playerArt = document.getElementById('playerArt');

let currentMode = 'Ragify Assistant';
let historyItems = [];
let currentAudioUrl = null;
let conversationContext = []; // Conversational memory
let chatStates = {}; // Object to store html and context for each mode

// Initialize current mode state
chatStates[currentMode] = {
  html: chatMessages.innerHTML,
  context: conversationContext
};

// Set initial mode UI
chatModeTitle.textContent = currentMode;
chatModeDesc.textContent = "AI song recommendations.";

toolBtns.forEach(btn => {
  btn.addEventListener('click', () => {
    // Save current state before switching
    chatStates[currentMode] = {
      html: chatMessages.innerHTML,
      context: conversationContext
    };

    toolBtns.forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    currentMode = btn.dataset.mode;
    chatModeTitle.textContent = currentMode;
    
    // Restore or initialize new state
    if (chatStates[currentMode]) {
      chatMessages.innerHTML = chatStates[currentMode].html;
      conversationContext = chatStates[currentMode].context;
    } else {
      conversationContext = [];
      chatMessages.innerHTML = '';
      appendSystemMessage(`Switched to **${currentMode}**. How can I help you?`);
    }
    
    if (currentMode === 'Scenario to Song') {
      chatModeDesc.textContent = "AI song recommendations.";
    } else if (currentMode === 'Sound Effects') {
      chatModeDesc.textContent = "Generate cinematic sound fx.";
    } else if (currentMode === 'Music') {
      chatModeDesc.textContent = "Compose a full track.";
    } else if (currentMode === 'Text to Voice') {
      chatModeDesc.textContent = "Convert script to speech.";
    }
    
    chatMessages.scrollTop = chatMessages.scrollHeight;
  });
});

function pauseAudio() {
  if (mainAudioPlayer && !mainAudioPlayer.paused) {
    mainAudioPlayer.pause();
  }
}

promptInput.addEventListener('keydown', (e) => {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault();
    sendBtn.click();
  }
});

function appendUserMessage(text) {
  const div = document.createElement('div');
  div.className = 'chat-message user';
  div.innerHTML = `<div class="message-bubble">${text}</div>`;
  chatMessages.appendChild(div);
  chatMessages.scrollTop = chatMessages.scrollHeight;
}

function appendSystemMessage(html) {
  const div = document.createElement('div');
  div.className = 'chat-message system';
  div.innerHTML = `<div class="message-bubble"><div class="sys-icon"><i class="fa-solid fa-wand-magic-sparkles"></i></div><div>${html}</div></div>`;
  chatMessages.appendChild(div);
  chatMessages.scrollTop = chatMessages.scrollHeight;
  return div;
}

window.switchModeAndRun = (mode, originalPrompt) => {
  const btn = Array.from(toolBtns).find(b => b.dataset.mode === mode);
  if (btn) btn.click();
  promptInput.value = originalPrompt;
  setTimeout(() => sendBtn.click(), 100);
};

window.playFromChat = (url, prompt, mode, artwork) => {
  currentAudioUrl = url;
  mainAudioPlayer.src = url;
  playerTitle.textContent = prompt;
  document.querySelector('.player-desc').textContent = mode;
  if(artwork) {
     playerArt.src = artwork;
     playerArt.style.display = 'block';
  } else {
     playerArt.style.display = 'none';
  }
  downloadBtn.disabled = false;
  mainAudioPlayer.play().catch(()=>{});
  
  const playerPanel = document.querySelector('.bottom-player');
  playerPanel.classList.remove('pop-animation');
  void playerPanel.offsetWidth;
  playerPanel.classList.add('pop-animation');
};

function appendBotMessage(html) {
  const div = document.createElement('div');
  div.className = 'chat-message bot';
  div.innerHTML = `<div class="message-bubble">${html}</div>`;
  chatMessages.appendChild(div);
  chatMessages.scrollTop = chatMessages.scrollHeight;
  return div;
}

function appendLoadingMessage() {
  const div = document.createElement('div');
  div.className = 'chat-message bot';
  div.innerHTML = `
    <div class="message-bubble">
      <div class="loading-dots">
        <span></span><span></span><span></span>
      </div>
    </div>`;
  chatMessages.appendChild(div);
  chatMessages.scrollTop = chatMessages.scrollHeight;
  return div;
}

function renderHistory() {
  historyCount.textContent = `See all (${historyItems.length})`;
  if (historyItems.length === 0) return;
  
  historyList.innerHTML = '';
  historyItems.forEach((item, index) => {
    const div = document.createElement('div');
    div.className = `history-item ${item.type === 'suggestion' ? 'suggestion' : ''}`;
    
    const timeStr = new Date().toLocaleTimeString([], { hour: 'numeric', minute: '2-digit', hour12: true });
    
    if (item.type === 'suggestion') {
      div.innerHTML = `
        <div class="hi-info">
          <div class="hi-title">${item.mode}</div>
          <div class="hi-sub">${timeStr}</div>
          <div class="hi-title" style="margin-top: 8px; white-space: pre-wrap; font-size: 0.85rem; color: var(--text-muted);">${item.text}</div>
        </div>
      `;
    } else {
      let iconHtml = `<div class="hi-icon"><i class="fa-solid fa-music"></i></div>`;
      if (item.artwork) {
        iconHtml = `<div class="hi-icon"><img src="${item.artwork}" alt="Art"></div>`;
      } else if (item.mode === 'Sound Effects') {
        iconHtml = `<div class="hi-icon"><i class="fa-solid fa-wave-square"></i></div>`;
      } else if (item.mode === 'Text to Voice') {
        iconHtml = `<div class="hi-icon"><i class="fa-solid fa-microphone"></i></div>`;
      }

      div.innerHTML = `
        ${iconHtml}
        <div class="hi-info">
          <div class="hi-title">${item.prompt}</div>
          <div class="hi-sub">${item.mode}</div>
        </div>
        <div class="hi-meta">
          <span class="hi-time">${timeStr}</span>
          <div class="hi-play"><i class="fa-solid fa-play"></i></div>
        </div>
      `;
      
      div.addEventListener('click', () => {
        currentAudioUrl = item.url;
        mainAudioPlayer.src = item.url;
        playerTitle.textContent = item.prompt;
        document.querySelector('.player-desc').textContent = item.mode;
        if(item.artwork) {
           playerArt.src = item.artwork;
           playerArt.style.display = 'block';
        } else {
           playerArt.style.display = 'none';
        }
        downloadBtn.disabled = false;
        mainAudioPlayer.play().catch(()=>{});
        
        // Trigger pop animation
        const playerPanel = document.querySelector('.bottom-player');
        playerPanel.classList.remove('pop-animation');
        void playerPanel.offsetWidth;
        playerPanel.classList.add('pop-animation');
      });
    }
    historyList.prepend(div);
  });
}

clearChatBtn.addEventListener('click', () => {
  conversationContext = [];
  chatMessages.innerHTML = '';
  appendBotMessage(`Chat memory cleared. We are starting fresh! What would you like to create?`);
  chatStates[currentMode] = {
    html: chatMessages.innerHTML,
    context: conversationContext
  };
});

sendBtn.addEventListener('click', async () => {
  const prompt = promptInput.value.trim();
  if (!prompt) return;

  appendUserMessage(prompt);
  promptInput.value = '';
  sendBtn.disabled = true;
  
  // Update memory array
  conversationContext.push({ role: 'user', content: prompt });
  const messagesToSend = [...conversationContext];

  const loadingBubble = appendLoadingMessage();

  try {
    if (currentMode === 'Ragify Assistant') {
      const res = await fetch('/api/route-intent', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prompt: prompt, messages: messagesToSend })
      });
      if (!res.ok) throw new Error(await res.text());
      const data = await res.json();
      
      let htmlContent = `<div class="message-bubble"><div>${data.message}</div>`;
      if (data.clarification_needed && data.suggested_modes && data.suggested_modes.length > 0) {
        htmlContent += `<div class="interactive-btn-group">`;
        data.suggested_modes.forEach(mode => {
           let icon = '<i class="fa-solid fa-wand-magic-sparkles"></i>';
           if (mode === 'Sound Effects') icon = '<i class="fa-solid fa-wave-square"></i>';
           if (mode === 'Text to Voice') icon = '<i class="fa-solid fa-microphone"></i>';
           if (mode === 'Scenario to Song') icon = '<i class="fa-solid fa-headphones"></i>';
           htmlContent += `<button class="interactive-btn" onclick="window.switchModeAndRun('${mode}', '${prompt.replace(/'/g, "\\'")}')">${icon} ${mode}</button>`;
        });
        htmlContent += `</div>`;
      }
      htmlContent += `</div>`;
      
      loadingBubble.innerHTML = htmlContent;
      conversationContext.push({ role: 'model', content: data.message });
      
    } else if (currentMode === 'Scenario to Song') {
      const res = await fetch('/api/suggest-song', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prompt: prompt, messages: messagesToSend })
      });
      if (!res.ok) throw new Error(await res.text());
      const data = await res.json();
      
      if (data.preview_url) {
        const title = data.song_title + " by " + data.artist;
        historyItems.push({ type: 'audio', mode: currentMode, prompt: title, url: data.preview_url, artwork: data.artwork_url });
        
        loadingBubble.innerHTML = `
          <div class="message-bubble">
            <strong>${data.song_title}</strong> by ${data.artist}<br>
            <button class="interactive-btn" style="margin-top: 10px;" onclick="playFromChat('${data.preview_url}', '${title.replace(/'/g, "\\'")}', '${currentMode}', '${data.artwork_url || ''}')"><i class="fa-solid fa-play"></i> Play Preview</button>
          </div>
        `;
        
        currentAudioUrl = data.preview_url;
        mainAudioPlayer.src = data.preview_url;
        playerTitle.textContent = title;
        document.querySelector('.player-desc').textContent = currentMode;
        if(data.artwork_url) {
           playerArt.src = data.artwork_url;
           playerArt.style.display = 'block';
        }
        downloadBtn.disabled = false;
        conversationContext.push({ role: 'model', content: `Suggested ${title}` });
      } else {
        historyItems.push({ type: 'suggestion', mode: currentMode, text: data.text });
        loadingBubble.innerHTML = `<div class="message-bubble">${data.text}</div>`;
        conversationContext.push({ role: 'model', content: data.text });
      }
    } else {
      let apiMode = 'sfx';
      if (currentMode === 'Text to Voice') apiMode = 'voice';

      const res = await fetch('/api/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prompt: prompt, messages: messagesToSend, mode: apiMode, duration_seconds: 5 })
      });

      if (!res.ok) throw new Error(await res.text());

      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      historyItems.push({ type: 'audio', mode: currentMode, prompt: prompt, url });
      
      conversationContext.push({ role: 'model', content: 'Generated audio successfully.' });
      
      loadingBubble.innerHTML = `
        <div class="message-bubble">
          Here is your generated audio:<br>
          <button class="interactive-btn" style="margin-top: 10px;" onclick="playFromChat('${url}', '${prompt.replace(/'/g, "\\'")}', '${currentMode}', '')"><i class="fa-solid fa-play"></i> Play Audio</button>
        </div>
      `;
      
      currentAudioUrl = url;
      mainAudioPlayer.src = url;
      playerTitle.textContent = currentMode;
      document.querySelector('.player-desc').textContent = prompt;
      playerArt.style.display = 'none';
      downloadBtn.disabled = false;
    }
    
    renderHistory();
  } catch (error) {
    loadingBubble.innerHTML = `<div class="message-bubble" style="color: #ef4444;">Generation Error: ${error.message}</div>`;
  } finally {
    sendBtn.disabled = false;
    promptInput.focus();
    
    // Auto scroll
    chatMessages.scrollTop = chatMessages.scrollHeight;
  }
});

downloadBtn.addEventListener('click', () => {
  if (!currentAudioUrl) return;
  const a = document.createElement('a');
  a.href = currentAudioUrl;
  a.download = `ragify_audio_${Date.now()}.mp3`;
  a.click();
});

// Global Audio Manager: Ensure only one audio plays at a time
document.addEventListener('play', function(e) {
  const audios = document.getElementsByTagName('audio');
  for (let i = 0; i < audios.length; i++) {
    if (audios[i] !== e.target) {
      audios[i].pause();
    }
  }
}, true); // Use capture phase since 'play' does not bubble

// Custom Player Logic
mainAudioPlayer.addEventListener('play', () => { customPlayPauseBtn.innerHTML = '<i class="fa-solid fa-pause"></i>'; });
mainAudioPlayer.addEventListener('pause', () => { customPlayPauseBtn.innerHTML = '<i class="fa-solid fa-play"></i>'; });
customPlayPauseBtn.addEventListener('click', () => {
  if (!mainAudioPlayer.src || mainAudioPlayer.src === window.location.href) return;
  if (mainAudioPlayer.paused) mainAudioPlayer.play();
  else mainAudioPlayer.pause();
});

function formatTime(seconds) {
  if (isNaN(seconds) || !isFinite(seconds)) return "0:00";
  const m = Math.floor(seconds / 60);
  const s = Math.floor(seconds % 60);
  return `${m}:${s.toString().padStart(2, '0')}`;
}

mainAudioPlayer.addEventListener('timeupdate', () => {
  const current = mainAudioPlayer.currentTime;
  const duration = mainAudioPlayer.duration;
  currentTimeDisplay.textContent = formatTime(current);
  if (!isNaN(duration) && isFinite(duration)) {
    durationDisplay.textContent = formatTime(duration);
    progressBarFill.style.width = `${(current / duration) * 100}%`;
  }
});
mainAudioPlayer.addEventListener('loadedmetadata', () => { durationDisplay.textContent = formatTime(mainAudioPlayer.duration); });
progressBarContainer.addEventListener('click', (e) => {
  if (!mainAudioPlayer.duration || !isFinite(mainAudioPlayer.duration)) return;
  const rect = progressBarContainer.getBoundingClientRect();
  mainAudioPlayer.currentTime = ((e.clientX - rect.left) / rect.width) * mainAudioPlayer.duration;
});
if (volumeSlider) volumeSlider.addEventListener('input', (e) => mainAudioPlayer.volume = e.target.value);

// Mic functionality
if (micBtn) {
  let recognition;
  if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    recognition = new SpeechRecognition();
    recognition.continuous = false;
    recognition.interimResults = true;
    let isRecording = false;
    recognition.onstart = () => {
      pauseAudio();
      isRecording = true;
      micBtn.classList.add('recording');
    };
    recognition.onaudiostart = pauseAudio;
    recognition.onresult = (event) => {
      let transcript = '';
      for (let i = event.resultIndex; i < event.results.length; i++) transcript += event.results[i][0].transcript;
      promptInput.value = transcript;
    };
    recognition.onend = () => {
      isRecording = false;
      micBtn.classList.remove('recording');
    };
    recognition.onerror = (event) => {
      isRecording = false;
      micBtn.classList.remove('recording');
      alert("Microphone error: " + event.error);
    };
    micBtn.addEventListener('click', () => {
      pauseAudio();
      if (isRecording) recognition.stop();
      else { promptInput.value = ''; recognition.start(); }
    });
  } else {
    micBtn.addEventListener('click', () => alert("Speech recognition is not supported in your browser."));
  }
}

async function checkApi() {
  try {
    const res = await fetch('/api/health');
    const data = await res.json();
    document.getElementById('apiStatusText').textContent = data.elevenlabs_configured ? 'API Online' : 'API Missing';
    if (!data.elevenlabs_configured) document.querySelector('.status-dot').classList.add('offline');
  } catch {
    document.getElementById('apiStatusText').textContent = 'API Offline';
    document.querySelector('.status-dot').classList.add('offline');
  }
}
checkApi();
