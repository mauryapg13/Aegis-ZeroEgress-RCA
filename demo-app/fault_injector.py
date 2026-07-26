#!/usr/bin/env python3
"""
fault_injector.py — Zero-Egress Fault Injection Controller for OpenTelemetry Demo App

Simulates feature-flag triggered incidents (e.g., Database Connection Pool Exhaustion)
by emitting structured OTLP Traces and Logs directly to the self-hosted SigNoz Ingester
via HTTP JSON on port 4318.
"""

import argparse
import json
import time
import uuid
import requests
import sys

DEFAULT_ENDPOINT = "http://localhost:4318"

def inject_db_pool_exhaustion(endpoint: str, service_name: str, count: int, interval: float):
    print(f"\033[91m⚠️  [FAULT INJECTION ENABLED] Simulating DB Connection Pool Exhaustion on '{service_name}'...\033[0m")
    print(f"📡 Target OTLP Endpoint: {endpoint}")
    print(f"🔄 Injecting {count} batches (interval: {interval}s)...\n")
    
    success_count = 0
    for i in range(1, count + 1):
        now_ns = int(time.time() * 1e9)
        trace_id = uuid.uuid4().hex
        span_id = uuid.uuid4().hex[:16]
        parent_span_id = uuid.uuid4().hex[:16]
        
        # 1. Generate Error Trace (5000ms duration, HTTP 500, exception event)
        trace_payload = {
            "resourceSpans": [{
                "resource": {
                    "attributes": [
                        {"key": "service.name", "value": {"stringValue": service_name}},
                        {"key": "service.namespace", "value": {"stringValue": "astronomy-shop"}},
                        {"key": "deployment.environment", "value": {"stringValue": "production"}}
                    ]
                },
                "scopeSpans": [{
                    "spans": [
                        {
                            "traceId": trace_id,
                            "spanId": parent_span_id,
                            "name": "HTTP POST /checkout",
                            "kind": 2, # SERVER
                            "startTimeUnixNano": str(now_ns - int(5.2 * 1e9)),
                            "endTimeUnixNano": str(now_ns),
                            "attributes": [
                                {"key": "http.method", "value": {"stringValue": "POST"}},
                                {"key": "http.route", "value": {"stringValue": "/checkout"}},
                                {"key": "http.status_code", "value": {"intValue": 500}},
                                {"key": "error", "value": {"boolValue": True}}
                            ],
                            "status": {"code": 2, "message": "HTTP 500 Internal Server Error"}
                        },
                        {
                            "traceId": trace_id,
                            "spanId": span_id,
                            "parentSpanId": parent_span_id,
                            "name": "HikariPool.getConnection",
                            "kind": 3, # CLIENT
                            "startTimeUnixNano": str(now_ns - int(5.0 * 1e9)),
                            "endTimeUnixNano": str(now_ns),
                            "attributes": [
                                {"key": "db.system", "value": {"stringValue": "postgresql"}},
                                {"key": "db.name", "value": {"stringValue": "orders_db"}},
                                {"key": "db.operation", "value": {"stringValue": "CONNECT"}},
                                {"key": "error", "value": {"boolValue": True}},
                                {"key": "exception.type", "value": {"stringValue": "java.sql.SQLTransientConnectionException"}},
                                {"key": "exception.message", "value": {"stringValue": "HikariPool-1 - Connection is not available, request timed out after 30000ms"}}
                            ],
                            "status": {"code": 2, "message": "Connection pool exhausted"}
                        }
                    ]
                }]
            }]
        }
        
        # 2. Generate Error Log with stack trace
        log_payload = {
            "resourceLogs": [{
                "resource": {
                    "attributes": [
                        {"key": "service.name", "value": {"stringValue": service_name}},
                        {"key": "service.namespace", "value": {"stringValue": "astronomy-shop"}}
                    ]
                },
                "scopeLogs": [{
                    "logRecords": [{
                        "timeUnixNano": str(now_ns),
                        "severityNumber": 17,
                        "severityText": "ERROR",
                        "body": {
                            "stringValue": f"ERROR [HikariPool-1]: DB connection pool exhausted in {service_name}. java.sql.SQLTransientConnectionException: HikariPool-1 - Connection is not available, request timed out after 30000ms. Check max_pool_size or database load."
                        },
                        "attributes": [
                            {"key": "trace_id", "value": {"stringValue": trace_id}},
                            {"key": "span_id", "value": {"stringValue": span_id}},
                            {"key": "error.type", "value": {"stringValue": "java.sql.SQLTransientConnectionException"}},
                            {"key": "fault.injected", "value": {"boolValue": True}}
                        ]
                    }]
                }]
            }]
        }
        
        try:
            r_trace = requests.post(f"{endpoint}/v1/traces", json=trace_payload, timeout=5)
            r_log = requests.post(f"{endpoint}/v1/logs", json=log_payload, timeout=5)
            
            if r_trace.status_code == 200 and r_log.status_code == 200:
                print(f"  [Batch {i}/{count}] ✅ Injected Error Trace ({trace_id[:8]}...) & Log (HTTP 500 / Timeout)")
                success_count += 1
            else:
                print(f"  [Batch {i}/{count}] ❌ Ingestion Failed -> Trace: {r_trace.status_code}, Log: {r_log.status_code}")
        except Exception as e:
            print(f"  [Batch {i}/{count}] ❌ Connection Error: {e}")
            
        if i < count:
            time.sleep(interval)
            
    print(f"\n🏁 Fault Injection Completed: {success_count}/{count} batches successfully indexed in ClickHouse.")

