<template>
  <div>
    <div class="page-head">
      <h2>选题库</h2>
      <p>筛选短平快 / 高成本，随时记下零碎灵感，导出 Markdown。</p>
    </div>
    <el-card>
      <el-space wrap>
        <div class="seg-tabs">
          <button class="seg-tab" :class="{ on: feasibility === '' }" @click="feasibility = ''; load()">全部</button>
          <button class="seg-tab" :class="{ on: feasibility === 'quick' }" @click="feasibility = 'quick'; load()">短平快可执行</button>
          <button class="seg-tab" :class="{ on: feasibility === 'deferred' }" @click="feasibility = 'deferred'; load()">高成本暂缓</button>
        </div>
        <el-input v-model="q" placeholder="搜索标题" style="width: 220px" clearable @clear="load" @keyup.enter="load" />
        <el-button @click="load">搜索</el-button>
        <el-button type="primary" @click="showManual = true">记一条零碎灵感</el-button>
        <el-button @click="exportMd">导出 Markdown</el-button>
      </el-space>
    </el-card>

    <el-table :data="topics" style="margin-top: 16px" v-loading="loading">
      <el-table-column prop="title" label="选题" min-width="180" />
      <el-table-column label="可行性" width="130">
        <template #default="{ row }">
          <el-tag :type="row.feasibility === 'quick' ? 'success' : 'warning'">
            {{ row.feasibility === "quick" ? "短平快" : "暂缓" }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="来源" width="110">
        <template #default="{ row }">{{ row.source === "extract" ? "AI 提取" : "零碎灵感" }}</template>
      </el-table-column>
      <el-table-column prop="why" label="理由" min-width="220" show-overflow-tooltip />
      <el-table-column label="操作" width="220">
        <template #default="{ row }">
          <el-button link type="primary" @click="goIdea(row)">去发散</el-button>
          <el-button link type="danger" @click="remove(row.id)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="showManual" title="随时增加零碎灵感" width="520px">
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
        <el-form-item label="成本/理由">
          <el-input v-model="manual.why" type="textarea" :rows="3" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showManual = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="saveManual">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from "vue";
import { useRouter } from "vue-router";
import { ElMessage } from "element-plus";
import { topicApi } from "../api";
import type { Topic } from "../types";

const router = useRouter();
const topics = ref<Topic[]>([]);
const feasibility = ref("");
const q = ref("");
const loading = ref(false);
const showManual = ref(false);
const saving = ref(false);
const manual = reactive({ title: "", highlights: "", feasibility: "quick", why: "" });

async function load() {
  loading.value = true;
  try {
    const { data } = await topicApi.list({
      feasibility: feasibility.value || undefined,
      q: q.value || undefined,
    });
    topics.value = data;
  } finally {
    loading.value = false;
  }
}

async function saveManual() {
  if (!manual.title.trim()) return;
  saving.value = true;
  try {
    await topicApi.create({
      title: manual.title,
      highlights: manual.highlights.split(/[,，]/).map((s) => s.trim()).filter(Boolean),
      feasibility: manual.feasibility,
      why: manual.why,
    });
    showManual.value = false;
    manual.title = "";
    manual.highlights = "";
    manual.why = "";
    ElMessage.success("已记入选题库");
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
  const { data } = await topicApi.exportMd(feasibility.value || undefined);
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

onMounted(load);
</script>
