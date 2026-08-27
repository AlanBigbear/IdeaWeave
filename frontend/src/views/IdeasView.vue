<template>
  <div>
    <div class="page-head">
      <h2>编导创意发散</h2>
      <p>只有一个模糊的念头也没关系，编导娘帮你抽 3 张差异化方案卡，都会自动存进创意库～</p>
    </div>
    <el-card>
      <el-form label-position="top">
        <el-form-item label="关联选题（可选）">
          <el-select v-model="topicId" clearable placeholder="从选题库捞一个" style="width: min(360px, 100%)">
            <el-option v-for="item in topics" :key="item.id" :label="item.title" :value="item.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="模糊想法">
          <el-input v-model="vague" type="textarea" :rows="4" placeholder="例如：想拍上海展会，但还没想好切口" />
        </el-form-item>
        <el-button type="primary" :loading="loading" @click="diverge">抽 3 张创意卡！</el-button>
      </el-form>
    </el-card>

    <div class="ai-progress-slot">
      <AiStream :active="loading" :thinking="thinking" :content="content" emoji="🪄" />
    </div>

    <div class="lib-head">
      <h3>🪄 创意卡库（{{ cards.length }}）</h3>
      <span class="muted">每次发散的方案都会自动存进来，可编辑、可删除、可一键去写脚本～</span>
    </div>
    <div v-if="cards.length" class="card-grid">
      <el-card v-for="card in cards" :key="card.session_id + '-' + card.index" shadow="hover">
        <div class="card-top">
          <el-tag size="small">创意卡</el-tag>
          <span class="time">{{ shortTime(card.created_at) }}</span>
        </div>
        <h3>{{ card.title }}</h3>
        <p><b>角度</b> {{ card.angle }}</p>
        <p><b>受众</b> {{ card.audience }}</p>
        <p><b>成本</b> {{ card.cost }}</p>
        <p><b>钩子</b> {{ card.hook }}</p>
        <p class="muted">{{ card.why_different }}</p>
        <div class="ops">
          <el-button type="primary" size="small" @click="goScript(card)">去写脚本</el-button>
          <el-button size="small" @click="openEdit(card)">编辑</el-button>
          <el-button size="small" type="danger" plain @click="removeCard(card)">删除</el-button>
        </div>
      </el-card>
    </div>
    <el-empty v-else-if="!loading" description="创意卡库还空空的，先抽一发～" />

    <el-dialog v-model="editDialog" title="编辑创意卡 ✏️" width="min(560px, 94vw)">
      <el-form label-position="top">
        <el-form-item label="标题">
          <el-input v-model="editForm.title" maxlength="24" show-word-limit />
        </el-form-item>
        <el-form-item label="角度">
          <el-input v-model="editForm.angle" type="textarea" :rows="2" />
        </el-form-item>
        <el-form-item label="受众">
          <el-input v-model="editForm.audience" />
        </el-form-item>
        <el-form-item label="成本">
          <el-input v-model="editForm.cost" />
        </el-form-item>
        <el-form-item label="钩子">
          <el-input v-model="editForm.hook" type="textarea" :rows="2" />
        </el-form-item>
        <el-form-item label="差异点">
          <el-input v-model="editForm.why_different" type="textarea" :rows="2" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="editDialog = false">取消</el-button>
        <el-button type="primary" :loading="savingEdit" @click="saveEdit">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { onActivated, onMounted, reactive, ref } from "vue";
import { useRoute, useRouter } from "vue-router";
import { ElMessage, ElMessageBox } from "element-plus";
import { divergeStream, ideaApi, topicApi } from "../api";
import type { IdeaCard, Topic } from "../types";
import { useWorkspaceStore } from "../stores/workspace";
import AiStream from "../components/AiStream.vue";

defineOptions({ name: "IdeasView" });

const route = useRoute();
const router = useRouter();
const workspace = useWorkspaceStore();
const topics = ref<Topic[]>([]);
const topicId = ref<number | undefined>();
const vague = ref("");
const loading = ref(false);
const thinking = ref("");
const content = ref("");
const cards = ref<IdeaCard[]>([]);

