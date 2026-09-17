export interface TimelineEvent {
  time: string;
  seconds?: number;
  event: string;
  tag: string;
}

export interface VigiMetadata {
  channel_id: string;
  channel_name: string;
  vigi_model: string;
  ip_address: string;
  rtsp_url: string;
  capture_timestamp: string;
  protocol: string;
  is_live: boolean;
}

export interface VideoDescription {
  title: string;
  summary: string;
  scene_type: string;
  duration_est: string;
  confidence: number;
  detected_objects: string[];
  timeline: TimelineEvent[];
  safety_highlights: string[];
  agent_provider?: string;
  vigi_metadata?: VigiMetadata;
}

export interface VigiChannel {
  channel_id: string;
  name: string;
  location: string;
  model: string;
  ip_address: string;
  port: number;
  status: string;
  resolution: string;
  fps: number;
  rtsp_url: string;
  sample_video?: string;
  video_url?: string;
}

export interface VigiConfig {
  vigi_rtsp_url: string;
  vigi_host: string;
  vigi_port: number;
  vigi_username: string;
  connection_type?: string;
  camera_provider?: string;
  enable_experimental_cloud_apis?: boolean;
  enable_mock_provider?: boolean;
}

export interface VigiCapabilities {
  status: string;
  provider: string;
  provider_name: string;
  capabilities: {
    supports_rtsp: boolean;
    supports_onvif: boolean;
    supports_openapi: boolean;
    supports_edge_connector?: boolean;
    supports_cloud_streaming?: boolean;
    supports_cloud_api?: boolean;
    supports_webhooks?: boolean;
    supports_ptz: boolean;
    supports_event_subscriptions?: boolean;
    supports_configuration?: boolean;
  };
  supported_providers: Record<string, string>;
}

export interface VigiHealthStatus {
  status: string;
  provider: string;
  display_name: string;
  total_channels?: number;
  capabilities: Record<string, boolean>;
  timestamp: string;
}

export interface VigiEdgeStreamHealth {
  channel_id: string;
  name: string;
  ip_address: string;
  rtsp_url: string;
  status: string;
  latency_ms: number;
  fps: number;
  packet_loss_pct: number;
  consecutive_failures: number;
  last_ping_time: string;
  reconnect_attempts: number;
  transport: string;
  edge_connector_id: string;
}

export interface VigiEdgeStatus {
  status: string;
  edge_connector_id: string;
  connector_status: string;
  total_streams: number;
  healthy_streams: number;
  reconnecting_streams: number;
  offline_streams: number;
  streams: VigiEdgeStreamHealth[];
  timestamp: string;
}

export interface VigiEdgeForwardedEvent {
  event_id: string;
  edge_connector_id: string;
  channel_id: string;
  channel_name: string;
  event_type: string;
  confidence: number;
  timestamp: string;
  transport_protocol: string;
  snapshot_url: string;
  clip_url: string;
  metadata: Record<string, any>;
  raw_stream_forwarded: boolean;
  cloud_status: string;
}

export interface VigiOpenApiDevice {
  device_id: string;
  name: string;
  location: string;
  model: string;
  ip_address: string;
  mac_address: string;
  firmware_version: string;
  status: string;
  openapi_enabled: boolean;
  rtsp_url: string;
  capabilities: string[];
}

export interface VigiOpenApiConfig {
  resolution: string;
  fps: number;
  bitrate_kbps: number;
  motion_sensitivity: number;
  night_vision_mode: string;
  wdr_enabled: boolean;
}

export interface VigiConnectRequest {
  vigi_host?: string;
  port?: number;
  username?: string;
  password?: string;
  rtsp_url?: string;
  provider?: string;
}

export interface VigiSummarizeRequest {
  channel_id?: string;
  rtsp_url?: string;
  vigi_host?: string;
  username?: string;
  password?: string;
  duration_seconds?: number;
}

export interface UploadVideoResponse {
  camera_id: string;
  camera_name: string;
  video_info: {
    video_id: string;
    filename: string;
    original_filename?: string;
    video_url: string;
    thumbnail_url: string;
    size_bytes: string;
  };
  description?: VideoDescription;
}

export interface SummaryData {
  id: string;
  camera_id?: string;
  timeframe_type: string;
  start_time: string;
  end_time: string;
  summary_text: string;
  metrics_json: {
    total_events?: number;
    people_count?: number;
    vehicle_count?: number;
    critical_alerts?: number;
    [key: string]: any;
  };
  created_at: string;
}

export interface VigiCloudDevice {
  device_id: string;
  name: string;
  location: string;
  model: string;
  status: string;
  connection_type: string;
  resolution: string;
  fps: number;
  mac_address: string;
  firmware: string;
  cloud_org_id: string;
  relay_stream_url: string;
  sample_video?: string;
}

export interface VigiCloudAuthRequest {
  client_id?: string;
  client_secret?: string;
  cloud_org_id?: string;
}

export interface VigiCloudStreamTicket {
  status: string;
  ticket_id: string;
  device_id: string;
  device_name: string;
  protocol: string;
  webrtc_sdp_endpoint: string;
  cloud_hls_endpoint: string;
  mjpeg_proxy_endpoint: string;
  expires_in_seconds: number;
  created_at: string;
}

export interface VigiCloudWebhookEvent {
  event_id?: string;
  device_id?: string;
  device_name?: string;
  location?: string;
  event_type?: string;
  timestamp?: string;
  snapshot_url?: string;
  status?: string;
}

export interface VigiCloudSummarizeRequest {
  device_id?: string;
  duration_seconds?: number;
}

export interface VigiCloudStatus {
  status: string;
  vigi_cloud_gateway: string;
  authenticated: boolean;
  registered_devices_count: number;
  cloud_devices: VigiCloudDevice[];
  recent_webhooks_count: number;
  supported_protocols: string[];
}

export interface ChatMessage {
  id: string;
  sender: 'user' | 'assistant';
  text: string;
  timestamp: string;
  videoTimestamp?: number;
  suggestions?: string[];
}

export interface VideoChatRequest {
  filename?: string;
  question: string;
  video_title?: string;
}

export interface VideoChatResponse {
  status: string;
  filename: string;
  question: string;
  answer: string;
  timeline?: TimelineEvent[];
  detected_objects?: string[];
  safety_highlights?: string[];
}
