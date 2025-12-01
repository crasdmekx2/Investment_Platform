export type JobStatus = 'pending' | 'active' | 'paused' | 'completed' | 'failed';
export type TriggerType = 'cron' | 'interval';
export type AssetType = 'stock' | 'forex' | 'crypto' | 'bond' | 'commodity' | 'economic_indicator';
export type ExecutionStatus = 'running' | 'success' | 'failed' | 'cancelled';
export type CollectionStatus = 'success' | 'failed' | 'partial';
export type DependencyCondition = 'success' | 'complete' | 'any';
export type ErrorCategory = 'transient' | 'permanent' | 'system';

export interface CronTriggerConfig {
  type: 'cron';
  year?: string;
  month?: string;
  day?: string;
  week?: string;
  day_of_week?: string;
  hour?: string;
  minute?: string;
  second?: string;
  execute_now?: boolean;
}

export interface IntervalTriggerConfig {
  type: 'interval';
  weeks?: number;
  days?: number;
  hours?: number;
  minutes?: number;
  seconds?: number;
  execute_now?: boolean;
}

export type TriggerConfig = CronTriggerConfig | IntervalTriggerConfig;

export interface JobDependency {
  depends_on_job_id: string;
  condition?: DependencyCondition;
}

export interface ScheduledJob {
  job_id: string;
  symbol: string;
  asset_type: AssetType;
  trigger_type: TriggerType;
  trigger_config: TriggerConfig;
  start_date?: string;
  end_date?: string;
  collector_kwargs?: Record<string, unknown>;
  asset_metadata?: Record<string, unknown>;
  status: JobStatus;
  created_at: string;
  updated_at: string;
  last_run_at?: string;
  next_run_at?: string;
  dependencies?: JobDependency[];
  max_retries?: number;
  retry_delay_seconds?: number;
  retry_backoff_multiplier?: number;
}

export interface JobCreate {
  symbol: string;
  asset_type: AssetType;
  trigger_type: TriggerType;
  trigger_config: TriggerConfig;
  start_date?: string;
  end_date?: string;
  collector_kwargs?: Record<string, unknown>;
  asset_metadata?: Record<string, unknown>;
  job_id?: string;
  dependencies?: JobDependency[];
  max_retries?: number;
  retry_delay_seconds?: number;
  retry_backoff_multiplier?: number;
}

export interface JobUpdate {
  symbol?: string;
  asset_type?: AssetType;
  trigger_type?: TriggerType;
  trigger_config?: TriggerConfig;
  start_date?: string;
  end_date?: string;
  collector_kwargs?: Record<string, unknown>;
  asset_metadata?: Record<string, unknown>;
  status?: JobStatus;
  dependencies?: JobDependency[];
  max_retries?: number;
  retry_delay_seconds?: number;
  retry_backoff_multiplier?: number;
}

export interface JobExecution {
  execution_id: number;
  job_id: string;
  log_id?: number;
  execution_status: ExecutionStatus;
  started_at: string;
  completed_at?: string;
  error_message?: string;
  error_category?: ErrorCategory;
  execution_time_ms?: number;
  retry_attempt?: number;
  created_at: string;
}

export interface CollectionLog {
  log_id: number;
  asset_id: number;
  collector_type: string;
  start_date: string;
  end_date: string;
  records_collected: number;
  status: CollectionStatus;
  error_message?: string;
  execution_time_ms?: number;
  created_at: string;
}

export interface CollectorMetadata {
  [assetType: string]: {
    name: string;
    description: string;
    collector_class: string;
    intervals?: string[];
    granularities?: string[];
    default_interval?: string;
    default_granularity?: string;
    supports_dividends?: boolean;
    supports_splits?: boolean;
    symbol_format?: string;
    series_ids?: string[];
    common_symbols?: string[];
    common_indicators?: string[];
  };
}

export interface AssetOption {
  symbol: string;
  name: string;
}

export interface CollectRequest {
  symbol: string;
  asset_type: AssetType;
  start_date?: string;
  end_date?: string;
  incremental: boolean;
  collector_kwargs?: Record<string, unknown>;
  asset_metadata?: Record<string, unknown>;
}

export interface CollectResponse {
  job_id: string;
  status: string;
  message: string;
  records_loaded?: number;
}

export interface Asset {
  asset_id: number;
  symbol: string;
  asset_type: AssetType;
  name: string;
  exchange?: string;
  currency?: string;
  sector?: string;
  industry?: string;
  base_currency?: string;
  quote_currency?: string;
  series_id?: string;
  security_type?: string;
  source: string;
  metadata?: Record<string, unknown>;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface DataCoverage {
  asset_id: number;
  asset_type: AssetType;
  has_data: boolean;
  earliest_date?: string;
  latest_date?: string;
  record_count: number;
}

export interface JobTemplate {
  template_id: number;
  name: string;
  description?: string;
  symbol?: string;
  asset_type: AssetType;
  trigger_type: TriggerType;
  trigger_config: TriggerConfig;
  start_date?: string;
  end_date?: string;
  collector_kwargs?: Record<string, unknown>;
  asset_metadata?: Record<string, unknown>;
  max_retries?: number;
  retry_delay_seconds?: number;
  retry_backoff_multiplier?: number;
  is_public: boolean;
  created_by?: string;
  created_at: string;
  updated_at: string;
}

export interface JobTemplateCreate {
  name: string;
  description?: string;
  symbol?: string;
  asset_type: AssetType;
  trigger_type: TriggerType;
  trigger_config: TriggerConfig;
  start_date?: string;
  end_date?: string;
  collector_kwargs?: Record<string, unknown>;
  asset_metadata?: Record<string, unknown>;
  max_retries?: number;
  retry_delay_seconds?: number;
  retry_backoff_multiplier?: number;
  is_public?: boolean;
  created_by?: string;
}

export interface JobTemplateUpdate {
  name?: string;
  description?: string;
  symbol?: string;
  asset_type?: AssetType;
  trigger_type?: TriggerType;
  trigger_config?: TriggerConfig;
  start_date?: string;
  end_date?: string;
  collector_kwargs?: Record<string, unknown>;
  asset_metadata?: Record<string, unknown>;
  max_retries?: number;
  retry_delay_seconds?: number;
  retry_backoff_multiplier?: number;
  is_public?: boolean;
}

