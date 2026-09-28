export type ScenarioId = "competition" | "contract" | "research" | "resume" | "reimbursement";

export type Scenario = {
  id: ScenarioId;
  name: string;
  description: string;
  status: "ready" | "preview" | "planned";
  documentTypes: string[];
};

export type Finding = {
  id: string;
  severity: "blocking" | "high" | "medium" | "info";
  title: string;
  detail: string;
  source: string;
  page: number;
  excerpt: string;
  suggestion: string;
  resolved: boolean;
};
