<template>
  <div>
    <div class="page-head">
      <h2>灵感采集</h2>
      <p>刷到的爆款直接丢进来，贴文字或甩链接都行，编导娘帮你把爆点薅出来～</p>
    </div>
    <el-row :gutter="16">
      <el-col :md="14">
        <el-card>
          <el-segmented
            v-model="mode"
            :options="[
              { label: '📝 粘贴文本', value: 'text' },
              { label: '🔗 链接抓取', value: 'link' },
            ]"
            block
            style="margin-bottom: 18px"
          />
          <el-form label-position="top">
            <template v-if="mode === 'link'">
              <el-form-item label="内容链接">
                <el-input
                  v-model="url"
                  placeholder="https://… 粘贴文章 / 专栏 / 新闻页链接"
                  clearable
                  @keyup.enter="extractByLink"
                >
                  <template #append>
                    <el-button :loading="loading" @click="extractByLink">冲！抓取提取</el-button>
                  </template>
                </el-input>
              </el-form-item>
              <p class="tip">
                公众号文章、新闻页、B 站专栏这种能直接打开的页面都支持；要登录或纯 JS
                渲染的页面可能薅不到正文，切回文本模式粘进来就好。点
                <el-button text size="small" :loading="fetching" @click="preview">先预览抓取内容</el-button>
                看看抓到了啥，也能编辑后再提取。
              </p>
              <AiProgress :active="fetching" variant="fetch" />
            </template>
            <el-form-item v-if="mode === 'text'" label="爆款摘要">
              <el-input
                v-model="rawText"
                type="textarea"
                :rows="12"
                placeholder="把你整理的爆款内容丢到这里，或者用右边的链接模式自动抓"
              />
            </el-form-item>
            <el-form-item label="来源备注（可选）">
              <el-input v-model="sourceNote" placeholder="例如：自己存的爆款笔记 / 评论区总结；链接模式留空会自动记来源" />
            </el-form-item>
            <el-space v-if="mode === 'text'">
              <el-button type="primary" :loading="loading" @click="extractByText">提取入库～</el-button>
              <el-button @click="rawText = SAMPLE_VIRAL">塞个示例</el-button>
            </el-space>
          </el-form>
          <AiProgress :active="loading" variant="extract" />
        </el-card>
      </el-col>
      <el-col :md="10">
        <el-card v-if="result">
          <template #header>提炼完成！已收进选题库</template>
          <h3>{{ result.title }}</h3>
          <el-tag :type="result.feasibility === 'quick' ? 'success' : 'warning'">
            {{ result.feasibility === "quick" ? "短平快可执行" : "高成本暂缓" }}
          </el-tag>
          <p>{{ result.why }}</p>
          <p class="muted">成本：{{ result.cost_note }}</p>
          <ul>
            <li v-for="item in result.highlights" :key="item">{{ item }}</li>
          </ul>
          <el-button type="primary" link @click="router.push('/topics')">去选题库瞅一眼</el-button>
        </el-card>
        <el-empty v-else description="提炼出的选题会在这里等你" />
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
import { useWorkspaceStore } from "../stores/workspace";
import AiProgress from "../components/AiProgress.vue";

defineOptions({ name: "InspirationView" });

const router = useRouter();
const workspace = useWorkspaceStore();
const mode = ref<"text" | "link">("text");
const url = ref("");
const rawText = ref("");
const sourceNote = ref("");
const loading = ref(false);
const fetching = ref(false);
const result = ref<Topic | null>(null);

function requireLink(): string | null {
  const value = url.value.trim();
  if (!/^https?:\/\//i.test(value)) {
    ElMessage.warning("请粘贴以 http(s):// 开头的链接");
    return null;
  }
  return value;
}

async function extractByText() {
  if (rawText.value.trim().length < 8) {
    ElMessage.warning("请粘贴更完整的摘要");
    return;
  }
  loading.value = true;
  try {
    const { data } = await inspirationApi.extract({ raw_text: rawText.value, source_note: sourceNote.value });
    result.value = data;
    void workspace.refreshTopics();
    ElMessage.success("收进选题库啦！");
  } finally {
    loading.value = false;
  }
}

async function extractByLink() {
  const link = requireLink();
  if (!link) return;
  loading.value = true;
  try {
    const { data } = await inspirationApi.extract({ url: link, source_note: sourceNote.value });
    result.value = data;
    void workspace.refreshTopics();
    ElMessage.success("原文到手，已收进选题库！");
  } finally {
    loading.value = false;
  }
}

async function preview() {
  const link = requireLink();
  if (!link) return;
  fetching.value = true;
  try {
    const { data } = await inspirationApi.fetchUrl(link);
    rawText.value = `《${data.title}》（来源：${data.site_name}）\n${data.text}`;
    mode.value = "text";
    if (!sourceNote.value) sourceNote.value = `链接抓取：${data.url}`;
    ElMessage.success(
      data.truncated ? "正文到手（太长已截断），改改再提取～" : "正文到手，改改就能提取～",
    );
  } finally {
    fetching.value = false;
  }
}
</script>

<style scoped>
.muted {
  color: #667085;
}

.tip {
  color: #8a7176;
  font-size: 13px;
  line-height: 1.7;
  margin: -10px 0 14px;
}

.tip .el-button {
  padding: 0;
  vertical-align: baseline;
}
</style>
