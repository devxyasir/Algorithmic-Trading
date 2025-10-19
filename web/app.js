// Global variables
let allResults = [];
let currentIndex = 0;
let totalSymbols = 0;
let selectedSymbols = [];
let aiEnabled = false;
let currentResultForAI = null;

// DOM elements
const analyzeBtn = document.getElementById('analyzeBtn');
const exportBtn = document.getElementById('exportBtn');
const csvFileInput = document.getElementById('csvFileInput');
const useTemplateBtn = document.getElementById('useTemplateBtn');
const clearSymbolsBtn = document.getElementById('clearSymbolsBtn');
const clearDataBtn = document.getElementById('clearDataBtn');
const fileName = document.getElementById('fileName');
const symbolsDisplay = document.getElementById('symbolsDisplay');
const symbolsList = document.getElementById('symbolsList');
const symbolCount = document.getElementById('symbolCount');
const timeframe = document.getElementById('timeframe');
const progressSection = document.getElementById('progressSection');
const progressFill = document.getElementById('progressFill');
const progressText = document.getElementById('progressText');
const statusMessages = document.getElementById('statusMessages');
const summary = document.getElementById('summary');
const resultsSection = document.getElementById('resultsSection');
const resultsBody = document.getElementById('resultsBody');
const detailModal = document.getElementById('detailModal');
const detailContent = document.getElementById('detailContent');
const aiModal = document.getElementById('aiModal');
const aiContent = document.getElementById('aiContent');

// Check AI status on load
checkAIStatus();

// Event listeners
analyzeBtn.addEventListener('click', startAnalysis);
exportBtn.addEventListener('click', exportResults);
csvFileInput.addEventListener('change', handleFileUpload);
useTemplateBtn.addEventListener('click', useTemplateFile);
clearSymbolsBtn.addEventListener('click', clearSymbols);
clearDataBtn.addEventListener('click', clearOldData);

document.querySelector('.close').addEventListener('click', () => {
    detailModal.style.display = 'none';
});

document.querySelector('.close-ai').addEventListener('click', () => {
    aiModal.style.display = 'none';
});

window.addEventListener('click', (e) => {
    if (e.target === detailModal) {
        detailModal.style.display = 'none';
    }
    if (e.target === aiModal) {
        aiModal.style.display = 'none';
    }
});

// Check if AI is enabled
async function checkAIStatus() {
    try {
        const status = await eel.get_ai_status()();
        aiEnabled = status.enabled;
        if (aiEnabled) {
            console.log('✅ AI Analysis enabled:', status.provider, status.model);
        } else {
            console.log('⚠️ AI Analysis disabled - check console for errors');
        }
    } catch (e) {
        aiEnabled = false;
        console.log('AI status check failed:', e);
    }
}

// AI Analysis function
async function analyzeWithAI(symbol, result) {
    if (!aiEnabled) {
        alert('❌ AI Analysis is not available.\n\nAPI key is hardcoded but AI failed to initialize.\n\nCheck the console for error details or restart the app.');
        return;
    }
    
    // Store current result
    currentResultForAI = result;
    
    // Show AI modal with loading
    aiModal.style.display = 'block';
    aiContent.innerHTML = `
        <div class="ai-loading" style="text-align: center; padding: 40px;">
            <div class="spinner"></div>
            <h2>🤖 AI is analyzing ${symbol}...</h2>
            <p>This may take 10-30 seconds</p>
        </div>
    `;
    
    try {
        const aiResult = await eel.analyze_with_ai(symbol, result)();
        
        if (aiResult.error) {
            aiContent.innerHTML = `
                <div style="padding: 20px; text-align: center;">
                    <h2>❌ AI Analysis Failed</h2>
                    <p style="color: #f56565;">${aiResult.error}</p>
                    <button class="btn-ai" onclick="aiModal.style.display='none'">Close</button>
                </div>
            `;
            return;
        }
        
        // Display AI analysis
        displayAIAnalysis(symbol, aiResult);
        
    } catch (e) {
        aiContent.innerHTML = `
            <div style="padding: 20px; text-align: center;">
                <h2>❌ Error</h2>
                <p style="color: #f56565;">${e.toString()}</p>
                <button class="btn-ai" onclick="aiModal.style.display='none'">Close</button>
            </div>
        `;
    }
}

