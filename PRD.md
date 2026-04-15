# Cloud Native Microservices Live Platform — PRD

**Product:** Self-demonstrating microservices platform — the visualizer IS the system  
**Version:** 2.1  
**Author:** Cesar A. Aguilar (Blueavian9)  
**Architect Pattern:** SOLID · Event-Driven · Cloud Native · Chain-of-Thought  
**Level Target:** Level 3 — Kubernetes Orchestration + Event-Driven Architecture  
**Repo:** github.com/Blueavian9/microservices-mall-architecture

---

## The Concept: The Diagram IS the System

> Instead of drawing a diagram *about* microservices — this project *becomes* one.  
> Real services run in Kubernetes pods. They publish events to NATS/Kafka.  
> The UI visualizes live pod health, real traffic between services, and event streams in real time.  
> Kill a pod in the UI → watch K8s restart it. Spike traffic → watch HPA scale it.  
> This is what a Distinguished Engineer's portfolio looks like.

---

## Legend

| Symbol | Meaning |
|--------|---------|
| ✅ | Completed |
| 🔄 | In Progress |
| ❌ | Not Started |
| 🧠 | Requires architectural decision |

---

## Delivery Discipline (Commits & PRD)

Work is checkpointed at every meaningful boundary:

1. **After** completing any **Main Step**, **Phase**, **EPIC**, or **Agent Task**: **commit** with a clear, scoped message and **push** to `main` (or the active integration branch).
2. **Immediately after** that push: **update this `PRD.md`** — phase/task status, tables, and notes — so the document stays aligned with the repo and remains the single source of truth for progress.

Skipping either step should be the exception (e.g., blocked network), not the default.

---

## Agent Tasks (A1–A9)

| Task | Maps to | Focus |
|------|---------|--------|
| **A1** | PHASE 1 | Local K8s: toolchain (kubectl, minikube, Helm, k9s) + Minikube running + ingress + metrics-server |
| **A2** | PHASE 2 | Microservices — build and containerize each service |
| **A3** | PHASE 3 | Kubernetes manifests (Deployments, Services, Ingress) |
| **A4** | PHASE 4 | NATS event bus (Helm) + shared schema / contracts |
| **A5** | PHASE 5 | Prometheus + service `/metrics` + metrics-service wiring |
| **A6** | PHASE 6 | React live dashboard (topology, events, WebSocket) |
| **A7** | PHASE 7 | HPA demo + load test |
| **A8** | PHASE 8 | Cloud deploy (e.g. EKS) |
| **A9** | PHASE 9 | README polish + demo assets + GIFs |

Execute in order **A1 → A2 → … → A9**. After each task: commit, push, update this PRD.

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                   KUBERNETES CLUSTER                     │
│                                                         │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌────────┐ │
│  │ API GW   │  │  Auth    │  │ Booking  │  │Notify  │ │
│  │ Service  │  │ Service  │  │ Service  │  │Service │ │
│  │ (Node)   │  │ (Python) │  │  (Node)  │  │(Python)│ │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └───┬────┘ │
│       │              │              │              │     │
│  ─────┴──────────────┴──────────────┴──────────────┴─── │
│                    NATS EVENT BUS                        │
│  ─────────────────────────────────────────────────────── │
│                    Postgres (PVC)                        │
└─────────────────────────────────────────────────────────┘
              │ Prometheus scrapes metrics
              ▼
