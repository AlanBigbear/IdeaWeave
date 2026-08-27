<template>
  <transition name="ai-pop">
    <div v-if="active" class="ai-stream">
      <div class="ai-stream-head">
        <span class="ai-emoji">{{ emoji }}</span>
        <span class="ai-title">编导娘思考中…</span>
        <span class="ai-timer">已 {{ elapsed }} 秒</span>
        <div class="ai-bar"><i /></div>
      </div>
      <div v-if="thinking" class="ai-thinking" ref="thinkingRef">
        <span class="tag">💭 思考</span>
        <span class="thinking-text">{{ displayThinking }}<span v-if="!content" class="cursor" /></span>
      </div>
      <div v-if="content || !thinking" class="ai-stream-body" ref="bodyRef">
        <span class="content">{{ displayContent }}</span><span class="cursor" />
      </div>
    </div>
  </transition>
</template>

<script setup lang="ts">
import { computed, nextTick, onUnmounted, ref, watch } from "vue";

defineOptions({ name: "AiStream" });

const props = withDefaults(
  defineProps<{ active: boolean; thinking?: string; content?: string; emoji?: string }>(),
  { thinking: "", content: "", emoji: "✨" },
);

const elapsed = ref(0);
const bodyRef = ref<HTMLElement | null>(null);
const thinkingRef = ref<HTMLElement | null>(null);
let timer: ReturnType<typeof setInterval> | undefined;

// 掐掉尾部空白，避免光标被末尾的换行顶到下一行，始终贴在最后一个可见字符后
const displayThinking = computed(() => props.thinking.replace(/\s+$/, ""));
const displayContent = computed(() => props.content.replace(/\s+$/, ""));

function stopTimer() {
  if (timer) clearInterval(timer);
  timer = undefined;
}

function scrollToEnd(el: HTMLElement | null) {
  if (el) el.scrollTop = el.scrollHeight;
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

watch(
  () => props.thinking,
  async () => {
    await nextTick();
    scrollToEnd(thinkingRef.value);
  },
);

watch(
  () => props.content,
  async () => {
    await nextTick();
    scrollToEnd(bodyRef.value);
  },
);

onUnmounted(stopTimer);
</script>

<style scoped>
.ai-stream {
  margin-top: 14px;
  background: #fff5f8;
  border: 1px solid #ffdbe8;
  border-radius: 16px;
  padding: 14px 16px;
}

.ai-stream-head {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.ai-emoji {
  font-size: 26px;
  line-height: 1;
  animation: ai-float 1.8s ease-in-out infinite;
}

.ai-title {
  font-weight: 700;
  font-size: 14px;
  color: #c4537a;
}

.ai-timer {
  margin-left: auto;
  font-size: 12px;
  color: #8a7176;
}

.ai-bar {
  flex-basis: 100%;
  height: 4px;
  border-radius: 999px;
  background: #ffeaf2;
  overflow: hidden;
  margin-top: 2px;
}

.ai-bar i {
  display: block;
  height: 100%;
  border-radius: 999px;
  background: linear-gradient(90deg, #ffdbe8 0%, #fb7299 30%, #ffa8c5 50%, #fb7299 70%, #ffdbe8 100%);
  background-size: 200% 100%;
  animation: ai-shimmer 1.8s linear infinite;
}

.ai-thinking {
  margin-top: 10px;
  display: flex;
  gap: 8px;
  align-items: flex-start;
  max-height: 220px;
  overflow-y: auto;
  background: #fff;
  border: 1px solid #f0dbe3;
  border-radius: 12px;
  padding: 8px 10px;
}

.tag {
  flex-shrink: 0;
  font-size: 11px;
  background: #f3e8ee;
  color: #8a7176;
  border-radius: 999px;
  padding: 2px 8px;
  font-weight: 600;
  white-space: nowrap;
}

.thinking-text {
  font-size: 13px;
  line-height: 1.6;
  color: #8a7176;
  white-space: pre-wrap;
  word-break: break-word;
}

.ai-stream-body {
  margin-top: 10px;
  max-height: 280px;
  overflow-y: auto;
  background: #fff;
  border: 1px solid #f0dbe3;
  border-radius: 12px;
  padding: 10px 12px;
  font-size: 13px;
  line-height: 1.7;
  color: #5c4750;
  white-space: pre-wrap;
  word-break: break-word;
}

.cursor {
  display: inline-block;
  width: 2px;
  height: 1em;
  margin-left: 2px;
  vertical-align: -0.1em;
  background: #fb7299;
  animation: ai-blink 0.9s step-end infinite;
}

@keyframes ai-float {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-6px); }
}

@keyframes ai-shimmer {
  0% { background-position: 0% 0; }
  100% { background-position: 100% 0; }
}

@keyframes ai-blink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0; }
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
