<template>
  <div>
    <div class="page-head">
      <h2>选题库</h2>
      <p>点点标签就能改状态和优先级，标签想怎么打就怎么打，还能导出 Markdown～</p>
    </div>
    <el-card>
      <el-space wrap>
        <div class="seg-tabs">
          <button class="seg-tab" :class="{ on: feasibility === '' }" @click="feasibility = ''; load()">全部</button>
          <button class="seg-tab" :class="{ on: feasibility === 'quick' }" @click="feasibility = 'quick'; load()">短平快可执行</button>
          <button class="seg-tab" :class="{ on: feasibility === 'deferred' }" @click="feasibility = 'deferred'; load()">高成本暂缓</button>
        </div>
        <el-select v-model="statusFilter" placeholder="状态" clearable style="width: min(110px, 40vw)" @change="load">
          <el-option v-for="(label, key) in STATUS_LABELS" :key="key" :label="label" :value="key" />
        </el-select>
        <el-select v-model="priorityFilter" placeholder="优先级" clearable style="width: min(100px, 40vw)" @change="load">
          <el-option v-for="(label, key) in PRIORITY_LABELS" :key="key" :label="label" :value="key" />
        </el-select>
        <el-select v-model="tagFilter" placeholder="标签" clearable filterable style="width: min(130px, 40vw)" @change="load">
          <el-option v-for="t in allTags" :key="t" :label="t" :value="t" />
        </el-select>
        <el-input v-model="q" placeholder="搜标题" style="width: min(200px, 60vw)" clearable @clear="load" @keyup.enter="load" />
        <el-button @click="load">搜索</el-button>
        <el-button type="primary" @click="showManual = true">冒灵感了？记一笔</el-button>
        <el-button @click="exportMd">导出 Markdown</el-button>
      </el-space>
    </el-card>

    <el-table v-if="!isMobile" :data="topics" style="margin-top: 16px" v-loading="loading" empty-text="选题库还空空的，先去采点灵感吧～">
      <el-table-column label="选题" min-width="220">
        <template #default="{ row }">
          <div>{{ row.title }}</div>
          <div v-if="row.tags?.length" class="topic-tags">
            <el-tag v-for="t in row.tags" :key="t" size="small" effect="plain">{{ t }}</el-tag>
          </div>
        </template>
      </el-table-column>
      <el-table-column label="可行性" width="96">
        <template #default="{ row }">
          <el-tag :type="row.feasibility === 'quick' ? 'success' : 'warning'">
            {{ row.feasibility === "quick" ? "短平快" : "暂缓" }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="优先级" width="90">
        <template #default="{ row }">
          <el-dropdown trigger="click" @command="(cmd: string) => patchField(row, 'priority', cmd)">
            <el-tag :type="PRIORITY_TYPES[row.priority] ?? 'info'" class="tag-trigger">
              {{ PRIORITY_LABELS[row.priority] || row.priority }}
            </el-tag>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item v-for="(label, key) in PRIORITY_LABELS" :key="key" :command="key">{{ label }}</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </template>
      </el-table-column>
      <el-table-column label="状态" width="90">
        <template #default="{ row }">
          <el-dropdown trigger="click" @command="(cmd: string) => patchField(row, 'status', cmd)">
            <el-tag :type="STATUS_TYPES[row.status] ?? 'info'" class="tag-trigger">
              {{ STATUS_LABELS[row.status] || row.status }}
            </el-tag>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item v-for="(label, key) in STATUS_LABELS" :key="key" :command="key">{{ label }}</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </template>
      </el-table-column>
      <el-table-column label="来源" width="96">
        <template #default="{ row }">{{ row.source === "extract" ? "AI 提取" : "零碎灵感" }}</template>
      </el-table-column>
      <el-table-column prop="why" label="理由" min-width="180" show-overflow-tooltip />
      <el-table-column label="操作" width="190" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" @click="goIdea(row)">去发散</el-button>
          <el-button link @click="openEdit(row)">编辑</el-button>
          <el-button link type="danger" @click="remove(row.id)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <!-- 手机端卡片列表 -->
    <div v-else class="topic-cards" v-loading="loading">
      <el-empty v-if="!topics.length" description="选题库还空空的，先去采点灵感吧～" />
      <el-card v-for="row in topics" :key="row.id" class="topic-card" shadow="hover">
        <div class="tc-head" @click="openEdit(row)">
          <b>{{ row.title }}</b>
          <el-tag size="small" :type="row.feasibility === 'quick' ? 'success' : 'warning'">
            {{ row.feasibility === "quick" ? "短平快" : "暂缓" }}
          </el-tag>
        </div>
        <div v-if="row.tags?.length" class="topic-tags">
          <el-tag v-for="t in row.tags" :key="t" size="small" effect="plain">{{ t }}</el-tag>
        </div>
        <p class="tc-why">{{ row.why }}</p>
        <div class="tc-marks">
          <el-dropdown trigger="click" @command="(cmd: string) => patchField(row, 'priority', cmd)">
            <el-tag :type="PRIORITY_TYPES[row.priority] ?? 'info'" class="tag-trigger">优先级 {{ PRIORITY_LABELS[row.priority] || row.priority }}</el-tag>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item v-for="(label, key) in PRIORITY_LABELS" :key="key" :command="key">{{ label }}</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
          <el-dropdown trigger="click" @command="(cmd: string) => patchField(row, 'status', cmd)">
            <el-tag :type="STATUS_TYPES[row.status] ?? 'info'" class="tag-trigger">{{ STATUS_LABELS[row.status] || row.status }}</el-tag>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item v-for="(label, key) in STATUS_LABELS" :key="key" :command="key">{{ label }}</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
        <div class="tc-ops">
          <el-button size="small" type="primary" plain round @click="goIdea(row)">去发散</el-button>
          <el-button size="small" plain round @click="openEdit(row)">编辑</el-button>
          <el-button size="small" type="danger" plain round @click="remove(row.id)">删除</el-button>
        </div>
      </el-card>
    </div>

    <el-dialog v-model="showManual" title="新灵感先记下来" width="min(540px, 94vw)">
      <el-form label-position="top">
        <el-form-item label="标题">
          <el-input v-model="manual.title" />
        </el-form-item>
        <el-form-item label="爆点（逗号分隔）">
          <el-input v-model="manual.highlights" />
        </el-form-item>
        <el-form-item label="可行性">
          <el-select v-model="manual.feasibility">
            <el-option label="短平快可执行" value="quick" />
            <el-option label="高成本暂缓" value="deferred" />
          </el-select>
        </el-form-item>
        <el-form-item label="优先级">
          <el-select v-model="manual.priority">
            <el-option v-for="(label, key) in PRIORITY_LABELS" :key="key" :label="label" :value="key" />
          </el-select>
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="manual.status">
            <el-option v-for="(label, key) in STATUS_LABELS" :key="key" :label="label" :value="key" />
          </el-select>
        </el-form-item>
        <el-form-item label="标签（输入后回车，自定义随便加）">
          <el-select
            v-model="manual.tags"
            multiple
            filterable
            allow-create
            default-first-option
            placeholder="添加标签"
            style="width: 100%"
          >
            <el-option v-for="t in allTags" :key="t" :label="t" :value="t" />
          </el-select>
        </el-form-item>
        <el-form-item label="成本/理由">
          <el-input v-model="manual.why" type="textarea" :rows="3" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showManual = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="saveManual">保存</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="showEdit" title="编辑选题" width="min(540px, 94vw)">
      <el-form label-position="top">
        <el-form-item label="标题">
          <el-input v-model="editForm.title" />
        </el-form-item>
        <el-form-item label="爆点（逗号分隔）">
          <el-input v-model="editForm.highlights" />
        </el-form-item>
        <el-form-item label="可行性">
          <el-select v-model="editForm.feasibility">
            <el-option label="短平快可执行" value="quick" />
            <el-option label="高成本暂缓" value="deferred" />
          </el-select>
        </el-form-item>
        <el-form-item label="优先级">
          <el-select v-model="editForm.priority">
            <el-option v-for="(label, key) in PRIORITY_LABELS" :key="key" :label="label" :value="key" />
          </el-select>
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="editForm.status">
            <el-option v-for="(label, key) in STATUS_LABELS" :key="key" :label="label" :value="key" />
          </el-select>
        </el-form-item>
        <el-form-item label="标签（输入后回车，自定义随便加）">
          <el-select
            v-model="editForm.tags"
            multiple
            filterable
            allow-create
            default-first-option
            placeholder="添加标签"
            style="width: 100%"
          >
            <el-option v-for="t in allTags" :key="t" :label="t" :value="t" />
          </el-select>
        </el-form-item>
        <el-form-item label="成本/理由">
          <el-input v-model="editForm.why" type="textarea" :rows="3" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showEdit = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="saveEdit">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { computed, onActivated, onBeforeUnmount, onMounted, reactive, ref } from "vue";
import { useRouter } from "vue-router";
import { ElMessage } from "element-plus";
import { topicApi } from "../api";
import { useWorkspaceStore } from "../stores/workspace";
import type { Topic } from "../types";

defineOptions({ name: "TopicsView" });

const MOBILE_QUERY = "(max-width: 768px)";
let mql: MediaQueryList | null = null;
const isMobile = ref(false);
function syncMobile() {
  isMobile.value = mql?.matches ?? false;
}
onMounted(() => {
  mql = window.matchMedia(MOBILE_QUERY);
  syncMobile();
  mql.addEventListener("change", syncMobile);
});
onBeforeUnmount(() => mql?.removeEventListener("change", syncMobile));

type TagType = "primary" | "success" | "warning" | "danger" | "info";

const STATUS_LABELS: Record<string, string> = { inbox: "待定", ready: "可用", paused: "暂缓", dropped: "弃用" };
const STATUS_TYPES: Record<string, TagType> = { inbox: "info", ready: "success", paused: "warning", dropped: "danger" };
const PRIORITY_LABELS: Record<string, string> = { high: "高", mid: "中", low: "低" };
const PRIORITY_TYPES: Record<string, TagType> = { high: "danger", mid: "warning", low: "info" };

const router = useRouter();
const workspace = useWorkspaceStore();
const topics = ref<Topic[]>([]);
const feasibility = ref("");
const statusFilter = ref("");
const priorityFilter = ref("");
const tagFilter = ref("");
const q = ref("");
const loading = ref(false);
const showManual = ref(false);
const showEdit = ref(false);
const saving = ref(false);
const knownTags = ref<Set<string>>(new Set());
const manual = reactive({
  title: "",
  highlights: "",
  feasibility: "quick",
  priority: "mid",
  status: "inbox",
  tags: [] as string[],
  why: "",
});
const editForm = reactive({
  id: 0,
  title: "",
  highlights: "",
  feasibility: "quick",
  priority: "mid",
  status: "inbox",
  tags: [] as string[],
  why: "",
});

const allTags = computed(() => Array.from(knownTags.value).sort());

function splitList(value: string) {
  return value
    .split(/[,，]/)
    .map((s) => s.trim())
    .filter(Boolean);
}

async function load(opts?: { silent?: boolean }) {
  const silent = Boolean(opts?.silent);
  if (!silent) loading.value = true;
  try {
    const { data } = await topicApi.list({
      feasibility: feasibility.value || undefined,
      q: q.value || undefined,
      status: statusFilter.value || undefined,
      priority: priorityFilter.value || undefined,
      tag: tagFilter.value || undefined,
    });
    topics.value = data;
    data.forEach((t) => t.tags?.forEach((tag) => knownTags.value.add(tag)));
    if (!feasibility.value && !q.value && !statusFilter.value && !priorityFilter.value && !tagFilter.value) {
      workspace.topics = data;
    }
  } finally {
    loading.value = false;
  }
}

async function patchField(row: Topic, field: "status" | "priority", value: string) {
  const { data } = await topicApi.patch(row.id, { [field]: value });
  Object.assign(row, data);
  ElMessage.success("改好了");
}

function openEdit(row: Topic) {
  editForm.id = row.id;
  editForm.title = row.title;
  editForm.highlights = row.highlights.join("，");
  editForm.feasibility = row.feasibility;
  editForm.priority = row.priority;
  editForm.status = row.status;
  editForm.tags = [...(row.tags || [])];
  editForm.why = row.why;
  showEdit.value = true;
}

async function saveEdit() {
  if (!editForm.title.trim()) return;
  saving.value = true;
  try {
    await topicApi.patch(editForm.id, {
      title: editForm.title,
      highlights: splitList(editForm.highlights),
      feasibility: editForm.feasibility,
      priority: editForm.priority,
      status: editForm.status,
      tags: editForm.tags,
      why: editForm.why,
    });
    showEdit.value = false;
    ElMessage.success("存好了～");
    await load();
  } finally {
    saving.value = false;
  }
}

async function saveManual() {
  if (!manual.title.trim()) return;
  saving.value = true;
  try {
    await topicApi.create({
      title: manual.title,
      highlights: splitList(manual.highlights),
      feasibility: manual.feasibility,
      priority: manual.priority,
      status: manual.status,
      tags: manual.tags,
      why: manual.why,
    });
    showManual.value = false;
    manual.title = "";
    manual.highlights = "";
    manual.priority = "mid";
    manual.status = "inbox";
    manual.tags = [];
    manual.why = "";
    ElMessage.success("记好啦，收进选题库～");
    await load();
  } finally {
    saving.value = false;
  }
}

async function remove(id: number) {
  await topicApi.remove(id);
  await load();
}

async function exportMd() {
  const { data } = await topicApi.exportMd({
    feasibility: feasibility.value || undefined,
    status: statusFilter.value || undefined,
    priority: priorityFilter.value || undefined,
    tag: tagFilter.value || undefined,
  });
  const blob = new Blob([data], { type: "text/markdown" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = "bstar-topics.md";
  a.click();
  URL.revokeObjectURL(url);
}

function goIdea(row: Topic) {
  router.push({ path: "/ideas", query: { topicId: String(row.id), hint: row.title } });
}

onMounted(() => {
  if (workspace.topics.length) {
    topics.value = workspace.topics;
    workspace.topics.forEach((t) => t.tags?.forEach((tag) => knownTags.value.add(tag)));
    void load({ silent: true });
  } else {
    void load();
  }
});
let skipActivate = true;
onActivated(() => {
  if (skipActivate) {
    skipActivate = false;
    return;
  }
  void load({ silent: topics.value.length > 0 });
});
</script>

<style scoped>
.topic-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  margin-top: 4px;
}

.tag-trigger {
  cursor: pointer;
  outline: none;
}

/* 手机卡片列表 */
.topic-cards {
  margin-top: 14px;
  display: flex;
  flex-direction: column;
  gap: 12px;
  min-height: 120px;
}

.tc-head {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 10px;
}

.tc-head b {
  font-size: 15px;
  line-height: 1.5;
}

.tc-why {
  margin: 8px 0;
  font-size: 13px;
  color: #8a7176;
  line-height: 1.6;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.tc-marks {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.tc-marks .el-tag {
  padding: 6px 10px;
}

.tc-ops {
  margin-top: 12px;
  display: flex;
  gap: 8px;
}

.tc-ops .el-button {
  flex: 1;
}

@media (max-width: 768px) {
  .tag-trigger {
    padding: 6px 10px;
  }
  .el-dialog .el-button {
    padding: 12px 18px;
  }
}
</style>