const editDialog = ref(false);
const savingEdit = ref(false);
const editing = ref<IdeaCard | null>(null);
const editForm = reactive({
  title: "",
  angle: "",
  audience: "",
  cost: "",
  hook: "",
  why_different: "",
});

function applyQuery() {
  if (route.query.topicId) topicId.value = Number(route.query.topicId);
  if (route.query.hint) vague.value = String(route.query.hint);
}

async function loadTopics(opts?: { silent?: boolean }) {
  if (opts?.silent && topics.value.length) {
    void topicApi.list().then(({ data }) => {
      topics.value = data;
      workspace.topics = data;
    });
    return;
  }
  if (workspace.topics.length && !topics.value.length) {
    topics.value = workspace.topics;
    void topicApi.list().then(({ data }) => {
      topics.value = data;
      workspace.topics = data;
    });
    return;
  }
  const { data } = await topicApi.list();
  topics.value = data;
  workspace.topics = data;
}

async function refreshCards() {
  const { data } = await ideaApi.listCards();
  cards.value = data;
}

function shortTime(iso: string) {
  if (!iso) return "";
  const d = new Date(iso);
  const p = (n: number) => String(n).padStart(2, "0");
  return `${d.getMonth() + 1}/${d.getDate()} ${p(d.getHours())}:${p(d.getMinutes())}`;
}

onMounted(async () => {
  await loadTopics();
  await refreshCards();
  applyQuery();
});

let skipActivate = true;
onActivated(() => {
  applyQuery();
  if (skipActivate) {
    skipActivate = false;
    return;
  }
  void loadTopics({ silent: true });
  void refreshCards();
});

async function diverge() {
  if (vague.value.trim().length < 4) {
    ElMessage.warning("再多写一点点，哪怕一个念头也行");
    return;
  }
  loading.value = true;
  thinking.value = "";
  content.value = "";
  try {
    await divergeStream(
      { vague_idea: vague.value, topic_id: topicId.value },
      (kind, text) => {
        if (kind === "thinking") thinking.value += text;
        else content.value += text;
      },
    );
    await refreshCards();
    ElMessage.success("3 张创意卡已存进创意库！");
  } catch (err) {
    ElMessage.error(err instanceof Error ? err.message : "生成失败");
  } finally {
    loading.value = false;
  }
}

function goScript(card: IdeaCard) {
  router.push({
    path: "/script",
    query: {
      ideaSessionId: String(card.session_id),
      outline: `${card.title}\n钩子：${card.hook}\n角度：${card.angle}`,
    },
  });
}

function openEdit(card: IdeaCard) {
  editing.value = card;
  editForm.title = card.title;
  editForm.angle = card.angle;
  editForm.audience = card.audience;
  editForm.cost = card.cost;
  editForm.hook = card.hook;
  editForm.why_different = card.why_different;
  editDialog.value = true;
}

async function saveEdit() {
  if (!editing.value) return;
  if (!editForm.title.trim()) {
    ElMessage.warning("标题不能为空");
    return;
  }
  savingEdit.value = true;
  try {
    await ideaApi.updateCard(editing.value.session_id, editing.value.index, { ...editForm });
    editDialog.value = false;
    await refreshCards();
    ElMessage.success("创意卡已更新～");
  } catch (err) {
    ElMessage.error(err instanceof Error ? err.message : "保存失败");
  } finally {
    savingEdit.value = false;
  }
}

async function removeCard(card: IdeaCard) {
  try {
    await ElMessageBox.confirm(`确定删除「${card.title}」这张创意卡吗？`, "删除创意卡", {
      type: "warning",
    });
  } catch {
    return;
  }
  await ideaApi.deleteCard(card.session_id, card.index);
  await refreshCards();
  ElMessage.success("已删除");
}
</script>

<style scoped>
.muted {
  color: #667085;
}

.ai-progress-slot {
  display: flex;
  justify-content: center;
}

.lib-head {
  display: flex;
  align-items: baseline;
  gap: 10px;
  margin: 24px 0 12px;
  flex-wrap: wrap;
}

.lib-head h3 {
  margin: 0;
  font-size: 17px;
}

.card-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 8px;
}

.time {
  font-size: 12px;
  color: #c48aa3;
}

.ops {
  display: flex;
  gap: 8px;
  margin-top: 12px;
  flex-wrap: wrap;
}
</style>
