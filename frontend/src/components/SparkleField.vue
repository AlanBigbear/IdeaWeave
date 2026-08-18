<template>
  <div class="sparkles" aria-hidden="true">
    <span v-for="n in props.count" :key="n" class="dot" :style="styleOf(n)">✦</span>
  </div>
</template>

<script setup lang="ts">
const props = withDefaults(defineProps<{ count?: number }>(), { count: 18 });

function styleOf(n: number) {
  const left = ((n * 37) % 100).toFixed(1);
  const delay = ((n * 0.37) % 6).toFixed(2);
  const duration = (4 + (n % 5)).toFixed(1);
  const size = 8 + (n % 7) * 2;
  return {
    left: `${left}%`,
    animationDelay: `${delay}s`,
    animationDuration: `${duration}s`,
    fontSize: `${size}px`,
  };
}
</script>

<style scoped>
.sparkles {
  pointer-events: none;
  position: absolute;
  inset: 0;
  overflow: hidden;
  z-index: 0;
}
.dot {
  position: absolute;
  bottom: -12px;
  color: #ff8fb4;
  opacity: 0;
  animation: rise linear infinite;
  text-shadow: 0 0 8px #ffd0e4;
}
@keyframes rise {
  0% {
    transform: translateY(0) rotate(0deg) scale(0.6);
    opacity: 0;
  }
  12% {
    opacity: 0.8;
  }
  100% {
    transform: translateY(-110vh) rotate(180deg) scale(1);
    opacity: 0;
  }
}
</style>
