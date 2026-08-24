<template>
  <div class="onboard">
    <SparkleField />
    <header class="top">
      <div class="brand">
        <span class="logo">B</span>
        捏一个你的创作者人设
      </div>
      <nav class="lux-tabs steps">
        <button
          v-for="(s, i) in steps"
          :key="s"
          class="lux-tab"
          :class="{ on: step === i, done: step > i }"
          @click="step = i"
        >
          <span class="num">{{ i + 1 }}</span>
          {{ s }}
        </button>
      </nav>
    </header>

    <main class="body">
      <section v-if="step === 0">
        <h1>你是哪个区的 UP 主？</h1>
        <p>分区决定选题口味，还有封面和钩子用什么口气说话～</p>
        <div class="pick-grid">
          <button
            v-for="z in options.zones"
            :key="z.key"
            class="pick-card"
            :class="{ active: form.zone === z.label }"
            @click="onPickZone(z.label)"
          >
            <i class="emoji">{{ z.emoji }}</i>
            <b>{{ z.label }}</b>
            <span>{{ z.desc }}</span>
          </button>
        </div>
      </section>

      <section v-else-if="step === 1">
        <h1>发布内容主要是什么风格？</h1>
        <p>已经按「{{ form.zone || "你选的分区" }}」帮你挑好了～可以多选。</p>
        <div class="chips">
          <button
            v-for="item in zoneStyles"
            :key="item"
            class="chip"
            :class="{ active: styles.includes(item) }"
            @click="toggleStyle(item)"
          >
            {{ item }}
          </button>
        </div>
        <el-input v-model="form.video_format" placeholder="视频形态，例如：8–15 分钟口播 + 实拍" style="margin-top: 20px" />
      </section>

      <section v-else-if="step === 2">
        <h1>你更习惯怎么更新？</h1>
        <p>节奏会影响选题是「短平快」还是「高成本暂缓」。</p>
        <div class="pick-grid">
          <button
            v-for="item in options.update_freqs"
            :key="item.key"
            class="pick-card"
            :class="{ active: form.update_freq === item.label }"
            @click="form.update_freq = item.label"
          >
            <b>{{ item.label }}</b>
            <span>{{ item.desc }}</span>
          </button>
        </div>
      </section>

      <section v-else-if="step === 3">
        <h1>评论区你想怎么玩？</h1>
        <p>脚本会照这个习惯提前埋好互动、置顶和回复话术。</p>
        <div class="pick-grid">
          <button
            v-for="item in options.comment_styles"
            :key="item.key"
            type="button"
            class="pick-card"
            :class="{ active: isCommentSelected(item) }"
            @click="pickComment(item)"
          >
            <b>{{ item.label }}</b>
            <span>{{ item.desc }}</span>
          </button>
        </div>
      </section>

      <section v-else-if="step === 4">
        <h1>给这套人设起个名字</h1>
        <p>也可以直接抄模板作业，再改成自己的～</p>
        <div class="templates">
          <button v-for="tpl in templates" :key="tpl.key" class="mini" @click="applyTemplate(tpl)">
            套用 {{ tpl.name }}
          </button>
        </div>
        <el-form label-position="top" class="final">
          <el-form-item label="人设名称">
            <el-input v-model="form.name" placeholder="例如：展会体验派 / 周末探店账号" />
          </el-form-item>
          <el-form-item label="受众">
            <el-input v-model="form.audience" placeholder="你在拍给谁看" />
          </el-form-item>
          <el-form-item label="禁忌">
            <el-input v-model="form.taboos" placeholder="不硬广、不未体验先吹…" />
          </el-form-item>
          <el-form-item label="口吻">
            <el-input v-model="form.sample_tone" type="textarea" :rows="3" placeholder="想让编导娘用什么语气写稿" />
          </el-form-item>
        </el-form>
        <div class="preview">
          <div class="preview-kicker">预览</div>
          <h3>{{ form.name || "还没名字的人设" }}</h3>
          <p>{{ form.zone }} · {{ styles.join(" / ") || "风格待选" }} · {{ form.update_freq || "更新待选" }}</p>
          <p>{{ form.comment_style || "评论风格待选" }}</p>
        </div>
        <div v-if="existing.length" class="existing">
          <p>已经有捏好的人设，直接进去也行</p>
          <el-button v-for="p in existing" :key="p.id" text type="primary" @click="useExisting(p)">
            {{ p.name }}
          </el-button>
        </div>
      </section>

      <section v-else>
        <h1>人设已就绪！</h1>
        <p>
          已经按你的分区、风格、节奏、评论习惯套好了一份<b>预置编导 Skill</b>，现在就能开工～
          想要更贴合的「注入灵魂」版（AI 深度定制），可以在这里生成，或之后随时去设置页弄。
        </p>
        <PersonaSkillCard v-if="created" :persona="created" @updated="created = $event" />
        <el-alert v-else type="info" :closable="false">
          先回上一步把人设存好～
        </el-alert>
      </section>
    </main>

    <img v-if="step < 5" class="corner-mascot" :src="mascot" alt="" />
    <footer class="bar">
      <el-button v-if="step > 0 && step < 5" @click="step -= 1">上一步</el-button>
      <span class="grow" />
      <el-button v-if="step < 4" type="primary" :disabled="!canNext" @click="step += 1">下一步</el-button>
      <el-button v-else-if="step === 4" type="primary" :loading="saving" @click="submit">
        保存人设，开工！
      </el-button>
      <el-button v-else type="primary" @click="goHome">开工！</el-button>
    </footer>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from "vue";
