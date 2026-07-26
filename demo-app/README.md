# OpenTelemetry Demo App (Astronomy Shop & Rideshare Telemetry)

This directory contains the Docker Compose stack that simulates our monitored microservices (`frontend`, `checkoutservice`, `productcatalogservice`, and `astronomy-shop`).

It connects directly to the external `signoz-network` Docker network and sends continuous OpenTelemetry OTLP Traces, Metrics, and Logs to `http://signoz-ingester-1:4317`.

## Launching Telemetry Generation
```bash
docker compose up -d
```

## Verifying in SigNoz UI
1. Open `http://localhost:8080` in your browser.
2. Go to **Services** -> You will see `checkoutservice`, `productcatalogservice`, `frontend`, and `astronomy-shop`.
3. Go to **Logs** -> You will see ERROR logs ("Database timeout in checkout pipeline").
4. Go to **Traces** -> You will see continuous span generation.
