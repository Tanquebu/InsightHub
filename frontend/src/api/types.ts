// Tipi allineati agli schema Pydantic del backend (app/schemas/*.py).

export interface Project {
  id: number;
  name: string;
  description: string | null;
}

export type DatasetStatus =
  | "uploaded"
  | "pending"
  | "processing"
  | "completed"
  | "failed";

export interface Dataset {
  id: number;
  project_id: number;
  name: string;
  status: DatasetStatus;
  source_type: string;
  file_path: string | null;
}

export interface DatasetProfile {
  dataset_id: number;
  row_count: number;
  column_count: number;
  column_missing_counts: Record<string, number>;
  column_dtypes: Record<string, string>;
}

export interface DatasetMetrics {
  row_count: number;
  column_count: number;
  total_missing_values: number;
  column_missing_ratios: Record<string, number>;
  completeness_score: number;
}

export interface DatasetQualityIssue {
  id: number;
  rule_code: string;
  severity: string;
  message: string;
  created_at: string;
}

export interface DatasetInsights {
  dataset_id: number;
  metrics: DatasetMetrics;
  issues: DatasetQualityIssue[];
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
}
