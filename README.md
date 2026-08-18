# 洛天依桌宠 (Tianyi Desktop Pet)

一个「活在电脑里」的桌面 AI 助手。基于 Electron + Three.js，支持 Live2D/PMX 模型渲染、语音对话、本地 Agent 控制电脑、AstrBot 云端接入。

## 功能

- **3D 角色模型** - 支持 PMX (MMD) 模型，自动加载贴图与材质
- **表情动画** - 眨眼、口型同步、多种表情（开心/难过/生气/惊讶等）
- **语音对话** - 内置 TTS 朗读回复，支持唇型同步
- **本地 Agent** - 通过 LLM function calling 控制电脑：运行命令、读写文件、搜索代码、打开应用
- **AstrBot 接入** - 可选连接云端 AstrBot，复用完整人格、工具、记忆
- **窗口交互** - 任意拖动、右键菜单、穿透模式、自定义缩放

## 快速开始

### 开发运行

需要 Node.js 18+。

```bash
npm install
npx electron .
```

模型文件放在 `models/` 目录下（PMX/VMD 格式）。

### 打包分发

```bash
npm run build        # 生成 win-unpacked
npm run build:dir    # 仅打包目录
```

## 配置

配置文件在 `%APPDATA%\tianyi-desktop-pet\config.json`：

```json
{
  "serverUrl": "ws://你的服务器:6186/ws/pet",
  "modelName": "models/模型.pmx",
  "modelScale": 0.4,
  "agentApiKey": "sk-你的本地Agent密钥",
  "agentApiBase": "https://api.deepseek.com/v1",
  "agentModel": "deepseek-chat",
  "ttsEnabled": true
}
```

### 本地 Agent 模式

在桌宠输入框输入 `agent: 你的任务`，即可让本地 LLM 通过 function calling 控制电脑。

支持的操作：

- `agent: 帮我打开记事本`
- `agent: 看看桌面有什么文件`
- `agent: 搜索 main.py 里的 bug`
- `agent: 我的电脑配置是什么`

Agent 使用 OpenAI 兼容 API，可接入任意服务（DeepSeek、Ollama、PPIO 等）。

### AstrBot 模式

默认连接云端 AstrBot，复用完整的洛天依人格（SKILL）、米家工具、记忆系统。

## 项目结构

```
desktop_pet/          # Electron 桌面端
  main.js             # 主进程（窗口、Agent、文件服务）
  preload.js          # IPC 桥接
  renderer.js         # 渲染进程（3D模型、动画、对话UI）
  index.html          # 界面
  agent.js            # 本地 Agent 引擎（function calling）
  agent_handler.js    # Agent 桥接
  models/             # PMX/VMD 模型目录

astrbot_plugin_pet_bridge/  # AstrBot 服务端插件（可选）
  main.py             # WebSocket 桥接 + 完整管道接入
```

## 技术栈

- Electron 34
- Three.js (PMX/MMD 渲染)
- Web Speech API (TTS/STT)
- OpenAI 兼容 API (本地 Agent)

## 开源协议

MIT License

## 致谢

- 模型：TDA式改变洛天依-TID Blue Lolita.Ver by 庆先生
