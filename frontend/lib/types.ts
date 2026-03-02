export type PromptSummary = {
  prompt_key: string;
  description: string | null;
  owner_team: string | null;
  updated_at: string;
  active_version: number | null;
};

export type PromptVersion = {
  id: number;
  version: number;
  status: string;
  checksum: string;
  content: string;
  variables_schema: Record<string, unknown> | null;
  created_by: string | null;
  created_at: string;
  updated_at: string;
};

export type PromptDetail = {
  prompt_key: string;
  description: string | null;
  owner_team: string | null;
  active_version_id: number | null;
  versions: PromptVersion[];
};

export type PushDeliveryItem = {
  id: number;
  publish_event_id: number;
  agent_id: number;
  status: string;
  attempt: number;
  last_http_status: number | null;
  last_error: string | null;
  next_retry_at: string | null;
  updated_at: string;
};

export type PublishEventItem = {
  publish_event_id: number;
  prompt_key: string;
  version: number;
  environment: string;
  published_by: string | null;
  published_at: string;
  deliveries: PushDeliveryItem[];
};
