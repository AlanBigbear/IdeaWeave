import client from "./client";
import type {
  CalendarEvent,
  FetchPreview,
  IdeaSession,
  Persona,
  PersonaOptions,
  PersonaTemplate,
  ScriptRecord,
  Settings,
  Topic,
  User,
} from "../types";

export const authApi = {
  register: (username: string, password: string) =>
    client.post<{ access_token: string }>("/auth/register", { username, password }),
  login: (username: string, password: string) =>
    client.post<{ access_token: string }>("/auth/login", { username, password }),
  me: () => client.get<User>("/auth/me"),
};

export const personaApi = {
  options: () => client.get<PersonaOptions>("/personas/options"),
  templates: () => client.get<PersonaTemplate[]>("/personas/templates"),
  list: () => client.get<Persona[]>("/personas"),
  create: (payload: Partial<Persona>) => client.post<Persona>("/personas", payload),
  setup: (payload: Partial<Persona>) => client.post<Persona>("/personas/setup", payload),
  activate: (payload: { template_key?: string; persona_id?: number }) =>
    client.post<Persona>("/personas/activate", payload),
  update: (id: number, payload: Partial<Persona>) => client.put<Persona>(`/personas/${id}`, payload),
  generateSkill: (id: number) => client.post<Persona>(`/personas/${id}/skill`),
  updateSkill: (id: number, skill_prompt: string) =>
    client.put<Persona>(`/personas/${id}/skill`, { skill_prompt }),
};

export const settingsApi = {
  get: () => client.get<Settings>("/settings"),
  update: (payload: { llm_base_url: string; llm_model: string; llm_api_key?: string }) =>
    client.put<Settings>("/settings", payload),
};

export const inspirationApi = {
  extract: (payload: { raw_text?: string; source_note?: string; url?: string }) =>
    client.post<Topic>("/inspirations/extract", payload),
  fetchUrl: (url: string) => client.post<FetchPreview>("/inspirations/fetch", { url }),
};

export const topicApi = {
  list: (params?: { feasibility?: string; q?: string }) =>
    client.get<Topic[]>("/topics", { params }),
  create: (payload: {
    title: string;
    highlights?: string[];
    feasibility?: string;
    cost_note?: string;
    why?: string;
  }) => client.post<Topic>("/topics", payload),
  patch: (id: number, payload: Partial<Topic>) => client.patch<Topic>(`/topics/${id}`, payload),
  remove: (id: number) => client.delete(`/topics/${id}`),
  exportMd: (feasibility?: string) =>
    client.get<string>("/topics/export.md", { params: { feasibility }, responseType: "text" }),
};

export const ideaApi = {
  diverge: (vague_idea: string, topic_id?: number | null) =>
    client.post<IdeaSession>("/ideas/diverge", { vague_idea, topic_id }),
  list: () => client.get<IdeaSession[]>("/ideas"),
  get: (id: number) => client.get<IdeaSession>(`/ideas/${id}`),
  select: (id: number, index: number) =>
    client.post<IdeaSession>(`/ideas/${id}/select`, { index }),
};

export const scriptApi = {
  expand: (payload: {
    outline: string;
    shot_list?: string;
    topic_id?: number | null;
    idea_session_id?: number | null;
  }) => client.post<ScriptRecord>("/scripts/expand", payload),
  list: () => client.get<ScriptRecord[]>("/scripts"),
  get: (id: number) => client.get<ScriptRecord>(`/scripts/${id}`),
};

export const calendarApi = {
  extract: (raw_text: string) => client.post<CalendarEvent>("/calendar/extract", { raw_text }),
  capture: () => client.post<{ created: number; skipped: number; warning: string; events: CalendarEvent[] }>("/calendar/capture"),
  list: () => client.get<CalendarEvent[]>("/calendar"),
  create: (payload: Partial<CalendarEvent> & { title: string }) => client.post<CalendarEvent>("/calendar", payload),
  update: (id: number, payload: Partial<CalendarEvent>) => client.patch<CalendarEvent>(`/calendar/${id}`, payload),
  remove: (id: number) => client.delete(`/calendar/${id}`),
};

export async function expandScriptStream(
  payload: {
    outline: string;
    shot_list?: string;
    topic_id?: number | null;
    idea_session_id?: number | null;
  },
  onStatus: (msg: string) => void,
): Promise<ScriptRecord> {
  const token = localStorage.getItem("bstar_token");
  const res = await fetch("/api/v1/scripts/expand/stream", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    body: JSON.stringify(payload),
  });
  if (!res.body) {
    throw new Error("无法建立流式连接");
  }
  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  let result: ScriptRecord | null = null;
  let errorMsg = "";
  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const chunks = buffer.split("\n\n");
    buffer = chunks.pop() || "";
    for (const chunk of chunks) {
      const eventMatch = chunk.match(/^event: (.+)$/m);
      const dataMatch = chunk.match(/^data: ([\s\S]+)$/m);
      if (!eventMatch || !dataMatch) continue;
      const event = eventMatch[1];
      const data = dataMatch[1];
      if (event === "status") onStatus(data);
      if (event === "done") result = JSON.parse(data) as ScriptRecord;
      if (event === "error") {
        const parsed = JSON.parse(data);
        errorMsg = parsed.detail || "生成失败";
      }
    }
  }
  if (errorMsg) throw new Error(errorMsg);
  if (!result) throw new Error("未收到脚本结果");
  return result;
}
