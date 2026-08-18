<template>
  <div
    class="pet"
    :class="[mood, { dragging }]"
    :style="style"
    @pointerdown="onDown"
    @click="onPet"
  >
    <div class="sprite" :class="{ flip }">
      <img :src="catSrc" alt="三花小猫" draggable="false" />
    </div>
    <span v-if="bubble" class="bubble">{{ bubble }}</span>
    <button class="stay" type="button" @pointerdown.stop @click.stop="toggleStay">
      {{ cat.roam ? "别跑了" : "可以跑" }}
    </button>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch } from "vue";
import { useCatStore } from "../stores/cat";

const POSES = {
  sit: "/pets/calico-sit-clear.png",
  walk: "/pets/calico-walk-clear.png",
  sleep: "/pets/calico-sleep-clear.png",
} as const;

const cat = useCatStore();
const SIZE = 128;
const mood = ref<"sit" | "walk" | "sleep">("sit");
const x = ref(24);
const y = ref(window.innerHeight - SIZE - 24);
const flip = ref(false);
const dragging = ref(false);
const bubble = ref("");
let timer = 0;
let dragOff = { x: 0, y: 0 };
let didDrag = false;

const catSrc = computed(() => POSES[mood.value]);
const style = computed(() => ({
  transform: `translate(${x.value}px, ${y.value}px)`,
  transition: dragging.value ? "none" : "transform 2.8s cubic-bezier(.4,.1,.2,1)",
}));

function clamp() {
  const maxX = Math.max(8, window.innerWidth - SIZE - 8);
  const maxY = Math.max(8, window.innerHeight - SIZE - 8);
  x.value = Math.min(maxX, Math.max(8, x.value));
  y.value = Math.min(maxY, Math.max(8, y.value));
}

function roam() {
  if (dragging.value || !cat.roam) return;
  const roll = Math.random();
  if (roll < 0.22) {
    mood.value = "sleep";
    bubble.value = "Zzz";
    schedule(2200 + Math.random() * 1800);
    return;
  }
  if (roll < 0.45) {
    mood.value = "sit";
    bubble.value = Math.random() > 0.5 ? "喵" : "";
    schedule(1400 + Math.random() * 1600);
    return;
  }
  const nx = 16 + Math.random() * (window.innerWidth - SIZE - 32);
  const ny = 16 + Math.random() * (window.innerHeight - SIZE - 32);
  flip.value = nx < x.value;
  mood.value = "walk";
  bubble.value = "";
  x.value = nx;
  y.value = ny;
  schedule(2800);
}

function schedule(ms: number) {
  window.clearTimeout(timer);
  if (!cat.roam) return;
  timer = window.setTimeout(roam, ms);
}

function park() {
  window.clearTimeout(timer);
  mood.value = "sit";
  bubble.value = "坐好了";
}

function toggleStay() {
  cat.toggle();
  if (cat.roam) {
    bubble.value = "去玩啦";
    schedule(400);
  } else {
    park();
  }
}

function onDown(e: PointerEvent) {
  didDrag = false;
  dragOff = { x: e.clientX - x.value, y: e.clientY - y.value };
  dragging.value = true;
  mood.value = "walk";
  (e.currentTarget as HTMLElement).setPointerCapture(e.pointerId);
  window.clearTimeout(timer);
  e.preventDefault();
}

function onMove(e: PointerEvent) {
  if (!dragging.value) return;
  const nx = e.clientX - dragOff.x;
  const ny = e.clientY - dragOff.y;
  if (Math.abs(nx - x.value) + Math.abs(ny - y.value) > 4) didDrag = true;
  flip.value = nx < x.value;
  x.value = nx;
  y.value = ny;
  clamp();
}

function onUp() {
  if (!dragging.value) return;
  dragging.value = false;
  mood.value = "sit";
  if (didDrag) {
    bubble.value = "放到这儿~";
    if (cat.roam) schedule(900);
  }
}

function onPet() {
  if (didDrag) return;
  mood.value = "sit";
  bubble.value = ["喵~", "摸摸头", "想拍 vlog", "今天也要更新"][Math.floor(Math.random() * 4)];
  if (cat.roam) schedule(1200);
}

onMounted(() => {
  clamp();
  window.addEventListener("pointermove", onMove);
  window.addEventListener("pointerup", onUp);
  if (cat.roam) schedule(800);
  else park();
});

watch(
  () => cat.roam,
  (value) => {
    if (value) schedule(400);
    else park();
  },
);

onUnmounted(() => {
  window.clearTimeout(timer);
  window.removeEventListener("pointermove", onMove);
  window.removeEventListener("pointerup", onUp);
});
</script>

<style scoped>
.pet {
  position: fixed;
  left: 0;
  top: 0;
  z-index: 80;
  width: 128px;
  cursor: grab;
  user-select: none;
  filter: drop-shadow(0 10px 12px rgba(40, 24, 16, 0.18));
}

.pet.dragging {
  cursor: grabbing;
  z-index: 90;
}

.pet .sprite {
  width: 128px;
  height: 128px;
}

.pet .sprite.flip {
  transform: scaleX(-1);
}

.pet img {
  width: 128px;
  height: 128px;
  object-fit: contain;
  pointer-events: none;
  background: transparent;
}

.pet.walk img {
  animation: crawl 0.42s ease-in-out infinite;
}

.bubble {
  position: absolute;
  left: 50%;
  top: -8px;
  transform: translate(-50%, -100%);
  background: #fff;
  color: #3a2430;
  border: 1px solid #f7d5e3;
  border-radius: 14px 14px 14px 4px;
  padding: 4px 10px;
  font-size: 12px;
  white-space: nowrap;
  box-shadow: 0 8px 18px rgba(255, 107, 157, 0.12);
}

.stay {
  position: absolute;
  left: 50%;
  bottom: -6px;
  transform: translateX(-50%);
  border: 1px solid var(--line);
  background: rgba(255, 255, 255, 0.92);
  color: var(--ink);
  border-radius: 999px;
  padding: 2px 10px;
  font-size: 11px;
  cursor: pointer;
  white-space: nowrap;
  letter-spacing: 0.04em;
}

.stay:hover {
  border-color: var(--accent);
  color: var(--accent);
}

@keyframes crawl {
  0% { transform: translateY(0) rotate(-2deg); }
  50% { transform: translateY(-4px) rotate(2deg); }
  100% { transform: translateY(0) rotate(-2deg); }
}
</style>
