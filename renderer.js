const { dialog } = require('@electron/remote');
const fs = require('fs');
const path = require('path');

let selectedCppFile = '';
let selectedOutputFolder = '';

const browseBtn = document.getElementById('browseBtn');
const outputBtn = document.getElementById('outputBtn');
const convertBtn = document.getElementById('convertBtn');
const convertAiBtn = document.getElementById('convertAiBtn');
const countdownText = document.getElementById('countdownText');
const aiStatus = document.getElementById('aiStatus');

browseBtn.addEventListener('click', async () => {
  const result = await dialog.showOpenDialog({
    properties: ['openFile'],
    filters: [{ name: 'C++ Files', extensions: ['cpp'] }]
  });
  if (!result.canceled && result.filePaths.length > 0) {
    selectedCppFile = result.filePaths[0];
    document.getElementById('cppPath').innerText = selectedCppFile;
  }
});

outputBtn.addEventListener('click', async () => {
  const result = await dialog.showOpenDialog({ properties: ['openDirectory'] });
  if (!result.canceled && result.filePaths.length > 0) {
    selectedOutputFolder = result.filePaths[0];
    document.getElementById('outputPath').innerText = selectedOutputFolder;
  }
});

convertBtn.addEventListener('click', async () => {
  if (!selectedCppFile || !selectedOutputFolder) {
    alert("Please select both the input file and output folder.");
    return;
  }

  const cppCode = fs.readFileSync(selectedCppFile, 'utf8');

  try {
    const response = await fetch('http://127.0.0.1:5000/convert', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        code: cppCode,
        output_folder: selectedOutputFolder
      })
    });

    const result = await response.json();

    if (response.ok) {
      alert('✅ Rule-based conversion successful!\nSaved to: ' + path.join(selectedOutputFolder, 'output_sastra.rs'));
    } else {
      alert('Error: ' + result.error);
    }
  } catch (err) {
    console.error("Fetch error:", err);
    alert('❌ Failed to connect to backend:\n' + err.message);
  }
});

convertAiBtn.addEventListener('click', async () => {
  if (!selectedCppFile || !selectedOutputFolder) {
    alert("Please select both the input file and output folder.");
    return;
  }

  const cppCode = fs.readFileSync(selectedCppFile, 'utf8');
  aiStatus.classList.remove('hidden');

  try {
    const response = await fetch('http://127.0.0.1:5000/convert_ai', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        code: cppCode,
        output_folder: selectedOutputFolder
      })
    });

    aiStatus.classList.add('hidden');
    const result = await response.json();

    if (response.ok) {
      alert('🤖 AI conversion successful!\nSaved to: ' + path.join(selectedOutputFolder, 'output_ai.rs'));
    } else {
      alert('Error: ' + result.error);
    }
  } catch (err) {
    aiStatus.classList.add('hidden');
    console.error("Fetch error:", err);
    alert('❌ Failed to connect to backend:\n' + err.message);
  }
});

// ⏳ Countdown before enabling conversion buttons
let countdown = 60;
convertBtn.disabled = true;
convertAiBtn.disabled = true;

countdownText.classList.remove('hidden');
countdownText.innerText = `AI Model Loading please wait: ${countdown}s`;

const timer = setInterval(() => {
  countdown--;
  countdownText.innerText = `AI Model Loading please wait: ${countdown}s`;

  if (countdown <= 0) {
    clearInterval(timer);
    convertBtn.disabled = false;
    convertAiBtn.disabled = false;

    countdownText.classList.add('fade-out'); // Add fade animation
    setTimeout(() => {
      countdownText.style.display = 'none'; // Fully remove it after fade
    }, 500); // Match CSS animation duration
  }
}, 1000);
