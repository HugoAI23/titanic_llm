/**
 * app.js - Lógica interactiva para la aplicación Titanic ML
 * Conexión con API Flask, animaciones Anime.js y diseño Bklit UI.
 */

// Estado global de la aplicación
const AppState = {
  sex: 'female',
  pclass: 1,
  age: 29,
  fare: 60,
  embarked: 'S',
  titulo: 'auto',
  sibsp: 0,
  parch: 0,
  model_type: 'rf',
  realtime: true,
  dashboardLoaded: false,
  isPredicting: false
};

const DEFAULT_FARES_MAP = {
  1: 60,
  2: 15,
  3: 8
};

// ============================================================================
// 1. CONTROL DE PESTAÑAS (TABS) & NAVEGACIÓN
// ============================================================================

function switchTab(tab) {
  const tabs = ['sim', 'dash', 'chat'];
  tabs.forEach(t => {
    const tabEl = document.getElementById(`tab-${t}`);
    const btnEl = document.getElementById(`tab-btn-${t}`);
    if (t === tab) {
      tabEl.classList.remove('hidden');
      btnEl.className = 'px-3.5 py-1.5 rounded-lg font-medium transition-all duration-200 flex items-center space-x-2 bg-brand-600 text-white shadow-sm';
      // Animación suave de entrada con Anime.js
      anime({
        targets: tabEl,
        opacity: [0, 1],
        translateY: [12, 0],
        duration: 300,
        easing: 'easeOutCubic'
      });
    } else {
      tabEl.classList.add('hidden');
      btnEl.className = 'px-3.5 py-1.5 rounded-lg font-medium transition-all duration-200 flex items-center space-x-2 text-slate-400 hover:text-white hover:bg-slate-800';
    }
  });

  if (tab === 'dash' && !AppState.dashboardLoaded) {
    loadDashboardData();
  }

  if (window.lucide) {
    lucide.createIcons();
  }
}

function syncModelSelection(val) {
  AppState.model_type = val;
  runPrediction();
}

// ============================================================================
// 2. CONTROL DEL FORMULARIO Y MEDICIONES (SIMULADOR)
// ============================================================================

function setSex(sex) {
  AppState.sex = sex;
  const btnFemale = document.getElementById('btn-sex-female');
  const btnMale = document.getElementById('btn-sex-male');

  if (sex === 'female') {
    btnFemale.className = 'py-2.5 px-3 rounded-xl border border-pink-500/40 bg-pink-500/15 text-pink-300 font-medium text-xs flex items-center justify-center space-x-2 transition shadow-sm';
    btnMale.className = 'py-2.5 px-3 rounded-xl border border-slate-800 bg-slate-900 text-slate-400 font-medium text-xs flex items-center justify-center space-x-2 transition';
  } else {
    btnFemale.className = 'py-2.5 px-3 rounded-xl border border-slate-800 bg-slate-900 text-slate-400 font-medium text-xs flex items-center justify-center space-x-2 transition';
    btnMale.className = 'py-2.5 px-3 rounded-xl border border-blue-500/40 bg-blue-500/15 text-blue-300 font-medium text-xs flex items-center justify-center space-x-2 transition shadow-sm';
  }

  if (window.lucide) lucide.createIcons();
  onInputChanged();
}

function setPclass(pclass) {
  AppState.pclass = pclass;
  const textIndicator = document.getElementById('class-indicator-text');

  for (let c = 1; c <= 3; c++) {
    const btn = document.getElementById(`btn-pclass-${c}`);
    if (c === pclass) {
      const colorClass = c === 1 ? 'border-emerald-500/40 bg-emerald-500/15 text-emerald-300' : (c === 2 ? 'border-cyan-500/40 bg-cyan-500/15 text-cyan-300' : 'border-amber-500/40 bg-amber-500/15 text-amber-300');
      btn.className = `py-2 rounded-xl border ${colorClass} text-xs font-semibold transition shadow-sm`;
    } else {
      btn.className = 'py-2 rounded-xl border border-slate-800 bg-slate-900 text-slate-400 text-xs font-medium transition';
    }
  }

  const names = {1: '1ª Clase (Alta)', 2: '2ª Clase (Media)', 3: '3ª Clase (Baja)'};
  textIndicator.textContent = names[pclass];

  // Ajustar tarifa automáticamente si el usuario no ha puesto una personalizada extrema
  resetDefaultFare();
}