// Display AI analysis results
function displayAIAnalysis(symbol, aiResult) {
    const ai = aiResult.ai_analysis;
    const comparison = aiResult.comparison;
    
    // Consensus badge with color coding
    let consensusBadgeClass = 'consensus-badge';
    if (comparison.consensus_score === 'STRONG_AGREEMENT') {
        consensusBadgeClass += ' consensus-strong';
    } else if (comparison.consensus_score === 'MODERATE_AGREEMENT') {
        consensusBadgeClass += ' consensus-moderate';
    } else if (comparison.consensus_score === 'DISAGREEMENT') {
        consensusBadgeClass += ' consensus-disagree';
    } else {
        consensusBadgeClass += ' consensus-weak';
    }
    
    aiContent.innerHTML = `
        <h1 style="margin-bottom: 20px;">🤖 AI-Enhanced Analysis: ${symbol}</h1>
        
        <div class="${consensusBadgeClass}" style="padding: 20px; border-radius: 12px; margin-bottom: 20px;">
            <div style="font-size: 1.5em; font-weight: bold; margin-bottom: 10px;">
                Consensus Rating: ${comparison.consensus_rating}/100
            </div>
            <div style="font-size: 1.2em; margin-bottom: 10px;">
                ${comparison.consensus_message}
            </div>
            <div style="font-size: 1.8em; font-weight: bold; margin-top: 15px;">
                ${comparison.final_action}
            </div>
        </div>
        
        <div class="ai-panel">
            <h2 style="margin: 0 0 15px 0;">AI Recommendation</h2>
            
            <div class="ai-recommendation">
                <div style="font-size: 2em; font-weight: bold; margin-bottom: 10px;">
                    ${ai.recommendation}
                </div>
                <div style="font-size: 1.5em;">${ai.confidence}% Confidence</div>
            </div>
            
            <div class="ai-grid">
                <div class="ai-card">
                    <strong>Entry Strategy:</strong><br/>
                    $${ai.entry_strategy?.price ? ai.entry_strategy.price.toFixed(2) : 'N/A'}<br/>
                    <small>${ai.entry_strategy?.timing || 'N/A'}</small><br/>
                    ${ai.entry_strategy?.trigger ? `<small style="font-style: italic;">${ai.entry_strategy.trigger}</small>` : ''}
                </div>
                <div class="ai-card">
                    <strong>Stop Loss:</strong><br/>
                    $${ai.stop_loss?.price ? ai.stop_loss.price.toFixed(2) : 'N/A'}<br/>
                    <small>${ai.stop_loss?.risk_pct ? ai.stop_loss.risk_pct.toFixed(2) + '% risk' : 'N/A'}</small><br/>
                    <small style="font-style: italic;">${ai.stop_loss?.reasoning || 'N/A'}</small>
                </div>
                <div class="ai-card">
                    <strong>Take Profit:</strong><br/>
                    $${ai.take_profit?.target_1?.price ? ai.take_profit.target_1.price.toFixed(2) : 'N/A'}<br/>
                    <small>${ai.take_profit?.target_1?.gain_pct ? '+' + ai.take_profit.target_1.gain_pct.toFixed(2) + '% gain' : 'N/A'}</small>
                </div>
            </div>
            
            <div class="ai-pattern">
                <strong>📊 Pattern:</strong> ${ai.pattern?.type || 'N/A'}<br/>
                <strong>⏱️ Timeline:</strong> ${ai.pattern?.timeline_days || 'N/A'} days<br/>
                <strong>📈 Success Probability:</strong> ${ai.pattern?.probability || 'N/A'}%<br/>
                <strong>⚠️ Risk Level:</strong> ${ai.risk_assessment?.level || 'N/A'}<br/>
                <strong>✅ Market Favorable:</strong> ${ai.risk_assessment?.market_favorable ? 'Yes' : 'No'}
            </div>
            
            <div class="ai-summary">
                <strong>💡 Plain English:</strong><br/>
                ${ai.plain_summary || 'Analysis summary not available'}
            </div>
        </div>
        
        <h2 style="margin: 30px 0 15px 0;">📊 Traditional vs AI Analysis</h2>
        
        <div class="comparison-grid">
            <div class="comparison-card">
                <h3>🔍 Traditional Analysis</h3>
                <p><strong>Signal:</strong> ${comparison.traditional.signal}</p>
                <p><strong>Confidence:</strong> ${comparison.traditional.confidence}%</p>
                <p><strong>Entry:</strong> $${comparison.traditional.entry?.toFixed(2) || 'N/A'}</p>
                <p><strong>Stop:</strong> $${comparison.traditional.stop?.toFixed(2) || 'N/A'}</p>
                <p><strong>Target:</strong> $${comparison.traditional.target?.toFixed(2) || 'N/A'}</p>
            </div>
            
            <div class="comparison-card">
                <h3>🤖 AI-Enhanced Analysis</h3>
                <p><strong>Signal:</strong> ${comparison.ai_enhanced.signal}</p>
                <p><strong>Confidence:</strong> ${comparison.ai_enhanced.confidence}%</p>
                <p><strong>Entry:</strong> $${comparison.ai_enhanced.entry?.toFixed(2) || 'N/A'}</p>
                <p><strong>Stop:</strong> $${comparison.ai_enhanced.stop?.toFixed(2) || 'N/A'}</p>
                <p><strong>Target:</strong> $${comparison.ai_enhanced.target?.toFixed(2) || 'N/A'}</p>
            </div>
        </div>
        
        <div style="margin-top: 20px;">
            <p style="color: #718096; font-size: 0.9em;">
                <strong>Model:</strong> ${ai.ai_model} | 
                <strong>Analyzed:</strong> ${new Date(ai.analyzed_at).toLocaleString()} | 
                <strong>Saved to:</strong> ${aiResult.saved_to}
            </p>
        </div>
    `;
}