def inject_memory_leak(endpoint: str, service_name: str, count: int, interval: float):
    print(f"\033[91m⚠️  [FAULT INJECTION ENABLED] Simulating Cascading Memory Leak & GC Pause on '{service_name}' -> 'paymentservice'...\033[0m")
    print(f"📡 Target OTLP Endpoint: {endpoint}")
    print(f"🔄 Injecting {count} batches (interval: {interval}s)...\n")
    
    success_count = 0
    for i in range(1, count + 1):
        now_ns = int(time.time() * 1e9)
        trace_id = uuid.uuid4().hex
        span_checkout = uuid.uuid4().hex[:16]
        span_payment = uuid.uuid4().hex[:16]
        
        trace_payload = {
            "resourceSpans": [
                {
                    "resource": {
                        "attributes": [
                            {"key": "service.name", "value": {"stringValue": "checkoutservice"}},
                            {"key": "service.namespace", "value": {"stringValue": "astronomy-shop"}}
                        ]
                    },
                    "scopeSpans": [{
                        "spans": [{
                            "traceId": trace_id,
                            "spanId": span_checkout,
                            "name": "HTTP POST /checkout/payment",
                            "kind": 2,
                            "startTimeUnixNano": str(now_ns - int(15.5 * 1e9)),
                            "endTimeUnixNano": str(now_ns),
                            "attributes": [
                                {"key": "http.status_code", "value": {"intValue": 504}},
                                {"key": "error", "value": {"boolValue": True}}
                            ],
                            "status": {"code": 2, "message": "504 Gateway Timeout"}
                        }]
                    }]
                },
                {
                    "resource": {
                        "attributes": [
                            {"key": "service.name", "value": {"stringValue": "paymentservice"}},
                            {"key": "service.namespace", "value": {"stringValue": "astronomy-shop"}}
                        ]
                    },
                    "scopeSpans": [{
                        "spans": [{
                            "traceId": trace_id,
                            "spanId": span_payment,
                            "parentSpanId": span_checkout,
                            "name": "PaymentService/ProcessTransaction",
                            "kind": 1,
                            "startTimeUnixNano": str(now_ns - int(15.0 * 1e9)),
                            "endTimeUnixNano": str(now_ns),
                            "attributes": [
                                {"key": "error", "value": {"boolValue": True}},
                                {"key": "jvm.gc.pause_ms", "value": {"doubleValue": 14850.0}},
                                {"key": "exception.type", "value": {"stringValue": "java.lang.OutOfMemoryError"}}
                            ],
                            "status": {"code": 2, "message": "Java heap space - GC Overhead Limit Exceeded"}
                        }]
                    }]
                }
            ]
        }
        
        log_payload = {
            "resourceLogs": [{
                "resource": {
                    "attributes": [
                        {"key": "service.name", "value": {"stringValue": "paymentservice"}},
                        {"key": "service.namespace", "value": {"stringValue": "astronomy-shop"}}
                    ]
                },
                "scopeLogs": [{
                    "logRecords": [{
                        "timeUnixNano": str(now_ns),
                        "severityNumber": 17,
                        "severityText": "ERROR",
                        "body": {
                            "stringValue": "FATAL [paymentservice]: java.lang.OutOfMemoryError: GC overhead limit exceeded in PaymentService worker pool. 14,850ms Stop-The-World GC pause. Active Heap: 99.8% (3.98GB / 4.00GB). Check heap dump at /tmp/heap_dump.hprof."
                        },
                        "attributes": [
                            {"key": "trace_id", "value": {"stringValue": trace_id}},
                            {"key": "span_id", "value": {"stringValue": span_payment}},
                            {"key": "error.type", "value": {"stringValue": "java.lang.OutOfMemoryError"}}
                        ]
                    }]
                }]
            }]
        }
        
        try:
            r_trace = requests.post(f"{endpoint}/v1/traces", json=trace_payload, timeout=5)
            r_log = requests.post(f"{endpoint}/v1/logs", json=log_payload, timeout=5)
            if r_trace.status_code == 200 and r_log.status_code == 200:
                print(f"  [Batch {i}/{count}] ✅ Injected Memory Leak & 15s GC Pause ({trace_id[:8]}...) -> HTTP 504 Timeout")
                success_count += 1
        except Exception as e:
            print(f"  [Batch {i}/{count}] ❌ Error: {e}")
        if i < count:
            time.sleep(interval)
            
    print(f"\n🏁 Memory Leak Fault Injection Completed: {success_count}/{count} batches indexed.")

