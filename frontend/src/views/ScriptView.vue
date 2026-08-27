<template>
  <div>
    <div class="page-head">
      <h2>大纲扩写脚本</h2>
      <p>丢进大纲和拍摄清单，钩子、台词、分镜、互动一次配齐，还附赠 6 套封面 Prompt 和风险自查～</p>
    </div>
    <el-row :gutter="16">
      <el-col :md="10">
        <el-card>
          <el-form label-position="top">
            <el-form-item label="大纲">
              <el-input v-model="outline" type="textarea" :rows="8" />
            </el-form-item>
            <el-form-item label="拍摄清单">
              <el-input v-model="shotList" type="textarea" :rows="3" />
            </el-form-item>
            <el-space>
              <el-button type="primary" :loading="loading" @click="expand">开写！</el-button>
              <el-button @click="fillSample">塞个示例</el-button>
            </el-space>
            <AiStream :active="loading" :thinking="thinking" :content="content" emoji="📝" />
          </el-form>
        </el-card>
      </el-col>
      <el-col :md="14">
        <el-empty v-if="!record" description="写好的脚本会在右边展开" />
        <template v-else>
          <el-card>
            <template #header>{{ record.script.title }} · {{ record.script.duration_hint }}</template>
            <el-alert :title="'钩子：' + record.script.hook" type="info" :closable="false" />
            <el-timeline style="margin-top: 16px">
              <el-timeline-item v-for="shot in record.script.shots" :key="shot.time_range" :timestamp="shot.time_range">
                <p><b>镜头</b> {{ shot.camera }}</p>
                <p><b>动作</b> {{ shot.action }}</p>
                <p><b>台词</b> {{ shot.line }}</p>
                <p v-if="shot.interaction"><b>互动</b> {{ shot.interaction }}</p>
              </el-timeline-item>
            </el-timeline>
            <p><b>结尾 CTA</b> {{ record.script.cta }}</p>
          </el-card>
          <el-card style="margin-top: 12px">
            <template #header>6 套封面生图 Prompt（拿去喂绘图工具）</template>
            <el-collapse>
              <el-collapse-item v-for="(cover, i) in record.cover_prompts" :key="i" :title="`${i + 1}. ${cover.style}`">
                {{ cover.prompt }}
              </el-collapse-item>
            </el-collapse>
          </el-card>
          <el-card style="margin-top: 12px">
            <template #header>风险自查（发布前过一遍）</template>
            <div class="table-scroll">
              <el-table :data="record.risks">
                <el-table-column prop="level" label="级别" width="80" />
                <el-table-column prop="category" label="类型" width="120" />
                <el-table-column prop="detail" label="问题" />
                <el-table-column prop="suggestion" label="建议" />
              </el-table>
            </div>
          </el-card>
        </template>
      </el-col>
    </el-row>

    <section v-if="scripts.length" class="saved-scripts">
      <div class="saved-head">
        <h3>📚 我的脚本（{{ scripts.length }}）</h3>
        <span class="muted">写好的脚本会自动存到这里，点一下就能回看～</span>
      </div>
      <div class="script-list">
        <button
          v-for="s in scripts"
          :key="s.id"
          class="script-item"
          :class="{ on: record?.id === s.id }"
          type="button"
          @click="openScript(s)"
        >
          <b>{{ s.script.title }}</b>
          <span>{{ formatTime(s.created_at) }}</span>
        </button>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { onActivated, onMounted, ref } from "vue";
import { useRoute } from "vue-router";
import { ElMessage } from "element-plus";
import { expandScriptStream, scriptApi } from "../api";
import { SAMPLE_OUTLINE, SAMPLE_SHOTLIST, type ScriptRecord } from "../types";
import AiStream from "../components/AiStream.vue";

defineOptions({ name: "ScriptView" });

const route = useRoute();
const outline = ref("");
const shotList = ref("");
const loading = ref(false);
const thinking = ref("");
const content = ref("");
const record = ref<ScriptRecord | null>(null);
const ideaSessionId = ref<number | null>(null);
const topicId = ref<number | null>(null);
const scripts = ref<ScriptRecord[]>([]);

function applyQuery() {
  if (route.query.outline) outline.value = String(route.query.outline);
  if (route.query.ideaSessionId) ideaSessionId.value = Number(route.query.ideaSessionId);
  if (route.query.topicId) topicId.value = Number(route.query.topicId);
}

async function refreshScripts() {
  const { data } = await scriptApi.list();
  scripts.value = data;
}

function formatTime(iso: string) {
  if (!iso) return "";
  const d = new Date(iso);
  const p = (n: number) => String(n).padStart(2, "0");
  return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())} ${p(d.getHours())}:${p(d.getMinutes())}`;
}

function openScript(s: ScriptRecord) {
  record.value = s;
  ElMessage.success("已加载脚本～");
}

onMounted(() => {
  applyQuery();
  void refreshScripts();
});
let skipActivate = true;
onActivated(() => {
  if (skipActivate) {
    skipActivate = false;
    return;
  }
  applyQuery();
  void refreshScripts();
});

function fillSample() {
  outline.value = SAMPLE_OUTLINE;
  shotList.value = SAMPLE_SHOTLIST;
}

async function expand() {
  if (outline.value.trim().length < 8) {
    ElMessage.warning("先写点大纲嘛");
    return;
  }
  loading.value = true;
  thinking.value = "";
  content.value = "";
  try {
    record.value = await expandScriptStream(
      {
        outline: outline.value,
        shot_list: shotList.value,
        idea_session_id: ideaSessionId.value,
        topic_id: topicId.value,
      },
      (kind, text) => {
        if (kind === "thinking") thinking.value += text;
        else content.value += text;
      },
    );
    await refreshScripts();
    ElMessage.success("脚本出炉，已存进脚本库～");
  } catch (err) {
    ElMessage.error(err instanceof Error ? err.message : "生成失败");
  } finally {
    loading.value = false;
  }
}
</script>

<style scoped>
.muted {
  color: #667085;
}

:deep(.el-card__header) {
  word-break: break-word;
}

@media (max-width: 600px) {
  .el-timeline-item__timestamp {
    font-size: 12px;
  }
  :deep(.el-collapse-item__title) {
    font-size: 13px;
    word-break: break-word;
  }
}

.saved-scripts {
  margin-top: 24px;
}

.saved-head {
  display: flex;
  align-items: baseline;
  gap: 10px;
  margin-bottom: 12px;
  flex-wrap: wrap;
}

.saved-head h3 {
  margin: 0;
  font-size: 17px;
}

.script-list {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(min(240px, 100%), 1fr));
  gap: 10px;
}

.script-item {
  appearance: none;
  border: 1px solid var(--line);
  background: #fff;
  border-radius: 14px;
  padding: 12px 14px;
  cursor: pointer;
  text-align: left;
  display: flex;
  flex-direction: column;
  gap: 4px;
  transition: 0.18s ease;
}

.script-item:hover {
  border-color: #ffb0cb;
  transform: translateY(-2px);
  box-shadow: var(--shadow);
}

.script-item.on {
  border-color: var(--accent);
  background: linear-gradient(180deg, #fff 0%, #fff0f5 100%);
}

.script-item b {
  font-size: 14px;
  color: var(--ink);
  line-height: 1.4;
}

.script-item span {
  font-size: 12px;
  color: var(--muted);
}
</style>
