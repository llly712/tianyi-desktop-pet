import asyncio
import json
import time
from pathlib import Path

import aiohttp
from aiohttp import web

from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star, register
from astrbot.api import logger, AstrBotConfig
from astrbot.core.message.components import Plain
from astrbot.core.platform.astrbot_message import AstrBotMessage, MessageMember, Group
from astrbot.core.platform.message_type import MessageType
from astrbot.core.platform.platform_metadata import PlatformMetadata
from astrbot.core.platform.platform import Platform

PLUGIN_NAME = "astrbot_plugin_pet_bridge"

AGENT_TOOLS_PROMPT = """
You have access to local PC control tools. When the user asks you to:
- Open a program/file: use agent_run with action "open_file" and path
- Run a terminal command: use agent_run with action "run_command" and command
- List files: use agent_run with action "list_files" and path (optional, defaults to home)
- Read a file: use agent_run with action "read_file" and path
- Write a file: use agent_run with action "write_file" with path and content  
- Get system info: use agent_run with action "system_info"
- List processes: use agent_run with action "list_processes"

The result will be returned to you. Always explain what you're doing before calling the tool.
"""


class PetMessageEvent(AstrMessageEvent):
    def __init__(self, *args, ws_sender=None, **kwargs):
        super().__init__(*args, **kwargs)
        self._ws_sender = ws_sender

    async def send(self, message_chain):
        await super().send(message_chain)
        if not self._ws_sender:
            return
        text = ""
        try:
            chain = message_chain.chain if hasattr(message_chain, 'chain') else []
            for comp in chain:
                if hasattr(comp, 'text') and comp.text:
                    text += str(comp.text)
                elif hasattr(comp, 'chain'):
                    for inner in comp.chain:
                        if hasattr(inner, 'text') and inner.text:
                            text += str(inner.text)
        except Exception:
            pass
        if text.strip():
            try:
                await self._ws_sender({"type": "reply", "data": {"text": text, "mood": "idle"}})
            except Exception:
                pass


class PetPlatform(Platform):
    def __init__(self, config, event_queue):
        super().__init__(config, event_queue)
        self.metadata = PlatformMetadata(name="aiocqhttp", description="Pet", id="aiocqhttp")
    async def run(self): pass
    def meta(self): return self.metadata


