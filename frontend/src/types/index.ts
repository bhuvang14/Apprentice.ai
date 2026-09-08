export interface User {
  id: string;
  name: string;
  email: string;
  role: 'faculty' | 'dept_admin' | 'system_admin';
  department: string | null;
  oidc_sub: string | null;
  created_at: string;
}

export interface Template {
  id: string;
  name: string;
  description: string | null;
  department: string | null;
  form_type: string | null;
  file_type: 'docx' | 'xlsx' | 'pdf';
  storage_path: string;
  version: number;
  required_fields: Record<string, any>;
  active: boolean;
  created_at: string;
  updated_at: string;
}

export interface TemplateSearchResult extends Template {
  similarity: number;
}

export interface PolicyChunk {
  id: string;
  source_doc: string;
  chunk_text: string;
  department: string | null;
  tags: string[] | null;
  created_at: string;
}

export interface PolicySearchResult extends PolicyChunk {
  similarity: number;
}

export interface Generation {
  id: string;
  user_id: string;
  template_id: string;
  template_version: number;
  field_values: Record<string, any>;
  output_path: string;
  created_at: string;
}

export interface ChatRequest {
  message: string;
  user_id: string;
  conversation_history: Array<{ role: string; content: string }>;
}

export interface ChatResponse {
  response: string;
  tool_calls?: Array<{ name: string; input: any; output: any }>;
  generated_file?: {
    output_path: string;
    filename: string;
    download_url: string;
  };
}

export interface FacultyProfile {
  name: string;
  title: string;
  department: string;
  email: string;
  courses: string[];
  office: string | null;
  phone: string | null;
}

export interface TemplateSchema {
  template_id: string;
  name: string;
  required_fields: Record<string, any>;
  field_descriptions: Record<string, string>;
}

export interface FillTemplateRequest {
  template_id: string;
  field_values: Record<string, any>;
}

export interface FillTemplateResponse {
  output_path: string;
  filename: string;
  download_url: string;
}

export interface Message {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  generated_file?: FillTemplateResponse;
  timestamp: Date;
}