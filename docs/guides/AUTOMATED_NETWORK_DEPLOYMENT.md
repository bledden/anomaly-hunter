# Automated Network Deployment Guide

**How to Deploy Anomaly Hunter Within Your Network Infrastructure**

This guide covers automated deployment strategies for integrating Anomaly Hunter into your existing network and monitoring infrastructure.

---

## Overview

Anomaly Hunter can be deployed in several ways depending on your infrastructure:

1. **Kubernetes Native** - Operator pattern with auto-discovery
2. **Docker Compose** - Standalone service with network monitoring
3. **Systemd Service** - Traditional Linux service deployment
4. **Air-Gapped Network** - Fully isolated deployment
5. **Cloud Auto-Deployment** - Terraform/CloudFormation automation

---

## 1. Kubernetes Native Deployment

### Architecture

```
┌─────────────────────────────────────────────────────┐
│              Kubernetes Cluster                      │
│                                                       │
│  ┌─────────────────┐      ┌──────────────────┐     │
│  │ Anomaly Hunter  │─────→│   Prometheus     │     │
│  │   Operator      │      │   (metrics)      │     │
│  └─────────────────┘      └──────────────────┘     │
│          │                                           │
│          ↓                                           │
│  ┌─────────────────────────────────────────┐       │
│  │   Auto-Discovered Services               │       │
│  │   • API Gateway (latency)                │       │
│  │   • Database (connections)               │       │
│  │   • Cache (hit rate)                     │       │
│  └─────────────────────────────────────────┘       │
└─────────────────────────────────────────────────────┘
```

### Installation

**Step 1: Install Custom Resource Definition (CRD)**

```bash
kubectl apply -f https://raw.githubusercontent.com/bledden/anomaly-hunter/main/k8s/crd.yaml
```

**Step 2: Deploy Operator**

```bash
kubectl apply -f https://raw.githubusercontent.com/bledden/anomaly-hunter/main/k8s/operator.yaml
```

**Step 3: Create AnomalyDetector Resource**

```yaml
# anomaly-detector.yaml
apiVersion: anomalyhunter.io/v1
kind: AnomalyDetector
metadata:
  name: production-monitor
spec:
  # Auto-discover all services in namespace
  autodiscovery:
    enabled: true
    namespaces:
      - production
      - staging

  # Metrics to monitor
  metrics:
    - name: api_latency
      source: prometheus
      query: "histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))"
      threshold: 0.5  # 500ms

    - name: error_rate
      source: prometheus
      query: "rate(http_requests_total{status=~\"5..\"}[5m])"
      threshold: 0.01  # 1%

    - name: db_connections
      source: prometheus
      query: "pg_stat_database_numbackends"
      threshold: 100

  # Alert destinations
  alerts:
    slack:
      webhook: https://hooks.slack.com/services/YOUR/WEBHOOK/URL
      channel: "#alerts"
    pagerduty:
      integrationKey: YOUR_PAGERDUTY_KEY
      severity: critical

  # Detection settings
  detection:
    sensitivity: medium  # low, medium, high
    learningPeriod: 7d   # learn patterns for 7 days before alerting
```

**Step 4: Apply Configuration**

```bash
kubectl apply -f anomaly-detector.yaml
```

**Step 5: Verify Deployment**

```bash
# Check operator logs
kubectl logs -f deployment/anomaly-hunter-operator

# Check detected anomalies
kubectl get anomalies

# Describe specific anomaly
kubectl describe anomaly <anomaly-name>
```

### How It Works

1. **Operator watches for AnomalyDetector resources**
2. **Auto-discovers Prometheus instances in specified namespaces**
3. **Queries metrics every 60 seconds (configurable)**
4. **Runs 3-agent analysis on detected anomalies**
5. **Creates Kubernetes Event and sends alerts**
6. **Updates AnomalyDetector status with findings**

### Auto-Discovery

The operator automatically finds:

- **Prometheus instances** (via ServiceMonitor CRDs)
- **Grafana dashboards** (imports metric queries)
- **Service dependencies** (via Istio/Linkerd service mesh)
- **Deployment events** (correlates anomalies with rollouts)

---

## 2. Docker Compose Deployment

### Architecture

```
┌──────────────────────────────────────────────┐
│           Host Network                        │
│                                               │
│  ┌──────────────┐      ┌─────────────┐      │
│  │  Anomaly     │─────→│  Prometheus │      │
│  │  Hunter      │      │  (optional) │      │
│  │  Container   │      └─────────────┘      │
│  └──────────────┘                            │
│         │                                     │
│         └────→ Monitor host network metrics  │
└──────────────────────────────────────────────┘
```

