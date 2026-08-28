import client from "./client";
import type {
  CalendarEvent,
  FetchPreview,
  IdeaCard,
  IdeaItem,
  IdeaSession,
  Persona,
  PersonaOptions,
  PersonaTemplate,
  ScriptRecord,
  Settings,
  SkillTemplate,
  Topic,
  User,
} from "../types";

export type TrialAccountKey = "tech" | "anime" | "pet";

export const authApi = {
  register: (username: string, password: string) =>
    client.post<{ access_token: string }>("/auth/register", { username, password }),
  login: (username: string, password: string) =>
    client.post<{ access_token: string }>("/auth/login", { username, password }),
  trial: (account: TrialAccountKey = "tech") =>
    client.post<{ access_token: string }>("/auth/trial", { account }),
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
  generateSkillAsync: (id: number) =>
    client.post<{ job_id: string }>(`/personas/${id}/skill/async`),
  skillJob: (jobId: string) =>
    client.get<{ status: string; error: string; persona: Persona | null }>(`/personas/skill-jobs/${jobId}`),
  updateSkill: (id: number, skill_prompt: string) =>
    client.put<Persona>(`/personas/${id}/skill`, { skill_prompt }),
  applyPresetSkill: (id: number, template_key?: string) =>
    client.post<Persona>(`/personas/${id}/skill/preset`, template_key ? { template_key } : {}),
  skillTemplates: () =>
    client.get<SkillTemplate[]>("/personas/skill-templates"),
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
  list: (params?: { feasibility?: string; q?: string; status?: string; priority?: string; tag?: string }) =>
    client.get<Topic[]>("/topics", { params }),
  create: (payload: {
    title: string;
    highlights?: string[];
    feasibility?: string;
    cost_note?: string;
    why?: string;
    status?: string;
    priority?: string;
    tags?: string[];
  }) => client.post<Topic>("/topics", payload),
  patch: (id: number, payload: Partial<Topic>) => client.patch<Topic>(`/topics/${id}`, payload),
  remove: (id: number) => client.delete(`/topics/${id}`),
  exportMd: (params?: { feasibility?: string; status?: string; priority?: string; tag?: string }) =>
    client.get<string>("/topics/export.md", { params, responseType: "text" }),
};

export const ideaApi = {
  diverge: (vague_idea: string, topic_id?: number | null) =>
    client.post<IdeaSession>("/ideas/diverge", { vague_idea, topic_id }),
  list: () => client.get<IdeaSession[]>("/ideas"),
  get: (id: number) => client.get<IdeaSession>(`/ideas/${id}`),
  select: (id: number, index: number) =>
    client.post<IdeaSession>(`/ideas/${id}/select`, { index }),
  save: (id: number, index: number, saved: boolean) =>
    client.post<IdeaSession>(`/ideas/${id}/save`, { index, saved }),
  listCards: () => client.get<IdeaCard[]>("/ideas/cards"),
  updateCard: (sessionId: number, index: number, payload: IdeaItem) =>
    client.patch<IdeaCard>(`/ideas/${sessionId}/cards/${index}`, payload),
  deleteCard: (sessionId: number, index: number) =>
    client.delete(`/ideas/${sessionId}/cards/${index}`),
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

export type TokenKind = "thinking" | "content";
export type TokenHandler = (kind: TokenKind, text: string) => void;

/**
 * 通用 SSE 流式客户端：POST JSON 到后端 /stream 端点。
 * 按需回调 onStatus（进度文案）或 onToken（逐字 token），最后返回 done 里的结构化结果。
 */
async function sseRequest<T>(
  url: string,
  payload: unknown,
  handlers: { onStatus?: (msg: string) => void; onToken?: TokenHandler } = {},
): Promise<T> {
  const { onStatus, onToken } = handlers;
  const token = localStorage.getItem("bstar_token");
  const res = await fetch(url, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    body: JSON.stringify(payload),
  });

  if (!res.ok) {
    let detail = `请求失败（${res.status}）`;
    try {
      const data = await res.json();
      if (typeof data.detail === "string") detail = data.detail;
    } catch {
      // 非 JSON 错误体，忽略
    }
    throw new Error(detail);
  }

  if (!res.body) {
    throw new Error("无法建立流式连接");
  }
  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  let result: T | null = null;
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
      const event = eventMatch[1].trim();
      const data = dataMatch[1];
      if (event === "status") onStatus?.(data);
      else if (event === "token") {
        const parsed = JSON.parse(data);
        onToken?.(parsed.kind, parsed.text);
      } else if (event === "done") result = JSON.parse(data) as T;
      else if (event === "error") {
        const parsed = JSON.parse(data);
        errorMsg = parsed.detail || "生成失败";
      }
    }
  }
  if (errorMsg) throw new Error(errorMsg);
  if (!result) throw new Error("未收到结果");
  return result;
}

export async function expandScriptStream(
  payload: {
    outline: string;
    shot_list?: string;
    topic_id?: number | null;
    idea_session_id?: number | null;
  },
  onToken: TokenHandler,
): Promise<ScriptRecord> {
  return sseRequest<ScriptRecord>("/api/v1/scripts/expand/stream", payload, { onToken });
}

export function divergeStream(
  payload: { vague_idea: string; topic_id?: number | null },
  onToken: TokenHandler,
): Promise<IdeaSession> {
  return sseRequest<IdeaSession>("/api/v1/ideas/diverge/stream", payload, { onToken });
}

export function extractInspirationStream(
  payload: { raw_text?: string; source_note?: string; url?: string },
  onToken: TokenHandler,
): Promise<Topic> {
  return sseRequest<Topic>("/api/v1/inspirations/extract/stream", payload, { onToken });
}

export function calendarExtractStream(
  raw_text: string,
  onStatus: (msg: string) => void,
): Promise<CalendarEvent> {
  return sseRequest<CalendarEvent>("/api/v1/calendar/extract/stream", { raw_text }, { onStatus });
}

export function calendarCaptureStream(
  onStatus: (msg: string) => void,
): Promise<{ created: number; skipped: number; warning: string; events: CalendarEvent[] }> {
  return sseRequest("/api/v1/calendar/capture/stream", {}, { onStatus });
}

export function generateSkillStream(
  personaId: number,
  onToken: TokenHandler,
): Promise<Persona> {
  return sseRequest<Persona>(`/api/v1/personas/${personaId}/skill/stream`, {}, { onToken });
}
