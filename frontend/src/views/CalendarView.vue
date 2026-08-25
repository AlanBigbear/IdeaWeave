<template>
  <div>
    <div class="page-head">
      <h2>热点日历</h2>
      <p>按你的人设蹲未来 30 天的热点，宁缺毋滥只留能拍的～点日历上的日期直接开写。</p>
    </div>

    <el-card>
      <el-space wrap>
        <el-button type="primary" :loading="capturing" @click="capture">蹲一波未来 30 天热点</el-button>
        <el-button @click="openCreate()">手动添加</el-button>
        <el-button @click="showPaste = !showPaste">从文本里薅一条</el-button>
      </el-space>
      <div v-if="showPaste" class="paste-box">
        <el-input v-model="rawText" type="textarea" :rows="3" placeholder="把展会 / 热点原文丢进来，编导娘帮你排进日历" />
        <el-space style="margin-top: 8px">
          <el-button type="primary" :loading="extracting" @click="extract">排进日历</el-button>
          <el-button @click="rawText = SAMPLE_HOTSPOT">填入示例</el-button>
        </el-space>
      </div>
      <AiProgress :active="capturing || extracting" variant="calendar" />
    </el-card>

    <el-row :gutter="16" style="margin-top: 16px">
      <el-col :md="14" :xs="24">
        <el-card>
          <el-calendar v-model="calDate">
            <template #header>
              <div class="cal-head">
                <b>{{ calDate.getFullYear() }} 年 {{ calDate.getMonth() + 1 }} 月</b>
                <el-button-group>
                  <el-button size="small" @click="calDate = new Date(calDate.getFullYear(), calDate.getMonth() - 1, 1)">‹ 上月</el-button>
                  <el-button size="small" @click="calDate = new Date()">今天</el-button>
                  <el-button size="small" @click="calDate = new Date(calDate.getFullYear(), calDate.getMonth() + 1, 1)">下月 ›</el-button>
                </el-button-group>
              </div>
            </template>
            <template #date-cell="{ data }">
              <div class="cell" :class="{ today: data.isToday, selected: data.isSelected }" @click="pickDay(data.day)">
                <span class="num">{{ dayNum(data.day) }}</span>
                <small v-for="item in eventsOn(data.day).slice(0, 2)" :key="item.id" class="dot">{{ item.title }}</small>
                <em v-if="eventsOn(data.day).length > 2">+{{ eventsOn(data.day).length - 2 }}</em>
              </div>
            </template>
          </el-calendar>
        </el-card>
      </el-col>
      <el-col :md="10" :xs="24">
        <el-card>
          <template #header>
            <div class="list-head">
              <span>{{ selectedLabel }} 的热点</span>
              <el-button link type="primary" @click="openCreate(selectedDay)">+ 这一天</el-button>
            </div>
          </template>
          <el-empty v-if="!dayEvents.length" description="这天还空空的" />
          <div v-for="item in dayEvents" :key="item.id" class="event">
            <div class="event-top">
              <b>{{ item.title }}</b>
              <el-tag size="small">{{ sourceText(item.source) }}</el-tag>
            </div>
            <p class="muted">{{ item.start_date }}{{ item.end_date && item.end_date !== item.start_date ? " ~ " + item.end_date : "" }} · {{ item.location || "地点未填" }}</p>
            <p v-if="item.vlog_fit"><b>怎么拍</b> {{ item.vlog_fit }}</p>
            <p v-if="item.commercial"><b>商业化</b> {{ item.commercial }}</p>
            <el-space>
              <el-button link type="primary" @click="goIdea(item)">去发散</el-button>
              <el-button link type="primary" @click="openEdit(item)">修改</el-button>
              <el-button link type="danger" @click="remove(item)">删除</el-button>
            </el-space>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <h3 class="all-title">全部热点（{{ events.length }}）</h3>
    <div class="card-grid">
      <el-card v-for="item in events" :key="item.id" shadow="hover">
        <el-tag>{{ sourceText(item.source) }}</el-tag>
        <h3>{{ item.title }}</h3>
        <p class="muted">{{ item.start_date }}{{ item.end_date && item.end_date !== item.start_date ? " ~ " + item.end_date : "" }}</p>
        <p>地点：{{ item.location || "—" }}</p>
        <p class="clamp">{{ item.vlog_fit }}</p>
        <el-space>
          <el-button link type="primary" @click="openEdit(item)">修改</el-button>
          <el-button link type="danger" @click="remove(item)">删除</el-button>
        </el-space>
      </el-card>
    </div>
    <el-empty v-if="!events.length && !capturing" description="热点列表空空的，先在上面蹲一波吧" />

    <el-dialog v-model="showForm" :title="editingId ? '修改热点' : '添加热点'" width="min(520px, 94vw)">
      <el-form label-position="top">
        <el-form-item label="标题">
          <el-input v-model="form.title" />
        </el-form-item>
        <el-form-item label="开始日期">
          <el-date-picker v-model="form.start_date" value-format="YYYY-MM-DD" placeholder="选择日期" style="width: 100%" />
        </el-form-item>
        <el-form-item label="结束日期">
          <el-date-picker v-model="form.end_date" value-format="YYYY-MM-DD" placeholder="可与开始相同" style="width: 100%" />
        </el-form-item>
        <el-form-item label="地点">
          <el-input v-model="form.location" placeholder="城市 / 展馆 / 线上" />
        </el-form-item>
        <el-form-item label="怎么拍">
          <el-input v-model="form.vlog_fit" type="textarea" :rows="2" />
        </el-form-item>
        <el-form-item label="商业化机会">
          <el-input v-model="form.commercial" type="textarea" :rows="2" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showForm = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="saveForm">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { computed, onActivated, onMounted, reactive, ref } from "vue";