function resetDefaultFare() {
  const defaultFare = DEFAULT_FARES_MAP[AppState.pclass] || 15;
  document.getElementById('input-fare').value = defaultFare;
  onInputChanged();
}

function onInputChanged() {
  AppState.age = parseFloat(document.getElementById('input-age').value);
  AppState.fare = parseFloat(document.getElementById('input-fare').value);
  AppState.embarked = document.getElementById('input-embarked').value;
  AppState.titulo = document.getElementById('input-title').value;
  AppState.sibsp = parseInt(document.getElementById('input-sibsp').value, 10);
  AppState.parch = parseInt(document.getElementById('input-parch').value, 10);
  AppState.realtime = document.getElementById('realtime-toggle').checked;

  // Actualizar displays numéricos en el DOM
  document.getElementById('age-val-display').textContent = AppState.age;
  document.getElementById('fare-val-display').textContent = `£${AppState.fare.toFixed(2)}`;
  document.getElementById('sibsp-val').textContent = AppState.sibsp;
  document.getElementById('parch-val').textContent = AppState.parch;

  const totalFam = AppState.sibsp + AppState.parch;
  const famBadge = document.getElementById('family-total-badge');
  if (totalFam === 0) {
    famBadge.textContent = 'Viaja Solo (0 fam.)';
    famBadge.className = 'px-2.5 py-0.5 text-[11px] font-mono font-medium rounded-full bg-slate-800 text-slate-300 border border-slate-700';
  } else if (totalFam <= 3) {
    famBadge.textContent = `Familia Pequeña (${totalFam} fam.)`;
    famBadge.className = 'px-2.5 py-0.5 text-[11px] font-mono font-medium rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20';
  } else {
    famBadge.textContent = `Familia Numerosa (${totalFam} fam.)`;
    famBadge.className = 'px-2.5 py-0.5 text-[11px] font-mono font-medium rounded-full bg-rose-500/10 text-rose-400 border border-rose-500/20';
  }

  if (AppState.realtime) {
    debouncePredict();
  }
}

// Control de llamadas concurrentes con debounce
let debounceTimer = null;
function debouncePredict() {
  clearTimeout(debounceTimer);
  debounceTimer = setTimeout(() => {
    runPrediction();
  }, 180);
}

// ============================================================================
// 3. CARGA DE CASOS DE USO PREDEFINIDOS (PRESETS)
// ============================================================================

const PRESETS = {
  rose: {
    sex: 'female',
    pclass: 1,
    age: 17,
    fare: 150,
    embarked: 'C',
    titulo: 'Miss',
    sibsp: 0,
    parch: 1
  },
  jack: {
    sex: 'male',
    pclass: 3,
    age: 20,
    fare: 7.75,
    embarked: 'S',
    titulo: 'Mr',
    sibsp: 0,
    parch: 0
  },
  child_2nd: {
    sex: 'male',
    pclass: 2,
    age: 4,
    fare: 15,
    embarked: 'S',
    titulo: 'Master',
    sibsp: 1,
    parch: 1
  },
  gentleman: {
    sex: 'male',
    pclass: 1,
    age: 48,
    fare: 70,
    embarked: 'C',
    titulo: 'Mr',
    sibsp: 0,
    parch: 0
  },
  family_3rd: {
    sex: 'female',
    pclass: 3,
    age: 32,
    fare: 29,
    embarked: 'S',
    titulo: 'Mrs',
    sibsp: 1,
    parch: 4
  }
};

function loadPreset(key) {
  const p = PRESETS[key];
  if (!p) return;

  setSex(p.sex);
  setPclass(p.pclass);
  document.getElementById('input-age').value = p.age;
  document.getElementById('input-fare').value = p.fare;
  document.getElementById('input-embarked').value = p.embarked;
  document.getElementById('input-title').value = p.titulo;
  document.getElementById('input-sibsp').value = p.sibsp;
  document.getElementById('input-parch').value = p.parch;

  onInputChanged();
  runPrediction();
}

