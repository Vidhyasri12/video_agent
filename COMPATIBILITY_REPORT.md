# TP-Link VIGI & VMS Integration Compatibility Report

## Executive Summary

This report documents the compatibility, support status, and architectural audit of all TP-Link VIGI and VMS features implemented within the **VideoAgent** platform.

To ensure enterprise production readiness, features are strictly audited against official TP-Link documentation and standard video streaming protocols. Undocumented or assumed APIs (such as cloud OpenAPI OAuth2 endpoints, WebRTC/HLS cloud relays, and cloud webhooks) are categorized as **Experimental** and isolated behind feature flags.

---

## Capability & Interface Matrix

| Feature / Interface | Implementation Mechanism | Support Status | Verification Status | Official TP-Link Documentation Reference | Production Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **RTSP Live Streaming** | `rtsp://<user>:<pass>@<ip>:554/stream1` (Main) / `stream2` (Sub) / `live/1/1/avm` (NVR) | **Officially Supported** | Verified via RTSP protocol & openCV ingestion | TP-Link VIGI NVR & Camera RTSP Stream User Guide | **Production Ready** |
| **ONVIF Camera Discovery** | WS-Discovery Multicast (UDP port 3702 `dn:NetworkVideoTransmitter`) | **Officially Supported** | Verified via socket multicast probe | ONVIF Profile S Core Specification v2.1 / TP-Link VIGI ONVIF Specs | **Production Ready** |
| **Local VMS Integration** | Direct RTSP / HTTP API connection to VIGI VMS software host | **Officially Supported** | Verified via network socket & stream test | TP-Link VIGI VMS User Manual | **Production Ready** |
| **Device Authentication** | RTSP Digest/Basic Authentication & Local Credentials | **Officially Supported** | Verified via stream access control | TP-Link VIGI Security Architecture Specification | **Production Ready** |
| **Provider Architecture** | Polymorphic abstraction (`VigiProvider`, `HikvisionProvider`, `DahuaProvider`, `AxisProvider`, `MockProvider`) | **Officially Supported** | Verified via test suite & factory instantiation | Standard Software Architecture (GoF Factory & Strategy Patterns) | **Production Ready** |
| **Runtime Capability Detection** | `/api/v1/vigi/capabilities` endpoint | **Officially Supported** | Verified via backend API & frontend UI state engine | OpenAPI 3.0 Standard Schema | **Production Ready** |
| **VIGI Cloud OAuth2 API** | `/api/v1/vigi/cloud/auth` | **Experimental** | Unverified / Undocumented by TP-Link Cloud | *Experimental - Not officially documented by TP-Link* | **Isolated (Disabled by default via `ENABLE_EXPERIMENTAL_CLOUD_APIS`)** |
| **VIGI Cloud Stream Tickets** | WebRTC / HLS relay endpoints (`/api/v1/vigi/cloud/stream-ticket`) | **Experimental** | Unverified / Undocumented by TP-Link Cloud | *Experimental - Not officially documented by TP-Link* | **Isolated (Disabled by default via `ENABLE_EXPERIMENTAL_CLOUD_APIS`)** |
| **VIGI Cloud Webhooks** | Event alert push endpoints (`/api/v1/vigi/cloud/webhook`) | **Experimental** | Unverified / Undocumented by TP-Link Cloud | *Experimental - Not officially documented by TP-Link* | **Isolated (Disabled by default via `ENABLE_EXPERIMENTAL_CLOUD_APIS`)** |
| **Simulated Stream Fallback** | Hardcoded sample video fallbacks | **Mock / Demo** | Software simulation | Internal VideoAgent Demo Suite | **Isolated (Disabled by default via `ENABLE_MOCK_PROVIDER`)** |

---

## Detailed Audit Breakdown

### 1. Officially Supported Features (Production Ready)

#### RTSP Live Stream Ingestion
- **Main Stream (High Quality)**: `rtsp://username:password@<IP>:554/stream1`
- **Sub Stream (Lower Latency)**: `rtsp://username:password@<IP>:554/stream2`
- **NVR Multi-Channel Stream**: `rtsp://username:password@<IP>:554/live/<channel_number>/1/avm`
- **Doc Reference**: TP-Link VIGI Camera & NVR Configuration Manual (RTSP RFC 2326 compliant).

#### ONVIF WS-Discovery
- Local subnet discovery using multicast UDP probe sent to `239.255.255.250:3702`.
- Auto-detects VIGI camera IP addresses and ONVIF profile endpoints.
- **Doc Reference**: ONVIF Core Specification v2.1 section 7 (WS-Discovery).

#### Provider Architecture
- Standardized `CameraProvider` interface enabling seamless switching between TP-Link VIGI, Hikvision, Dahua, Axis, and Mock providers without breaking upper-layer logic.

---

### 2. Experimental Features (Isolated Behind Feature Flags)

The following APIs are marked as **Experimental** because official public documentation from TP-Link is not available for direct VIGI Cloud VMS third-party integration:
- `POST /api/v1/vigi/cloud/auth`
- `GET /api/v1/vigi/cloud/devices`
- `POST /api/v1/vigi/cloud/stream-ticket`
- `POST /api/v1/vigi/cloud/webhook`
- `GET /api/v1/vigi/cloud/webhooks`
- `GET /api/v1/vigi/cloud/stream`
- `POST /api/v1/vigi/cloud/summarize`
- `GET /api/v1/vigi/cloud/status`

**Enforcement Policy**:
Controlled by environment variable `ENABLE_EXPERIMENTAL_CLOUD_APIS` (default: `False`). When disabled, accessing any of these endpoints returns HTTP `501 Not Implemented` with an explicit `UNSUPPORTED_CAPABILITY` payload.

---

### 3. Mock / Demo Functionality

- Simulated camera feeds and sample video playback are isolated within `MockProvider`.
- Controlled by environment variable `ENABLE_MOCK_PROVIDER` (default: `False`).
- When real camera RTSP connection fails in production mode (`ENABLE_MOCK_PROVIDER=False`), the system raises a `CameraOfflineError` rather than silently serving mock footage.

---

## Production Security & Hardening Safeguards

1. **Zero Credential Exposure**: Sensitive fields (`password`, `access_token`, `client_secret`) are automatically redacted from API responses and structured log files.
2. **Exponential Backoff**: Stream connection and discovery attempts utilize exponential backoff retries with random jitter to prevent server throttling. Authentication retries are strictly capped at 3 attempts to avoid account lockout.
3. **Structured Exception Taxonomy**: Replaced generic exceptions with specific `VmsException` error types (`CameraOfflineError`, `AuthenticationFailedError`, `RTSPTimeoutError`, `UnsupportedCapabilityError`, `NetworkFailureError`).
