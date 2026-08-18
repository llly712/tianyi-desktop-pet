const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('petAPI', {
  getConfig: () => ipcRenderer.invoke('get-config'),
  saveConfig: (partial) => ipcRenderer.send('save-config', partial),
  moveWindow: (dx, dy) => ipcRenderer.send('move-window', { dx, dy }),
  getIdleTime: () => ipcRenderer.invoke('get-idle-time'),
  setAlwaysOnTop: (flag) => ipcRenderer.send('set-always-on-top', flag),
  setClickThrough: (flag) => ipcRenderer.send('set-click-through', flag),
  setSize: (w, h) => ipcRenderer.send('set-size', { width: w, height: h }),
  onShutdown: (cb) => ipcRenderer.on('shutdown', () => cb()),
  onClickThroughChanged: (cb) => ipcRenderer.on('click-through-changed', (_e, flag) => cb(flag)),
  // Agent
  runCommand: (cmd, timeout, cwd) => ipcRenderer.invoke('agent-run', { action: 'runCommand', params: [cmd, timeout, cwd] }),
  systemInfo: () => ipcRenderer.invoke('agent-run', { action: 'systemInfo', params: [] }),
  listFiles: (dir) => ipcRenderer.invoke('agent-run', { action: 'listFiles', params: [dir] }),
  readFile: (p) => ipcRenderer.invoke('agent-run', { action: 'readFile', params: [p] }),
  writeFile: (p, c) => ipcRenderer.invoke('agent-run', { action: 'writeFile', params: [p, c] }),
  openFile: (p) => ipcRenderer.invoke('agent-run', { action: 'openFile', params: [p] }),
  listProcesses: () => ipcRenderer.invoke('agent-run', { action: 'listProcesses', params: [] }),
  searchCode: (dir, pattern, types) => ipcRenderer.invoke('agent-run', { action: 'searchCode', params: [dir, pattern, types] }),
  editFile: (p, edits) => ipcRenderer.invoke('agent-run', { action: 'editFile', params: [p, edits] }),
  gitStatus: (dir) => ipcRenderer.invoke('agent-run', { action: 'gitStatus', params: [dir] }),
  gitLog: (dir, n) => ipcRenderer.invoke('agent-run', { action: 'gitLog', params: [dir, n] }),
  gitDiff: (dir) => ipcRenderer.invoke('agent-run', { action: 'gitDiff', params: [dir] }),
  llmCall: (key, base, model, msgs) => ipcRenderer.invoke('agent-run', { action: 'llmCall', params: [key, base, model, msgs] }),
  // Agent loop
  runAgentLoop: (key, base, model, task) => ipcRenderer.invoke('agent-run', { action: 'agent_loop', params: [key, base, model, task] }),
});
