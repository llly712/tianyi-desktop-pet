// Local Agent Engine - function calling loop
const { exec } = require('child_process');
const fs = require('fs');
const path = require('path');
const os = require('os');
const https = require('https');
const http = require('http');

// ═══ System Tools ═══
const tools = {
  run_command: { fn: (c) => new Promise(r => exec(c, {timeout:30000,maxBuffer:2*1024*1024}, (e,o,s)=>r({stdout:o?.slice(-5000)||'',stderr:s?.slice(-1000)||'',error:e?.message}))), schema: {command:'string'} },
  read_file: { fn: (p) => { try { return {content:fs.readFileSync(p,'utf-8').slice(0,8000),path:p}; } catch(e) { return {error:e.message}; } }, schema: {path:'string'} },
  write_file: { fn: (p,c) => { try { const d=path.dirname(p); if(!fs.existsSync(d))fs.mkdirSync(d,{recursive:true}); fs.writeFileSync(p,c,'utf-8'); return {success:true,path:p}; } catch(e) { return {error:e.message}; } }, schema: {path:'string',content:'string'} },
  list_files: { fn: (p) => { try { const items=fs.readdirSync(p||os.homedir()).slice(0,50).map(n=>({name:n,type:fs.statSync(path.join(p||os.homedir(),n)).isDirectory()?'dir':'file'})); return {items,dir:p||os.homedir()}; } catch(e) { return {error:e.message}; } }, schema: {path:'string'} },
  search_code: { fn: (d,p) => new Promise(r => exec(`rg --no-heading -n "${p}" "${d}" 2>nul || findstr /s /n /i "${p}" "${d}\\*" 2>nul`,{timeout:15000},(e,o)=>r({matches:(o||'').split('\n').filter(l=>l.trim()).slice(0,30)}))), schema: {directory:'string',pattern:'string'} },
  system_info: { fn: () => ({platform:os.platform(),arch:os.arch(),cpus:os.cpus().length,hostname:os.hostname(),memory:{total:Math.round(os.totalmem()/1024/1024/1024)+'GB',free:Math.round(os.freemem()/1024/1024)+'MB'},homedir:os.homedir(),uptime:Math.round(os.uptime()/3600)+'h'}), schema: {} },
  open_file: { fn: (p) => new Promise(r => exec(`start "" "${p}"`,{shell:'powershell.exe'},()=>r({opened:p}))), schema: {path:'string'} },
  list_processes: { fn: () => new Promise(r => exec('tasklist /FO CSV /NH 2>nul',{timeout:10000},(e,o)=>r({processes:(o||'').trim().split('\n').slice(0,20).map(l=>{const p=l.replace(/"/g,'').split(',');return{name:p[0]?.trim(),pid:p[1]?.trim()}})}))), schema: {} },
};

// ═══ LLM Call ═══
function llmCall(apiKey, apiBase, model, messages) {
  return new Promise((resolve) => {
    const url = new URL(apiBase.replace(/\/+$/,'') + '/chat/completions');
    const transport = url.protocol === 'https:' ? https : http;
    const body = JSON.stringify({ model, messages, max_tokens: 2048, temperature: 0.7 });
    const req = transport.request({
      hostname: url.hostname, port: url.port || (url.protocol==='https:'?443:80),
      path: url.pathname, method: 'POST',
      headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${apiKey}` },
      timeout: 120000,
    }, (res) => { let d=''; res.on('data',c=>d+=c); res.on('end',()=>{ try { resolve(JSON.parse(d)); } catch(_) { resolve({raw:d}); } }); });
    req.on('error', e => resolve({ error: e.message }));
    req.on('timeout', () => { req.destroy(); resolve({ error: 'timeout' }); });
    req.write(body); req.end();
  });
}

// ═══ Agent Loop ═══
async function agentLoop(apiKey, apiBase, model, task, onProgress) {
  const toolDefs = Object.entries(tools).map(([name, t]) => ({
    type: 'function',
    function: {
      name,
      description: `Tool: ${name}`,
      parameters: { type: 'object', properties: Object.fromEntries(Object.entries(t.schema).map(([k,v])=>[k,{type:v,description:k}])), required: Object.keys(t.schema) },
    }
  }));

  const messages = [
    { role: 'system', content: `You are a PC control agent running on Windows. You can use tools to control the computer, read/write files, run commands, and get system info. Always explain what you're doing before using a tool. When the task is complete, give a clear summary. Work step by step.` },
    { role: 'user', content: task },
  ];

  let steps = 0;
  while (steps < 15) {
    steps++;
    const resp = await llmCall(apiKey, apiBase, model, messages);
    if (resp.error) return `Agent error: ${resp.error}`;

    const msg = resp.choices?.[0]?.message;
    if (!msg) return `No response from LLM`;

    messages.push(msg);

    if (msg.content) {
      onProgress?.({ type: 'thinking', text: msg.content });
    }

    if (msg.tool_calls?.length) {
      for (const tc of msg.tool_calls) {
        const name = tc.function.name;
        const tool = tools[name];
        if (!tool) {
          messages.push({ role: 'tool', tool_call_id: tc.id, content: `Unknown tool: ${name}` });
          continue;
        }
        try {
          const args = JSON.parse(tc.function.arguments || '{}');
          onProgress?.({ type: 'tool', tool: name, args });
          const result = await tool.fn(...Object.values(args));
          const resultStr = JSON.stringify(result);
          messages.push({ role: 'tool', tool_call_id: tc.id, content: resultStr });
          onProgress?.({ type: 'result', tool: name, result: resultStr.slice(0, 200) });
        } catch (e) {
          messages.push({ role: 'tool', tool_call_id: tc.id, content: `Error: ${e.message}` });
        }
      }
    } else if (msg.content) {
      // Final answer
      return msg.content;
    }
  }
  return 'Agent reached max steps without completing the task.';
}

module.exports = { agentLoop, llmCall, tools };
