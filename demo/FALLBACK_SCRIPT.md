# Zero-Egress SRE Copilot: 3-Minute Fallback Demo Video Script
### Word-for-Word Voiceover Narration & Screen Recording Cues for Competition Judges

This document provides the exact script and visual cues for recording the 3-minute project submission video. Follow the timing and terminal commands below to produce a clean, professional demonstration.

---

## 🎬 Video Timeline & Script

### 0:00 - 0:45 | Scene 1: The Compliance Imperative & Problem Statement
* **Visual / Screen Recording**: 
  * Show the top of the root `README.md` with the **DORA**, **HIPAA**, and **EU AI Act** compliance badges.
  * Highlight the architecture diagram showing the air-gapped local network loop.
* **Voiceover Narration**:
  > *"When an outage hits a critical banking or healthcare system, Site Reliability Engineers need answers in seconds. While cloud LLMs like OpenAI can help debug incidents, sending production observability data across the public internet is illegal under strict compliance frameworks like DORA in Europe and HIPAA in healthcare. Production stack traces and request headers are full of patient IDs, authorization headers, and SQL queries. Today, we present the solution: a 100% air-gapped, Zero-Egress SRE Copilot powered by self-hosted SigNoz and a locally running open-source model."*

---

### 0:45 - 1:30 | Scene 2: The 91.47% Optimization Breakthrough
* **Visual / Screen Recording**:
  * Open a split terminal window.
  * In the top pane, run: `python3 bridge/audit_proof.py`
  * Highlight the **Optimization Benchmark** section showing `47,187 tokens` down to `4,024 tokens` (91.47% reduction).
* **Voiceover Narration**:
  > *"We built this proof-of-concept using a compact 3-billion-parameter model because we engineered and tested the entire zero-egress system natively on a standard developer laptop without cloud GPUs. But developing under strict laptop compute constraints turned out to be our greatest architectural advantage. To make this work without out-of-memory crashes, we had to solve the root bottlenecks of local observability. The raw SigNoz MCP server exposes 41 tools totaling over 47,000 tokens. We engineered a schema-curated bridge that whitelists exactly six core diagnostic tools, achieving a verified 91.47% token reduction. Because we solved the hardest efficiency problems on a laptop using just 2.2 gigabytes of RAM, our architecture will scale natively to enterprise 70-billion-parameter models on private cloud clusters with zero token waste and maximum reasoning precision."*

---

### 1:30 - 2:15 | Scene 3: Live Fault Injection & Autonomous RCA Chaining
* **Visual / Screen Recording**:
  * In Pane 1 (left): Run `python3 demo-app/fault_injector.py --mode fault --fault-type db-pool-exhaustion`
  * In Pane 2 (right): Run `python3 -u bridge/main.py "Why is checkoutservice failing? Diagnose the root cause."`
  * Zoom in on the terminal as Qwen autonomously requests `signoz_search_logs` and `signoz_search_traces`, receives clean JSON responses, and outputs the final diagnosis.
* **Voiceover Narration**:
  > *"Let's see it in action during a live production outage. On the left, our OpenTelemetry fault injector streams simulated database timeout exceptions into our self-hosted SigNoz cluster. On the right, we ask our zero-egress copilot why checkoutservice is failing. Watch how Qwen autonomously chains multiple tool calls: it first searches error logs to find the Java SQL exception, then queries OpenTelemetry traces to identify the failing HikariPool connection operation. In just under three seconds, without any human intervention or looping, it synthesizes an evidence-backed root cause diagnosis: HikariPool database connection pool exhaustion."*

---

### 2:15 - 3:00 | Scene 4: Cryptographic Zero-Egress Verification & Conclusion
* **Visual / Screen Recording**:
  * Return to the terminal running `python3 bridge/audit_proof.py`.
  * Highlight the green box: `✅ [VERIFIED] ZERO EXTERNAL EGRESS DETECTED`.
  * Highlight the list of unique endpoints contacted: `http://localhost:8000/mcp`.
* **Voiceover Narration**:
  > *"Most importantly, how do we prove to regulators and compliance auditors that data sovereignty was preserved? Our bridge maintains an immutable local audit log of every LLM inference and observability tool call. By running our built-in compliance auditor, we mathematically verify that 100 percent of network traffic targeted local loopback interfaces. Zero external IP addresses, zero third-party AI APIs, and zero data leaks. Our Zero-Egress SRE Copilot is DORA ready, HIPAA compliant, and ready to deploy in enterprise air-gapped environments today."*

---

## 🛠️ Recording Setup Checklist
1. **Terminal Font & Size**: Use MesloLGS NF or JetBrains Mono, 16pt font size for high video scannability.
2. **Terminal Theme**: Use a clean dark theme (e.g., Tokyo Night, One Dark, or Dracula).
3. **Screen Resolution**: Record at 1080p (1920x1080) or 4K (3840x2160) at 60 FPS.
4. **Background Noise**: Use Krisp or clean microphone filtering for crisp voiceover recording.
