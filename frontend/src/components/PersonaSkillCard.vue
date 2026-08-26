<template>
  <div class="skill-panel">
    <template v-if="!persona.skill_prompt">
      <p class="muted">
        编导娘会把你的人设「编译」成一份专属 Skill，之后灵感提取、创意发散、脚本扩写、热点日历全都听它的——
        换个人设就对不上号的那种。
      </p>
      <el-alert v-if="llmMissing" type="warning" :closable="false" class="llm-tip">
        先去「设置 → 大模型」把 Base URL、模型名和 API Key 配好再来～也可以先跳过，之后在设置页生成。
      </el-alert>

      <AiStream v-if="generating" :active="generating" :thinking="thinking" :content="content" emoji="🪄" />
      <template v-else>
        <el-button type="primary" round @click="generate">AI 注入灵魂（深度定制）</el-button>
        <el-button round @click="openTemplates">套用编导模板</el-button>
      </template>
    </template>

    <template v-else>
      <div class="editor">
        <div class="editor-head">
          <span class="editor-title">📜 Skill Prompt</span>
          <span class="editor-sub">编导娘的「灵魂本体」，所有 AI 模块都按它工作，可以手动微调</span>
        </div>
        <el-input v-model="skillPrompt" type="textarea" :autosize="{ minRows: 4, maxRows: 10 }" />
        <div class="ops">
          <el-button type="primary" round :loading="saving" :disabled="!dirty" @click="save">
            保存修改
          </el-button>
          <el-button round :loading="generating" @click="generate">AI 重新生成</el-button>
          <el-button round @click="openTemplates">换个编导模板</el-button>
        </div>
        <AiStream v-if="generating" :active="generating" :thinking="thinking" :content="content" emoji="🪄" />
      </div>

      <div v-if="brief" class="brief">
        <div class="positioning">
          <span class="k">频道定位</span>
          {{ brief.positioning }}
        </div>
        <el-collapse class="brief-collapse">
          <el-collapse-item :title="`🪝 钩子公式 · ${brief.hook_formula.length} 个`" name="hook">
            <ul class="chip-list">
              <li v-for="item in brief.hook_formula" :key="item">{{ item }}</li>
            </ul>
          </el-collapse-item>
          <el-collapse-item :title="`🗣 语言风格 · ${brief.tone_rules.length} 条`" name="tone">
            <ul class="chip-list">
              <li v-for="item in brief.tone_rules" :key="item">{{ item }}</li>
            </ul>
          </el-collapse-item>
          <el-collapse-item :title="`🎯 选题偏好 · ${brief.topic_preferences.length} 条`" name="topics">
            <ul class="chip-list">
              <li v-for="item in brief.topic_preferences" :key="item">{{ item }}</li>
            </ul>
          </el-collapse-item>
          <el-collapse-item title="🎬 脚本骨架" name="structure">
            <p class="block-text">{{ brief.script_structure }}</p>
          </el-collapse-item>
          <el-collapse-item title="💬 互动玩法" name="interaction">
            <p class="block-text">{{ brief.interaction_style }}</p>
          </el-collapse-item>
          <el-collapse-item :title="`🚫 内容红线 · ${brief.red_lines.length} 条`" name="red">
            <ul class="chip-list danger">
              <li v-for="item in brief.red_lines" :key="item">{{ item }}</li>
            </ul>
          </el-collapse-item>
        </el-collapse>
      </div>
    </template>

    <el-dialog v-model="showTemplates" title="挑一个编导模板 ✨" width="min(640px, 94vw)">
      <p class="tpl-tip">
        模板自带频道定位、招牌钩子和口头禅；更新节奏、互动玩法仍按你的选择保留。点一下就套用～
      </p>
      <div class="tpl-grid">
        <button class="tpl-card auto" @click="applyPreset()">
          <b>🪄 自动匹配</b>
          <span>按你的分区和风格智能拼装，不套固定人设</span>
        </button>
        <button
          v-for="tpl in sortedTemplates"
          :key="tpl.key"
          class="tpl-card"
          :class="{ match: tpl.zone_key === personaZoneKey }"
          :disabled="presetting"
          @click="applyPreset(tpl.key)"
        >
          <b>{{ tpl.name }}<i v-if="tpl.zone_key === personaZoneKey">本区</i></b>
          <span>{{ tpl.desc }}</span>
          <em>{{ tpl.zone_label }}</em>
        </button>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, watch } from "vue";
