import axios from 'axios';
import {
  UploadVideoResponse,
  VideoDescription,
  SummaryData,
  VigiChannel,
  VigiConfig,
  VigiCapabilities,
  VigiHealthStatus,
  VigiConnectRequest,
  VigiSummarizeRequest,
  VigiEdgeStatus,
  VigiEdgeForwardedEvent,
  VigiOpenApiDevice,
  VigiOpenApiConfig,
  VigiCloudDevice,
  VigiCloudAuthRequest,
  VigiCloudStreamTicket,
  VigiCloudWebhookEvent,
  VigiCloudSummarizeRequest,
  VigiCloudStatus,
  VideoChatRequest,
  VideoChatResponse
} from '../types';

const API_BASE = import.meta.env.VITE_API_BASE || '/api/v1';
const BACKEND_BASE = import.meta.env.VITE_BACKEND_BASE ?? '';

export function getBackendBase(): string {
  return BACKEND_BASE;
}

export function getApiBase(): string {
  return API_BASE;
}

export const api = {
  uploadVideo: async (file: File, cameraName: string = "Uploaded Video"): Promise<UploadVideoResponse> => {
    const formData = new FormData();
    formData.append('file', file);
    const res = await axios.post(`${API_BASE}/video/upload?camera_name=${encodeURIComponent(cameraName)}`, formData, {
      timeout: 120000
    });
    return res.data;
  },

  describeVideo: async (filename: string): Promise<{ description: VideoDescription; summary?: VideoDescription }> => {
    const res = await axios.post(`${API_BASE}/video/summarize?filename=${encodeURIComponent(filename)}`, {}, {
      timeout: 60000
    });
    return res.data;
  },

  // Capability & Health Endpoints
  getVigiCapabilities: async (provider?: string): Promise<VigiCapabilities> => {
    const url = provider ? `${API_BASE}/vigi/capabilities?provider=${encodeURIComponent(provider)}` : `${API_BASE}/vigi/capabilities`;
    const res = await axios.get(url, { timeout: 10000 });
    return res.data;
  },

  getVigiHealth: async (provider?: string): Promise<VigiHealthStatus> => {
    const url = provider ? `${API_BASE}/vigi/health?provider=${encodeURIComponent(provider)}` : `${API_BASE}/vigi/health`;
    const res = await axios.get(url, { timeout: 10000 });
    return res.data;
  },

  // TP-Link VIGI Core Endpoints
  getVigiConfig: async (): Promise<VigiConfig> => {
    const res = await axios.get(`${API_BASE}/vigi/config`, { timeout: 10000 });
    return res.data;
  },

  updateVigiConfig: async (payload: { vigi_host?: string; vigi_rtsp_url?: string; username?: string; password?: string; connection_type?: string; provider?: string }): Promise<VigiConfig> => {
    const res = await axios.post(`${API_BASE}/vigi/update-config`, payload, { timeout: 10000 });
    return res.data;
  },

  getVigiChannels: async (provider?: string): Promise<{ channels: VigiChannel[]; vigi_rtsp_url?: string }> => {
    const url = provider ? `${API_BASE}/vigi/channels?provider=${encodeURIComponent(provider)}` : `${API_BASE}/vigi/channels`;
    const res = await axios.get(url, { timeout: 10000 });
    return res.data;
  },

  connectVigi: async (payload: VigiConnectRequest): Promise<any> => {
    const res = await axios.post(`${API_BASE}/vigi/connect`, payload, { timeout: 15000 });
    return res.data;
  },

  summarizeVigiStream: async (payload: VigiSummarizeRequest): Promise<{ description: VideoDescription; summary?: string; vigi_metadata?: any }> => {
    const res = await axios.post(`${API_BASE}/vigi/summarize`, payload, { timeout: 45000 });
    return res.data;
  },

  // VIGI Edge Connector Endpoints
  getEdgeStatus: async (): Promise<VigiEdgeStatus> => {
    const res = await axios.get(`${API_BASE}/vigi/edge/status`, { timeout: 10000 });
    return res.data;
  },

  discoverEdgeCameras: async (): Promise<{ status: string; count: number; devices: any[] }> => {
    const res = await axios.get(`${API_BASE}/vigi/edge/discover`, { timeout: 10000 });
    return res.data;
  },

  reconnectEdgeStream: async (channelId: string): Promise<any> => {
    const res = await axios.post(`${API_BASE}/vigi/edge/reconnect`, { channel_id: channelId }, { timeout: 10000 });
    return res.data;
  },

  forwardEdgeEvent: async (payload: { channel_id: string; event_type: string; confidence?: number; snapshot_url?: string; clip_url?: string }): Promise<any> => {
    const res = await axios.post(`${API_BASE}/vigi/edge/forward-event`, payload, { timeout: 10000 });
    return res.data;
  },

  getEdgeForwardedEvents: async (limit: number = 20): Promise<{ status: string; count: number; events: VigiEdgeForwardedEvent[] }> => {
    const res = await axios.get(`${API_BASE}/vigi/edge/forwarded-events?limit=${limit}`, { timeout: 10000 });
    return res.data;
  },

  // VIGI OpenAPI Integration Endpoints
  getOpenApiDevices: async (): Promise<{ status: string; count: number; devices: VigiOpenApiDevice[] }> => {
    const res = await axios.get(`${API_BASE}/vigi/openapi/devices`, { timeout: 10000 });
    return res.data;
  },

  getOpenApiDeviceConfig: async (deviceId: string): Promise<{ status: string; device_id: string; config: VigiOpenApiConfig }> => {
    const res = await axios.get(`${API_BASE}/vigi/openapi/config/${deviceId}`, { timeout: 10000 });
    return res.data;
  },

  updateOpenApiDeviceConfig: async (deviceId: string, updates: Partial<VigiOpenApiConfig>): Promise<any> => {
    const res = await axios.post(`${API_BASE}/vigi/openapi/config/${deviceId}`, updates, { timeout: 10000 });
    return res.data;
  },

  subscribeOpenApiEvents: async (payload: { webhook_url: string; event_types?: string[]; device_ids?: string[] }): Promise<any> => {
    const res = await axios.post(`${API_BASE}/vigi/openapi/subscribe`, payload, { timeout: 10000 });
    return res.data;
  },

  // TP-Link VIGI Cloud VMS API (Experimental - feature flag check)
  authVigiCloud: async (payload: VigiCloudAuthRequest = {}): Promise<any> => {
    const res = await axios.post(`${API_BASE}/vigi/cloud/auth`, payload, { timeout: 10000 });
    return res.data;
  },

  getVigiCloudDevices: async (): Promise<{ status: string; count: number; devices: VigiCloudDevice[] }> => {
    const res = await axios.get(`${API_BASE}/vigi/cloud/devices`, { timeout: 10000 });
    return res.data;
  },

  getVigiCloudTicket: async (deviceId: string): Promise<VigiCloudStreamTicket> => {
    const res = await axios.post(`${API_BASE}/vigi/cloud/stream-ticket`, { device_id: deviceId }, { timeout: 10000 });
    return res.data;
  },

  sendVigiCloudWebhook: async (payload: VigiCloudWebhookEvent): Promise<any> => {
    const res = await axios.post(`${API_BASE}/vigi/cloud/webhook`, payload, { timeout: 10000 });
    return res.data;
  },

  getVigiCloudWebhooks: async (): Promise<{ status: string; history: VigiCloudWebhookEvent[] }> => {
    const res = await axios.get(`${API_BASE}/vigi/cloud/webhooks`, { timeout: 10000 });
    return res.data;
  },

  getVigiCloudStatus: async (): Promise<VigiCloudStatus> => {
    const res = await axios.get(`${API_BASE}/vigi/cloud/status`, { timeout: 10000 });
    return res.data;
  },

  summarizeVigiCloudStream: async (payload: VigiCloudSummarizeRequest): Promise<{ description: VideoDescription; summary?: string; vigi_metadata?: any }> => {
    const res = await axios.post(`${API_BASE}/vigi/cloud/summarize`, payload, { timeout: 45000 });
    return res.data;
  },

  chatWithVideoAssistant: async (payload: VideoChatRequest): Promise<VideoChatResponse> => {
    const res = await axios.post(`${API_BASE}/video/chat`, payload, { timeout: 30000 });
    return res.data;
  },

  // NVIDIA VSS Settings
  getNvidiaStatus: async (): Promise<{
    nvidia_api_configured: boolean;
    nvidia_key_preview: string | null;
    model: string;
    vss_url: string;
    mode: string;
    description: string;
  }> => {
    const res = await axios.get(`${API_BASE}/settings/status`, { timeout: 5000 });
    return res.data;
  },

  setNvidiaKey: async (api_key: string, model?: string): Promise<{
    status: string;
    nvidia_api_configured: boolean;
    model: string;
    message: string;
  }> => {
    const res = await axios.post(`${API_BASE}/settings/nvidia`, { api_key, model }, { timeout: 10000 });
    return res.data;
  }
};
