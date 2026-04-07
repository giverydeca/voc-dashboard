export interface CsvFile {
  id: string;
  name: string;
  content: string;
  size: number;
}

export enum ProcessingStatus {
  IDLE = 'IDLE',
  UPLOADING = 'UPLOADING',
  PROCESSING = 'PROCESSING',
  COMPLETE = 'COMPLETE',
  ERROR = 'ERROR',
  CANCELLED = 'CANCELLED'
}

export interface PreviewData {
  headers: string[];
  rows: string[][];
}

export interface OutputRecord {
  id: string;
  createdAt: number;
  filenameBase: string;
  chunks?: string[];
  outputs?: OutputEntry[];
  model?: string;
}

export interface OutputEntry {
  label: string;
  chunks: string[];
}