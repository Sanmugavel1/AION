import { apiClient } from "./client";
import {
  BusinessImpact,
  ContinuityReport,
  EmployeeKnowledgeProfile,
  SuccessorRoadmap,
} from "@/types";

export const ocsieApi = {
  getProfile: async (employeeId: string): Promise<EmployeeKnowledgeProfile> => {
    const res = await apiClient.get(`/ocsie/employee/${employeeId}/profile`);
    return res.data;
  },

  getContinuityReport: async (employeeId: string): Promise<ContinuityReport> => {
    const res = await apiClient.get(`/ocsie/continuity-report/${employeeId}`);
    return res.data;
  },

  initiateTransition: async (
    employeeId: string,
    params: { departure_date?: string; reason?: string },
  ) => {
    const res = await apiClient.post(`/ocsie/transition/${employeeId}`, null, { params });
    return res.data;
  },

  getUnfinishedWork: async (employeeId: string) => {
    const res = await apiClient.get(`/ocsie/unfinished-work/${employeeId}`);
    return res.data;
  },

  getSuccessorRoadmap: async (employeeId: string): Promise<SuccessorRoadmap> => {
    const res = await apiClient.get(`/ocsie/successor-roadmap/${employeeId}`);
    return res.data;
  },

  getKnowledgeGap: async (fromId: string, toId: string) => {
    const res = await apiClient.get(`/ocsie/knowledge-gap/${fromId}/${toId}`);
    return res.data;
  },

  getBusinessImpact: async (employeeId: string): Promise<BusinessImpact> => {
    const res = await apiClient.get(`/ocsie/business-impact/${employeeId}`);
    return res.data;
  },
};
