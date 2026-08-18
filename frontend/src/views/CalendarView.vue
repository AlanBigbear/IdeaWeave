<template>
  <div>
    <div class="page-head">
      <h2>热点日历</h2>
      <p>粘贴热点 / 展会文本，AI 抽取日期、地点、Vlog 适配与商业化机会。</p>
    </div>
    <el-card>
      <el-input v-model="rawText" type="textarea" :rows="4" />
      <el-space style="margin-top: 12px">
        <el-button type="primary" :loading="loading" @click="extract">生成日历卡片</el-button>
        <el-button @click="rawText = SAMPLE_HOTSPOT">填入路演示例</el-button>
      </el-space>
    </el-card>
    <div class="card-grid" style="margin-top: 16px">
      <el-card v-for="item in events" :key="item.id">
        <el-tag>{{ item.start_date }} ~ {{ item.end_date }}</el-tag>
        <h3>{{ item.title }}</h3>
        <p>地点：{{ item.location }}</p>
        <p>Vlog 适配：{{ item.vlog_fit }}</p>
        <p>商业化：{{ item.commercial }}</p>
        <el-button link type="danger" @click="remove(item.id)">删除</el-button>
      </el-card>
    </div>
    <el-empty v-if="!events.length && !loading" description="还没有热点，先粘贴一段文本" />
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from "vue";
import { ElMessage } from "element-plus";
import { calendarApi } from "../api";
import { SAMPLE_HOTSPOT, type CalendarEvent } from "../types";

const rawText = ref("");
const loading = ref(false);
const events = ref<CalendarEvent[]>([]);

async function load() {
  const { data } = await calendarApi.list();
  events.value = data;
}

async function extract() {
  if (rawText.value.trim().length < 8) {
    ElMessage.warning("请粘贴热点文本");
    return;
  }
  loading.value = true;
  try {
    await calendarApi.extract(rawText.value);
    ElMessage.success("已加入日历");
    await load();
  } finally {
    loading.value = false;
  }
}

async function remove(id: number) {
  await calendarApi.remove(id);
  await load();
}

onMounted(load);
</script>
