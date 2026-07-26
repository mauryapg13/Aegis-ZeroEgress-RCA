# Zero-Egress SRE Copilot: 3-Minute Hackathon Submission Script
### Exact Structure: About the Project | Tech Stack | Architecture | Demo

This document provides the exact word-for-word voiceover script, screen recording cues, and terminal commands mapped directly to your required 4-part hackathon structure. Keep your total run time between **2 minutes 45 seconds and 3 minutes**.

---

## 🎬 Video Timeline & Script

### 1️⃣ 0:00 - 0:40 | About the Project
* **Visual / Screen Recording**: 
  * Show the top of the root `README.md` highlighting the project title and the **DORA**, **HIPAA**, and **EU AI Act** compliance badges.
  * Show a quick visual of an enterprise outage or split-screen terminal.
* **Voiceover Narration**:
  > *"Hello judges! We are excited to present **Aegis: The Zero-Egress SRE Copilot for SigNoz**. In critical banking, healthcare, and European enterprises, Site Reliability Engineers need instant answers during outages. While cloud-based LLMs like OpenAI can analyze logs, sending production observability data across the public internet violates strict data sovereignty laws like DORA in Europe and HIPAA in healthcare. Production stack traces and request headers are loaded with sensitive customer IDs, authorization tokens, and SQL queries. Aegis solves this by bringing autonomous AI root-cause analysis directly inside your private network perimeter—100% air-gapped with zero data leaks."*

---

### 2️⃣ 0:40 - 1:10 | Tech Stack
* **Visual / Screen Recording**:
  * Highlight the technology logos or list in `README.md`: SigNoz, ClickHouse, OpenTelemetry, Ollama, Python MCP, and SSE streaming.
  * Show a quick glance at the web console at `http://localhost:8088`.
* **Voiceover Narration**:
  > *"Our technology stack is built entirely on open-source, self-hosted infrastructure. For telemetry ingestion and storage, we rely on self-hosted SigNoz powered by OpenTelemetry and ClickHouse columnar databases. For our AI engine, we run Ollama hosting the open-source Qwen 2.5 3-billion-parameter local model. To connect them, we built a custom Python bridge adhering to the Model Context Protocol. Finally, for live interaction, we engineered a lightweight web terminal that uses Server-Sent Events to stream real-time execution telemetry and diagnostic steps directly to the browser without third-party UI dependencies."*

---

### 3️⃣ 1:10 - 1:45 | Architecture (The 91.47% Laptop Breakthrough)
* **Visual / Screen Recording**:
  * Display the system architecture diagram showing the local network loopback interface.
  * In a terminal tab, run: `python3 bridge/audit_proof.py` and zoom in on the **Optimization Benchmark** box showing `47,187 tokens -> 4,024 tokens (91.47% reduction)`.
* **Voiceover Narration**:
  > *"Our core architectural breakthrough was engineering and testing this entire zero-egress system natively on a standard developer laptop using just 2.2 gigabytes of RAM. Developing under strict laptop compute constraints forced us to solve the root bottlenecks of local observability. A raw SigNoz MCP server exposes forty-one tools totaling over forty-seven thousand tokens, which causes small local models to crash or hallucinate. We engineered a schema-curated bridge that whitelists exactly six core diagnostic tools. This slashed prompt overhead by a verified 91.47%. Because we solved the hardest efficiency problems on a developer laptop, our architecture scales natively to enterprise 70-billion-parameter models on private cloud clusters with zero token waste."*

---

### 4️⃣ 1:45 - 3:00 | Live Demo (SRE Console, SSE Telemetry & Anti-Hallucination)
* **Visual / Screen Recording**:
  * **Split Screen**: On the left pane, run `python3 demo-app/fault_injector.py --mode fault --fault-type memory-leak-gc-pause` (or `db-pool-exhaustion`).
  * On the right pane, open **`http://localhost:8088`** showcasing the **Aegis Zero-Egress Command Console**.
  * Click an Incident Preset (e.g., *"Why is paymentservice experiencing severe latency and GC pauses?"*) and click **EXECUTE**.
  * Watch real-time **Server-Sent Events (SSE)** stream execution metrics onto the console with exact millisecond latency, payload byte sizes, and JSON-RPC parameters! Show how Qwen executes our **Mandatory 2-Step Workflow** (querying traces first, then correlating logs) before rendering the formatted Markdown diagnosis.
  * **Anti-Hallucination Test**: Enter a query for a healthy service: `Why is adservice failing?` Notice Qwen inspect ClickHouse and report: `✅ Zero errors or failures detected for adservice in recent telemetry. The service is operating normally.`
  * Return to the `audit_proof.py` terminal and highlight: `✅ [VERIFIED] ZERO EXTERNAL EGRESS DETECTED`.
* **Voiceover Narration**:
  > *"Let's see the demo in action during a live production outage. On the left, our OpenTelemetry fault injector streams simulated memory leaks and fifteen-second Garbage Collection pauses into our self-hosted SigNoz cluster. On the right, we open our interactive Aegis SRE console and execute a query. Notice the real-time Server-Sent Events streaming tool execution metrics directly to the browser. We enforced a mandatory two-step tool chaining workflow: Qwen never jumps to conclusions. It first queries traces to isolate the failing microservice, measures exact loopback latency, and then automatically calls log search to retrieve the exact OutOfMemory exception before rendering an evidence-backed diagnosis in clean Markdown. What if an engineer queries a healthy service like adservice? Instead of hallucinating a false connection, our Anti-Hallucination engine verifies zero errors in ClickHouse and honestly reports that the service is healthy. Finally, running our cryptographic compliance auditor mathematically proves that 100 percent of network traffic targeted local loopback interfaces. Zero external IP addresses, zero third-party AI APIs, and zero data leaks. Aegis is ready for enterprise deployment today."*

---

## 🛠️ Recording Cheat Sheet & Commands

### 1. Pre-Recording Setup (Start Servers in Background Tabs)
```bash
# Terminal Tab 1: Start Bridge & MCP Loopback
python3 bridge/main.py

# Terminal Tab 2: Start Interactive Web Terminal
python3 bridge/web_ui.py
```

### 2. Live Demo Fault Injection Mapping
Run the matching command in your left terminal pane right before clicking the preset in the Web UI:
* 🗄️ **Database Pool Exhaustion** (`checkoutservice` preset):
  ```bash
  python3 demo-app/fault_injector.py --mode fault --fault-type db-pool-exhaustion
  ```
* 📬 **Kafka Consumer Lag & DLQ** (`emailservice` preset):
  ```bash
  python3 demo-app/fault_injector.py --mode fault --fault-type kafka-consumer-lag-deadletter
  ```
* 💾 **Memory Leak & GC Stalls** (`paymentservice` preset):
  ```bash
  python3 demo-app/fault_injector.py --mode fault --fault-type memory-leak-gc-pause
  ```
* 🌱 **Healthy Baseline / Clear Outage**:
  ```bash
  python3 demo-app/fault_injector.py --mode baseline --count 10
  ```

### 3. Verification & Benchmark Command
To display the 91.47% token reduction and Zero-Egress proof:
```bash
python3 bridge/audit_proof.py
```