import { ElMessage, ElMessageBox } from "element-plus";
import { generateSkillStream, personaApi } from "../api";
import AiStream from "./AiStream.vue";
import type { Persona, SkillTemplate } from "../types";

const props = defineProps<{ persona: Persona }>();
const emit = defineEmits<{ (e: "updated", persona: Persona): void }>();

const generating = ref(false);
const saving = ref(false);
const presetting = ref(false);
const llmMissing = ref(false);
const thinking = ref("");
const content = ref("");
const skillPrompt = ref(props.persona.skill_prompt);
const showTemplates = ref(false);
const templates = ref<SkillTemplate[]>([]);

const ZONE_KEY_BY_LABEL: Record<string, string> = {
  生活区: "life", 美食区: "food", 时尚区: "fashion", 科技区: "tech",
  游戏区: "game", 知识区: "knowledge", 运动区: "sports", 影视区: "cine",
  音乐区: "music", 旅游出行: "travel", 汽车区: "auto", 动物圈: "animal",
  舞蹈区: "dance", 二次元: "otaku", 鬼畜区: "danmu", 搞笑区: "funny",
  娱乐区: "vlog_ent", 虚拟主播: "digital", 校园学习: "campus",
};

const personaZoneKey = computed(() => ZONE_KEY_BY_LABEL[props.persona.zone] || "");

const sortedTemplates = computed(() => {
  const zone = personaZoneKey.value;
  return [...templates.value].sort((a, b) => {
    if (a.zone_key === zone && b.zone_key !== zone) return -1;
    if (b.zone_key === zone && a.zone_key !== zone) return 1;
    return a.zone_key.localeCompare(b.zone_key);
  });
});

const brief = computed(() => props.persona.skill_brief);
const dirty = computed(
  () => skillPrompt.value.trim() !== props.persona.skill_prompt.trim(),
);
watch(
  () => props.persona.id,
  () => {
    skillPrompt.value = props.persona.skill_prompt;
    llmMissing.value = false;
  },
);

function applyPersona(persona: Persona) {
  skillPrompt.value = persona.skill_prompt;
  emit("updated", persona);
}

async function generate() {
  if (props.persona.skill_prompt && dirty.value) {
    try {
      await ElMessageBox.confirm("重新生成会把你手改过的 Skill Prompt 覆盖掉，真的要重来吗？", "提示", {
        type: "warning",
      });
    } catch {
      return;
    }
  }
  generating.value = true;
  llmMissing.value = false;
  thinking.value = "";
  content.value = "";
  try {
    const data = await generateSkillStream(props.persona.id, (kind, text) => {
      if (kind === "thinking") thinking.value += text;
      else content.value += text;
    });
    applyPersona(data);
    ElMessage.success("灵魂注入完成！专属 Skill 上线");
  } catch (error) {
    const message = error instanceof Error ? error.message : "";
    if (message.includes("大模型")) {
      llmMissing.value = true;
    } else {
      ElMessage.error(message ? `注入灵魂失败：${message}` : "注入灵魂失败，稍后再试");
    }
  } finally {
    generating.value = false;
  }
}

async function openTemplates() {
  showTemplates.value = true;
  if (!templates.value.length) {
    const { data } = await personaApi.skillTemplates();
    templates.value = data;
  }
}

async function applyPreset(templateKey?: string) {
  if (dirty.value) {
    try {
      await ElMessageBox.confirm("套用模板会覆盖你手改过的内容，确定吗？", "提示", {
        type: "warning",
      });
    } catch {
      return;
    }
  }
  presetting.value = true;
  try {
    const { data } = await personaApi.applyPresetSkill(props.persona.id, templateKey);
    applyPersona(data);
    showTemplates.value = false;
    const tpl = templates.value.find((t) => t.key === templateKey);
    ElMessage.success(tpl ? `已套用「${tpl.name}」～` : "自动匹配模板套好了～");
  } finally {
    presetting.value = false;
  }
}

async function save() {
  saving.value = true;
  try {
    const { data } = await personaApi.updateSkill(props.persona.id, skillPrompt.value);
    skillPrompt.value = data.skill_prompt;
    emit("updated", data);
    ElMessage.success("改好了，马上生效～");
  } finally {
    saving.value = false;
  }
}
</script>

<style scoped>
.muted {
  color: #8a7176;
  line-height: 1.8;
  margin: 0 0 16px;
}

.llm-tip {
  margin-bottom: 14px;
}