def inject_redis_refused(endpoint: str, service_name: str, count: int, interval: float):
    print(f"\033[91m⚠️  [FAULT INJECTION ENABLED] Simulating Redis Cache Outage on '{service_name}'...\033[0m")
    print(f"📡 Target OTLP Endpoint: {endpoint}")
    print(f"🔄 Injecting {count} batches (interval: {interval}s)...\n")
    
    success_count = 0
    for i in range(1, count + 1):
        now_ns = int(time.time() * 1e9)
        trace_id = uuid.uuid4().hex
        span_rec = uuid.uuid4().hex[:16]
        
        trace_payload = {
            "resourceSpans": [{
                "resource": {
                    "attributes": [
                        {"key": "service.name", "value": {"stringValue": "recommendationservice"}},
                        {"key": "service.namespace", "value": {"stringValue": "astronomy-shop"}}
                    ]
                },
                "scopeSpans": [{
                    "spans": [{
                        "traceId": trace_id,
                        "spanId": span_rec,
                        "name": "Redis.GET /product_recommendations",
                        "kind": 3,
                        "startTimeUnixNano": str(now_ns - int(8.0 * 1e9)),
                        "endTimeUnixNano": str(now_ns),
                        "attributes": [
                            {"key": "db.system", "value": {"stringValue": "redis"}},
                            {"key": "net.peer.name", "value": {"stringValue": "redis-master"}},
                            {"key": "net.peer.port", "value": {"intValue": 6379}},
                            {"key": "error", "value": {"boolValue": True}},
                            {"key": "exception.type", "value": {"stringValue": "io.lettuce.core.RedisConnectionException"}}
                        ],
                        "status": {"code": 2, "message": "Connection refused: redis-master/172.18.0.5:6379"}
                    }]
                }]
            }]
        }
        
        log_payload = {
            "resourceLogs": [{
                "resource": {
                    "attributes": [
                        {"key": "service.name", "value": {"stringValue": "recommendationservice"}},
                        {"key": "service.namespace", "value": {"stringValue": "astronomy-shop"}}
                    ]
                },
                "scopeLogs": [{
                    "logRecords": [{
                        "timeUnixNano": str(now_ns),
                        "severityNumber": 17,
                        "severityText": "ERROR",
                        "body": {
                            "stringValue": "ERROR [recommendationservice]: io.lettuce.core.RedisConnectionException: Connection refused to redis-master:6379. Redis cluster unreachable or OOM-killed. Fallback DB queries triggered database bottleneck."
                        },
                        "attributes": [
                            {"key": "trace_id", "value": {"stringValue": trace_id}},
                            {"key": "span_id", "value": {"stringValue": span_rec}}
                        ]
                    }]
                }]
            }]
        }
        
        try:
            r_trace = requests.post(f"{endpoint}/v1/traces", json=trace_payload, timeout=5)
            r_log = requests.post(f"{endpoint}/v1/logs", json=log_payload, timeout=5)
            if r_trace.status_code == 200 and r_log.status_code == 200:
                print(f"  [Batch {i}/{count}] ✅ Injected Redis Cache Failure ({trace_id[:8]}...) -> Connection Refused")
                success_count += 1
        except Exception as e:
            print(f"  [Batch {i}/{count}] ❌ Error: {e}")
        if i < count:
            time.sleep(interval)
            
    print(f"\n🏁 Redis Outage Injection Completed: {success_count}/{count} batches indexed.")