// Handle file upload
async function handleFileUpload(e) {
    const file = e.target.files[0];
    if (!file) return;
    
    fileName.textContent = file.name;
    
    const reader = new FileReader();
    reader.onload = async function(event) {
        const content = event.target.result;
        const result = await eel.read_symbols_from_csv(content)();
        
        if (result.error) {
            alert('Error reading CSV: ' + result.error);
        } else {
            selectedSymbols = result.symbols;
            displaySymbols();
        }
    };
    reader.readAsText(file);
}

// Use template file
async function useTemplateFile() {
    const result = await eel.read_symbols_from_csv()();
    
    if (result.error) {
        alert('Error reading template: ' + result.error);
    } else {
        selectedSymbols = result.symbols;
        displaySymbols();
    }
}

// Display selected symbols
function displaySymbols() {
    symbolsList.innerHTML = '';
    selectedSymbols.forEach(symbol => {
        const tag = document.createElement('span');
        tag.className = 'symbol-tag';
        tag.textContent = symbol;
        symbolsList.appendChild(tag);
    });
    
    symbolCount.textContent = selectedSymbols.length;
    symbolsDisplay.style.display = 'block';
    analyzeBtn.disabled = false;
}

// Clear symbols
function clearSymbols() {
    selectedSymbols = [];
    symbolsList.innerHTML = '';
    symbolsDisplay.style.display = 'none';
    analyzeBtn.disabled = true;
    fileName.textContent = 'Choose File';
    csvFileInput.value = '';
}

// Handle status updates from Python
function send_status(message) {
    const statusDiv = document.createElement('div');
    statusDiv.className = 'status-message';
    statusDiv.textContent = message;
    statusMessages.insertBefore(statusDiv, statusMessages.firstChild);
    
    // Auto-scroll to top
    statusMessages.scrollTop = 0;
    
    // Keep only last 50 messages
    while (statusMessages.children.length > 50) {
        statusMessages.removeChild(statusMessages.lastChild);
    }
}

