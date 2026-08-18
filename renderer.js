import * as THREE from 'three';
import { MMDLoader } from 'three/addons/loaders/MMDLoader.js';
import { MMDAnimationHelper } from 'three/addons/animation/MMDAnimationHelper.js';

const container = document.getElementById('canvas-container');
const bubble = document.getElementById('bubble');
const statusDot = document.getElementById('status-dot');
const inputArea = document.getElementById('input-area');
const chatInput = document.getElementById('chat-input');
const sendBtn = document.getElementById('send-btn');

let config = {}, ws = null, wsReconnectTimer = null, bubbleTimer = null;
let scene, camera, renderer, clock, mmdHelper, mmdMesh;
let morphDict = {}, morphLen = 0;
let lipTimer = null, blinkAnimId = null, blinkStartTime = 0;
let clickBounce = 0;

async function loadConfig() {
  if (window.petAPI) config = await window.petAPI.getConfig();
  else config = { serverUrl: 'ws://8.130.43.250:6186/ws/pet', modelBaseUrl: 'http://127.0.0.1:59876', modelName: 'tianyi_model/TID Blue Lolita.Ver.pmx', modelScale: 0.35 };
}

function initThree() {
  const w = container.clientWidth || 400, h = container.clientHeight || 500;
  scene = new THREE.Scene();
  camera = new THREE.PerspectiveCamera(45, w/h, 0.1, 100);
  camera.position.set(0, 3, 12); camera.lookAt(0, 4, 0);
  renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
  renderer.setSize(w, h); renderer.setClearColor(0x000000, 0);
  container.appendChild(renderer.domElement);
  clock = new THREE.Clock();
  scene.add(new THREE.AmbientLight(0xffffff, 0.9));
  const dl = new THREE.DirectionalLight(0xffffff, 1.2);
  dl.position.set(5, 15, 10); scene.add(dl);
  mmdHelper = new MMDAnimationHelper({ afterglow: 2.0, physics: false });
}

function loadModel(url, scale) {
  new MMDLoader().load(url, (mesh) => {
    mmdMesh = mesh;
    mesh.scale.set(scale, scale, scale);
    mesh.position.set(0, -3, 0);
    scene.add(mesh);
    if (mesh.morphTargetDictionary) { morphDict = mesh.morphTargetDictionary; morphLen = mesh.morphTargetInfluences?.length || 0; }
    mmdHelper.add(mesh);
    updateStatus('connected');
    showBubble('老大我来啦', 3000);
    inputArea.classList.add('visible');
    chatInput.focus();
  }, () => {}, () => { showBubble('模型加载失败', 5000); });
}

function setMorph(name, val) {
  if (!mmdMesh?.morphTargetInfluences) return;
  const i = morphDict[name];
  if (i !== undefined) mmdMesh.morphTargetInfluences[i] = Math.max(0, Math.min(1, val));
}
function resetFace() {
  if (!mmdMesh?.morphTargetInfluences) return;
  for (let i = 0; i < morphLen; i++) mmdMesh.morphTargetInfluences[i] = 0;
}

const BLINK_NAMES = ['まばたき', 'ウィンク', 'ウィンク右', 'ウィンク２', 'ウィンク２右'];
function startBlink() {
  function trigger() {
    blinkStartTime = performance.now();
    if (!blinkAnimId) blinkAnimId = requestAnimationFrame(animateBlink);
    setTimeout(trigger, 4000 + Math.random() * 6000);
  }
  trigger();
}
function animateBlink(ts) {
  if (!mmdMesh?.morphTargetInfluences) { blinkAnimId = requestAnimationFrame(animateBlink); return; }
  const e = ts - blinkStartTime;
  let v = 0;
  if (e < 80) v = e / 80;
  else if (e < 120) v = 1;
  else if (e < 260) v = 1 - (e - 120) / 140;
  else { blinkAnimId = null; return; }
  BLINK_NAMES.forEach(n => setMorph(n, v));
  blinkAnimId = requestAnimationFrame(animateBlink);
}

