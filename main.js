const { app, BrowserWindow, screen, ipcMain, powerMonitor, globalShortcut, Tray, Menu, nativeImage } = require('electron');
const path = require('path');
const fs = require('fs');
const http = require('http');
const agent = require('./agent');

let config = {
  serverUrl: 'ws://8.130.43.250:6186/ws/pet', authToken: '',
  modelName: 'tianyi_model/TID Blue Lolita.Ver.pmx', modelBaseUrl: '', modelScale: 0.35,
  windowWidth: 400, windowHeight: 500,   alwaysOnTop: true,
  clickThrough: false,
  // Agent config
  agentApiKey: '',
  agentApiBase: 'https://api.deepseek.com/v1',
  agentModel: 'deepseek-chat',
  astrobotEnabled: true, llmApiKey: 'sk_eSEuE4z0RYMdKf34QPkK-vo8JvDGQfFCy6-TRXUcsnM',
  llmApiBase: 'https://api.ppio.com/v1', llmModel: 'deepseek/deepseek-v4-flash',
  ttsEnabled: true, ttsSource: 'ppio', ttsVoiceId: 'voice_19a09232-676f-47b9-93bb-10dc47820f2b',
  ttsRate: 1.1, sttEnabled: true,
};

const configPath = path.join(app.getPath('userData'), 'config.json');
try { if (fs.existsSync(configPath)) config = { ...config, ...JSON.parse(fs.readFileSync(configPath, 'utf-8')) }; } catch (e) {}
function saveConfig() { fs.writeFileSync(configPath, JSON.stringify(config, null, 2)); }

const FILE_SERVER_PORT = 59876;
const modelsDir = path.join(__dirname, 'models');
let fileServer = null;
function startFileServer() {
  if (fileServer) return;
  fileServer = http.createServer((req, res) => {
    const p = decodeURIComponent(req.url.split('?')[0]).replace(/^\/+/, '');
    const fp = path.join(modelsDir, path.normalize(p));
    if (!fp.startsWith(modelsDir)) { res.writeHead(403); res.end(); return; }
    const ext = path.extname(fp).toLowerCase();
    const mime = { '.pmx':'application/octet-stream','.vmd':'application/octet-stream','.png':'image/png','.jpg':'image/jpeg','.bmp':'image/bmp','.js':'application/javascript' };
    try { const d = fs.readFileSync(fp); res.writeHead(200, { 'Content-Type': mime[ext]||'application/octet-stream', 'Access-Control-Allow-Origin':'*' }); res.end(d); }
    catch(e) { res.writeHead(404); res.end(); }
  });
  fileServer.listen(FILE_SERVER_PORT, '127.0.0.1');
  config.modelBaseUrl = `http://127.0.0.1:${FILE_SERVER_PORT}`;
}

let mainWindow = null, settingsWindow = null, tray = null;

app.whenReady().then(() => {
  startFileServer();
  createMainWindow();
  createTray();
  globalShortcut.register('CommandOrControl+Shift+P', () => {
    config.clickThrough = !config.clickThrough;
    mainWindow?.setIgnoreMouseEvents(config.clickThrough, { forward: true });
    saveConfig();
  });
});

function createMainWindow() {
  const { width: sw, height: sh } = screen.getPrimaryDisplay().workAreaSize;
  mainWindow = new BrowserWindow({
    width: config.windowWidth, height: config.windowHeight,
    x: Math.max(0, sw - config.windowWidth - 50),
    y: Math.max(0, sh - config.windowHeight - 100),
    transparent: true, frame: false, alwaysOnTop: true,
    hasShadow: false, resizable: true, skipTaskbar: true,
    webPreferences: { preload: path.join(__dirname, 'preload.js'), contextIsolation: true, nodeIntegration: false, webSecurity: false },
  });
  mainWindow.loadFile('index.html');
  mainWindow.webContents.openDevTools({ mode: 'detach' });
  mainWindow.on('closed', () => { mainWindow = null; });
  mainWindow.on('closed', () => { mainWindow = null; });
}

function createTray() {
  try {
    let icon;
    try { icon = nativeImage.createFromPath(path.join(__dirname, 'tray_icon.png')); } catch(e) { icon = null; }
    if (!icon || icon.isEmpty()) icon = nativeImage.createFromDataURL('data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAAAPklEQVQ4T2NkYPj/n4EBBJgYKAQMowYMfAcwjBoAMBgNIINHMQMGjBoAwGg0gAwexYABowYAGA0GkMGjGDBg1ICBBwDHSxQRSqdXhAAAAABJRU5ErkJggg==');
    tray = new Tray(icon);
    tray.setToolTip('Tianyi Pet');
    tray.on('click', () => { if (mainWindow) mainWindow.isVisible() ? mainWindow.hide() : mainWindow.show(); });
    tray.on('right-click', () => {
      tray.popUpContextMenu(Menu.buildFromTemplate([
        { label: '显示/隐藏', click: () => { if (mainWindow) mainWindow.isVisible() ? mainWindow.hide() : mainWindow.show(); } },
        { label: '设置', click: () => openSettings() },
        { type: 'separator' },
        { label: '退出', click: () => app.quit() },
      ]));
  ipcMain.handle('agent-run', async (_e, { action, params }) => {
    try {
      if (action === 'agent_loop') {
        const [apiKey, apiBase, model, task] = params;
        return await agent.agentLoop(apiKey, apiBase, model, task);
      }
      if (!agent.tools[action]) return { success: false, error: `Unknown: ${action}` };
      const result = await agent.tools[action].fn(...(params || []));
      return result;
    } catch (e) {
      return { success: false, error: e.message };
    }
  });
});
  } catch(e) { console.error('Tray failed:', e.message); }
}

function openSettings() {
  if (settingsWindow) { settingsWindow.focus(); return; }
  settingsWindow = new BrowserWindow({
    width: 500, height: 600, resizable: false,
    webPreferences: { nodeIntegration: true, contextIsolation: false },
  });
  settingsWindow.loadFile('settings.html');
  settingsWindow.on('closed', () => { settingsWindow = null; });
}

  ipcMain.handle('get-config', () => {
    // Reload from disk each time
    try {
      if (fs.existsSync(configPath)) {
        const disk = JSON.parse(fs.readFileSync(configPath, 'utf-8'));
        config = { ...config, ...disk };
      }
    } catch (_) {}
    return {
      ...config,
      serverUrl: config.serverUrl,
      modelBaseUrl: config.modelBaseUrl,
      modelName: config.modelName,
      modelScale: config.modelScale,
      agentApiKey: config.agentApiKey,
      agentApiBase: config.agentApiBase,
      agentModel: config.agentModel,
    };
  });
ipcMain.on('save-config', (_e, partial) => { if (partial && typeof partial === 'object') { config = { ...config, ...partial }; saveConfig(); } });
ipcMain.handle('get-idle-time', () => powerMonitor.getSystemIdleTime());
ipcMain.on('open-devtools', () => mainWindow?.webContents.openDevTools({ mode: 'detach' }));

app.on('before-quit', () => { if (fileServer) { fileServer.close(); fileServer = null; } });