// Expose to Python
eel.expose(send_status);

// Clear old data
async function clearOldData() {
    if (!confirm('⚠️ This will delete:\n\n• All downloaded OHLCV data\n• All indicator analysis files\n• All AI analysis files\n\nYou will need to re-download data for next analysis.\n\nContinue?')) {
        return;
    }
    
    clearDataBtn.disabled = true;
    clearDataBtn.textContent = '🗑️ Clearing...';
    
    try {
        const result = await eel.clear_old_data()();
        
        if (result.error) {
            alert(`Error: ${result.error}`);
        } else {
            alert(`✅ Cleared Successfully!\n\n${result.message}`);
            console.log('Deleted:', result.deleted);
        }
    } catch (e) {
        alert(`Error: ${e.toString()}`);
    } finally {
        clearDataBtn.disabled = false;
        clearDataBtn.textContent = '🗑️ Clear Old Data';
    }
}

// Start analysis
async function startAnalysis() {
    if (selectedSymbols.length === 0) {
        alert('Please select symbols first');
        return;
    }

    totalSymbols = selectedSymbols.length;
    currentIndex = 0;
    allResults = [];

    // Show progress, hide results
    progressSection.style.display = 'block';
    summary.style.display = 'none';
    resultsSection.style.display = 'none';
    analyzeBtn.disabled = true;
    
    // Clear status messages
    statusMessages.innerHTML = '';
    send_status('🚀 Starting analysis...');

    // Analyze each symbol
    for (let symbol of selectedSymbols) {
        currentIndex++;
        updateProgress(symbol, null);

        const result = await eel.analyze_symbol(symbol, timeframe.value)();
        
        if (result.error) {
            result.symbol = symbol;
            result.recommendation = 'ERROR';
        }
        
        allResults.push(result);
        updateResults();
    }

    // Done
    progressSection.style.display = 'none';
    summary.style.display = 'grid';
    resultsSection.style.display = 'block';
    analyzeBtn.disabled = false;
}

// Update progress bar
function updateProgress(symbol, result) {
    const percent = (currentIndex / totalSymbols) * 100;
    progressFill.style.width = percent + '%';
    progressText.textContent = `Analyzing ${symbol}... (${currentIndex}/${totalSymbols})`;
}