### Installation

**Step 1: Create docker-compose.yml**

```yaml
version: '3.8'

services:
  anomaly-hunter:
    image: bledden/anomaly-hunter:latest
    container_name: anomaly-hunter
    restart: unless-stopped

    # Network mode: monitor host network
    network_mode: host

    environment:
      # API keys
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - STACKAI_API_KEY=${STACKAI_API_KEY}
      - TFY_API_KEY=${TFY_API_KEY}
      - TFY_HOST=https://app.truefoundry.com
      - SENTRY_DSN=${SENTRY_DSN}

      # Auto-discovery
      - AUTODISCOVER_PROMETHEUS=true
      - AUTODISCOVER_GRAFANA=true
      - PROMETHEUS_URL=http://localhost:9090

      # Monitoring targets
      - MONITOR_NETWORK_INTERFACE=eth0
      - MONITOR_PROCESSES=true
      - MONITOR_DOCKER_CONTAINERS=true

    volumes:
      # Mount Docker socket to monitor containers
      - /var/run/docker.sock:/var/run/docker.sock:ro

      # Persistent storage for learning
      - ./data:/app/data

      # Config file
      - ./config.yaml:/app/config.yaml:ro

    ports:
      - "8000:8000"  # API endpoint

    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  # Optional: Prometheus for metrics collection
  prometheus:
    image: prom/prometheus:latest
    container_name: prometheus
    restart: unless-stopped
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus-data:/prometheus
    ports:
      - "9090:9090"

volumes:
  prometheus-data:
```

**Step 2: Create config.yaml**

```yaml
# config.yaml
detection:
  # Auto-discover metrics from Prometheus
  autodiscovery:
    enabled: true
    interval: 60  # seconds

  # Metrics to monitor
  metrics:
    # Network metrics
    - name: network_bandwidth
      source: host
      metric: net.bytes_sent
      interface: eth0

    - name: packet_loss
      source: host
      metric: net.packets_dropped
      interface: eth0

    # Process metrics
    - name: cpu_usage
      source: host
      metric: cpu.percent

    - name: memory_usage
      source: host
      metric: mem.percent

    # Docker container metrics
    - name: container_restarts
      source: docker
      metric: container.restarts

    - name: container_memory
      source: docker
      metric: container.memory.usage

  # Detection settings
  sensitivity: medium
  learning_period: 7d

# Alerts
alerts:
  slack:
    webhook: ${SLACK_WEBHOOK}
    channel: "#infrastructure"

  email:
    smtp_server: smtp.gmail.com
    smtp_port: 587
    from: alerts@yourcompany.com
    to:
      - oncall@yourcompany.com
```

**Step 3: Create .env file**

```bash
# .env
OPENAI_API_KEY=sk-proj-...
STACKAI_API_KEY=...
TFY_API_KEY=...
SENTRY_DSN=https://...
SLACK_WEBHOOK=https://hooks.slack.com/services/...
```

**Step 4: Start Services**

```bash
docker-compose up -d
```

**Step 5: Verify Deployment**

```bash
# Check logs
docker-compose logs -f anomaly-hunter

# Check health
curl http://localhost:8000/health

# View detected anomalies
curl http://localhost:8000/api/v1/anomalies
```

### Network Monitoring

The container automatically monitors:

- **Network interface metrics** (bandwidth, packet loss, errors)
- **Docker container stats** (CPU, memory, restarts)
- **Host system metrics** (via /proc if mounted)
- **Prometheus exporters** (if auto-discovery enabled)

---

## 3. Systemd Service Deployment

### Installation

**Step 1: Install Anomaly Hunter**

```bash
# Clone repository
git clone https://github.com/bledden/anomaly-hunter.git
cd anomaly-hunter

# Install system-wide
sudo pip install -r requirements.txt
sudo cp -r . /opt/anomaly-hunter
sudo cp config/anomaly-hunter.service /etc/systemd/system/
```

**Step 2: Create Service File**

```ini
# /etc/systemd/system/anomaly-hunter.service
[Unit]
Description=Anomaly Hunter - Autonomous Anomaly Detection
After=network.target

[Service]
Type=simple
User=anomaly-hunter
Group=anomaly-hunter
WorkingDirectory=/opt/anomaly-hunter

# Environment file
EnvironmentFile=/etc/anomaly-hunter/env

# Start command
ExecStart=/usr/bin/python3 /opt/anomaly-hunter/api.py

# Auto-restart on failure
Restart=on-failure
RestartSec=10

# Resource limits
MemoryLimit=2G
CPUQuota=200%

# Logging
StandardOutput=journal
StandardError=journal
SyslogIdentifier=anomaly-hunter

[Install]
WantedBy=multi-user.target
```