.editor {
  background: linear-gradient(120deg, #fff5f9, #fff);
  border: 1px solid #ffdbe8;
  border-radius: 18px;
  padding: 16px 18px 14px;
  margin-bottom: 16px;
}

.editor-head {
  display: flex;
  align-items: baseline;
  gap: 10px;
  flex-wrap: wrap;
  margin-bottom: 10px;
}

.editor-title {
  font-weight: 800;
  font-size: 15px;
  color: var(--ink, #3d2f35);
}

.editor-sub {
  font-size: 12px;
  color: #8a7176;
}

.ops {
  margin-top: 12px;
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.generating-box {
  text-align: center;
  padding: 22px 16px;
  border: 1px dashed #ffb0cb;
  border-radius: 18px;
  background: #fff;
}

.generating-face {
  font-size: 34px;
  animation: floaty 1.6s ease-in-out infinite;
}

.generating-main {
  margin: 8px 0 4px;
  font-weight: 600;
}

.generating-sub {
  margin: 0;
  font-size: 12px;
  color: #8a7176;
}

.generating-inline {
  margin-top: 10px;
  font-size: 12px;
  color: #c4537a;
}

.brief {
  margin-bottom: 6px;
}

.positioning {
  background: linear-gradient(120deg, #fff0f6, #fff);
  border: 1px solid #ffd0e4;
  border-radius: 14px;
  padding: 12px 16px;
  font-weight: 600;
  margin-bottom: 12px;
}

.positioning .k {
  display: inline-block;
  background: var(--accent, #fb7299);
  color: #fff;
  font-size: 12px;
  border-radius: 999px;
  padding: 2px 10px;
  margin-right: 10px;
  font-weight: 700;
}

.brief-collapse {
  border: 1px solid var(--line, #f0dbe3);
  border-radius: 14px;
  overflow: hidden;
  background: #fff;
}

.brief-collapse :deep(.el-collapse-item__header) {
  padding: 0 14px;
  font-size: 13px;
  font-weight: 600;
  color: #5c4750;
  border-bottom-color: var(--line, #f0dbe3);
}

.brief-collapse :deep(.el-collapse-item__wrap) {
  border-bottom-color: var(--line, #f0dbe3);
}

.brief-collapse :deep(.el-collapse-item__content) {
  padding: 10px 14px 12px;
}

.chip-list {
  margin: 0;
  padding: 0;
  list-style: none;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.chip-list li {
  background: #fff5f8;
  border: 1px solid #ffdbe8;
  border-radius: 10px;
  padding: 6px 10px;
  font-size: 13px;
  color: #5c4750;
  line-height: 1.6;
}

.chip-list.danger li {
  background: #fff5f5;
  border-color: #ffd3d3;
}

.tpl-tip {
  margin: 0 0 14px;
  font-size: 13px;
  color: #8a7176;
  line-height: 1.7;
}

.tpl-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
  max-height: 56vh;
  overflow: auto;
  padding: 2px;
}

.tpl-card {
  appearance: none;
  text-align: left;
  border: 1px solid var(--line, #f0dbe3);
  background: #fff;
  border-radius: 14px;
  padding: 12px 14px;
  cursor: pointer;
  display: flex;
  flex-direction: column;
  gap: 6px;
  transition: 0.18s ease;
}

.tpl-card:hover {
  border-color: var(--accent, #fb7299);
  box-shadow: 0 8px 18px rgba(255, 107, 157, 0.14);
  transform: translateY(-2px);
}

.tpl-card.auto {
  background: linear-gradient(120deg, #fff0f6, #fff);
  border-style: dashed;
}

.tpl-card.match {
  border-color: #ffb0cb;
  background: #fff8fb;
}

.tpl-card b {
  font-size: 14px;
  color: var(--ink, #3d2f35);
  display: flex;
  align-items: center;
  gap: 6px;
}

.tpl-card b i {
  font-style: normal;
  font-size: 10px;
  background: var(--accent, #fb7299);
  color: #fff;
  border-radius: 999px;
  padding: 1px 8px;
  font-weight: 600;
}

.tpl-card span {
  font-size: 12px;
  color: #8a7176;
  line-height: 1.6;
}

.tpl-card em {
  font-style: normal;
  font-size: 11px;
  color: #c48aa3;
}

.block-text {
  margin: 0;
  font-size: 13px;
  color: #5c4750;
  line-height: 1.7;
  white-space: pre-line;
}

@keyframes floaty {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-6px); }
}

@media (max-width: 720px) {
  .editor-head {
    flex-direction: column;
    gap: 2px;
  }
  .tpl-grid {
    grid-template-columns: 1fr;
  }
}
</style>
