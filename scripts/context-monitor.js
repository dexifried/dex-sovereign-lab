#!/usr/bin/env node
// Session context monitor — checks main session token usage and writes a warning if near limit
// Run via cron every 30 min. Does NOT consume context from the main session.

import { execSync } from 'child_process';
import { writeFileSync, existsSync } from 'fs';

const WARNING_THRESHOLD = 150000;
const CRITICAL_THRESHOLD = 175000;
const WARNING_FILE = '/root/.openclaw/workspace/memory/context-warning.json';

try {
  // Use openclaw CLI to get session status without spawning a model call
  const raw = execSync('openclaw status --json 2>/dev/null || echo "{}"', {
    timeout: 10000,
    encoding: 'utf8',
  }).trim();

  let sessionInfo;
  try {
    sessionInfo = JSON.parse(raw);
  } catch {
    // CLI might not support --json, try alternative
    console.log('[context-monitor] Could not parse status output');
    process.exit(0);
  }

  // Extract context token count from the status output
  const contextTokens = sessionInfo?.contextTokens 
    || sessionInfo?.session?.contextTokens 
    || sessionInfo?.tokens?.context
    || 0;

  const totalTokens = sessionInfo?.totalTokens
    || sessionInfo?.session?.totalTokens
    || sessionInfo?.tokens?.total
    || 0;

  if (contextTokens >= WARNING_THRESHOLD) {
    const level = contextTokens >= CRITICAL_THRESHOLD ? 'critical' : 'warning';
    const record = {
      ts: new Date().toISOString(),
      level,
      contextTokens,
      totalTokens,
      threshold: WARNING_THRESHOLD,
      message: level === 'critical'
        ? `⚠️ CRITICAL: Session at ${Math.round(contextTokens/1000)}k/${Math.round(200000/1000)}k tokens (${Math.round(contextTokens/2000)}% of limit). Context reset recommended NOW.`
        : `🟡 WARNING: Session at ${Math.round(contextTokens/1000)}k/${Math.round(200000/1000)}k tokens (${Math.round(contextTokens/2000)}% of limit). Consider context reset soon.`,
    };
    writeFileSync(WARNING_FILE, JSON.stringify(record, null, 2));
    console.log(`[context-monitor] ${record.message}`);
  } else {
    // Clear warning if we're back under threshold
    if (existsSync(WARNING_FILE)) {
      writeFileSync(WARNING_FILE, JSON.stringify({
        ts: new Date().toISOString(),
        level: 'ok',
        contextTokens,
        message: `✅ Context healthy at ${Math.round(contextTokens/1000)}k tokens.`,
      }, null, 2));
    }
    console.log(`[context-monitor] OK: ${contextTokens} tokens`);
  }
} catch (err) {
  console.error('[context-monitor] Error:', err.message);
}