**Step 3: Create Environment File**

```bash
# /etc/anomaly-hunter/env
OPENAI_API_KEY=sk-proj-...
STACKAI_API_KEY=...
TFY_API_KEY=...
SENTRY_DSN=https://...
AUTODISCOVER_PROMETHEUS=true
PROMETHEUS_URL=http://localhost:9090
```

**Step 4: Start Service**

```bash
# Create user
sudo useradd -r -s /bin/false anomaly-hunter

# Set permissions
sudo chown -R anomaly-hunter:anomaly-hunter /opt/anomaly-hunter
sudo chmod 600 /etc/anomaly-hunter/env

# Enable and start
sudo systemctl daemon-reload
sudo systemctl enable anomaly-hunter
sudo systemctl start anomaly-hunter

# Check status
sudo systemctl status anomaly-hunter
```

**Step 5: View Logs**

```bash
# Follow logs
sudo journalctl -u anomaly-hunter -f

# View recent logs
sudo journalctl -u anomaly-hunter -n 100
```

---

## 4. Air-Gapped Network Deployment

For environments without internet access (e.g., financial institutions, government networks).

### Preparation (On Internet-Connected System)

**Step 1: Download Offline Bundle**

```bash
# Download complete offline package
wget https://github.com/bledden/anomaly-hunter/releases/download/v1.0.0/anomaly-hunter-offline-bundle.tar.gz

# Or build your own
python3 scripts/create_offline_bundle.py
```

**Step 2: Transfer to Air-Gapped Network**

```bash
# Copy bundle to USB drive or secure transfer mechanism
cp anomaly-hunter-offline-bundle.tar.gz /media/usb/
```

### Installation (On Air-Gapped System)

**Step 1: Extract Bundle**

```bash
tar -xzf anomaly-hunter-offline-bundle.tar.gz
cd anomaly-hunter-offline
```

**Step 2: Run Installer**

```bash
sudo ./install.sh
```

The installer will:
- Install Python dependencies from bundled wheels
- Set up local database (SQLite)
- Configure systemd service
- Run health checks

**Step 3: Configure for Offline Mode**

```bash
# Edit config
sudo vim /etc/anomaly-hunter/config.yaml
```

```yaml
# config.yaml
offline_mode: true

# Use local models (no API calls)
models:
  pattern_analyst:
    provider: local
    model: /opt/anomaly-hunter/models/llama-3.1-8b

  change_detective:
    provider: local
    model: /opt/anomaly-hunter/models/llama-3.1-8b

  root_cause:
    provider: local
    model: /opt/anomaly-hunter/models/llama-3.1-70b

# Disable cloud integrations
integrations:
  truefoundry:
    enabled: false
  sentry:
    enabled: false
  redpanda:
    enabled: false

# Local alternatives
database:
  type: sqlite
  path: /var/lib/anomaly-hunter/db.sqlite

logging:
  type: file
  path: /var/log/anomaly-hunter/

streaming:
  type: local_queue
  backend: sqlite
```

**Step 4: Start Service**

```bash
sudo systemctl start anomaly-hunter
sudo systemctl status anomaly-hunter
```

### Offline Features

- **Local LLM inference** (Llama 3.1 8B/70B models included)
- **SQLite database** (no external database required)
- **File-based logging** (no cloud monitoring)
- **Local message queue** (SQLite-backed event streaming)
- **Web UI included** (no CDN dependencies)

---

## 5. Cloud Auto-Deployment

### Terraform (AWS Example)