import { useRouter } from "vue-router";
import { ElMessage, ElMessageBox } from "element-plus";
import { calendarApi } from "../api";
import { SAMPLE_HOTSPOT, type CalendarEvent } from "../types";
import { useWorkspaceStore } from "../stores/workspace";
import AiProgress from "../components/AiProgress.vue";

defineOptions({ name: "CalendarView" });

const router = useRouter();
const workspace = useWorkspaceStore();
const events = ref<CalendarEvent[]>([]);
const calDate = ref(new Date());
const capturing = ref(false);
const extracting = ref(false);
const saving = ref(false);
const showPaste = ref(false);
const showForm = ref(false);
const editingId = ref<number | null>(null);
const rawText = ref("");
const form = reactive({
  title: "",
  start_date: "",
  end_date: "",
  location: "",
  vlog_fit: "",
  commercial: "",
});

const selectedDay = computed(() => formatDay(calDate.value));
const selectedLabel = computed(() => selectedDay.value || "当天");
const dayEvents = computed(() => eventsOn(selectedDay.value));

function formatDay(value: Date | string) {
  if (typeof value === "string") return value.slice(0, 10);
  const y = value.getFullYear();
  const m = String(value.getMonth() + 1).padStart(2, "0");
  const d = String(value.getDate()).padStart(2, "0");
  return `${y}-${m}-${d}`;
}

function dayNum(day: string) {
  return day.split("-")[2];
}

function inRange(item: CalendarEvent, day: string) {
  const start = item.start_date || "";
  const end = item.end_date || start;
  if (!start) return false;
  return start <= day && day <= end;
}

function eventsOn(day: string) {
  return events.value.filter((item) => inRange(item, day));
}

function sourceText(source: string) {
  if (source === "capture") return "自动捕捉";
  if (source === "extract") return "文本提取";
  return "手动";
}

function pickDay(day: string) {
  calDate.value = new Date(`${day}T00:00:00`);
}

async function load(opts?: { silent?: boolean }) {
  if (opts?.silent && events.value.length) {
    void calendarApi.list().then(({ data }) => {
      events.value = data;
      workspace.events = data;
    });
    return;
  }
  const { data } = await calendarApi.list();
  events.value = data;
  workspace.events = data;
}

async function capture() {
  capturing.value = true;
  try {
    const { data } = await calendarApi.capture();
    if (data.warning) ElMessage.warning(data.warning);
    else if (data.created) ElMessage.success(`蹲到 ${data.created} 条热点！`);
    else ElMessage.info("这波没有蹲到够具体的热点，过几天再来试试");
    await load();
  } finally {
    capturing.value = false;
  }
}