┌─────────────────────────┐
│  React Dashboard (UI)   │ ← WebSocket from metrics service
│  Live pod health        │
│  Event stream log       │
│  Traffic flow diagram   │
│  Kill pod button        │
└─────────────────────────┘
```

## SOLID Application

```
S — Each microservice owns exactly one business domain
O — Add new services via Kubernetes manifests — zero changes to existing services
L — All services implement the same health check and event schema contracts
I — Services subscribe only to events they care about (not a shared god-interface)
D — Services depend on NATS abstractions — swap broker without touching business logic
```

---

## PHASE SUMMARY

| Phase | Focus | Status |
|-------|-------|--------|
| PHASE 1 | Local K8s Environment (Minikube) | ✅ COMPLETE |
| PHASE 2 | Microservices — Build Each Service | 🔄 IN PROGRESS |
| PHASE 3 | Kubernetes Manifests | ❌ NOT STARTED |
| PHASE 4 | NATS Event Bus Setup | ❌ NOT STARTED |
| PHASE 5 | Prometheus + Metrics | ❌ NOT STARTED |
| PHASE 6 | React Live Dashboard | ❌ NOT STARTED |
| PHASE 7 | Horizontal Pod Autoscaling Demo | ❌ NOT STARTED |
| PHASE 8 | Cloud Deploy (AWS EKS or GKE) | ❌ NOT STARTED |
| PHASE 9 | README + Demo Video | ❌ NOT STARTED |

---

## PHASE 1: Local K8s Environment ✅

### Task 1: Install Toolchain ✅

- kubectl, minikube, Helm, k9s installed via Scoop on Windows
- Docker Desktop installed and running
- `minikube start --driver=docker --cpus=4 --memory=8192 --disk-size=20g` ✅
- `minikube addons enable ingress` ✅
- `minikube addons enable metrics-server` ✅
- Commit: `chore: toolchain setup + Minikube running`

### Task 2: Monorepo Scaffold ✅

- Full directory tree created with `.gitkeep` files
- Directories: `services/api-gateway`, `services/auth-service`, `services/booking-service`, `services/notification-service`, `services/metrics-service`, `k8s`, `k8s/base`, `k8s/monitoring`, `frontend`, `scripts`
- `.gitignore`, `.env.example`, `docker-compose.yml` (postgres:16-alpine + nats:2.10-alpine)
- `README.md` placeholder committed
- Commit: `chore: monorepo scaffold with service directories`

---

## PHASE 2: Microservices — Build Each Service 🔄

Each service is a separate Docker image. Each owns its domain. Each emits events.

### booking-service ✅
- Source files committed: `src/index.js`, `src/app.js`, `src/db.js`, `src/nats.js`, `src/routes/bookings.js`
- `package.json` + `package-lock.json` present
- Dockerfile fixed: renamed `node` user → `appuser` (conflict with base image resolved)
- Docker image built and verified: `booking-service:v1` (214MB)
- Commit: `feat(booking-service): add source files, Dockerfile fix, package-lock` (`97ddc3d`)

### api-gateway 🔄
- Source files present: `src/app.js`, `src/env.validate.js`, `src/index.js`, `src/routes/`, `src/middleware/`, `src/metrics/`
- **Next step:** Run `docker build -t api-gateway:v1 .` to verify image builds cleanly

### auth-service ❌
- Directory scaffolded — source files not yet committed
- Stack: Python / FastAPI
- Needs: `GET /health`, `POST /register`, `POST /login` (JWT), NATS publish `auth.user_registered`, Prometheus metrics via `prometheus-fastapi-instrumentator`

### notification-service ❌
- Directory scaffolded — source files not yet committed
- Stack: Python / FastAPI
- Needs: NATS subscriber for `booking.created` + `auth.user_registered`; `GET /health` only

### metrics-service ✅
- Source files committed: `src/index.js`
- `package.json` present
- Dockerfile: non-root `appuser`, healthcheck, `EXPOSE 3002`
- Docker image built and verified: `metrics-service:v1` (240MB / 58MB compressed)
- Implements: WebSocket server (`ws`), NATS wildcard subscriber (`>`), Prometheus default metrics (`prom-client`), in-memory event log (last 100 events), HTTP `/health` + `/metrics` endpoints
- Commit: `feat: add metrics-service with WebSocket, NATS subscriber, and Prometheus` (`286bd5b`)
- Tag: `metrics-service-v1`

---

## PHASE 3: Kubernetes Manifests ❌

Namespace, ConfigMaps, secrets template; Deployments and Services for all five services; Ingress for `/api/*` and `/ws`.

---

## PHASE 4: NATS Event Bus Setup ❌

Helm deploy NATS; shared event schema in `shared/events`; subjects contract; event chain testing.

---

## PHASE 5: Prometheus + Metrics ❌

kube-prometheus-stack; `/metrics` on services; metrics-service aggregates Prometheus + K8s + NATS → WebSocket.

---

## PHASE 6: React Live Dashboard ❌

Topology (React Flow), PodCard, EventStream, TrafficGraph, `useLivePlatform` hook.

---

## PHASE 7: Horizontal Pod Autoscaling Demo ❌

HPA for booking-service; k6 load test; GIF for README.

---

## PHASE 8: Cloud Deploy (AWS EKS) ❌

eksctl cluster; ECR push; manifests; frontend on Vercel/S3.

---

## PHASE 9: README + Demo ❌

Mermaid/Excalidraw diagram; three GIFs; full README sections and live demo URL.

---

## Quick Status Overview

| Phase | Status | Key Deliverable |
|-------|--------|-----------------|
| 1 — K8s Local | ✅ | Monorepo scaffold ✅ · toolchain ✅ · Minikube + addons ✅ |
| 2 — Services | 🔄 | booking-service ✅ · api-gateway 🔄 · auth ❌ · notification ❌ · metrics-service ✅ |
| 3 — K8s Manifests | ❌ | Deployments + Ingress |
| 4 — NATS | ❌ | Event-driven architecture |
| 5 — Prometheus | ❌ | Live metrics scraping |
| 6 — React Dashboard | ❌ | Live K8s visualization |
| 7 — HPA Demo | ❌ | Auto-scaling in action |
| 8 — EKS Deploy | ❌ | Live on AWS |
| 9 — README | ❌ | Demo GIFs |

---

## Estimated Timeline

| Phase | Estimated Hours |
|-------|-----------------|
| 1 — K8s Setup | 2 hrs |
| 2 — Services | 10 hrs |
| 3 — K8s Manifests | 4 hrs |
| 4 — NATS | 4 hrs |
| 5 — Prometheus | 3 hrs |
| 6 — React Dashboard | 8 hrs |
| 7 — HPA | 2 hrs |
| 8 — EKS Deploy | 4 hrs |
| 9 — README | 3 hrs |
| **Total** | **~40 hrs** |

---

## Docker Desktop (notes)

- Minikube container running: `fa53fbc76dfa` · 39.9% CPU · 762.6MB / 3GB RAM
- Docker Desktop v4.69.0 · RAM 7.21GB · CPU 12.07% · Disk 5.65GB used

---

## The Three GIFs That Got Me the Interview

1. **Pod self-healing:** Kill a pod → K8s restarts it → UI shows recovery.
2. **Event-driven flow:** Book a session → event cascade through NATS → email arrives.
3. **HPA scale-up:** Load test → booking-service scales 1 → 5 replicas.

---

## Recent Commits

| Commit | Message |
|--------|---------|
| `286bd5b` | feat: add metrics-service with WebSocket, NATS subscriber, and Prometheus |
| `metrics-service-v1` (tag) | metrics-service initial build v1 |
| `3b85dfc` | docs(PRD): bump to v2.1 - phase 2 service details and monorepo paths |
| `97ddc3d` | feat(booking-service): add source files, Dockerfile fix, package-lock |
| `d5ab3ca` | fix(booking-service): rename node→appuser, add package-lock.json |

---

*This PRD is the single source of truth for scope and phase deliverables.*
