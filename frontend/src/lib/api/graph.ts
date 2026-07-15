import { apiClient } from "./client";
import {
  CreatePersonRequest,
  CreateKnowledgeRequest,
  CreateRelationshipRequest,
  NodeType,
} from "@/types";

export const graphApi = {
  getNodes: async (params?: { node_type?: NodeType; limit?: number }) => {
    const res = await apiClient.get("/graph/nodes", { params });
    return res.data as { nodes: import("@/types").GraphNode[]; total: number };
  },

  createPerson: async (data: CreatePersonRequest) => {
    const res = await apiClient.post("/graph/nodes/person", data);
    return res.data;
  },

  createKnowledge: async (data: CreateKnowledgeRequest) => {
    const res = await apiClient.post("/graph/nodes/knowledge", data);
    return res.data;
  },

  createRelationship: async (data: CreateRelationshipRequest) => {
    const res = await apiClient.post("/graph/relationships", data);
    return res.data;
  },

  traverse: async (params: {
    from_node_id: string;
    relationship_type?: string;
    max_depth?: number;
  }) => {
    const res = await apiClient.get("/graph/traverse", { params });
    return res.data;
  },

  search: async (q: string, domain?: string) => {
    const res = await apiClient.get("/graph/search", { params: { q, domain } });
    return res.data;
  },

  listDepartments: async () => {
    const res = await apiClient.get("/graph/departments");
    return res.data as {
      departments: Array<{
        id: string; name: string; headcount: number; knowledge_items: number;
        policy_count: number; created_at: string;
      }>;
      total: number;
    };
  },

  createDepartment: async (name: string) => {
    const res = await apiClient.post("/graph/nodes/department", { name });
    return res.data;
  },

  bulkCreatePeople: async (people: Array<{
    name: string; email: string; department?: string; role?: string; expertise?: string[];
  }>) => {
    const res = await apiClient.post("/graph/nodes/person/bulk", { people });
    return res.data as { status: string; count: number; nodes: unknown[] };
  },

  bulkCreatePolicies: async (policies: Array<{
    title: string; summary?: string; department?: string; tags?: string[];
  }>) => {
    const res = await apiClient.post("/graph/nodes/policy/bulk", { policies });
    return res.data as { status: string; count: number; nodes: unknown[] };
  },

  listPolicies: async (department?: string) => {
    const res = await apiClient.get("/graph/policies", { params: { department } });
    return res.data as { policies: unknown[]; total: number };
  },
};

export type { CreatePersonRequest, CreateKnowledgeRequest, CreateRelationshipRequest };