async function extract() {
  if (rawText.value.trim().length < 8) {
    ElMessage.warning("请粘贴更完整的文本");
    return;
  }
  extracting.value = true;
  try {
    await calendarApi.extract(rawText.value);
    ElMessage.success("排进日历啦");
    rawText.value = "";
    await load();
  } finally {
    extracting.value = false;
  }
}

function resetForm() {
  form.title = "";
  form.start_date = selectedDay.value;
  form.end_date = selectedDay.value;
  form.location = "";
  form.vlog_fit = "";
  form.commercial = "";
}

function openCreate(day?: string) {
  editingId.value = null;
  resetForm();
  if (day) {
    form.start_date = day;
    form.end_date = day;
  }
  showForm.value = true;
}

function openEdit(item: CalendarEvent) {
  editingId.value = item.id;
  form.title = item.title;
  form.start_date = item.start_date;
  form.end_date = item.end_date || item.start_date;
  form.location = item.location;
  form.vlog_fit = item.vlog_fit;
  form.commercial = item.commercial;
  showForm.value = true;
}

async function saveForm() {
  if (!form.title.trim()) {
    ElMessage.warning("请填写标题");
    return;
  }
  saving.value = true;
  try {
    const payload = {
      title: form.title.trim(),
      start_date: form.start_date || "",
      end_date: form.end_date || form.start_date || "",
      location: form.location,
      vlog_fit: form.vlog_fit,
      commercial: form.commercial,
      source: "manual" as const,
    };
    if (editingId.value) {
      await calendarApi.update(editingId.value, payload);
      ElMessage.success("改好了");
    } else {
      await calendarApi.create(payload);
      ElMessage.success("记上了");
    }
    showForm.value = false;
    await load();
  } finally {
    saving.value = false;
  }
}

async function remove(item: CalendarEvent) {
  await ElMessageBox.confirm(`真的要把「${item.title}」删掉吗？`, "删除热点", { type: "warning" });
  await calendarApi.remove(item.id);
  ElMessage.success("删掉了");
  await load();
}

function goIdea(item: CalendarEvent) {
  router.push({
    path: "/ideas",
    query: { hint: `${item.title}。${item.vlog_fit || "围绕这个热点做一期"}` },
  });
}

onMounted(() => {
  if (workspace.events.length) {
    events.value = workspace.events;
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
  void load({ silent: events.value.length > 0 });
});
</script>

<style scoped>
.paste-box {
  margin-top: 12px;
}
.list-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.event {
  padding: 12px 0;
  border-bottom: 1px solid var(--line);
}
.event:last-child {
  border-bottom: 0;
}
.event-top {
  display: flex;
  align-items: center;
  gap: 8px;
}
.cell {
  min-height: 64px;
  padding: 4px;
  cursor: pointer;
}
.cell .num {
  display: block;
  font-weight: 600;
}
.cell .dot {
  display: block;
  font-size: 11px;
  color: var(--accent);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.cell em {
  font-style: normal;
  font-size: 11px;
  color: var(--muted);
}
.cell.today .num {
  color: var(--accent);
}
.all-title {
  margin: 24px 0 12px;
  font-size: 16px;
}
.clamp {
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.cal-head {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  flex-wrap: wrap;
}

/* 手机：日历紧凑化，事件标题变圆点 */
@media (max-width: 600px) {
  .cell {
    min-height: 44px;
    padding: 2px;
  }
  .cell .num {
    font-size: 12px;
  }
  .cell .dot {
    width: 6px;
    height: 6px;
    border-radius: 50%;
    background: var(--accent);
    margin: 2px auto 0;
    font-size: 0;
    padding: 0;
    overflow: visible;
    white-space: normal;
    text-overflow: unset;
  }
  .cell em {
    font-size: 10px;
  }
  .el-calendar :deep(.el-calendar__header) {
    padding: 8px 6px;
  }
  .el-calendar :deep(.el-calendar-table td) {
    padding: 0;
  }
  .event-top {
    flex-wrap: wrap;
  }
}
</style>
