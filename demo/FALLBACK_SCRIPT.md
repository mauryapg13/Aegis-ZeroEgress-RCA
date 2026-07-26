# Zero-Egress SRE Copilot: 3-Minute Hackathon Submission Script
### Exact Structure: About the Project | Tech Stack & Arch | Demo | Learning & Growth

This document provides the exact word-for-word voiceover script, screen recording cues, and terminal commands mapped directly to your required 4-part hackathon structure. Keep your total run time between **2 minutes 45 seconds and 3 minutes**.

---

## 🎬 Video Timeline & Script

### 1️⃣ 0:00 - 0:40 | About the Project
* **Visual / Screen Recording**: 
  * Show the top of the root `README.md` highlighting the **DORA**, **HIPAA**, and **EU AI Act** compliance badges.
  * Show a quick visual of an enterprise outage or split-screen terminal.
* **Voiceover Narration**:
  > *"When an outage strikes a critical banking, healthcare, or European enterprise system, Site Reliability Engineers need answers in seconds. While cloud-based LLMs like OpenAI can analyze logs, sending production observability data across the public internet is illegal under strict data sovereignty laws like DORA in Europe and HIPAA in healthcare. Production stack traces and request headers are loaded with sensitive customer IDs, authorization tokens, and SQL queries. To solve this, we built Aegis: a 100% air-gapped, Zero-Egress SRE Copilot that brings autonomous root-cause analysis directly inside the private perimeter."*

---

### 2️⃣ 0:40 - 1:20 | Tech Stack & Architecture
* **Visual / Screen Recording**:
  * Display the system architecture diagram showing the local network loop between **SigNoz (ClickHouse / OpenTelemetry)**, the **Python MCP Bridge**, and local **Ollama (Qwen 2.5 3B)**.
  * In a terminal tab, run: `python3 bridge/audit_proof.py` and highlight the **Optimization Benchmark** box showing `47,187 tokens -> 4,024 tokens (91.47% reduction)`.
* **Voiceover Narration**:
  > *"Our technology stack combines self-hosted SigNoz for OpenTelemetry telemetry, a custom Python Model Context Protocol bridge, Ollama running Qwen 2.5 local models, and our Retro-Futuristic SRE Command Terminal. We engineered and tested this entire system natively on a standard developer laptop using just 2.2 gigabytes of RAM. Why? Because developing under strict laptop compute constraints turned out to be our greatest architectural breakthrough. To prevent memory crashes, we engineered a schema-curated bridge that whitelists exactly six core diagnostic tools out of forty-one. This slashed prompt overhead by a verified 91.47%. Because we solved the hardest efficiency problems on a developer laptop, our architecture will scale natively to enterprise 70-billion-parameter models on private cloud clusters with zero token waste."*

---

### 3️⃣ 1:20 - 2:25 | Live Demo (HUD Console, SSE Telemetry & Anti-Hallucination)
* **Visual / Screen Recording**:
  * **Split Screen**: On the left pane, run `python3 demo-app/fault_injector.py --mode fault --fault-type memory-leak-gc-pause` (or `db-pool-exhaustion`).
  * On the right pane, open **`http://localhost:8088`** showcasing the **Aegis Zero-Egress Command Terminal** in true `#000000` Dark Mode with neon-orange HUD accents. (Briefly click the top-right toggle to show Sci-Fi Lab Light Mode, then switch back).
  * Click an Incident Preset (e.g., *"Why is paymentservice experiencing severe latency and GC pauses?"*) and click **EXECUTE**.
  * Watch real-time **Server-Sent Events (SSE)** stream step cards onto the HUD with exact millisecond latency, payload byte sizes, and JSON-RPC previews! Show how Qwen executes our **Mandatory 2-Step Workflow** (querying traces first, then correlating logs) before rendering the formatted Markdown diagnosis.
  * **Anti-Hallucination Test**: Enter a query for a healthy service: `Why is adservice failing?` Notice Qwen inspect ClickHouse and report: `✅ Zero errors or failures detected for adservice in recent telemetry. The service is operating normally.`
  * Return to the `audit_proof.py` terminal and highlight: `✅ [VERIFIED] ZERO EXTERNAL EGRESS DETECTED`.
* **Voiceover Narration**:
  > *"Let's see the demo in action during a live production outage. On the left, our OpenTelemetry fault injector streams simulated memory leaks and fifteen-second Garbage Collection pauses into our self-hosted SigNoz cluster. On the right, we open our retro-futuristic Aegis command terminal and execute an SRE query. Notice the real-time Server-Sent Events streaming execution telemetry directly to the HUD. We enforced a mandatory two-step tool chaining workflow: Qwen never jumps to conclusions. It first queries traces to isolate the failing microservice, measures exact loopback latency, and then automatically calls log search to retrieve the exact OutOfMemory exception before rendering an evidence-backed diagnosis in clean Markdown. What if an engineer queries a healthy service like adservice? Instead of hallucinating a false connection, our Anti-Hallucination engine verifies zero errors in ClickHouse and honestly reports that the service is healthy. Finally, running our cryptographic compliance auditor mathematically proves that 100 percent of network traffic targeted local loopback interfaces. Zero external IP addresses and zero data leaks."*

---

### 4️⃣ 2:25 - 3:00 | Learning & Growth (Reflections)
* **Visual / Screen Recording**:
  * Show the UI timeline with multiple completed diagnoses or return to the main project banner.
  * Show the team / developer closing slide or GitHub repository link: `https://github.com/mauryapg13/Aegis-ZeroEgress-RCA`.
* **Voiceover Narration**:
  > *"Building Aegis was an incredible learning experience. Our biggest technical insight was that autonomous AI agent performance in observability is not bottlenecked by model parameter size, but by schema noise and tool design. By forcing ourselves to build for strict laptop compute constraints, we learned how to engineer high-precision, low-latency agentic loops that eliminate LLM sycophancy and hallucination. Combining OpenTelemetry, Model Context Protocol, and real-time streaming taught us how to bridge open-source AI with enterprise systems. Aegis is DORA ready, HIPAA compliant, and ready to transform enterprise observability today. Thank you for watching!"*

---

## 🛠️ Recording Cheat Sheet & Commands

### 1. Pre-Recording Setup (Start Servers in Background Tabs)
```bash
# Terminal Tab 1: Start Bridge & MCP Loopback
python3 bridge/main.py

# Terminal Tab 2: Start Retro-Futuristic Web Terminal
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