// ============================================================================
// 4. INFERENCIA EN PRODUCCIÓN (CALL API /api/predict)
// ============================================================================

async function runPrediction() {
  if (AppState.isPredicting) return;
  AppState.isPredicting = true;

  const payload = {
    sex: AppState.sex,
    pclass: AppState.pclass,
    age: AppState.age,
    fare: AppState.fare,
    embarked: AppState.embarked,
    titulo: AppState.titulo === 'auto' ? null : AppState.titulo,
    sibsp: AppState.sibsp,
    parch: AppState.parch,
    model_type: AppState.model_type
  };

  try {
    const res = await fetch('/api/predict', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify(payload)
    });

    const json = await res.json();
    if (json.status === 'success') {
      renderPredictionResult(json.data);
    }
  } catch (err) {
    console.error('Error al predecir:', err);
  } finally {
    AppState.isPredicting = false;
  }
}

function renderPredictionResult(data) {
  const primary = data.primary;
  const card = document.getElementById('prediction-card');
  const statusPill = document.getElementById('status-pill');
  const statusIcon = document.getElementById('status-icon');
  const statusText = document.getElementById('status-text');
  const percentEl = document.getElementById('survival-percentage');
  const probSurviveText = document.getElementById('prob-survive-text');
  const probDieText = document.getElementById('prob-die-text');
  const barSurvive = document.getElementById('bar-survive');
  const activeModelBadge = document.getElementById('active-model-badge');
  const confidenceBadge = document.getElementById('confidence-badge');

  activeModelBadge.textContent = primary.model;
  confidenceBadge.textContent = `Confianza ${primary.confidence}`;

  const isSurvived = primary.survived;
  const survPct = primary.probability_survival;
  const diePct = primary.probability_death;

  // Actualizar badge de estado
  if (isSurvived) {
    card.className = 'bklit-card rounded-2xl p-6 relative overflow-hidden transition-all duration-300 border-emerald-500/30 glow-emerald';
    statusPill.className = 'inline-flex items-center space-x-2 px-4 py-1.5 rounded-full text-xs font-bold uppercase tracking-wider bg-emerald-500/15 text-emerald-400 border border-emerald-500/30 pulse-badge mb-3';
    statusIcon.setAttribute('data-lucide', 'check-circle-2');
    statusText.textContent = 'SOBREVIVE';
  } else {
    card.className = 'bklit-card rounded-2xl p-6 relative overflow-hidden transition-all duration-300 border-rose-500/30 glow-rose';
    statusPill.className = 'inline-flex items-center space-x-2 px-4 py-1.5 rounded-full text-xs font-bold uppercase tracking-wider bg-rose-500/15 text-rose-400 border border-rose-500/30 pulse-badge mb-3';
    statusIcon.setAttribute('data-lucide', 'alert-triangle');
    statusText.textContent = 'NO SOBREVIVE';
  }

  // Animación del porcentaje con Anime.js
  const currentVal = parseFloat(percentEl.textContent) || 0;
  const obj = { val: currentVal };
  anime({
    targets: obj,
    val: survPct,
    round: 10,
    duration: 450,
    easing: 'easeOutQuad',
    update: function() {
      percentEl.textContent = obj.val.toFixed(1);
    }
  });

  probSurviveText.textContent = `${survPct.toFixed(1)}%`;
  probDieText.textContent = `${diePct.toFixed(1)}%`;
  barSurvive.style.width = `${Math.max(4, survPct)}%`;

  // Comparativa si se seleccionó 'both'
  const compBlock = document.getElementById('comparison-block');
  if (data.results) {
    compBlock.classList.remove('hidden');
    document.getElementById('cmp-rf-val').textContent = `${data.results.rf.probability_survival}%`;
    document.getElementById('cmp-lr-val').textContent = `${data.results.lr.probability_survival}%`;
  } else {
    compBlock.classList.add('hidden');
  }

  // Renderizar factores determinantes (explicabilidad)
  const factorsCont = document.getElementById('factors-container');
  factorsCont.innerHTML = '';
  (data.factors || []).forEach(f => {
    const isPos = f.impact === 'positive';
    const isNeg = f.impact === 'negative';
    const borderBg = isPos ? 'bg-emerald-500/10 border-emerald-500/20 text-emerald-300' : (isNeg ? 'bg-rose-500/10 border-rose-500/20 text-rose-300' : 'bg-slate-800/80 border-slate-700 text-slate-300');
    const iconName = isPos ? 'plus-circle' : (isNeg ? 'minus-circle' : 'info');
    const iconColor = isPos ? 'text-emerald-400' : (isNeg ? 'text-rose-400' : 'text-slate-400');

    const item = document.createElement('div');
    item.className = `p-2.5 rounded-xl border ${borderBg} text-xs flex items-start space-x-2 transition-all duration-200`;
    item.innerHTML = `
      <i data-lucide="${iconName}" class="w-4 h-4 ${iconColor} mt-0.5 flex-shrink-0"></i>
      <div>
        <span class="font-semibold text-white block">${f.factor}</span>
        <span class="text-[11px] text-slate-400">${f.text}</span>
      </div>
    `;
    factorsCont.appendChild(item);
  });

  if (window.lucide) {
    lucide.createIcons();
  }
}

