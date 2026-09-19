# 洛天依桌宠 (Tianyi Desktop Pet)

一个「活在电脑里」的桌面 AI 助手。基于 Python + OpenGL，支持 PMX (MMD) 模型渲染、语音合成、本地 Agent 控制电脑、AstrBot 云端接入。

## 功能

- **3D 角色模型** - 支持 PMX (MMD) 模型，自动加载贴图与材质，透明窗口展示
- **表情与动画** - 眨眼、呼吸、口型同步、20 多种表情（开心/生气/惊讶/害羞等）
- **语音合成** - 
- **本地 Agent** - 套壳 Open Interpreter
- **AstrBot 接入** - 可选连接云端 AstrBot，复用完整人格、工具、记忆
- **桌面窗口** - 透明无边框、置顶、任意拖动、点击穿透（Ctrl+Shift+P）

## 截图



## 环境

- Windows 10/11
- Python 3.12
- 一块支持 OpenGL 的显卡（兼容模式 profile）

## 快速开始

```bash
py -3.12 -m venv .venv
.venv\Scripts\pip install -r requirements.txt

# 把 PMX 模型放到 models/ 下，然后在 config.json 里设置 model_path
.venv\Scripts\python main.py
```

### Agent 环境（可选）

本地 Agent 依赖 Open Interpreter，单独装在隔离环境里，避免污染渲染依赖：

```bash
py -3.12 -m venv .venv-agent
.venv-agent\Scripts\pip install -r requirements-agent.txt
.venv-agent\Scripts\pip install --no-deps open-interpreter==0.4.3
.venv-agent\Scripts\pip install "setuptools<81"
```

## 配置

配置保存在 `config.json`（不提交，含密钥）。主要字段：

```json
{
  "model_path": "models/你的模型.pmx",
  "ws_url": "ws://你的服务器:6186/ws/pet",

  "tts_provider": "ppio",
  "ppio_api_key": "sk-你的PPIO密钥",
  "tts_voice_id": "voice_复刻音色ID",

  "agent_enabled": true,
  "agent_prefix": "agent:",
  "agent_model": "deepseek/deepseek-flash",
  "agent_api_key": "sk-你的DeepSeek密钥",
  "agent_api_base": "https://api.deepseek.com/v1"
}
```

## 使用

- 在底部输入框聊天 -> 走 AstrBot 云端管道
- 输入 `agent: 你的任务` -> 让本地 Agent 控制电脑
- 右键菜单 -> 表情 / 缩放 / 半身全身 / 穿透 / 置顶 / 设置
- `Ctrl+Shift+P` -> 切换鼠标穿透

## 项目结构

```
app/                          # 应用主体
  main.py                     # 入口与主循环
  renderer.py                 # PMX 渲染、相机、表情/口型驱动
  morph.py                    # morph(表情/口型) 控制器
  expressions.py              # 表情 -> morph 名称映射
  window.py                   # GLFW 透明窗口 + imgui
  ui.py                       # imgui 界面 (66ccff 主题)
  net.py                      # AstrBot WebSocket 客户端
  voice.py                    # PPIO / edge TTS
  agent.py                    # 本地 Agent 子进程桥
  config.py                   # 配置
tools/                        # 调试与构建脚本
  patch_mmdpy.py              # 为 vendored mmdpy 打补丁
vendor/                       # mmdpy (MMD/PMX 渲染库, 已打补丁)
models/                       # PMX/VMD 模型目录 (不入库)
astrbot_plugin_pet_bridge/    # AstrBot 服务端插件 (可选)
```

## 技术栈

- Python 3.12
- mmdpy + PyOpenGL（PMX/MMD 渲染）
- GLFW + pyimgui（窗口与界面）
- WebSocket（AstrBot 接入）

## 开源协议

MIT License

## 致谢

- 模型：TDA式改变洛天依-TID Blue Lolita.Ver by 庆先生
- 渲染库：mmdpy (MIT)
