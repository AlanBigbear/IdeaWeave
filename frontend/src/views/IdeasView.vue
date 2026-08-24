<template>
  <div>
    <div class="page-head">
      <h2>编导创意发散</h2>
      <p>输入模糊想法，输出 3 个差异化方案（复刻编导面试考核）。选定后进入脚本扩写。</p>
    </div>
    <el-card>
      <el-form label-position="top">
        <el-form-item label="关联选题（可选）">
          <el-select v-model="topicId" clearable placeholder="从选题库带入" style="width: 360px">
            <el-option v-for="item in topics" :key="item.id" :label="item.title" :value="item.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="模糊想法">
          <el-input v-model="vague" type="textarea" :rows="5" placeholder="例如：想拍上海展会，但还没想好切口" />
        </el-form-item>
        <el-button type="primary" :loading="loading" @click="diverge">生成 3 个创意</el-button>
      </el-form>
    </el-card>

    <div class="card-grid" style="margin-top: 16px">
      <el-card v-for="(idea, index) in session?.ideas || []" :key="idea.title" shadow="hover">
        <el-tag>方案 {{ index + 1 }}</el-tag>
        <h3>{{ idea.title }}</h3>
        <p><b>角度</b> {{ idea.angle }}</p>
        <p><b>受众</b> {{ idea.audience }}</p>
        <p><b>成本</b> {{ idea.cost }}</p>
        <p><b>钩子</b> {{ idea.hook }}</p>
        <p class="muted">{{ idea.why_different }}</p>
        <el-button type="primary" @click="select(index)">选定并去写脚本</el-button>
      </el-card>
    </div>
    <el-empty v-if="!session && !loading" description="生成后会出现 3 张差异化创意卡" />
    <el-empty v-else-if="loading && !session" description="正在生成 3 个创意，切到其它页也不会中断" />
  </div>
</template>

<script setup lang="ts">
import { onActivated, onMounted, ref } from "vue";
import { useRoute, useRouter } from "vue-router";
import { ElMessage } from "element-plus";
import { ideaApi, topicApi } from "../api";
import type { IdeaSession, Topic } from "../types";

defineOptions({ name: "IdeasView" });

const route = useRoute();
const router = useRouter();
const topics = ref<Topic[]>([]);
const topicId = ref<number | undefined>();
const vague = ref("");
const loading = ref(false);
const session = ref<IdeaSession | null>(null);

function applyQuery() {
  if (route.query.topicId) topicId.value = Number(route.query.topicId);
  if (route.query.hint) vague.value = String(route.query.hint);
}

async function loadTopics() {
  const { data } = await topicApi.list();
  topics.value = data;
}

onMounted(async () => {
  await loadTopics();
  applyQuery();
});

onActivated(async () => {
  applyQuery();
  await loadTopics();
});

async function diverge() {
  if (vague.value.trim().length < 4) {
    ElMessage.warning("请写得再具体一点");
    return;
  }
  loading.value = true;
  try {
    const { data } = await ideaApi.diverge(vague.value, topicId.value);
    session.value = data;
  } finally {
    loading.value = false;
  }
}

async function select(index: number) {
  if (!session.value) return;
  await ideaApi.select(session.value.id, index);
  ElMessage.success("已选定创意");
  const idea = session.value.ideas[index];
  router.push({
    path: "/script",
    query: {
      ideaSessionId: String(session.value.id),
      topicId: session.value.topic_id ? String(session.value.topic_id) : undefined,
      outline: `${idea.title}\n钩子：${idea.hook}\n角度：${idea.angle}`,
    },
  });
}
</script>

<style scoped>
.muted {
  color: #667085;
}
</style>