// ============================================================================
// 5. DASHBOARD DE INSIGHTS (CARGA DE DATOS & ANIMACIONES)
// ============================================================================

async function loadDashboardData() {
  try {
    const res = await fetch('/api/dashboard');
    const json = await res.json();
    if (json.status === 'success') {
      renderDashboard(json.data);
      AppState.dashboardLoaded = true;
    }
  } catch (err) {
    console.error('Error cargando dashboard:', err);
  }
}

function renderDashboard(data) {
  // Animar contadores de KPIs principales con Anime.js
  const animateNum = (id, targetVal) => {
    const el = document.getElementById(id);
    if (!el) return;
    const obj = { val: 0 };
    anime({
      targets: obj,
      val: targetVal,
      round: 1,
      duration: 1000,
      easing: 'easeOutExpo',
      update: () => { el.textContent = Math.round(obj.val); }
    });
  };

  animateNum('kpi-passengers', 891);
  animateNum('kpi-survivors', 342);
  animateNum('kpi-deaths', 549);

  // Tabla: Pasajeros de mayor edad que murieron
  const oldestTable = document.getElementById('oldest-died-table');
  oldestTable.innerHTML = '';
  (data.oldest_died || []).forEach(p => {
    const tr = document.createElement('tr');
    tr.className = 'hover:bg-slate-800/40 transition';
    tr.innerHTML = `
      <td class="py-2.5 font-medium text-white pr-2">${p.name}</td>
      <td class="py-2.5 font-mono text-rose-400 font-bold">${p.age} años</td>
      <td class="py-2.5 text-slate-300">Clase ${p.pclass}</td>
      <td class="py-2.5 font-mono text-slate-400">${p.fare}</td>
    `;
    oldestTable.appendChild(tr);
  });

  // Tabla: Boletos más caros
  const topFaresTable = document.getElementById('top-fares-table');
  topFaresTable.innerHTML = '';
  (data.top_fares || []).forEach(p => {
    const tr = document.createElement('tr');
    tr.className = 'hover:bg-slate-800/40 transition';
    const survBadge = p.survived 
      ? '<span class="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">Sobrevivió</span>'
      : '<span class="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-rose-500/10 text-rose-400 border border-rose-500/20">Falleció</span>';
    tr.innerHTML = `
      <td class="py-2.5 font-medium text-white pr-2">${p.name}</td>
      <td class="py-2.5 font-mono text-amber-400 font-bold">${p.fare}</td>
      <td class="py-2.5 text-slate-300">1ª Clase</td>
      <td class="py-2.5">${survBadge}</td>
    `;
    topFaresTable.appendChild(tr);
  });

  // Tarjetas de Insights
  const insightsGrid = document.getElementById('insights-grid');
  insightsGrid.innerHTML = '';
  (data.insights || []).forEach(ins => {
    const card = document.createElement('div');
    card.className = 'bklit-card rounded-2xl p-5 space-y-2 border-slate-800 hover:border-slate-700 transition';
    card.innerHTML = `
      <div class="flex items-center space-x-2 text-brand-400 text-xs font-semibold">
        <i data-lucide="${ins.icon || 'sparkles'}" class="w-4 h-4"></i>
        <span>${ins.title}</span>
      </div>
      <p class="text-xs text-slate-300 leading-relaxed">${ins.detail}</p>
    `;
    insightsGrid.appendChild(card);
  });

  if (window.lucide) {
    lucide.createIcons();
  }
}

