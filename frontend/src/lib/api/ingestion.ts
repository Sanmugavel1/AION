import { apiClient } from "./client";

export interface UploadResult {
  knowledge_id: string;
  title: string;
  domain: string;
  plain_summary: string;
  relevance_score: number;
  tags: string[];
  source_filename: string;
  word_count: number;
}

export interface RecentUpload {
  knowledge_id: string;
  title: string;
  domain: string | null;
  plain_summary: string | null;
  relevance_score: number;
  created_at: string;
}

export const ingestionApi = {
  upload: async (file: File): Promise<UploadResult> => {
    const form = new FormData();
    form.append("file", file);
    const res = await apiClient.post<UploadResult>("/ingestion/upload", form, {
      headers: { "Content-Type": "multipart/form-data" },
      timeout: 60000,
    });
    return res.data;
  },

  recent: async (limit = 20): Promise<RecentUpload[]> => {
    const res = await apiClient.get<RecentUpload[]>("/ingestion/recent", { params: { limit } });
    return res.data;
  },
};
