<template>
  <div>
    <div class="page-head">
      <h2>灵感采集</h2>
      <p>像发笔记一样，把你整理的爆款摘要贴进来。AI 抽爆点，并按你的分区和更新节奏打标。</p>
    </div>
    <el-row :gutter="16">
      <el-col :md="14">
        <el-card>
          <el-form label-position="top">
            <el-form-item label="来源备注（可选）">
              <el-input v-model="sourceNote" placeholder="例如：自己存的爆款笔记 / 评论区总结" />
            </el-form-item>
            <el-form-item label="爆款摘要">
              <el-input v-model="rawText" type="textarea" :rows="12" placeholder="把你整理的爆款内容粘贴到这里" />
            </el-form-item>
            <el-space>
              <el-button type="primary" :loading="loading" @click="extract">提取并入库</el-button>
              <el-button @click="rawText = SAMPLE_VIRAL">填入路演示例</el-button>
            </el-space>
          </el-form>
        </el-card>
      </el-col>
      <el-col :md="10">
        <el-card v-if="result">
          <template #header>提取结果（已写入选题库）</template>
          <h3>{{ result.title }}</h3>
          <el-tag :type="result.feasibility === 'quick' ? 'success' : 'warning'">
            {{ result.feasibility === "quick" ? "短平快可执行" : "高成本暂缓" }}
          </el-tag>
          <p>{{ result.why }}</p>
          <p class="muted">成本：{{ result.cost_note }}</p>
          <ul>
            <li v-for="item in result.highlights" :key="item">{{ item }}</li>
          </ul>
          <el-button type="primary" link @click="router.push('/topics')">去选题库查看</el-button>
        </el-card>
        <el-empty v-else description="提取结果会显示在这里" />
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { ref } from "vue";
import { useRouter } from "vue-router";
import { ElMessage } from "element-plus";
import { inspirationApi } from "../api";
import { SAMPLE_VIRAL, type Topic } from "../types";

const router = useRouter();
const rawText = ref("");
const sourceNote = ref("");
const loading = ref(false);
const result = ref<Topic | null>(null);

async function extract() {
  if (rawText.value.trim().length < 8) {
    ElMessage.warning("请粘贴更完整的摘要");
    return;
  }
  loading.value = true;
  try {
    const { data } = await inspirationApi.extract(rawText.value, sourceNote.value);
    result.value = data;
    ElMessage.success("已写入选题库");
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