// ============================================================================
// 6. ASISTENTE DE CONSULTAS (CHAT INTELIGENTE)
// ============================================================================

function sendQuickQuery(text) {
  document.getElementById('chat-input').value = text;
  handleChatSubmit(new Event('submit'));
}

async function handleChatSubmit(e) {
  if (e) e.preventDefault();
  const input = document.getElementById('chat-input');
  const query = input.value.trim();
  if (!query) return;

  // Añadir mensaje del usuario
  addChatMessage('user', query);
  input.value = '';

  // Mensaje temporal de pensando
  const loadingId = addChatLoadingIndicator();

  try {
    const res = await fetch('/api/chat', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({ query: query })
    });

    const json = await res.json();
    removeChatLoadingIndicator(loadingId);

    if (json.status === 'success') {
      addChatBotResponse(json.response);
    } else {
      addChatMessage('bot', '❌ Ocurrió un error al procesar tu consulta. Intenta reformularla.');
    }
  } catch (err) {
    removeChatLoadingIndicator(loadingId);
    addChatMessage('bot', '❌ Error de conexión con el servidor.');
  }
}

function addChatMessage(sender, text) {
  const container = document.getElementById('chat-messages');
  const div = document.createElement('div');
  
  if (sender === 'user') {
    div.className = 'flex items-start justify-end space-x-2';
    div.innerHTML = `
      <div class="bg-brand-600 text-white p-3.5 rounded-2xl rounded-tr-sm max-w-lg text-xs sm:text-sm shadow-md">
        ${escapeHtml(text)}
      </div>
      <div class="w-7 h-7 rounded-lg bg-slate-800 border border-slate-700 text-slate-300 flex items-center justify-center flex-shrink-0 text-xs mt-0.5">
        <i data-lucide="user" class="w-3.5 h-3.5"></i>
      </div>
    `;
  } else {
    div.className = 'flex items-start space-x-3';
    div.innerHTML = `
      <div class="w-8 h-8 rounded-lg bg-brand-500/20 text-brand-400 flex items-center justify-center flex-shrink-0 mt-0.5">
        <i data-lucide="bot" class="w-4 h-4"></i>
      </div>
      <div class="bklit-card-subtle p-4 rounded-2xl max-w-2xl text-xs sm:text-sm text-slate-200">
        ${formatMarkdownText(text)}
      </div>
    `;
  }

  container.appendChild(div);
  container.scrollTop = container.scrollHeight;
  if (window.lucide) lucide.createIcons();
}

function addChatBotResponse(resp) {
  const container = document.getElementById('chat-messages');
  const div = document.createElement('div');
  div.className = 'flex items-start space-x-3';

  // Highlights badges
  let highlightsHtml = '';
  if (resp.highlights && resp.highlights.length > 0) {
    highlightsHtml = '<div class="flex flex-wrap gap-2 pt-2 border-t border-slate-800/80 mt-3">';
    resp.highlights.forEach(h => {
      highlightsHtml += `
        <div class="px-2.5 py-1 rounded-lg bg-slate-900 border border-slate-800 text-[11px]">
          <span class="text-slate-400 block">${h.label}</span>
          <span class="text-brand-300 font-mono font-bold">${h.value}</span>
        </div>
      `;
    });
    highlightsHtml += '</div>';
  }

  // Suggestions chips
  let suggestionsHtml = '';
  if (resp.suggestions && resp.suggestions.length > 0) {
    suggestionsHtml = '<div class="pt-3 flex flex-wrap gap-1.5 items-center">';
    suggestionsHtml += '<span class="text-[10px] text-slate-400 block w-full">Preguntas relacionadas:</span>';
    resp.suggestions.forEach(s => {
      suggestionsHtml += `
        <button onclick="sendQuickQuery('${escapeHtml(s)}')" class="px-2.5 py-1 text-[11px] rounded-lg bg-slate-800/80 hover:bg-slate-700 text-slate-300 hover:text-white border border-slate-700/60 transition">
          ${escapeHtml(s)}
        </button>
      `;
    });
    suggestionsHtml += '</div>';
  }

  div.innerHTML = `
    <div class="w-8 h-8 rounded-lg bg-brand-500/20 text-brand-400 flex items-center justify-center flex-shrink-0 mt-0.5">
      <i data-lucide="bot" class="w-4 h-4"></i>
    </div>
    <div class="bklit-card-subtle p-4 rounded-2xl max-w-2xl text-xs sm:text-sm text-slate-200 space-y-2">
      <div class="text-xs font-semibold text-brand-400 flex items-center space-x-1.5">
        <i data-lucide="sparkles" class="w-3.5 h-3.5"></i>
        <span>${escapeHtml(resp.title || 'Respuesta')}</span>
      </div>
      <div>${formatMarkdownText(resp.text)}</div>
      ${highlightsHtml}
      ${suggestionsHtml}
    </div>
  `;

  container.appendChild(div);
  container.scrollTop = container.scrollHeight;
  if (window.lucide) lucide.createIcons();
}