const EXPRESSIONS = {
  idle:{}, smile:{ 'にやり':0.4,'にやり２':0.3,'笑い':0.3,'にっこり':0.3,'口角上げ':0.2 },
  happy:{ 'にやり':0.6,'にやり２':0.4,'笑い':0.5,'にっこり':0.4,'口角上げ':0.3 },
  sad:{ '困る':0.5,'なごみ':0.3,'涙':0.2,'涙2':0.2,'口角下げ':0.3 },
  angry:{ '怒り':0.6,'真面目':0.3,'口角下げ':0.2,'じと目':0.2 },
  surprised:{ 'びっくり':0.5,'あ':0.3,'お':0.3,'はぅ':0.4,'ω':0.3 },
};
function setExpression(name) {
  resetFace();
  const t = EXPRESSIONS[name] || {};
  for (const [k, v] of Object.entries(t)) setMorph(k, v);
}

function startLipSync() {
  if (lipTimer) return;
  let open = false;
  lipTimer = setInterval(() => {
    open = !open;
    const v = open ? 0.15 + Math.random() * 0.3 : 0;
    setMorph('あ', v); setMorph('い', open ? v*0.4 : 0);
    setMorph('う', open ? v*0.3 : 0); setMorph('お', open ? v*0.2 : 0);
    setMorph('え', open ? v*0.15 : 0);
  }, 100 + Math.random() * 50);
}
function stopLipSync() {
  if (lipTimer) { clearInterval(lipTimer); lipTimer = null; }
  ['あ','い','う','え','お'].forEach(n => setMorph(n, 0));
}

function animate() {
  requestAnimationFrame(animate);
  mmdHelper?.update(clock.getDelta());
  renderer.render(scene, camera);
  if (mmdMesh) {
    let y = -3 + Math.sin(Date.now() * 0.0008) * 0.1;
    if (clickBounce > 0.001) { y -= Math.sin(clickBounce * Math.PI) * clickBounce * 0.8; clickBounce *= 0.85; }
    mmdMesh.position.y = y;
  }
}

function connectWS() {
  if (ws?.readyState === WebSocket.OPEN) return;
  try {
    ws = new WebSocket(config.serverUrl);
    ws.onopen = () => { updateStatus('connected'); ws.send(JSON.stringify({type:'ready'})); };
    ws.onmessage = (e) => {
      try {
        const m = JSON.parse(e.data);
        if ((m.type === 'reply' || m.type === 'speak') && m.data.text) {
          showBubble(m.data.text, 8000);
          setExpression(m.data.mood || 'idle');
          if (config.ttsVoiceId && config.llmApiKey) {
            fetch('https://api.ppio.com/v3/minimax-speech-02-hd', {
              method: 'POST',
              headers: { 'Authorization': 'Bearer ' + config.llmApiKey, 'Content-Type': 'application/json' },
              body: JSON.stringify({ text: m.data.text, stream: false, output_format: 'url', voice_setting: { voice_id: config.ttsVoiceId, speed: 1.1 } }),
            }).then(r => r.json()).then(d => { if (d.audio) { const a = new Audio(d.audio); a.onplay = () => startLipSync(); a.onended = () => stopLipSync(); a.onerror = () => stopLipSync(); a.play(); }             }).catch(() => {});
          }
        } else if (m.type === 'agent') {
          window._agentHandler(m.data).then(r => {
            if (ws && ws.readyState === WebSocket.OPEN) {
              ws.send(JSON.stringify({ type: 'agent_result', data: { request_id: m.data.request_id, result: r } }));
            }
          });
        }
      } catch(_) {}
    };
    ws.onclose = () => { ws = null; updateStatus('disconnected'); scheduleReconnect(); };
    ws.onerror = () => updateStatus('disconnected');
  } catch(_) { scheduleReconnect(); }
}
function scheduleReconnect() { if (wsReconnectTimer) return; updateStatus('disconnected'); wsReconnectTimer = setTimeout(() => { wsReconnectTimer = null; connectWS(); }, 5000); }
function sendMessage(text) {
  if (text.startsWith('agent:')) {
    showBubble('Agent启动中...', 2000);
    const task = text.slice(6).trim();
    if (!window._agentHandler) {
      showBubble('Agent未加载!', 5000);
      return;
    }
    window._agentHandler({ action: 'agent_task', task }).then(r => {
      const out = typeof r === 'string' ? r : (r?.error || JSON.stringify(r));
      showBubble(out, 15000);
    }).catch(e => {
      showBubble('Agent错误: ' + e.message, 5000);
    });
    return;
  }
  if (ws?.readyState === WebSocket.OPEN) ws.send(JSON.stringify({type:'chat',data:{text}}));
}
function showBubble(text, dur) { bubble.textContent = text; bubble.classList.add('visible'); if (bubbleTimer) clearTimeout(bubbleTimer); bubbleTimer = setTimeout(() => bubble.classList.remove('visible'), dur || 5000); }
function updateStatus(s) { statusDot.className = s === 'connected' ? 'connected' : 'disconnected'; }

