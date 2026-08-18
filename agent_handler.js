// Agent handler - local agent loop + WS bridge
window._agentHandler = async function(cmd) {
  const api = window.petAPI;
  if (!api) return { error: 'no API' };
  try {
    // If it's a full agent task, use the agent loop
    if (cmd.action === 'agent_task') {
      const config = await api.getConfig();
      const key = config.agentApiKey || config.llmApiKey || '';
      const base = config.agentApiBase || 'https://api.deepseek.com/v1';
      const model = config.agentModel || 'deepseek-chat';
      if (!key) return { error: 'No API key configured' };
      return await api.runAgentLoop(key, base, model, cmd.task);
    }

    // Single tool calls
    let result;
    switch (cmd.action) {
      case 'run_command':   result = await api.runCommand(cmd.params?.[0]); break;
      case 'read_file':     result = await api.readFile(cmd.params?.[0]); break;
      case 'write_file':    result = await api.writeFile(cmd.params?.[0], cmd.params?.[1]); break;
      case 'list_files':    result = await api.listFiles(cmd.params?.[0]); break;
      case 'search_code':   result = await api.searchCode(cmd.params?.[0], cmd.params?.[1]); break;
      case 'system_info':   result = await api.systemInfo(); break;
      case 'list_processes':result = await api.listProcesses(); break;
      case 'open_file':     result = await api.openFile(cmd.params?.[0]); break;
      default: result = { error: 'unknown: ' + cmd.action };
    }
    return result;
  } catch(e) {
    return { error: e.message };
  }
};
console.log('[Pet] Agent v3 ready (local loop + tools)');