let loadingCounter = 0;
function addChatLoadingIndicator() {
  loadingCounter++;
  const id = `chat-loading-${loadingCounter}`;
  const container = document.getElementById('chat-messages');
  const div = document.createElement('div');
  div.id = id;
  div.className = 'flex items-start space-x-3';
  div.innerHTML = `
    <div class="w-8 h-8 rounded-lg bg-brand-500/20 text-brand-400 flex items-center justify-center flex-shrink-0 mt-0.5">
      <i data-lucide="bot" class="w-4 h-4"></i>
    </div>
    <div class="bklit-card-subtle px-4 py-3 rounded-2xl text-xs text-slate-400 flex items-center space-x-2">
      <span class="w-2 h-2 rounded-full bg-brand-400 animate-pulse"></span>
      <span>Consultando datos históricos...</span>
    </div>
  `;
  container.appendChild(div);
  container.scrollTop = container.scrollHeight;
  if (window.lucide) lucide.createIcons();
  return id;
}

function removeChatLoadingIndicator(id) {
  const el = document.getElementById(id);
  if (el) el.remove();
}

function clearChat() {
  const container = document.getElementById('chat-messages');
  container.innerHTML = `
    <div class="flex items-start space-x-3">
      <div class="w-8 h-8 rounded-lg bg-brand-500/20 text-brand-400 flex items-center justify-center flex-shrink-0 mt-0.5">
        <i data-lucide="bot" class="w-4 h-4"></i>
      </div>
      <div class="bklit-card-subtle p-4 rounded-2xl max-w-2xl text-xs sm:text-sm text-slate-200 space-y-2">
        <p>Chat reiniciado. Puedes consultar libremente sobre cualquier aspecto del Titanic.</p>
      </div>
    </div>
  `;
  if (window.lucide) lucide.createIcons();
}

// ============================================================================
// 7. UTILIDADES DE FORMATEO Y SANITIZACIÓN
// ============================================================================

function escapeHtml(str) {
  if (!str) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}

function formatMarkdownText(text) {
  if (!text) return '';
  // Convertir **bold**, *italic*, bullet points y saltos de línea
  let html = text
    .replace(/\*\*(.*?)\*\*/g, '<strong class="text-white font-semibold">$1</strong>')
    .replace(/\*(.*?)\*/g, '<em class="text-slate-300">$1</em>')
    .replace(/•\s*(.*?)(?=(\n|$))/g, '<li class="ml-4 list-disc text-slate-300 my-0.5">$1</li>')
    .replace(/\n\n/g, '<br/><br/>')
    .replace(/\n/g, '<br/>');
  return html;
}

// ============================================================================
// 8. INICIALIZACIÓN AL CARGAR LA PÁGINA
// ============================================================================

document.addEventListener('DOMContentLoaded', () => {
  // Configurar estado inicial
  setSex('female');
  setPclass(1);
  onInputChanged();
  runPrediction();
});
