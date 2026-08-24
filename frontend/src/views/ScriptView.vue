<template>
  <div>
    <div class="page-head">
      <h2>大纲扩写脚本</h2>
      <p>输入大纲 + 拍摄清单，生成钩子、台词、镜头、互动；附 6 套封面 Prompt 与审核风险。</p>
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
              <el-button type="primary" :loading="loading" @click="expand">生成脚本</el-button>
              <el-button @click="fillSample">填入路演示例</el-button>
            </el-space>
            <p v-if="status" class="muted">{{ status }}</p>
          </el-form>
        </el-card>
      </el-col>
      <el-col :md="14">
        <el-empty v-if="!record" description="脚本、封面 Prompt、风险预警会显示在右侧" />
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
            <template #header>6 套封面生图 Prompt（不生图）</template>
            <el-collapse>
              <el-collapse-item v-for="(cover, i) in record.cover_prompts" :key="i" :title="`${i + 1}. ${cover.style}`">
                {{ cover.prompt }}
              </el-collapse-item>
            </el-collapse>
          </el-card>
          <el-card style="margin-top: 12px">
            <template #header>脚本风险预警</template>
            <el-table :data="record.risks">
              <el-table-column prop="level" label="级别" width="80" />
              <el-table-column prop="category" label="类型" width="120" />
              <el-table-column prop="detail" label="问题" />
              <el-table-column prop="suggestion" label="建议" />
            </el-table>
          </el-card>
        </template>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { onActivated, onMounted, ref } from "vue";
import { useRoute } from "vue-router";
import { ElMessage } from "element-plus";
import { expandScriptStream } from "../api";
import { SAMPLE_OUTLINE, SAMPLE_SHOTLIST, type ScriptRecord } from "../types";

defineOptions({ name: "ScriptView" });

const route = useRoute();
const outline = ref("");
const shotList = ref("");
const loading = ref(false);
const status = ref("");
const record = ref<ScriptRecord | null>(null);
const ideaSessionId = ref<number | null>(null);
const topicId = ref<number | null>(null);

function applyQuery() {
  if (route.query.outline) outline.value = String(route.query.outline);
  if (route.query.ideaSessionId) ideaSessionId.value = Number(route.query.ideaSessionId);
  if (route.query.topicId) topicId.value = Number(route.query.topicId);
}

onMounted(applyQuery);
onActivated(applyQuery);

function fillSample() {
  outline.value = SAMPLE_OUTLINE;
  shotList.value = SAMPLE_SHOTLIST;
}

async function expand() {
  if (outline.value.trim().length < 8) {
    ElMessage.warning("请先填写大纲");
    return;
  }
  loading.value = true;
  status.value = "正在连接模型...";
  try {
    record.value = await expandScriptStream(
      {
        outline: outline.value,
        shot_list: shotList.value,
        idea_session_id: ideaSessionId.value,
        topic_id: topicId.value,
      },
      (msg) => {
        status.value = msg;
      },
    );
    ElMessage.success("脚本已生成");
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
</style>