@register(PLUGIN_NAME, "community", "桌宠桥接v5——完整管道+Agent电脑控制", "5.0.0")
class PetBridgePlugin(Star):
    def __init__(self, context: Context, config: AstrBotConfig = None):
        super().__init__(context)
        self.config = config or {}
        self.ws_host = self.config.get("ws_host", "0.0.0.0")
        self.ws_port = int(self.config.get("ws_port", 6186))
        self._connections = {}
        self._ws_app = None
        self._runner = None
        self._task = None
        self._platform = None
        self._provider_id = ""
        self._pending_agents = {}
        self._pet_meta = PlatformMetadata(name="desktop_pet", description="Desktop Pet", id="desktop_pet")
        self._pending_agents = {}  # request_id -> asyncio.Event + result

    async def initialize(self):
        self._task = asyncio.create_task(self._start_and_init())
        self._register_agent_tools()

    async def _start_and_init(self):
        self._ws_app = web.Application()
        self._ws_app.router.add_get("/ws/pet", self._handle_ws)
        self._ws_app.router.add_get("/health", self._handle_health)
        self._runner = web.AppRunner(self._ws_app)
        await self._runner.setup()
        try:
            await web.TCPSite(self._runner, self.ws_host, self.ws_port).start()
            logger.info(f"[PetBridge] v5 WS {self.ws_host}:{self.ws_port}")
        except OSError as e:
            logger.error(f"[PetBridge] WS error: {e}")
        try:
            self._provider_id = await self.context.get_current_chat_provider_id("aiocqhttp")
        except Exception:
            self._provider_id = "deepseek/deepseek-v4-flash"

    async def _handle_health(self, request):
        return web.json_response({"status": "ok", "connections": len(self._connections)})

    def _get_platform(self):
        if self._platform is None:
            self._platform = PetPlatform(
                config={"id": "desktop_pet", "enable": True},
                event_queue=self.context.get_event_queue(),
            )
        return self._platform

    async def _handle_ws(self, request):
        ws = web.WebSocketResponse(max_msg_size=256 * 1024, heartbeat=15.0)
        await ws.prepare(request)
        pet_id = f"pet_{int(time.time())}"
        self._connections[pet_id] = ws
        logger.info(f"[PetBridge] connect: {pet_id}")

        async def ws_sender(payload):
            try:
                if not ws.closed:
                    await ws.send_json(payload)
            except Exception:
                pass

        platform = self._get_platform()
        try:
            async for msg in ws:
                if msg.type == aiohttp.WSMsgType.TEXT:
                    await self._dispatch(pet_id, platform, ws_sender, msg.data)
                elif msg.type in (aiohttp.WSMsgType.ERROR, aiohttp.WSMsgType.CLOSE):
                    break
        except Exception as e:
            logger.warning(f"[PetBridge] WS: {e}")
        finally:
            self._connections.pop(pet_id, None)
        return ws

    async def _dispatch(self, pet_id, platform, ws_sender, raw):
        try:
            p = json.loads(raw)
        except json.JSONDecodeError:
            return
        t = p.get("type", "")
        d = p.get("data", {})
        if t == "ping":
            await ws_sender({"type": "pong"})
        elif t == "chat":
            await self._handle_chat(pet_id, platform, ws_sender, d)
        elif t == "agent_result":
            rid = d.get("request_id", "")
            if rid in self._pending_agents:
                self._pending_agents[rid]["result"] = d.get("result", {})
                self._pending_agents[rid]["event"].set()
        elif t == "ready":
            await ws_sender({"type": "ready_ack"})

    async def _handle_chat(self, pet_id, platform, ws_sender, data):
        user_text = str(data.get("text", "")).strip()
        if not user_text or not self._provider_id:
            return

        session_id = f"pet_{pet_id}"
        abm = AstrBotMessage()
        abm.type = MessageType.GROUP_MESSAGE
        abm.self_id = "2854196310"
        abm.session_id = session_id
        abm.message_id = str(int(time.time() * 1000))
        abm.sender = MessageMember(user_id="desktop_pet_user", nickname="老大")
        abm.group = Group(group_id=pet_id)
        abm.message = [Plain(text=user_text)]
        abm.message_str = user_text

        event = PetMessageEvent(
            message_str=user_text, message_obj=abm,
            platform_meta=platform.meta(), session_id=session_id,
            ws_sender=ws_sender,
        )
        event.is_wake = True
        event.is_at_or_wake_command = True
        event.role = "admin"

        # Build system prompt with agent tools
        persona = self._load_persona()
        system_prompt = AGENT_TOOLS_PROMPT
        if persona:
            system_prompt = persona + "\n\n" + AGENT_TOOLS_PROMPT

        try:
            response = await self.context.tool_loop_agent(
                event=event, chat_provider_id=self._provider_id,
                prompt=user_text, system_prompt=system_prompt, tools=None,
            )
            answer = response.completion_text or "唔..."
        except Exception as e:
            logger.error(f"[PetBridge] agent error: {e}")
            answer = f"出错了: {str(e)[:50]}"

        await ws_sender({"type": "reply", "data": {"text": answer, "mood": "idle"}})

    def _load_persona(self):
        skills_dir = Path("/AstrBot/data/skills")
        if not skills_dir.exists():
            return ""
        parts = []
        for d in sorted(skills_dir.iterdir()):
            if d.is_dir():
                md = d / "SKILL.md"
                if md.exists():
                    try:
                        parts.append(md.read_text(encoding="utf-8"))
                    except Exception:
                        pass
        return "\n\n---\n\n".join(parts) if parts else ""

    async def _agent_run(self, event, action, params):
        return await self._send_agent_to_pet(action, params)

    def _register_agent_tools(self):
        tool_mgr = self.context.get_llm_tool_manager()

        async def run_command_handler(command: str = ""):
            return await self._send_agent_to_pet("run_command", [command])
        tool_mgr.add_func(
            name="agent_run_command",
            func_args=[{"type": "string", "name": "command", "description": "Command to execute on user's PC"}],
            desc="Run a shell command on the user's Windows PC and return the output. Use for opening apps, checking system, running scripts.",
            handler=run_command_handler,
        )

        async def read_file_handler(path: str = ""):
            return await self._send_agent_to_pet("read_file", [path])
        tool_mgr.add_func(
            name="agent_read_file",
            func_args=[{"type": "string", "name": "path", "description": "Full path to the file"}],
            desc="Read a file from the user's PC and return its content.",
            handler=read_file_handler,
        )

        async def write_file_handler(path: str = "", content: str = ""):
            return await self._send_agent_to_pet("write_file", [path, content])
        tool_mgr.add_func(
            name="agent_write_file",
            func_args=[
                {"type": "string", "name": "path", "description": "Full file path"},
                {"type": "string", "name": "content", "description": "Content to write"},
            ],
            desc="Write content to a file on the user's PC.",
            handler=write_file_handler,
        )

        async def list_files_handler(path: str = ""):
            return await self._send_agent_to_pet("list_files", [path or None])
        tool_mgr.add_func(
            name="agent_list_files",
            func_args=[{"type": "string", "name": "path", "description": "Directory path, defaults to home"}],
            desc="List files in a directory on the user's PC.",
            handler=list_files_handler,
        )

        async def system_info_handler():
            return await self._send_agent_to_pet("system_info", [])
        tool_mgr.add_func(
            name="agent_system_info",
            func_args=[],
            desc="Get system information about the user's PC (CPU, memory, OS).",
            handler=system_info_handler,
        )

        async def search_code_handler(directory: str = "", pattern: str = ""):
            return await self._send_agent_to_pet("search_code", [directory, pattern])
        tool_mgr.add_func(
            name="agent_search_code",
            func_args=[
                {"type": "string", "name": "directory", "description": "Directory to search in"},
                {"type": "string", "name": "pattern", "description": "Pattern to search for"},
            ],
            desc="Search for a text pattern in files on the user's PC.",
            handler=search_code_handler,
        )

        logger.info(f"[PetBridge] 6 agent tools registered")

    async def broadcast(self, payload):
        for ws in list(self._connections.values()):
            try:
                await ws.send_json(payload)
            except Exception:
                pass

    async def terminate(self):
        for ws in list(self._connections.values()):
            try:
                await ws.close()
            except Exception:
                pass
        self._connections.clear()
        if self._runner:
            await self._runner.cleanup()
        if self._task:
            self._task.cancel()