// Update results display
function updateResults() {
    // Update summary
    const buyCount = allResults.filter(r => r.recommendation === 'BUY').length;
    const sellCount = allResults.filter(r => r.recommendation === 'SELL').length;
    const holdCount = allResults.filter(r => r.recommendation === 'HOLD').length;
    
    document.getElementById('buyCount').textContent = buyCount;
    document.getElementById('sellCount').textContent = sellCount;
    document.getElementById('holdCount').textContent = holdCount;
    document.getElementById('totalCount').textContent = allResults.length;

    // Update table
    resultsBody.innerHTML = '';
    
    allResults.forEach(result => {
        if (result.error) {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${result.symbol}</td>
                <td colspan="7" style="color: #f56565;">${result.error}</td>
            `;
            resultsBody.appendChild(row);
            return;
        }

        const row = document.createElement('tr');
        row.style.cursor = 'pointer';
        row.addEventListener('click', () => showDetail(result));

        row.innerHTML = `
            <td><strong>${result.symbol}</strong></td>
            <td><span class="signal-badge ${result.recommendation}">${result.recommendation}</span></td>
            <td>
                <div class="confidence-bar">
                    <div class="confidence-fill" style="width: ${result.confidence_score}%"></div>
                </div>
                ${result.confidence_score}%
            </td>
            <td>$${result.entry_price}</td>
            <td>${result.stop_loss ? '$' + result.stop_loss : '-'}</td>
            <td>${result.take_profit ? '$' + result.take_profit : '-'}</td>
            <td>${result.risk_reward_ratio ? result.risk_reward_ratio.toFixed(2) : '-'}</td>
            <td style="max-width: 300px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">
                ${result.rationale}
            </td>
        `;

        resultsBody.appendChild(row);
    });
}

// Show detail modal
function showDetail(result) {
    const indicators = result.key_indicators || [];
    const allIndicators = result.all_indicators || {};
    
    let indicatorHTML = '';
    indicators.forEach(ind => {
        indicatorHTML += `
            <div style="display: flex; justify-content: space-between; padding: 10px; background: #f7fafc; margin-bottom: 8px; border-radius: 6px;">
                <strong>${ind.name}</strong>
                <span>${ind.value}</span>
            </div>
        `;
    });
    
    // Build all 52+ indicators table
    let allIndicatorsHTML = '<table style="width: 100%; border-collapse: collapse; font-size: 0.9em;">';
    allIndicatorsHTML += '<thead><tr style="background: #edf2f7;"><th style="padding: 10px; text-align: left;">Indicator Name</th><th style="padding: 10px; text-align: right;">Value</th></tr></thead><tbody>';
    
    // Group indicators by category
    const categories = {
        'TREND INDICATORS': ['EMA_9', 'EMA_20', 'EMA_50', 'EMA_100', 'EMA_200', 'EMA_250', 'SMA_20', 'SMA_50', 'SMA_200', 'MACD', 'MACD_Signal', 'MACD_Histogram', 'ADX', 'DI_Positive', 'DI_Negative'],
        'MOMENTUM INDICATORS': ['RSI', 'Stochastic_K', 'Stochastic_D', 'Williams_R', 'ROC', 'TSI', 'Ultimate_Oscillator', 'Momentum', 'CCI'],
        'VOLATILITY INDICATORS': ['ATR', 'Bollinger_Upper', 'Bollinger_Middle', 'Bollinger_Lower', 'Bollinger_Width', 'Bollinger_Percent'],
        'VOLUME INDICATORS': ['OBV', 'CMF', 'MFI', 'Force_Index', 'EOM', 'VPT', 'NVI', 'VWAP', 'Volume_SMA', 'Volume_Ratio'],
        'PRICE ACTION': ['Price_vs_SMA20_Pct', 'Price_vs_SMA50_Pct', 'Price_vs_SMA200_Pct', 'Close_vs_Open_Pct', 'Parabolic_SAR', 'Aroon_Up', 'Aroon_Down', 'Ichimoku_A', 'Ichimoku_B']
    };
    
    for (let category in categories) {
        allIndicatorsHTML += `<tr><td colspan="2" style="background: #667eea; color: white; padding: 8px; font-weight: bold;">${category}</td></tr>`;
        
        categories[category].forEach(key => {
            if (allIndicators[key] !== undefined && allIndicators[key] !== null) {
                const value = typeof allIndicators[key] === 'number' ? allIndicators[key].toFixed(2) : allIndicators[key];
                allIndicatorsHTML += `
                    <tr style="border-bottom: 1px solid #e2e8f0;">
                        <td style="padding: 8px;">${key.replace(/_/g, ' ')}</td>
                        <td style="padding: 8px; text-align: right; font-weight: 600;">${value}</td>
                    </tr>
                `;
            }
        });
    }
    
    allIndicatorsHTML += '</tbody></table>';

    detailContent.innerHTML = `
        <h2 style="margin-bottom: 20px; color: #2d3748;">${result.symbol} - Detailed Analysis</h2>
        
        <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 20px; margin-bottom: 30px;">
            <div>
                <h3 style="color: #718096; margin-bottom: 10px;">Signal</h3>
                <span class="signal-badge ${result.recommendation}" style="font-size: 1.2em; padding: 10px 20px;">
                    ${result.recommendation}
                </span>
            </div>
            <div>
                <h3 style="color: #718096; margin-bottom: 10px;">Confidence</h3>
                <div style="font-size: 2em; font-weight: bold; color: #2d3748;">
                    ${result.confidence_score}%
                </div>
            </div>
        </div>

        <div style="background: #f7fafc; padding: 20px; border-radius: 8px; margin-bottom: 20px;">
            <h3 style="margin-bottom: 15px; color: #2d3748;">Trade Setup</h3>
            <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 15px;">
                <div>
                    <strong>Entry Price:</strong><br/>
                    <span style="font-size: 1.3em; color: #667eea;">$${result.entry_price}</span>
                </div>
                <div>
                    <strong>Stop Loss:</strong><br/>
                    <span style="font-size: 1.3em; color: #f56565;">
                        ${result.stop_loss ? '$' + result.stop_loss : 'N/A'}
                    </span>
                </div>
                <div>
                    <strong>Take Profit:</strong><br/>
                    <span style="font-size: 1.3em; color: #48bb78;">
                        ${result.take_profit ? '$' + result.take_profit : 'N/A'}
                    </span>
                </div>
                <div>
                    <strong>Risk:Reward:</strong><br/>
                    <span style="font-size: 1.3em; color: #2d3748;">
                        ${result.risk_reward_ratio ? '1:' + result.risk_reward_ratio.toFixed(2) : 'N/A'}
                    </span>
                </div>
            </div>
        </div>

        <div style="margin-bottom: 20px;">
            <h3 style="margin-bottom: 10px; color: #2d3748;">Rationale</h3>
            <p style="background: #fff5f5; padding: 15px; border-left: 4px solid #667eea; border-radius: 4px; line-height: 1.6;">
                ${result.rationale}
            </p>
        </div>

        <div>
            <h3 style="margin-bottom: 10px; color: #2d3748;">Key Indicators</h3>
            ${indicatorHTML}
        </div>

        <div style="margin-top: 30px;">
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 15px; border-radius: 8px; cursor: pointer; color: white; font-weight: 600; display: flex; justify-content: space-between; align-items: center;" onclick="toggleAllIndicators()">
                <span>📊 View All 52+ Technical Indicators</span>
                <span id="toggleIcon">▼</span>
            </div>
            <div id="allIndicatorsPanel" style="display: none; margin-top: 10px; border: 2px solid #667eea; border-radius: 8px; overflow: hidden;">
                ${allIndicatorsHTML}
            </div>
        </div>

        <div style="margin-top: 30px; text-align: center;">
            <button class="btn-ai" onclick='analyzeWithAI("${result.symbol}", ${JSON.stringify(result).replace(/'/g, "\\'")})' ${!aiEnabled ? 'disabled' : ''}>
                🤖 Get AI Analysis
            </button>
            ${!aiEnabled ? '<p style="color: #718096; font-size: 0.9em; margin-top: 10px;">AI analysis disabled - check console for errors</p>' : ''}
        </div>

        <div style="margin-top: 20px; padding: 15px; background: #edf2f7; border-radius: 8px;">
            <small style="color: #718096;">
                <strong>Analysis Time:</strong> ${new Date(result.analysis_time).toLocaleString()}<br/>
                <strong>Raw Score:</strong> ${result.raw_score}<br/>
                <strong>Indicators Saved:</strong> results/indicators/${result.symbol}_indicators.csv
            </small>
        </div>
    `;

    detailModal.style.display = 'block';
}

// Toggle all indicators panel
function toggleAllIndicators() {
    const panel = document.getElementById('allIndicatorsPanel');
    const icon = document.getElementById('toggleIcon');
    
    if (panel.style.display === 'none') {
        panel.style.display = 'block';
        icon.textContent = '▲';
    } else {
        panel.style.display = 'none';
        icon.textContent = '▼';
    }
}

// Export results
async function exportResults() {
    if (allResults.length === 0) {
        alert('No results to export');
        return;
    }

    const result = await eel.export_results(allResults)();
    
    if (result.error) {
        alert('Export failed: ' + result.error);
    } else {
        alert('✅ Results Exported!\n\nMain Results: results/' + result.filename + '\n\nAll 52+ indicators for each symbol saved in:\nresults/indicators/');
    }
}

// Expose function for Python to call
eel.expose(updateProgress);
