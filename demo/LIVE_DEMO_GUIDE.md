# Live Interactive Demo Guide & Presenter Cheat Sheet
### Step-by-Step Execution Guide for Live Stakeholder Meetings & Judging Sessions

When presenting the Zero-Egress SRE Copilot live, follow this structured presentation flow to guarantee zero hiccups, rapid execution, and maximum impact on compliance and technical sophistication.

---

## 📋 PRE-DEMO CHECKLIST (Execute 10 Minutes Before Presentation)

1. **Verify Docker Stack is Healthy**:
   ```bash
   cd signoz-deploy/deploy/docker/standalone
   docker-compose ps
   ```
   *Ensure `signoz-clickhouse`, `signoz-query-service`, `signoz-otel-collector`, and `signoz-mcp-server` are all `Up`.*

2. **Verify Local Ollama Metal Runtime**:
   ```bash
   export OLLAMA_FLASH_ATTENTION="1"
   export OLLAMA_KV_CACHE_TYPE="q8_0"
   curl -s http://localhost:11434/api/tags | grep qwen2.5:3b
   ```
   *Verify Qwen 2.5 3B is loaded and responsive in local memory.*

3. **Pre-Warm the Model** (Prevents cold-start delays during live demo):
   ```bash
   python3 -c "from openai import OpenAI; c=OpenAI(base_url='http://localhost:11434/v1', api_key='ollama'); c.chat.completions.create(model='qwen2.5:3b', messages=[{'role':'user','content':'hi'}], max_tokens=5)"
   ```

---

## 🎤 LIVE DEMO EXECUTION FLOW

### Phase 1: Establish the Compliance Imperative (2 Minutes)
* **Action**: Open the root `README.md` on screen or show your presentation slide.
* **Key Talking Points**:
  * Explain the tension in modern SRE: teams desperately need LLM automation to resolve complex microservice outages, but legal/compliance teams block cloud AI adoption (OpenAI, Anthropic).
  * Why? Because logs and traces contain PHI (HIPAA), PII, financial transactions, and SQL query strings.
  * Mention **DORA (EU)**: Financial institutions cannot rely on third-party cloud AI vendors during critical operational outages.
  * Introduce our solution: 100% air-gapped, zero-egress SRE Copilot running locally on Apple Silicon / edge hardware.

### Phase 2: Demonstrate Technical Superiority & Token Economics (2 Minutes)
* **Action**: Run the built-in audit and benchmark proof script:
  ```bash
  python3 bridge/audit_proof.py
  ```
* **Key Talking Points**:
  * Point to the **91.47% Token Reduction**: Explain how the raw 41-tool MCP schema is over 47,000 tokens, causing SLMs to OOM or hallucinate. Our curated 6-tool whitelist compresses the schema to 4,024 tokens.
  * Point to the **Ollama Memory Footprint**: Explain that 4-bit Metal quantization requires only ~2.2 GB RAM, leaving full system memory available for databases and collectors.

### Phase 3: Trigger Live Incident & Autonomous RCA Chaining (3 Minutes)
* **Action 1**: Open a split-pane terminal. In Pane 1, inject the production fault:
  ```bash
  python3 demo-app/fault_injector.py --mode fault --fault-type db-pool-exhaustion
  ```
  *Explain: "We are now injecting realistic database timeout errors and 500 HTTP exceptions into our local OpenTelemetry collector."*

* **Action 2**: In Pane 2, run the natural language RCA query:
  ```bash
  python3 -u bridge/main.py "Why is checkoutservice failing? Diagnose the root cause."
  ```
* **Key Talking Points During Execution (~3 Seconds)**:
  * Point out Step 1: The model autonomously inspects `signoz_search_logs` and discovers the `HikariPool-1` SQL timeout exception.
  * Point out Step 2: The model automatically chains a call to `signoz_search_traces` to isolate the exact failing operation (`HikariPool.getConnection`).
  * Highlight the final plain-text synthesis: "In under 3 seconds, without any human guidance or looping, it correctly diagnoses HikariPool DB connection pool exhaustion."

### Phase 4: Data Sovereignty Audit Proof & Wrap-Up (1 Minute)
* **Action**: Re-run the audit auditor to show the newly logged transaction:
  ```bash
  python3 bridge/audit_proof.py
  ```
* **Key Talking Points**:
  * Point to the **Zero External Egress Detected** verification badge.
  * Conclude: "Every prompt, schema fetch, and telemetry query stayed 100% on our local loopback network. DORA ready, HIPAA compliant, and ready for production enterprise adoption."

---

## ❓ ANTICIPATED JUDGE / STAKEHOLDER Q&A

**Q1: Why use `qwen2.5:3b` instead of larger enterprise models like Llama 3 70B?**
> **Answer**: We built this proof-of-concept using a compact 3B model because we engineered and tested the entire zero-egress system natively on a standard developer laptop without cloud GPU clusters. But developing under strict laptop compute constraints turned out to be our greatest architectural advantage! To make this work without out-of-memory crashes, we had to solve the root bottlenecks of local observability: we compressed the 41-tool MCP schema by 91.47% and built real-time JSON sanitization. Because we solved the hardest efficiency problems on a laptop using just 2.2 GB of RAM, our architecture will scale natively to enterprise 70B+ models on private cloud clusters with zero token waste and maximum reasoning precision.

**Q2: How do you prevent the small LLM from getting stuck in infinite tool-calling loops?**
> **Answer**: We identified three primary loop triggers in raw observability data: ClickHouse SQL query syntax errors, pagination command prompts (`note: fetch next page...`), and null-attribute bloat in span waterfalls. We engineered our client (`mcp_client.py`) to automatically sanitize outputs, filter out pagination prompts, and strip null fields before feeding the context to Qwen.

**Q3: Can this be deployed on air-gapped Kubernetes clusters?**
> **Answer**: Yes! The entire stack (SigNoz, OTel Collector, MCP Server, and Ollama/Qwen) is fully containerized in Docker Standalone / Helm charts and requires zero outbound internet connectivity once container images are pulled.
