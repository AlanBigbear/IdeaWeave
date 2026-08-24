<template>
  <div class="skill-panel">
    <template v-if="!persona.skill_prompt">
      <p class="muted">
        虚拟编导会把你的人设「编译」成一份专属 Skill：一句话频道定位、3 个专属钩子公式、语言风格规则、
        选题偏好、脚本骨架、互动玩法、内容红线。之后灵感提取、创意发散、脚本扩写、热点日历全部按这份 Skill 工作——
        换一个人设就不适用的那种。
      </p>
      <el-alert v-if="llmMissing" type="warning" :closable="false" class="llm-tip">
        请先在「设置 → 大模型」配置 Base URL、模型名和 API Key 后再编译；也可以先跳过，稍后在设置页生成。
      </el-alert>
      <el-button type="primary" round :loading="generating" @click="generate">
        {{ generating ? "正在编译专属 Skill…" : "AI 编译专属编导 Skill" }}
      </el-button>
    </template>

    <template v-else>
      <div v-if="brief" class="brief">
        <div class="positioning">
          <span class="k">频道定位</span>
          {{ brief.positioning }}
        </div>
        <div class="grid">
          <div class="cell">
            <b>🪝 专属钩子公式</b>
            <ul><li v-for="item in brief.hook_formula" :key="item">{{ item }}</li></ul>
          </div>
          <div class="cell">
            <b>🗣 语言风格规则</b>
            <ul><li v-for="item in brief.tone_rules" :key="item">{{ item }}</li></ul>
          </div>
          <div class="cell">
            <b>🎯 选题偏好</b>
            <ul><li v-for="item in brief.topic_preferences" :key="item">{{ item }}</li></ul>
          </div>
          <div class="cell">
            <b>🚫 内容红线</b>
            <ul><li v-for="item in brief.red_lines" :key="item">{{ item }}</li></ul>
          </div>
          <div class="cell wide">
            <b>🎬 脚本骨架</b>
            <p>{{ brief.script_structure }}</p>
          </div>
          <div class="cell wide">
            <b>💬 互动玩法</b>
            <p>{{ brief.interaction_style }}</p>
          </div>
        </div>
      </div>

      <div class="editor">
        <div class="editor-label">Skill Prompt（已注入所有 AI 模块，可手动微调）</div>
        <el-input v-model="skillPrompt" type="textarea" :rows="10" />
        <div class="ops">
          <el-button type="primary" round :loading="saving" :disabled="!dirty" @click="save">
            保存修改
          </el-button>
          <el-button round :loading="generating" @click="generate">重新生成</el-button>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, watch } from "vue";
import { ElMessage, ElMessageBox } from "element-plus";
import { personaApi } from "../api";
import type { Persona } from "../types";

const props = defineProps<{ persona: Persona }>();
const emit = defineEmits<{ (e: "updated", persona: Persona): void }>();

const generating = ref(false);
const saving = ref(false);
const llmMissing = ref(false);
const skillPrompt = ref(props.persona.skill_prompt);

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

async function generate() {
  if (props.persona.skill_prompt && dirty.value) {
    try {
      await ElMessageBox.confirm("重新生成会覆盖你手动修改过的 Skill Prompt，确定继续？", "提示", {
        type: "warning",
      });
    } catch {
      return;
    }
  }
  generating.value = true;
  llmMissing.value = false;
  try {
    const { data } = await personaApi.generateSkill(props.persona.id);
    skillPrompt.value = data.skill_prompt;
    emit("updated", data);
    ElMessage.success("专属编导 Skill 已编译完成");
  } catch (error) {
    const detail = String((error as { response?: { data?: { detail?: string } } })?.response?.data?.detail ?? "");
    if (detail.includes("大模型")) llmMissing.value = true;
  } finally {
    generating.value = false;
  }
}

async function save() {
  saving.value = true;
  try {
    const { data } = await personaApi.updateSkill(props.persona.id, skillPrompt.value);
    skillPrompt.value = data.skill_prompt;
    emit("updated", data);
    ElMessage.success("Skill Prompt 已保存，即刻生效");
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

.brief {
  margin-bottom: 18px;
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

.grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.cell {
  background: #fff;
  border: 1px solid var(--line, #f0dbe3);
  border-radius: 14px;
  padding: 12px 14px;
}

.cell.wide {
  grid-column: 1 / -1;
}

.cell b {
  display: block;
  margin-bottom: 8px;
  font-size: 13px;
}

.cell ul {
  margin: 0;
  padding-left: 18px;
}

.cell li {
  margin: 4px 0;
  font-size: 13px;
  color: #5c4750;
  line-height: 1.6;
}

.cell p {
  margin: 0;
  font-size: 13px;
  color: #5c4750;
  line-height: 1.7;
}

.editor-label {
  font-size: 13px;
  color: #8a7176;
  margin-bottom: 8px;
}

.ops {
  margin-top: 12px;
  display: flex;
  gap: 10px;
}

@media (max-width: 720px) {
  .grid {
    grid-template-columns: 1fr;
  }
}
</style>