```hcl
# main.tf
provider "aws" {
  region = "us-west-2"
}

# ECS Cluster
resource "aws_ecs_cluster" "anomaly_hunter" {
  name = "anomaly-hunter-cluster"
}

# ECS Task Definition
resource "aws_ecs_task_definition" "anomaly_hunter" {
  family                   = "anomaly-hunter"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = "1024"
  memory                   = "2048"

  container_definitions = jsonencode([{
    name  = "anomaly-hunter"
    image = "bledden/anomaly-hunter:latest"

    environment = [
      { name = "AUTODISCOVER_CLOUDWATCH", value = "true" },
      { name = "AWS_REGION", value = "us-west-2" }
    ]

    secrets = [
      { name = "OPENAI_API_KEY", valueFrom = aws_secretsmanager_secret.api_keys.arn }
    ]

    portMappings = [{
      containerPort = 8000
      protocol      = "tcp"
    }]

    logConfiguration = {
      logDriver = "awslogs"
      options = {
        "awslogs-group"         = "/ecs/anomaly-hunter"
        "awslogs-region"        = "us-west-2"
        "awslogs-stream-prefix" = "ecs"
      }
    }
  }])
}

# ECS Service
resource "aws_ecs_service" "anomaly_hunter" {
  name            = "anomaly-hunter-service"
  cluster         = aws_ecs_cluster.anomaly_hunter.id
  task_definition = aws_ecs_task_definition.anomaly_hunter.arn
  desired_count   = 2
  launch_type     = "FARGATE"

  network_configuration {
    subnets         = aws_subnet.private[*].id
    security_groups = [aws_security_group.anomaly_hunter.id]
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.anomaly_hunter.arn
    container_name   = "anomaly-hunter"
    container_port   = 8000
  }
}

# Auto-scaling
resource "aws_appautoscaling_target" "anomaly_hunter" {
  max_capacity       = 10
  min_capacity       = 2
  resource_id        = "service/${aws_ecs_cluster.anomaly_hunter.name}/${aws_ecs_service.anomaly_hunter.name}"
  scalable_dimension = "ecs:service:DesiredCount"
  service_namespace  = "ecs"
}

resource "aws_appautoscaling_policy" "cpu" {
  name               = "cpu-autoscaling"
  policy_type        = "TargetTrackingScaling"
  resource_id        = aws_appautoscaling_target.anomaly_hunter.resource_id
  scalable_dimension = aws_appautoscaling_target.anomaly_hunter.scalable_dimension
  service_namespace  = aws_appautoscaling_target.anomaly_hunter.service_namespace

  target_tracking_scaling_policy_configuration {
    predefined_metric_specification {
      predefined_metric_type = "ECSServiceAverageCPUUtilization"
    }
    target_value = 70.0
  }
}
```

**Deploy:**

```bash
terraform init
terraform plan
terraform apply
```

### CloudFormation (AWS)

See `cloudformation/anomaly-hunter-stack.yaml` in the repository for a complete example.

### Google Cloud Deployment Manager

See `gcp/deployment.yaml` in the repository.

---

## 6. Network Monitoring Best Practices

### What to Monitor

**1. Network Layer**
- Bandwidth utilization (inbound/outbound)
- Packet loss rate
- Latency (ping, traceroute)
- DNS query times
- Connection states (established, time_wait, etc.)

**2. Application Layer**
- HTTP request rate
- API latency (P50, P95, P99)
- Error rate (4xx, 5xx)
- WebSocket connection count

**3. Infrastructure Layer**
- Server CPU/memory
- Database connections
- Cache hit rate
- Disk I/O

### Example: Complete Network Monitoring Setup

```yaml
# config.yaml
metrics:
  # Network metrics (collected every 10s)
  - name: network_bandwidth_in
    source: prometheus
    query: rate(node_network_receive_bytes_total{device="eth0"}[1m])
    unit: bytes/sec

  - name: network_bandwidth_out
    source: prometheus
    query: rate(node_network_transmit_bytes_total{device="eth0"}[1m])
    unit: bytes/sec

  - name: packet_loss
    source: prometheus
    query: rate(node_network_transmit_drop_total[1m])
    unit: packets/sec

  # Application metrics (collected every 30s)
  - name: api_latency_p95
    source: prometheus
    query: histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))
    unit: seconds

  - name: error_rate
    source: prometheus
    query: rate(http_requests_total{status=~"5.."}[5m])
    unit: errors/sec

  # Infrastructure metrics (collected every 60s)
  - name: db_connections
    source: prometheus
    query: pg_stat_database_numbackends
    unit: connections

  - name: cache_hit_rate
    source: prometheus
    query: rate(redis_keyspace_hits_total[5m]) / (rate(redis_keyspace_hits_total[5m]) + rate(redis_keyspace_misses_total[5m]))
    unit: ratio

# Anomaly detection settings
detection:
  # Sensitivity: how aggressive to detect anomalies
  sensitivity: medium  # low, medium, high

  # Learning period: how long to learn baseline before alerting
  learning_period: 7d

  # Minimum confidence to alert
  min_confidence: 0.70

  # Correlation window: look for related anomalies within this time
  correlation_window: 5m

# Alerting rules
alerts:
  # Critical (page immediately)
  - name: critical_anomaly
    severity: critical
    conditions:
      - metric: api_latency_p95
        threshold: 5.0  # 5 seconds
      - metric: error_rate
        threshold: 0.05  # 5%
    destinations:
      - pagerduty
      - slack
      - voice  # ElevenLabs voice call

  # Warning (notify but don't page)
  - name: warning_anomaly
    severity: warning
    conditions:
      - metric: packet_loss
        threshold: 0.01  # 1%
      - metric: cache_hit_rate
        threshold: 0.7  # <70%
    destinations:
      - slack
      - email
```

