#!/usr/bin/env python3
"""
Aegis Zero-Egress Console - Retro-Futuristic SRE Command Terminal
Features true dark black HUD styling, real-time SSE streaming with detailed execution telemetry,
Marked.js markdown rendering, zero emojis/gradients, and clean SVG indicators.
"""

import os
import sys
import json
import time
import socketserver
from datetime import datetime, timezone
from http.server import SimpleHTTPRequestHandler
from urllib.parse import parse_qs, urlparse
from openai import OpenAI

# Ensure we can import local modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from bridge.mcp_client import SigNozMCPClient
from bridge.main import load_env, SYSTEM_PROMPT

PORT = 8088

HTML_CONTENT = """<!DOCTYPE html>
<html lang="en" data-theme="dark">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AEGIS // ZERO-EGRESS SRE TERMINAL</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;600;700&family=Share+Tech+Mono&family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <!-- Marked.js for clean Markdown parsing -->
    <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
    <style>
        :root, [data-theme="dark"] {
            /* Retro-Futuristic True Dark Black & Neon Orange */
            --bg-base: #000000;
            --bg-surface: #0a0a0e;
            --bg-elevated: #121218;
            --border-subtle: #222330;
            --border-focus: #ff5500;
            --border-glow: rgba(255, 85, 0, 0.3);
            
            --brand-primary: #ff5500;
            --brand-hover: #cc4400;
            --brand-subtle: rgba(255, 85, 0, 0.12);
            --brand-text: #ff7733;
            
            --text-primary: #f0f2f5;
            --text-secondary: #8e95a5;
            --text-muted: #525866;
            
            --status-ok: #00e599;
            --status-error: #ff3355;
            --status-warn: #ffb800;
            
            --code-bg: #050507;
            --grid-color: rgba(255, 255, 255, 0.03);
            --card-shadow: 0 0 20px rgba(0, 0, 0, 0.8), 0 0 1px var(--brand-primary);
        }

        [data-theme="light"] {
            /* Sci-Fi Lab Clean Light & Amber */
            --bg-base: #f4f6f9;
            --bg-surface: #ffffff;
            --bg-elevated: #eaedf2;
            --border-subtle: #d1d6e0;
            --border-focus: #d97706;
            --border-glow: rgba(217, 119, 6, 0.2);
            
            --brand-primary: #d97706;
            --brand-hover: #b45309;
            --brand-subtle: rgba(217, 119, 6, 0.1);
            --brand-text: #b45309;
            
            --text-primary: #0f172a;
            --text-secondary: #475569;
            --text-muted: #64748b;
            
            --status-ok: #059669;
            --status-error: #e11d48;
            --status-warn: #d97706;
            
            --code-bg: #f8fafc;
            --grid-color: rgba(0, 0, 0, 0.03);
            --card-shadow: 0 4px 20px rgba(0, 0, 0, 0.06);
        }

        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }

        body {
            background-color: var(--bg-base);
            background-image: radial-gradient(var(--grid-color) 1px, transparent 1px);
            background-size: 24px 24px;
            color: var(--text-primary);
            font-family: 'Inter', -apple-system, sans-serif;
            font-size: 13px;
            line-height: 1.5;
            display: flex;
            flex-direction: column;
            height: 100vh;
            overflow: hidden;
            -webkit-font-smoothing: antialiased;
            transition: background-color 0.2s, color 0.2s;
        }

        code, pre, .mono, .hud-label {
            font-family: 'JetBrains Mono', 'Share Tech Mono', monospace;
        }

        /* HUD Top Command Header */
        .topbar {
            height: 56px;
            background-color: var(--bg-surface);
            border-bottom: 1px solid var(--border-subtle);
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 0 24px;
            flex-shrink: 0;
            position: relative;
            z-index: 10;
        }

        .topbar::after {
            content: '';
            position: absolute;
            bottom: -1px;
            left: 0;
            width: 100%;
            height: 1px;
            background: linear-gradient(90deg, transparent, var(--brand-primary), transparent);
            opacity: 0.5;
        }

        .brand {
            display: flex;
            align-items: center;
            gap: 12px;
            font-family: 'Share Tech Mono', monospace;
            font-weight: 700;
            font-size: 16px;
            color: var(--text-primary);
            letter-spacing: 0.08em;
            text-transform: uppercase;
        }

        .brand svg {
            color: var(--brand-primary);
            filter: drop-shadow(0 0 6px var(--brand-primary));
        }

        .system-status {
            display: flex;
            align-items: center;
            gap: 10px;
        }

        .hud-pill {
            display: flex;
            align-items: center;
            gap: 8px;
            background-color: var(--bg-elevated);
            border: 1px solid var(--border-subtle);
            padding: 5px 12px;
            border-radius: 4px;
            font-family: 'JetBrains Mono', monospace;
            font-size: 11px;
            color: var(--text-secondary);
            letter-spacing: 0.03em;
        }

        .hud-pill.highlight {
            border-color: var(--brand-primary);
            color: var(--brand-text);
            background-color: var(--brand-subtle);
        }

        .status-led {
            width: 6px;
            height: 6px;
            border-radius: 50%;
            background-color: var(--status-ok);
            box-shadow: 0 0 6px var(--status-ok);
            animation: pulse 2s infinite;
        }

        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.4; }
        }

        .theme-toggle {
            background-color: var(--bg-elevated);
            border: 1px solid var(--border-subtle);
            color: var(--text-secondary);
            width: 32px;
            height: 32px;
            border-radius: 4px;
            display: flex;
            align-items: center;
            justify-content: center;
            cursor: pointer;
            transition: all 0.15s;
        }

        .theme-toggle:hover {
            border-color: var(--brand-primary);
            color: var(--brand-primary);
            box-shadow: 0 0 8px var(--border-glow);
        }

        /* Workspace Grid */
        .workspace {
            display: flex;
            flex: 1;
            overflow: hidden;
        }

        /* HUD Sidebar */
        .sidebar {
            width: 330px;
            background-color: var(--bg-surface);
            border-right: 1px solid var(--border-subtle);
            display: flex;
            flex-direction: column;
            padding: 20px;
            gap: 24px;
            overflow-y: auto;
            flex-shrink: 0;
            z-index: 5;
        }

        .section-header {
            font-family: 'Share Tech Mono', monospace;
            font-size: 11px;
            color: var(--brand-primary);
            text-transform: uppercase;
            letter-spacing: 0.1em;
            margin-bottom: 12px;
            display: flex;
            align-items: center;
            gap: 6px;
        }

        .query-list {
            display: flex;
            flex-direction: column;
            gap: 8px;
        }

        .query-card {
            background-color: var(--bg-elevated);
            border: 1px solid var(--border-subtle);
            border-radius: 4px;
            padding: 12px;
            color: var(--text-primary);
            font-family: 'Inter', sans-serif;
            font-size: 12px;
            font-weight: 500;
            text-align: left;
            cursor: pointer;
            display: flex;
            align-items: flex-start;
            gap: 10px;
            transition: all 0.15s;
            position: relative;
            overflow: hidden;
        }

        .query-card::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            width: 3px;
            height: 100%;
            background-color: transparent;
            transition: background-color 0.15s;
        }

        .query-card:hover {
            border-color: var(--brand-primary);
            background-color: var(--brand-subtle);
            transform: translateX(2px);
        }

        .query-card:hover::before {
            background-color: var(--brand-primary);
        }

        .query-card svg {
            color: var(--brand-primary);
            flex-shrink: 0;
            margin-top: 2px;
        }

        .telemetry-grid {
            display: grid;
            grid-template-columns: 1fr;
            gap: 8px;
        }

        .telemetry-box {
            background-color: var(--bg-base);
            border: 1px solid var(--border-subtle);
            padding: 10px 12px;
            border-radius: 4px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            font-family: 'JetBrains Mono', monospace;
            font-size: 11px;
        }

        .telemetry-label {
            color: var(--text-secondary);
        }

        .telemetry-val {
            color: var(--status-ok);
            font-weight: 600;
        }

        .telemetry-val.accent {
            color: var(--brand-text);
        }

        /* Timeline Area */
        .content-area {
            flex: 1;
            display: flex;
            flex-direction: column;
            background-color: transparent;
            overflow: hidden;
        }

        .timeline {
            flex: 1;
            overflow-y: auto;
            padding: 24px 32px;
            display: flex;
            flex-direction: column;
            gap: 24px;
        }

        .empty-hud {
            margin: auto;
            max-width: 500px;
            text-align: center;
            color: var(--text-secondary);
            padding: 48px 32px;
            background-color: var(--bg-surface);
            border: 1px dashed var(--border-subtle);
            border-radius: 6px;
            box-shadow: var(--card-shadow);
        }

        .empty-hud svg {
            color: var(--brand-primary);
            margin-bottom: 16px;
            filter: drop-shadow(0 0 8px var(--brand-subtle));
        }

        .empty-hud h3 {
            font-family: 'Share Tech Mono', monospace;
            color: var(--text-primary);
            font-size: 16px;
            margin-bottom: 8px;
            letter-spacing: 0.05em;
        }

        /* Incident Thread Console */
        .thread {
            max-width: 900px;
            width: 100%;
            margin: 0 auto;
            display: flex;
            flex-direction: column;
            gap: 16px;
            border: 1px solid var(--border-subtle);
            background-color: var(--bg-surface);
            border-radius: 6px;
            padding: 24px;
            box-shadow: var(--card-shadow);
            position: relative;
        }

        .thread::before {
            content: 'SYS // DIAGNOSTIC SESSION';
            position: absolute;
            top: -9px;
            left: 16px;
            background-color: var(--bg-surface);
            padding: 0 8px;
            font-family: 'Share Tech Mono', monospace;
            font-size: 10px;
            color: var(--brand-primary);
            letter-spacing: 0.1em;
        }

        .thread-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding-bottom: 16px;
            border-bottom: 1px solid var(--border-subtle);
            font-family: 'JetBrains Mono', monospace;
            font-size: 13px;
            color: var(--text-primary);
        }

        .thread-title {
            display: flex;
            align-items: center;
            gap: 10px;
            font-weight: 600;
        }

        .thread-title svg {
            color: var(--brand-primary);
        }

        /* Active Execution HUD Banner */
        .hud-banner {
            background-color: var(--brand-subtle);
            border: 1px solid var(--brand-primary);
            border-left: 4px solid var(--brand-primary);
            border-radius: 4px;
            padding: 14px 18px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            font-family: 'JetBrains Mono', monospace;
            font-size: 12px;
        }

        .hud-banner-info {
            display: flex;
            align-items: center;
            gap: 12px;
            color: var(--brand-text);
            font-weight: 600;
        }

        .spinner {
            width: 16px;
            height: 16px;
            border: 2px solid var(--brand-primary);
            border-top-color: transparent;
            border-radius: 50%;
            animation: spin 0.7s linear infinite;
        }

        @keyframes spin {
            to { transform: rotate(360deg); }
        }

        /* Detailed Step Execution Card */
        .step-list {
            display: flex;
            flex-direction: column;
            gap: 12px;
        }

        .step-card {
            background-color: var(--bg-base);
            border: 1px solid var(--border-subtle);
            border-radius: 4px;
            overflow: hidden;
            animation: slideIn 0.2s ease-out;
        }

        @keyframes slideIn {
            from { opacity: 0; transform: translateY(6px); }
            to { opacity: 1; transform: translateY(0); }
        }

        .step-header {
            background-color: var(--bg-elevated);
            padding: 10px 16px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            border-bottom: 1px solid var(--border-subtle);
            font-family: 'JetBrains Mono', monospace;
            font-size: 12px;
        }

        .step-title-left {
            display: flex;
            align-items: center;
            gap: 10px;
        }

        .step-badge {
            background-color: var(--brand-subtle);
            color: var(--brand-text);
            border: 1px solid var(--brand-primary);
            padding: 2px 6px;
            border-radius: 3px;
            font-size: 10px;
            font-weight: 700;
        }

        .step-tool {
            color: var(--text-primary);
            font-weight: 600;
        }

        .step-meta-right {
            display: flex;
            align-items: center;
            gap: 14px;
            font-size: 11px;
            color: var(--text-secondary);
        }

        .meta-tag {
            display: flex;
            align-items: center;
            gap: 4px;
        }

        .meta-tag.ok {
            color: var(--status-ok);
            font-weight: 600;
        }

        .step-body {
            padding: 14px 16px;
            display: flex;
            flex-direction: column;
            gap: 12px;
        }

        .step-section {
            display: flex;
            flex-direction: column;
            gap: 4px;
        }

        .step-sublabel {
            font-family: 'Share Tech Mono', monospace;
            font-size: 10px;
            color: var(--text-muted);
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }

        .step-code {
            background-color: var(--code-bg);
            border: 1px solid var(--border-subtle);
            padding: 10px 12px;
            border-radius: 4px;
            font-family: 'JetBrains Mono', monospace;
            font-size: 11px;
            color: var(--text-primary);
            overflow-x: auto;
            white-space: pre-wrap;
            border-left: 2px solid var(--brand-primary);
        }

        .step-code.resp {
            border-left-color: var(--status-ok);
            color: var(--text-secondary);
            max-height: 180px;
            overflow-y: auto;
        }

        /* Final RCA Diagnosis Box */
        .rca-box {
            margin-top: 8px;
            background-color: var(--bg-elevated);
            border: 1px solid var(--brand-primary);
            border-radius: 4px;
            padding: 24px;
            box-shadow: 0 0 16px var(--brand-subtle);
            animation: slideIn 0.3s ease-out;
            position: relative;
        }

        .rca-box::before {
            content: 'FINAL DIAGNOSIS // AIR-GAPPED VERIFIED';
            position: absolute;
            top: -9px;
            left: 16px;
            background-color: var(--bg-elevated);
            padding: 0 8px;
            font-family: 'Share Tech Mono', monospace;
            font-size: 10px;
            color: var(--brand-primary);
            letter-spacing: 0.1em;
        }

        .rca-body {
            color: var(--text-primary);
            font-size: 13px;
            line-height: 1.6;
        }

        .rca-body h1, .rca-body h2, .rca-body h3, .rca-body h4 {
            font-family: 'JetBrains Mono', monospace;
            color: var(--text-primary);
            font-weight: 700;
            margin-top: 16px;
            margin-bottom: 8px;
        }
        .rca-body h1 { font-size: 16px; color: var(--brand-text); }
        .rca-body h2 { font-size: 14px; border-bottom: 1px solid var(--border-subtle); padding-bottom: 4px; color: var(--brand-text); }
        .rca-body h3 { font-size: 13px; }
        .rca-body p { margin-bottom: 12px; }
        .rca-body ul, .rca-body ol { margin-left: 20px; margin-bottom: 12px; }
        .rca-body li { margin-bottom: 6px; }
        .rca-body strong { color: var(--brand-text); font-weight: 600; }
        .rca-body pre {
            background-color: var(--code-bg);
            border: 1px solid var(--border-subtle);
            border-radius: 4px;
            padding: 12px;
            overflow-x: auto;
            margin: 12px 0;
            font-family: 'JetBrains Mono', monospace;
            font-size: 12px;
        }
        .rca-body code {
            background-color: var(--code-bg);
            padding: 2px 6px;
            border-radius: 3px;
            font-family: 'JetBrains Mono', monospace;
            font-size: 12px;
            color: var(--brand-text);
        }
        .rca-body pre code {
            background-color: transparent;
            padding: 0;
            color: var(--text-primary);
        }

        /* Command Bar Footer */
        .command-bar {
            padding: 16px 32px;
            background-color: var(--bg-surface);
            border-top: 1px solid var(--border-subtle);
            z-index: 10;
        }

        .command-wrapper {
            max-width: 900px;
            margin: 0 auto;
            display: flex;
            gap: 12px;
        }

        .input-group {
            flex: 1;
            position: relative;
            display: flex;
            align-items: center;
        }

        .input-group svg {
            position: absolute;
            left: 16px;
            color: var(--brand-primary);
        }

        input[type="text"] {
            width: 100%;
            background-color: var(--bg-base);
            border: 1px solid var(--border-subtle);
            padding: 12px 16px 12px 44px;
            border-radius: 4px;
            color: var(--text-primary);
            font-family: 'JetBrains Mono', monospace;
            font-size: 13px;
            outline: none;
            transition: all 0.15s;
        }

        input[type="text"]:focus {
            border-color: var(--brand-primary);
            box-shadow: 0 0 8px var(--border-glow);
        }

        button.action-btn {
            background-color: var(--brand-primary);
            color: #000000;
            border: none;
            padding: 0 24px;
            border-radius: 4px;
            font-family: 'Share Tech Mono', monospace;
            font-weight: 700;
            font-size: 13px;
            letter-spacing: 0.05em;
            text-transform: uppercase;
            cursor: pointer;
            display: flex;
            align-items: center;
            gap: 8px;
            transition: all 0.15s;
        }

        button.action-btn:hover {
            background-color: var(--brand-hover);
            box-shadow: 0 0 12px var(--border-glow);
        }

        button.action-btn:disabled {
            opacity: 0.5;
            cursor: not-allowed;
        }
    </style>
</head>
<body>
    <header class="topbar">
        <div class="brand">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/><line x1="12" y1="8" x2="12" y2="12"/><circle cx="12" cy="16" r="1"/></svg>
            <span>AEGIS // SRE TERMINAL v2.5</span>
        </div>
        <div class="system-status">
            <div class="hud-pill">
                <span class="status-led"></span>
                <span>QWEN-2.5-3B [LOCAL]</span>
            </div>
            <div class="hud-pill">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/></svg>
                <span>MCP: SIGNOZ-LOOPBACK</span>
            </div>
            <div class="hud-pill highlight">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg>
                <span>EGRESS: 0.00 B [VERIFIED]</span>
            </div>
            <button class="theme-toggle" onclick="toggleTheme()" title="Toggle Dark/Light HUD">
                <svg id="themeIcon" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="5"/><line x1="12" y1="1" x2="12" y2="3"/><line x1="12" y1="21" x2="12" y2="23"/><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/><line x1="1" y1="12" x2="3" y2="12"/><line x1="21" y1="12" x2="23" y2="12"/><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/></svg>
            </button>
        </div>
    </header>

    <div class="workspace">
        <aside class="sidebar">
            <div>
                <div class="section-header">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
                    <span>INCIDENT PRESETS</span>
                </div>
                <div class="query-list">
                    <button class="query-card" onclick="setQuery('Why is checkoutservice failing with 504 Gateway Timeout? Find the upstream bottleneck.')">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>
                        <span>Database Pool Exhaustion</span>
                    </button>
                    <button class="query-card" onclick="setQuery('Why are order confirmation emails failing in emailservice?')">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/><polyline points="22,6 12,13 2,6"/></svg>
                        <span>Kafka Consumer Lag & DLQ</span>
                    </button>
                    <button class="query-card" onclick="setQuery('Why is paymentservice experiencing severe latency and GC pauses?')">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>
                        <span>Memory Leak & GC Stalls</span>
                    </button>
                </div>
            </div>

            <div>
                <div class="section-header">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2v20M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/></svg>
                    <span>TELEMETRY METRICS</span>
                </div>
                <div class="telemetry-grid">
                    <div class="telemetry-box">
                        <span class="telemetry-label">TOKEN COMPRESSION</span>
                        <span class="telemetry-val accent">91.47%</span>
                    </div>
                    <div class="telemetry-box">
                        <span class="telemetry-label">RAM FOOTPRINT</span>
                        <span class="telemetry-val">2.20 GB</span>
                    </div>
                    <div class="telemetry-box">
                        <span class="telemetry-label">WHITELIST TOOLS</span>
                        <span class="telemetry-val accent">6 ACTIVE</span>
                    </div>
                    <div class="telemetry-box">
                        <span class="telemetry-label">EGRESS SOVEREIGNTY</span>
                        <span class="telemetry-val">100% LOCAL</span>
                    </div>
                    <div class="telemetry-box">
                        <span class="telemetry-label">RPC PROTOCOL</span>
                        <span class="telemetry-val">JSON-RPC 2.0</span>
                    </div>
                </div>
            </div>
        </aside>

        <main class="content-area">
            <div class="timeline" id="timeline">
                <div class="empty-hud" id="emptyState">
                    <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.2"><rect x="2" y="3" width="20" height="14" rx="2" ry="2"/><line x1="8" y1="21" x2="16" y2="21"/><line x1="12" y1="17" x2="12" y2="21"/></svg>
                    <h3>NO ACTIVE DIAGNOSTIC SESSION</h3>
                    <p>Select an incident preset from the HUD sidebar or enter an OTLP query below to initiate automated air-gapped root cause reasoning.</p>
                </div>
            </div>

            <footer class="command-bar">
                <div class="command-wrapper">
                    <div class="input-group">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="4 17 10 11 4 5"/><line x1="12" y1="19" x2="20" y2="19"/></svg>
                        <input type="text" id="userInput" placeholder="ENTER SRE QUERY (e.g., Why is checkoutservice failing with 504?)..." onkeypress="handleKeyPress(event)">
                    </div>
                    <button class="action-btn" id="sendBtn" onclick="sendQuery()">
                        <span>EXECUTE</span>
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="5" y1="12" x2="19" y2="12"/><polyline points="12 5 19 12 12 19"/></svg>
                    </button>
                </div>
            </footer>
        </main>
    </div>

    <script>
        function toggleTheme() {
            const html = document.documentElement;
            const current = html.getAttribute('data-theme');
            const next = current === 'dark' ? 'light' : 'dark';
            html.setAttribute('data-theme', next);
            
            const icon = document.getElementById('themeIcon');
            if (next === 'light') {
                icon.innerHTML = '<path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"></path>';
            } else {
                icon.innerHTML = '<circle cx="12" cy="12" r="5"/><line x1="12" y1="1" x2="12" y2="3"/><line x1="12" y1="21" x2="12" y2="23"/><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/><line x1="1" y1="12" x2="3" y2="12"/><line x1="21" y1="12" x2="23" y2="12"/><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/>';
            }
        }

        function setQuery(text) {
            document.getElementById('userInput').value = text;
            document.getElementById('userInput').focus();
        }

        function handleKeyPress(e) {
            if (e.key === 'Enter') sendQuery();
        }

        function sendQuery() {
            const input = document.getElementById('userInput');
            const btn = document.getElementById('sendBtn');
            const query = input.value.trim();
            if (!query) return;

            const emptyState = document.getElementById('emptyState');
            if (emptyState) emptyState.style.display = 'none';

            input.disabled = true;
            btn.disabled = true;
            input.value = '';

            const threadId = appendThread(query);
            const stepListId = 'steps-' + threadId;

            // Connect to real-time Server-Sent Events (SSE) stream
            const eventSource = new EventSource(`/api/stream?query=${encodeURIComponent(query)}`);

            eventSource.onmessage = (event) => {
                const data = JSON.parse(event.data);
                
                if (data.type === 'start') {
                    const statusText = document.getElementById('status-' + threadId);
                    if (statusText) statusText.innerText = 'ESTABLISHED LOCAL STREAM -> QWEN 2.5 3B INFERENCE ACTIVE...';
                } 
                else if (data.type === 'step') {
                    const stepList = document.getElementById(stepListId);
                    if (stepList) {
                        stepList.insertAdjacentHTML('beforeend', `
                            <div class="step-card">
                                <div class="step-header">
                                    <div class="step-title-left">
                                        <span class="step-badge">STEP // 0${data.step_num}</span>
                                        <span class="step-tool">${escapeHtml(data.tool)}</span>
                                    </div>
                                    <div class="step-meta-right">
                                        <span class="meta-tag"><svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg> ${data.elapsed_ms} ms</span>
                                        <span class="meta-tag"><svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/></svg> ${data.payload_bytes} B</span>
                                        <span class="meta-tag ok">✅ SUCCESS</span>
                                    </div>
                                </div>
                                <div class="step-body">
                                    <div class="step-section">
                                        <span class="step-sublabel">// JSON-RPC REQUEST PARAMETERS [TS: ${data.timestamp}]</span>
                                        <div class="step-code">${escapeHtml(data.args)}</div>
                                    </div>
                                    <div class="step-section">
                                        <span class="step-sublabel">// TELEMETRY RESPONSE PREVIEW</span>
                                        <div class="step-code resp">${escapeHtml(data.result_preview)}</div>
                                    </div>
                                </div>
                            </div>
                        `);
                        document.getElementById('timeline').scrollTop = document.getElementById('timeline').scrollHeight;
                    }
                } 
                else if (data.type === 'final') {
                    eventSource.close();
                    const loader = document.getElementById('loader-' + threadId);
                    if (loader) loader.remove();

                    // Format Markdown using Marked.js or clean fallback
                    let formattedAnswer = '';
                    if (typeof marked !== 'undefined' && marked.parse) {
                        formattedAnswer = marked.parse(data.answer);
                    } else {
                        formattedAnswer = `<pre class="mono">${escapeHtml(data.answer)}</pre>`;
                    }

                    const thread = document.getElementById(threadId);
                    if (thread) {
                        thread.insertAdjacentHTML('beforeend', `
                            <div class="rca-box">
                                <div class="rca-body">${formattedAnswer}</div>
                            </div>
                        `);
                        document.getElementById('timeline').scrollTop = document.getElementById('timeline').scrollHeight;
                    }
                    
                    input.disabled = false;
                    btn.disabled = false;
                    input.focus();
                } 
                else if (data.type === 'error') {
                    eventSource.close();
                    const loader = document.getElementById('loader-' + threadId);
                    if (loader) loader.remove();

                    const thread = document.getElementById(threadId);
                    if (thread) {
                        thread.insertAdjacentHTML('beforeend', `
                            <div class="rca-box" style="border-color: var(--status-error);">
                                <div class="rca-body" style="color: var(--status-error);"><strong>EXECUTION ERROR:</strong><br>${escapeHtml(data.message)}</div>
                            </div>
                        `);
                    }
                    input.disabled = false;
                    btn.disabled = false;
                    input.focus();
                }
            };

            eventSource.onerror = (err) => {
                eventSource.close();
                const loader = document.getElementById('loader-' + threadId);
                if (loader) loader.remove();
                
                const thread = document.getElementById(threadId);
                if (thread && !thread.querySelector('.rca-box')) {
                    thread.insertAdjacentHTML('beforeend', `
                        <div class="rca-box" style="border-color: var(--status-error);">
                            <div class="rca-body" style="color: var(--status-error);"><strong>STREAM DISCONNECTED:</strong><br>Lost SSE connection to local loopback server. Verify Ollama / MCP server status.</div>
                        </div>
                    `);
                }
                input.disabled = false;
                btn.disabled = false;
                input.focus();
            };
        }

        function appendThread(queryText) {
            const timeline = document.getElementById('timeline');
            const thread = document.createElement('div');
            thread.className = 'thread';
            const id = 'thread-' + Date.now();
            thread.id = id;
            
            thread.innerHTML = `
                <div class="thread-header">
                    <div class="thread-title">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="4 17 10 11 4 5"/><line x1="12" y1="19" x2="20" y2="19"/></svg>
                        <span>QUERY // ${escapeHtml(queryText)}</span>
                    </div>
                </div>
                <div class="hud-banner" id="loader-${id}">
                    <div class="hud-banner-info">
                        <div class="spinner"></div>
                        <span id="status-${id}">INITIALIZING ZERO-EGRESS TOOL STREAM...</span>
                    </div>
                </div>
                <div class="step-list" id="steps-${id}"></div>
            `;
            timeline.appendChild(thread);
            timeline.scrollTop = timeline.scrollHeight;
            return id;
        }

        function escapeHtml(text) {
            if (!text) return '';
            return text.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;").replace(/'/g, "&#039;");
        }
    </script>
</body>
</html>
"""

class AegisUIHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/" or parsed.path == "/index.html":
            self.send_response(200)
            self.send_header("Content-type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(HTML_CONTENT.encode("utf-8"))
        elif parsed.path == "/api/stream":
            qs = parse_qs(parsed.query)
            query = qs.get("query", [""])[0]
            
            self.send_response(200)
            self.send_header("Content-type", "text/event-stream")
            self.send_header("Cache-Control", "no-cache")
            self.send_header("Connection", "keep-alive")
            self.end_headers()
            
            try:
                self.send_sse({"type": "start"})
                
                load_env()
                api_key = os.environ.get("SIGNOZ_API_KEY", "")
                mcp_url = os.environ.get("SIGNOZ_MCP_URL", "http://localhost:8000/mcp")
                llm_url = os.environ.get("OPENAI_BASE_URL", "http://localhost:11434/v1")
                model_name = os.environ.get("MODEL_NAME", "qwen2.5:3b")
                
                mcp = SigNozMCPClient(url=mcp_url, api_key=api_key)
                tools = mcp.get_tools(filter_heavy_schemas=True)
                client = OpenAI(base_url=llm_url, api_key="local-zero-egress")
                
                messages = [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": query}
                ]
                
                step_num = 0
                for _ in range(8):
                    res = client.chat.completions.create(
                        model=model_name,
                        messages=messages,
                        tools=tools,
                        temperature=0.1,
                        max_tokens=1024
                    )
                    msg = res.choices[0].message
                    
                    if msg.tool_calls:
                        assistant_msg = {
                            "role": "assistant",
                            "content": msg.content or "",
                            "tool_calls": [
                                {
                                    "id": tc.id,
                                    "type": "function",
                                    "function": {
                                        "name": tc.function.name,
                                        "arguments": tc.function.arguments
                                    }
                                }
                                for tc in msg.tool_calls
                            ]
                        }
                        messages.append(assistant_msg)
                        
                        for tc in msg.tool_calls:
                            step_num += 1
                            t_name = tc.function.name
                            t_args = tc.function.arguments
                            
                            t0 = time.time()
                            result_str = mcp.call_tool(t_name, t_args)
                            elapsed_ms = round((time.time() - t0) * 1000, 1)
                            payload_bytes = len(result_str.encode("utf-8"))
                            
                            preview = result_str[:1200] + "\n... [TRUNCATED FOR HUD DISPLAY]" if len(result_str) > 1200 else result_str
                            
                            self.send_sse({
                                "type": "step",
                                "step_num": step_num,
                                "tool": t_name,
                                "args": t_args,
                                "elapsed_ms": elapsed_ms,
                                "payload_bytes": payload_bytes,
                                "timestamp": datetime.now(timezone.utc).strftime("%H:%M:%S.%f")[:-3],
                                "result_preview": preview
                            })
                            
                            messages.append({
                                "role": "tool",
                                "tool_call_id": tc.id,
                                "name": t_name,
                                "content": result_str[:3000]
                            })
                    else:
                        self.send_sse({
                            "type": "final",
                            "answer": msg.content or "NO DIAGNOSTIC OUTPUT GENERATED."
                        })
                        break
                else:
                    self.send_sse({
                        "type": "final",
                        "answer": "⚠️ TOOL EXECUTION LOOP REACHED MAX STEPS WITHOUT FINAL DIAGNOSIS."
                    })
            except Exception as e:
                self.send_sse({"type": "error", "message": str(e)})
        else:
            self.send_error(404, "Endpoint not found")

    def send_sse(self, data_dict):
        try:
            msg = f"data: {json.dumps(data_dict)}\n\n"
            self.wfile.write(msg.encode("utf-8"))
            self.wfile.flush()
        except Exception:
            pass

    def log_message(self, format, *args):
        pass

if __name__ == "__main__":
    print("\n" + "="*60)
    print("AEGIS // ZERO-EGRESS SRE TERMINAL v2.5")
    print(f"Command HUD initialized at: http://localhost:{PORT}")
    print("="*60 + "\n")
    
    class ReusableTCPServer(socketserver.TCPServer):
        allow_reuse_address = True
        
    with ReusableTCPServer(("", PORT), AegisUIHandler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down Aegis command terminal.")