let hideInputTimer = null;
function resetHideTimer() { if (hideInputTimer) clearTimeout(hideInputTimer); if (inputArea.classList.contains('visible')) hideInputTimer = setTimeout(() => inputArea.classList.remove('visible'), 10000); }
document.addEventListener('mouseover', (e) => { if (container.contains(e.target) && !inputArea.classList.contains('visible')) { inputArea.classList.add('visible'); resetHideTimer(); } });
document.body.addEventListener('click', (e) => {
  if (inputArea.contains(e.target)) return;
  if (inputArea.classList.contains('visible')) { inputArea.classList.remove('visible'); }
  else { inputArea.classList.add('visible'); chatInput.focus(); resetHideTimer(); }
  clickBounce = 0.3;
  setTimeout(() => BLINK_NAMES.forEach(n => setMorph(n, 0.6)), 30);
  setTimeout(() => BLINK_NAMES.forEach(n => setMorph(n, 0)), 180);
});
setTimeout(() => { inputArea.classList.add('visible'); resetHideTimer(); }, 1000);
sendBtn.onclick = () => { const t = chatInput.value.trim(); if (t) { sendMessage(t); chatInput.value = ''; resetHideTimer(); } };
chatInput.onkeydown = (e) => { resetHideTimer(); if (e.key === 'Enter') { const t = chatInput.value.trim(); if (t) { sendMessage(t); chatInput.value = ''; } } if (e.key === 'Escape') inputArea.classList.remove('visible'); };
chatInput.addEventListener('input', resetHideTimer);
document.addEventListener('click', (e) => { if (!inputArea.contains(e.target) && !container.contains(e.target)) inputArea.classList.remove('visible'); });
document.addEventListener('keydown', (e) => { if (e.key === 'Escape' && document.body.style.display === 'none') document.body.style.display = ''; });
window.addEventListener('resize', () => { const cw = container.clientWidth, ch = container.clientHeight; if (!cw || !ch) return; const s = renderer.getSize(new THREE.Vector2()); if (Math.abs(s.x - cw) < 1 && Math.abs(s.y - ch) < 1) return; renderer.setSize(cw, ch); camera.aspect = cw / ch; camera.updateProjectionMatrix(); });

let worldInterval = null;
function startWorldPolling() { worldInterval = setInterval(async () => { if (!ws || ws.readyState !== WebSocket.OPEN) return; const n = new Date(); const ts = n.getHours().toString().padStart(2,'0')+':'+n.getMinutes().toString().padStart(2,'0'); let idle = 0; try { idle = await window.petAPI?.getIdleTime() || 0; } catch(_) {} ws.send(JSON.stringify({type:'world_update',data:{time_of_day:ts,idle_seconds:Math.round(idle),active_window:''}})); }, 15000); }

async function start() {
  await loadConfig();
  initThree();
  animate();
  loadModel(config.modelBaseUrl+'/'+config.modelName, config.modelScale||0.35);
  let bc = setInterval(() => { if (mmdMesh && morphDict['まばたき'] !== undefined) { clearInterval(bc); startBlink(); } }, 500);
  setTimeout(() => { connectWS(); startWorldPolling(); }, 2000);
}
if (window.petAPI) window.petAPI.onShutdown(() => { if (ws) { ws.close(); ws = null; } if (worldInterval) clearInterval(worldInterval); });
start();