---

## 7. Troubleshooting

### Common Issues

**Issue: Auto-discovery not finding Prometheus**

```bash
# Check Prometheus is reachable
curl http://localhost:9090/-/healthy

# Check Anomaly Hunter can access it
docker exec anomaly-hunter curl http://host.docker.internal:9090/-/healthy

# Fix: Add to docker-compose.yml
extra_hosts:
  - "host.docker.internal:host-gateway"
```

**Issue: High memory usage**

```bash
# Check detection frequency
# Reduce polling interval in config.yaml
detection:
  interval: 120  # Increase from 60 to 120 seconds

# Limit metric retention
retention:
  max_age: 7d  # Only keep 7 days of data
  cleanup_interval: 1d
```

**Issue: Missed anomalies**

```bash
# Lower sensitivity
detection:
  sensitivity: high  # Detect more anomalies
  min_confidence: 0.60  # Lower threshold from 0.70
```

**Issue: Too many false positives**

```bash
# Increase learning period
detection:
  learning_period: 14d  # Learn for 2 weeks instead of 1

# Raise confidence threshold
detection:
  min_confidence: 0.80  # Increase from 0.70
```

---

## 8. Security Considerations

### Network Security

1. **Encrypt all traffic**
   - Use TLS for API endpoints
   - Encrypt communication with Prometheus (if remote)
   - Use VPN for multi-site deployments

2. **Restrict network access**
   - Firewall rules to limit inbound connections
   - Use network policies in Kubernetes
   - Implement RBAC for API access

3. **API key management**
   - Use Kubernetes Secrets or AWS Secrets Manager
   - Rotate keys regularly
   - Never commit keys to git

4. **Audit logging**
   - Log all API access
   - Log configuration changes
   - Monitor for suspicious activity

### Example: Security-Hardened Deployment

```yaml
# kubernetes/secure-deployment.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: anomaly-hunter
  labels:
    pod-security.kubernetes.io/enforce: restricted
---
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: anomaly-hunter-network-policy
  namespace: anomaly-hunter
spec:
  podSelector:
    matchLabels:
      app: anomaly-hunter
  policyTypes:
    - Ingress
    - Egress
  ingress:
    # Only allow traffic from ingress controller
    - from:
      - namespaceSelector:
          matchLabels:
            name: ingress-nginx
      ports:
      - protocol: TCP
        port: 8000
  egress:
    # Allow only to Prometheus
    - to:
      - namespaceSelector:
          matchLabels:
            name: monitoring
      ports:
      - protocol: TCP
        port: 9090
    # Allow DNS
    - to:
      - namespaceSelector:
          matchLabels:
            name: kube-system
      ports:
      - protocol: UDP
        port: 53
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: anomaly-hunter
  namespace: anomaly-hunter
spec:
  replicas: 2
  template:
    spec:
      securityContext:
        runAsNonRoot: true
        runAsUser: 1000
        fsGroup: 1000
        seccompProfile:
          type: RuntimeDefault
      containers:
      - name: anomaly-hunter
        image: bledden/anomaly-hunter:latest
        securityContext:
          allowPrivilegeEscalation: false
          readOnlyRootFilesystem: true
          capabilities:
            drop:
            - ALL
        resources:
          limits:
            cpu: "2"
            memory: 2Gi
          requests:
            cpu: "1"
            memory: 1Gi
        volumeMounts:
        - name: tmp
          mountPath: /tmp
        - name: cache
          mountPath: /app/cache
      volumes:
      - name: tmp
        emptyDir: {}
      - name: cache
        emptyDir: {}
```

---

## Conclusion

Anomaly Hunter can be deployed in various network configurations:

- **Kubernetes**: Best for cloud-native, auto-scaling deployments
- **Docker Compose**: Best for single-server or small-scale deployments
- **Systemd**: Best for traditional Linux environments
- **Air-Gapped**: Best for highly regulated/secure environments
- **Cloud (Terraform)**: Best for infrastructure-as-code workflows

Choose the deployment method that matches your infrastructure and security requirements.

For additional help:
- [GitHub Issues](https://github.com/bledden/anomaly-hunter/issues)
- [Documentation](https://github.com/bledden/anomaly-hunter/tree/main/docs)
- Email: blake@facilitair.ai
