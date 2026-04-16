# Cloud Native Microservices Live Platform — PRD

**Product:** Self-demonstrating microservices platform — the visualizer IS the system  
**Version:** 2.0  
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

## Delivery discipline (commits & PRD)

Work is checkpointed at every meaningful boundary:

1. **After** completing any **Main Step**, **Phase**, **EPIC**, or **Agent Task**: **commit** with a clear, scoped message and **push** to `main` (or the active integration branch).
2. **Immediately after** that push: **update this `PRD.md`** — phase/task status, tables, and notes — so the document stays aligned with the repo and remains the single source of truth for progress.

Skipping either step should be the exception (e.g., blocked network), not the default.

---

## Agent tasks (A1–A9)

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
│  │ (Node)   │  │ (Python) │  │  (Go)    │  │(Python)│ │
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
| PHASE 1 | Local K8s Environment (Minikube) | 🔄 IN PROGRESS |
| PHASE 2 | Microservices — Build Each Service | ❌ NOT STARTED |
| PHASE 3 | Kubernetes Manifests | ❌ NOT STARTED |
| PHASE 4 | NATS Event Bus Setup | ❌ NOT STARTED |
| PHASE 5 | Prometheus + Metrics | ❌ NOT STARTED |
| PHASE 6 | React Live Dashboard | ❌ NOT STARTED |
| PHASE 7 | Horizontal Pod Autoscaling Demo | ❌ NOT STARTED |
| PHASE 8 | Cloud Deploy (AWS EKS or GKE) | ❌ NOT STARTED |
| PHASE 9 | README + Demo Video | ❌ NOT STARTED |

---

## PHASE 1: Local K8s Environment

### Task 1: Install Toolchain

**Status:** 🔄 In progress — CLIs installed (Scoop: kubectl, minikube, helm, k9s); **Minikube cluster not running** until Docker Desktop is installed and on `PATH`, then `minikube start --driver=docker ...` + addons.

- Install Minikube, kubectl, Helm, k9s — **done on dev machine via Scoop** (see `scripts/install-toolchain.ps1`). Verify with `scripts/verify-toolchain.ps1`.
- Start Minikube with `--cpus=4 --memory=8192 --disk-size=20g`; enable **ingress** and **metrics-server** addons — **pending Docker**.
- Commit: `chore: toolchain setup + Minikube running`

**A1 completion checklist (run on your machine):**

1. **Docker Desktop** — Install for Windows, finish first-run setup, confirm `docker version` works in PowerShell (Docker must be on `PATH`).
2. **Cluster + addons** — From repo root: `.\scripts\install-toolchain.ps1` (installs CLIs if needed, then starts Minikube and enables addons when `docker` exists). *Or* run only the Minikube lines if CLIs are already installed:
   - `minikube start --driver=docker --cpus=4 --memory=8192 --disk-size=20g`
   - `minikube addons enable ingress`
   - `minikube addons enable metrics-server`
3. **Verify** — `.\scripts\verify-toolchain.ps1`; `kubectl get nodes`; `minikube status`; `minikube addons list` (ingress and metrics-server enabled).
4. **Gate** — When the above passes, mark **A1** ✅ and **PHASE 1** complete in this file, commit + push, then begin **A2** (microservices).

Until A1 is finished locally, `git status` may stay clean — there is nothing to commit until you update the PRD after Minikube is up or add automation/docs from that work.

### Task 2: Monorepo Scaffold

**Status:** ✅ Complete

- Create project root (this repo root; PRD names `/microservices-live-platform/` as conceptual).
- Directories: `services/api-gateway`, `services/auth-service`, `services/booking-service`, `services/notification-service`, `services/metrics-service`, `k8s`, `k8s/base`, `k8s/monitoring`, `frontend`, `scripts` (plus `services/*/src`, `frontend/src/components/{topology,events,metrics}`, `frontend/src/hooks`, `shared/events`).
- Root `docker-compose.yml` for local dev (before K8s) — Postgres + NATS only.
- Root `README.md` with architecture diagram placeholder; root `.gitignore`, `.env.example`.
- Commit: `chore: monorepo scaffold with service directories`

---

## PHASE 2: Microservices — Build Each Service

Each service is a separate Docker image. Each owns its domain. Each emits events.

- **API Gateway (Node/Express):** health, proxy routes, NATS `request.received`.
- **Auth (Python/FastAPI):** register, login, JWT, NATS `user.registered`.
- **Booking (Node/Express per PRD stretch):** create/list bookings, Postgres, NATS `booking.created`.
- **Notification (Python/FastAPI):** NATS subscriber for `booking.created`, `user.registered`; health only otherwise.
- **Metrics (Node):** K8s API + NATS + WebSocket to UI.

---

## PHASE 3: Kubernetes Manifests

Namespace, ConfigMaps, secrets template; Deployments and Services for all five services; Ingress for `/api/*` and `/ws`.

---

## PHASE 4: NATS Event Bus Setup

Helm deploy NATS; shared event schema in `shared/events`; subjects contract; event chain testing.

---

## PHASE 5: Prometheus + Metrics

kube-prometheus-stack; `/metrics` on services; metrics-service aggregates Prometheus + K8s + NATS → WebSocket.

---

## PHASE 6: React Live Dashboard

Topology (React Flow), PodCard, EventStream, TrafficGraph, `useLivePlatform` hook.

---

## PHASE 7: Horizontal Pod Autoscaling Demo

HPA for booking-service; k6 load test; GIF for README.

---

## PHASE 8: Cloud Deploy (AWS EKS)

eksctl cluster; ECR push; manifests; frontend on Vercel/S3.

---

## PHASE 9: README + Demo

Mermaid/Excalidraw diagram; three GIFs; full README sections and live demo URL.

---

## Quick Status Overview

| Phase | Status | Key Deliverable |
|-------|--------|-----------------|
| 1 — K8s Local | 🔄 | Monorepo scaffold ✅; toolchain CLIs ✅ (Scoop); Minikube cluster + addons ⏳ (needs Docker) |
| 2 — Services | ❌ | 5 Dockerized microservices |
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

## The Three GIFs That Got me the Interview

1. **Pod self-healing:** Kill a pod → K8s restarts it → UI shows recovery.
2. **Event-driven flow:** Book a session → event cascade through NATS → email arrives.
3. **HPA scale-up:** Load test → booking-service scales 1 → 5 replicas.

---

*This PRD is the single source of truth for scope and phase deliverables. Detailed step-by-step checklists for Phases 2–9 follow the same structure as the original v2.0 specification (service files, Helm commands, exact YAML snippets, and README section list).*
