#!/usr/bin/env node
/**
 * HTTP to STDIO proxy for Study4Me MCP Server
 * This allows Claude Desktop to connect to our HTTP MCP server
 */

const { spawn } = require('child_process');

// Configuration
const MCP_SERVER_URL = process.env.MCP_SERVER_URL || 'http://127.0.0.1:8001/mcp/';

console.error(`Starting HTTP to STDIO proxy for ${MCP_SERVER_URL}`);

// Use npx to run mcp-remote which handles HTTP to STDIO conversion
const proxy = spawn('npx', [
  'mcp-remote',
  MCP_SERVER_URL
], {
  stdio: 'inherit',
  env: {
    ...process.env,
    OPENAI_API_KEY: process.env.OPENAI_API_KEY
  }
});

proxy.on('close', (code) => {
  console.error(`HTTP proxy exited with code ${code}`);
  process.exit(code);
});

proxy.on('error', (err) => {
  console.error('Failed to start HTTP proxy:', err);
  process.exit(1);
});