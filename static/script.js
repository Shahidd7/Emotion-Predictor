const examples = [
    "I feel terrified when walking down dark alleyways alone.",
    "I am furious that they cancelled the trip at the last minute.",
    "I feel deep love and romantic affection for my partner."
];

function fillExample(index) {
    document.getElementById('textInput').value = examples[index];
}

const emotionConfig = {
    sadness: { icon: '😢', color: '#3b82f6' },
    joy: { icon: '😄', color: '#facc15' },
    love: { icon: '❤️', color: '#ec4899' },
    anger: { icon: '😠', color: '#ef4444' },
    fear: { icon: '😨', color: '#8b5cf6' },
    surprise: { icon: '😲', color: '#10b981' }
};

async function predictEmotion() {
    const text = document.getElementById('textInput').value;
    const btn = document.getElementById('predictBtn');
    const resultArea = document.getElementById('resultArea');

    if (!text.trim()) {
        alert("Please enter some text first.");
        return;
    }

    btn.disabled = true;
    btn.innerHTML = "Analyzing...";
    resultArea.innerHTML = '<div class="loader"></div>';

    try {
        // Send to FastAPI backend
        const response = await fetch('/predict', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ text: text })
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        
        displayResult(data.prediction_emotion, data.confidence, data.all_probabilities);
    } catch (error) {
        console.error("Error:", error);
        resultArea.innerHTML = '<div class="result-empty"><div>⚠️</div><p>Error connecting to API. Is FastAPI running?</p></div>';
    }

    btn.disabled = false;
    btn.innerHTML = "Predict Emotion";
}

function displayResult(emotion, confidence, allProbabilities) {
    // Fallbacks in case names don't match perfectly
    emotion = emotion || "unknown";
    confidence = confidence || 0.0;
    
    const config = emotionConfig[emotion] || { icon: '🤔', color: '#8b9bb4' };
    const resultArea = document.getElementById('resultArea');
    
    resultArea.style.borderColor = config.color;
    resultArea.style.backgroundColor = `${config.color}11`; // Add transparency
    
    // Safely create a string to show all probabilities
    let probBars = '';
    if (allProbabilities && typeof allProbabilities === 'object') {
        for (const [emotionName, prob] of Object.entries(allProbabilities)) {
            const percent = (prob * 100).toFixed(1);
            probBars += `<div style="margin-top: 10px; font-size: 0.9rem; color: var(--text-muted);">
                ${emotionName.charAt(0).toUpperCase() + emotionName.slice(1)}: ${percent}%
            </div>`;
        }
    }
    
    resultArea.innerHTML = `
        <div class="result-display" style="display: block;">
            <div class="emotion-icon" style="border-color: ${config.color}; color: ${config.color};">
                ${config.icon}
            </div>
            <div class="emotion-label" style="color: ${config.color}">${emotion}</div>
            <div class="emotion-probability">Confidence: ${(confidence * 100).toFixed(1)}%</div>
            <div style="margin-top: 1.5rem; padding-top: 1rem; border-top: 1px solid var(--border);">
                <strong style="font-size: 0.85rem; color: var(--text-muted);">ALL PROBABILITIES:</strong>
                ${probBars}
            </div>
        </div>
    `;
}