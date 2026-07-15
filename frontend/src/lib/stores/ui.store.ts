import { create } from "zustand";
import { GraphNode, SimulationResult } from "@/types";

interface UIState {
  sidebarOpen: boolean;
  setSidebarOpen: (open: boolean) => void;
  toggleSidebar: () => void;

  // MRI
  selectedNode: GraphNode | null;
  setSelectedNode: (node: GraphNode | null) => void;
  mriFilter: string | null;
  setMRIFilter: (filter: string | null) => void;

  // Simulation
  lastSimulationResult: SimulationResult | null;
  setSimulationResult: (result: SimulationResult | null) => void;
  isSimulationRunning: boolean;
  setSimulationRunning: (running: boolean) => void;

  // Global loading
  globalLoading: boolean;
  setGlobalLoading: (loading: boolean) => void;
}

export const useUIStore = create<UIState>((set) => ({
  sidebarOpen: true,
  setSidebarOpen: (open) => set({ sidebarOpen: open }),
  toggleSidebar: () => set((s) => ({ sidebarOpen: !s.sidebarOpen })),

  selectedNode: null,
  setSelectedNode: (node) => set({ selectedNode: node }),
  mriFilter: null,
  setMRIFilter: (filter) => set({ mriFilter: filter }),

  lastSimulationResult: null,
  setSimulationResult: (result) => set({ lastSimulationResult: result }),
  isSimulationRunning: false,
  setSimulationRunning: (running) => set({ isSimulationRunning: running }),

  globalLoading: false,
  setGlobalLoading: (loading) => set({ globalLoading: loading }),
}));