import { useRouter } from "vue-router";
import { ElMessage } from "element-plus";
import { personaApi } from "../api";
import { useAuthStore } from "../stores/auth";
import SparkleField from "../components/SparkleField.vue";
import PersonaSkillCard from "../components/PersonaSkillCard.vue";
import type { OptionItem, Persona, PersonaOptions, PersonaTemplate } from "../types";
import mascot from "../assets/mascot-director.png";

const steps = ["分区", "风格", "更新", "评论", "确认", "Skill"];
const step = ref(0);
const saving = ref(false);
const created = ref<Persona | null>(null);
const router = useRouter();
const auth = useAuthStore();
const styles = ref<string[]>([]);
const existing = ref<Persona[]>([]);
const templates = ref<PersonaTemplate[]>([]);
const options = ref<PersonaOptions>({
  zones: [] as OptionItem[],
  content_styles: [],
  update_freqs: [] as OptionItem[],
  comment_styles: [] as OptionItem[],
});

const form = reactive({
  name: "",
  zone: "",
  content_style: "",
  update_freq: "",
  comment_style: "",
  audience: "",
  video_format: "B 站中长视频，口播 + 实拍",
  taboos: "隐瞒广告、未体验先吹、引战",
  sample_tone: "",
  style_desc: "",
  template_key: "custom",
});

const canNext = computed(() => {
  if (step.value === 0) return Boolean(form.zone);
  if (step.value === 1) return styles.value.length > 0;
  if (step.value === 2) return Boolean(form.update_freq);
  if (step.value === 3) return Boolean(form.comment_style);
  return true;
});

const zoneKey = computed(
  () => options.value.zones.find((z) => z.label === form.zone)?.key || "",
);

const zoneStyles = computed(() => {
  const specific = zoneKey.value ? options.value.zone_content_styles?.[zoneKey.value] : undefined;
  if (specific?.length) return [...specific, ...(options.value.common_content_styles || [])];
  return options.value.content_styles;
});

onMounted(async () => {
  const [opt, tpl, list] = await Promise.all([
    personaApi.options(),
    personaApi.templates(),
    personaApi.list(),
  ]);
  options.value = opt.data;
  templates.value = tpl.data;
  existing.value = list.data;
});

function pickComment(item: OptionItem) {
  form.comment_style = `${item.label}，${item.desc}`;
}

function isCommentSelected(item: OptionItem) {
  const value = form.comment_style || "";
  return value === item.label || value.startsWith(`${item.label}，`) || value.startsWith(item.label);
}

function onPickZone(label: string) {
  form.zone = label;
  // 换分区后清掉不属于新分区的风格选择
  const valid = zoneStyles.value;
  styles.value = styles.value.filter((s) => valid.includes(s));
}

function toggleStyle(item: string) {
  if (styles.value.includes(item)) {
    styles.value = styles.value.filter((s) => s !== item);
  } else {
    styles.value = [...styles.value, item];
  }
}

function applyTemplate(tpl: PersonaTemplate) {
  form.name = tpl.name;
  form.zone = tpl.zone;
  form.update_freq = tpl.update_freq;
  form.comment_style = tpl.comment_style;
  form.audience = tpl.audience;
  form.video_format = tpl.video_format;
  form.taboos = tpl.taboos;
  form.sample_tone = tpl.sample_tone;
  form.style_desc = tpl.style_desc;
  form.template_key = tpl.key;
  styles.value = tpl.content_style ? [tpl.content_style] : [];
  ElMessage.success(`套用了「${tpl.name}」，不满意继续改～`);
}

async function useExisting(p: Persona) {
  await personaApi.activate({ persona_id: p.id });
  await auth.fetchMe();
  await router.push("/inspiration");
}