def inject_baseline(endpoint: str, service_name: str, count: int, interval: float):
    print(f"\033[92m🌱 [BASELINE MODE] Sending healthy telemetry for '{service_name}'...\033[0m")
    for i in range(1, count + 1):
        now_ns = int(time.time() * 1e9)
        trace_payload = {
            "resourceSpans": [{
                "resource": {"attributes": [{"key": "service.name", "value": {"stringValue": service_name}}]},
                "scopeSpans": [{
                    "spans": [{
                        "traceId": uuid.uuid4().hex,
                        "spanId": uuid.uuid4().hex[:16],
                        "name": "HTTP POST /checkout",
                        "kind": 2,
                        "startTimeUnixNano": str(now_ns - int(0.05 * 1e9)),
                        "endTimeUnixNano": str(now_ns),
                        "status": {"code": 1, "message": "OK"}
                    }]
                }]
            }]
        }
        try:
            requests.post(f"{endpoint}/v1/traces", json=trace_payload, timeout=5)
            print(f"  [Batch {i}/{count}] ✅ Sent healthy trace (200 OK, 50ms)")
        except Exception as e:
            print(f"  [Batch {i}/{count}] ❌ Error: {e}")
        time.sleep(interval)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="SigNoz Demo App Fault Injector")
    parser.add_argument("--mode", choices=["fault", "baseline"], default="fault", help="Telemetry mode to inject")
    parser.add_argument("--fault-type", choices=["db-pool-exhaustion", "memory-leak-gc-pause", "redis-connection-refused"], default="db-pool-exhaustion", help="Type of fault to simulate")
    parser.add_argument("--service", default="checkoutservice", help="Target microservice name")
    parser.add_argument("--endpoint", default=DEFAULT_ENDPOINT, help="OTLP HTTP endpoint (default: http://localhost:4318)")
    parser.add_argument("--count", type=int, default=5, help="Number of telemetry batches to send")
    parser.add_argument("--interval", type=float, default=1.0, help="Seconds between batches")
    
    args = parser.parse_args()
    
    if args.mode == "fault":
        if args.fault_type == "memory-leak-gc-pause":
            inject_memory_leak(args.endpoint, args.service, args.count, args.interval)
        elif args.fault_type == "redis-connection-refused":
            inject_redis_refused(args.endpoint, args.service, args.count, args.interval)
        else:
            inject_db_pool_exhaustion(args.endpoint, args.service, args.count, args.interval)
    else:
        inject_baseline(args.endpoint, args.service, args.count, args.interval)

