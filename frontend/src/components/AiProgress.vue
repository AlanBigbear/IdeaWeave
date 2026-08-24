<template>
  <transition name="ai-pop">
    <div v-if="active" class="ai-progress">
      <div class="ai-emoji">{{ emoji }}</div>
      <div class="ai-body">
        <p class="ai-hint">{{ currentHint }}</p>
        <p class="ai-sub">已等 {{ elapsed }} 秒 · 编导娘努力中，可以先去别的页面逛～</p>
        <div class="ai-bar"><i /></div>
      </div>
    </div>
  </transition>
</template>

<script setup lang="ts">
import { computed, onUnmounted, ref, watch } from "vue";

defineOptions({ name: "AiProgress" });

const props = withDefaults(defineProps<{ active: boolean; variant?: string }>(), {
  variant: "extract",
});

const HINTS: Record<string, string[]> = {
  extract: [
    "编导娘正在翻笔记，把爆点一条条薅出来…",
    "逐句拆钩子，看看哪句最上头…",
    "对着你的人设掂量成本和可行性…",
    "马上排进选题库，最后润色中…",
  ],
  diverge: [
    "编导娘正在翻脑洞仓库…",
    "一个念头掰成三个角度，脑细胞全开…",
    "给每张卡配专属钩子和受众…",
    "反复对比差异点，宁缺毋滥…",
    "卡片排版中，即将出炉…",
  ],
  calendar: [
    "编导娘探出头去蹲热点…",
    "翻遍未来 30 天的日历格子…",
    "按你的人设筛一遍，只留能拍的…",
    "把热点一条条排进日历…",
  ],
  fetch: [
    "编导娘撒腿冲向原文页面…",
    "正在把页面小广告扒干净…",
    "正文装袋中，薅到就回…",
    "页面有点倔，再给人家一点点时间…",
  ],
};

const EMOJI: Record<string, string> = {
  extract: "✨",
  diverge: "🪄",
  calendar: "📅",
  fetch: "🐾",
};

const elapsed = ref(0);
let timer: ReturnType<typeof setInterval> | undefined;

const hints = computed(() => HINTS[props.variant] || HINTS.extract);
const emoji = computed(() => EMOJI[props.variant] || EMOJI.extract);
const currentHint = computed(
  () => hints.value[Math.min(Math.floor(elapsed.value / 10), hints.value.length - 1)],
);

function stopTimer() {
  if (timer) clearInterval(timer);
  timer = undefined;
}

watch(
  () => props.active,
  (active) => {
    stopTimer();
    elapsed.value = 0;
    if (active) {
      timer = setInterval(() => {
        elapsed.value += 1;
      }, 1000);
    }
  },
  { immediate: true },
);

onUnmounted(stopTimer);
</script>

<style scoped>
.ai-progress {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 14px 16px;
  margin-top: 14px;
  background: #fff5f8;
  border: 1px solid #ffdbe8;
  border-radius: 16px;
  text-align: center;
}

.ai-emoji {
  font-size: 32px;
  line-height: 1;
  flex-shrink: 0;
  animation: ai-float 1.8s ease-in-out infinite;
}

.ai-body {
  flex: 1;
  min-width: 0;
}

.ai-hint {
  margin: 0 0 2px;
  font-weight: 600;
  font-size: 14px;
  color: #c4537a;
}

.ai-sub {
  margin: 0 0 10px;
  font-size: 12px;
  color: #8a7176;
}

.ai-bar {
  height: 6px;
  border-radius: 999px;
  background: #ffeaf2;
  overflow: hidden;
}

.ai-bar i {
  display: block;
  height: 100%;
  border-radius: 999px;
  background: linear-gradient(90deg, #ffdbe8 0%, #fb7299 30%, #ffa8c5 50%, #fb7299 70%, #ffdbe8 100%);
  background-size: 200% 100%;
  animation: ai-shimmer 1.8s linear infinite;
}

@keyframes ai-float {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-6px); }
}

@keyframes ai-shimmer {
  0% { background-position: 0% 0; }
  100% { background-position: 100% 0; }
}

.ai-pop-enter-active,
.ai-pop-leave-active {
  transition: opacity 0.25s ease, transform 0.25s ease;
}

.ai-pop-enter-from,
.ai-pop-leave-to {
  opacity: 0;
  transform: translateY(8px);
}
</style>