async function submit() {
  if (!form.name.trim()) {
    ElMessage.warning("总得给这个人设起个名字吧");
    return;
  }
  saving.value = true;
  try {
    form.content_style = styles.value.join("、");
    form.style_desc =
      form.style_desc ||
      `${form.zone} UP 主，内容以${form.content_style}为主，${form.update_freq}，评论区${form.comment_style}`;
    const { data } = await personaApi.setup({ ...form });
    created.value = data;
    await auth.fetchMe();
    ElMessage.success("人设存好了！已套用预置 Skill，可以直接开工～");
    step.value = 5;
  } finally {
    saving.value = false;
  }
}

function goHome() {
  router.push("/inspiration");
}
</script>

<style scoped>
.onboard {
  min-height: 100%;
  display: flex;
  flex-direction: column;
  position: relative;
  overflow: hidden;
  background:
    radial-gradient(circle at 90% 0%, #ffd0e4, transparent 36%),
    var(--bg);
}

.top,
.body,
.bar {
  position: relative;
  z-index: 1;
}

.corner-mascot {
  position: absolute;
  width: 120px;
  right: 18px;
  bottom: 84px;
  z-index: 0;
  opacity: 0.92;
  pointer-events: none;
  border-radius: 26px;
  border: 4px solid rgba(255, 255, 255, 0.9);
  box-shadow: 0 16px 32px rgba(255, 107, 157, 0.18);
  animation: floaty 3.6s ease-in-out infinite;
}

@keyframes floaty {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-8px); }
}

.top {
  padding: 8px 40px 0;
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
  border-bottom: 1px solid var(--line);
  background: rgba(255, 255, 255, 0.7);
  backdrop-filter: blur(14px);
}

.brand {
  display: flex;
  align-items: center;
  gap: 10px;
  font-weight: 700;
}

.logo {
  width: 30px;
  height: 30px;
  border-radius: 10px;
  background: var(--accent);
  color: #fff;
  display: grid;
  place-items: center;
}

.steps {
  height: 56px;
}

.steps .lux-tab {
  height: 56px;
  padding: 0 14px;
  font-size: 13px;
}

.num {
  width: 18px;
  height: 18px;
  border-radius: 50%;
  border: 1px solid currentColor;
  display: inline-grid;
  place-items: center;
  font-size: 11px;
  opacity: 0.7;
}

.steps .on .num {
  background: var(--accent);
  border-color: var(--accent);
  color: #fff;
  opacity: 1;
}

.steps .done {
  color: var(--ink);
}

.body {
  flex: 1;
  padding: 12px 40px 100px;
  max-width: 1080px;
}

h1 {
  margin: 8px 0 8px;
  font-size: 36px;
  letter-spacing: -0.04em;
}

.body p {
  color: #8a7176;
  margin: 0 0 22px;
}

.chips {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.final {
  max-width: 640px;
}

.templates {
  display: flex;
  gap: 8px;
  margin-bottom: 16px;
  flex-wrap: wrap;
}

.mini {
  border: 1px dashed #ffb0cb;
  background: #fff;
  color: var(--accent);
  border-radius: 999px;
  padding: 6px 12px;
  cursor: pointer;
}

.preview {
  margin-top: 8px;
  background: #fff;
  border-radius: 20px;
  padding: 18px 20px;
  border: 1px solid var(--line);
}

.preview-kicker {
  color: var(--accent);
  font-size: 12px;
  font-weight: 700;
}

.existing {
  margin-top: 16px;
}

.bar {
  position: sticky;
  bottom: 0;
  z-index: 95;
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px 40px;
  background: rgba(255, 244, 248, 0.92);
  backdrop-filter: blur(10px);
  border-top: 1px solid var(--line);
}

.grow {
  flex: 1;
}

@media (max-width: 720px) {
  .top,
  .body,
  .bar {
    padding-left: 18px;
    padding-right: 18px;
  }
  h1 {
    font-size: 28px;
  }
  .brand {
    font-size: 0;
  }
  .top {
    gap: 8px;
  }
  .steps {
    overflow-x: auto;
    scrollbar-width: none;
    -webkit-overflow-scrolling: touch;
    min-width: 0;
  }
  .steps::-webkit-scrollbar {
    display: none;
  }
  .steps .lux-tab {
    padding: 0 10px;
    flex-shrink: 0;
  }
  .corner-mascot {
    display: none;
  }
  .bar {
    padding-top: 10px;
    padding-bottom: 10px;
  }
  .bar .el-button {
    height: 40px;
    padding: 0 18px;
  }
  .mini {
    padding: 10px 16px;
  }
}
</style>
