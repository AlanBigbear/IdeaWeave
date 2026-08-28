export interface User {
  id: number;
  username: string;
  active_persona_id: number | null;
  created_at: string;
  is_trial: boolean;
}

export interface PersonaSkillBrief {
  positioning: string;
  hook_formula: string[];
  tone_rules: string[];
  topic_preferences: string[];
  script_structure: string;
  interaction_style: string;
  red_lines: string[];
  system_prompt: string;
}

export interface Persona {
  id: number;
  template_key: string;
  name: string;
  style_desc: string;
  audience: string;
  video_format: string;
  taboos: string;
  sample_tone: string;
  zone: string;
  content_style: string;
  update_freq: string;
  comment_style: string;
  skill_prompt: string;
  skill_brief: PersonaSkillBrief | null;
  skill_generated_at: string | null;
  created_at: string;
}

export interface PersonaTemplate {
  key: string;
  name: string;
  style_desc: string;
  audience: string;
  video_format: string;
  taboos: string;
  sample_tone: string;
  zone: string;
  content_style: string;
  update_freq: string;
  comment_style: string;
}

export interface OptionItem {
  key: string;
  label: string;
  desc: string;
  emoji: string;
}

export interface PersonaOptions {
  zones: OptionItem[];
  content_styles: string[];
  zone_content_styles?: Record<string, string[]>;
  common_content_styles?: string[];
  update_freqs: OptionItem[];
  comment_styles: OptionItem[];
}

export interface SkillTemplate {
  key: string;
  zone_key: string;
  zone_label: string;
  name: string;
  desc: string;
}

export interface Settings {
  llm_base_url: string;
  llm_model: string;
  has_api_key: boolean;
  default_llm_base_url: string;
  default_llm_model: string;
}

export interface FetchPreview {
  url: string;
  title: string;
  site_name: string;
  text: string;
  truncated: boolean;
}

export interface Topic {
  id: number;
  inspiration_id: number | null;
  title: string;
  highlights: string[];
  feasibility: "quick" | "deferred" | string;
  cost_note: string;
  why: string;
  source: string;
  status: string;
  priority: string;
  tags: string[];
  created_at: string;
}

export interface IdeaItem {
  title: string;
  angle: string;
  audience: string;
  cost: string;
  hook: string;
  why_different: string;
}

export interface IdeaCard extends IdeaItem {
  session_id: number;
  index: number;
  created_at: string;
}

export interface IdeaSession {
  id: number;
  topic_id: number | null;
  vague_idea: string;
  ideas: IdeaItem[];
  selected_index: number | null;
  saved_indexes: number[];
  created_at: string;
}

export interface Shot {
  time_range: string;
  camera: string;
  action: string;
  line: string;
  interaction: string;
}

export interface ScriptBody {
  title: string;
  hook: string;
  duration_hint: string;
  shots: Shot[];
  cta: string;
}

export interface CoverPrompt {
  style: string;
  prompt: string;
}

export interface RiskItem {
  level: string;
  category: string;
  detail: string;
  suggestion: string;
}

export interface ScriptRecord {
  id: number;
  topic_id: number | null;
  idea_session_id: number | null;
  outline: string;
  shot_list: string;
  comments_text: string;
  script: ScriptBody;
  cover_prompts: CoverPrompt[];
  risks: RiskItem[];
  created_at: string;
}

export interface CalendarEvent {
  id: number;
  title: string;
  start_date: string;
  end_date: string;
  location: string;
  vlog_fit: string;
  commercial: string;
  raw_text: string;
  source: "capture" | "extract" | "manual" | string;
  created_at: string;
}

export const SAMPLE_VIRAL = `上周上海一家快闪店排队 3 小时，门口全是打卡机位，但进去后货架空、服务差、灯光全是手机补光。评论区一边骂一边求「到底值不值得去」。适合做体验派长视频：真实排队、进店落差、消费决策。预算低，周末就能拍。`;

export const SAMPLE_OUTLINE = `主题：上海户外潮流展值不值得去
1. 开头抛冲突：展会门票贵，到底是内容还是拍照局
2. 到达国家会展中心，记录动线、排队、第一印象
3. 三个展位深度体验：好看但买不到 / 能试穿 / 有品牌活动
4. 商业化机会：联名、探店、线下活动怎么接
5. 结论：适合哪类 UP、怎么拍才不踩坑`;

export const SAMPLE_SHOTLIST = `相机+手机、稳定器、收音麦、展会票、充电宝、名片、备用口播提纲`;

export const SAMPLE_HOTSPOT = `2026年9月10-15日，上海户外潮流展；地点上海国家会展中心；适合做线下体验vlog，商业化机会多。`;
