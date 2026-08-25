<template>
  <div class="studio">
    <aside class="rail">
      <div class="brand">
        <span class="logo">I</span>
        <div>
          <b>IdeaWeave</b>
          <small>把灵感织成脚本</small>
        </div>
      </div>
      <nav class="side-nav">
        <button
          v-for="item in navs"
          :key="item.path"
          class="side-tab"
          :class="{ on: route.path === item.path }"
          @mouseenter="warm(item.path)"
          @click="go(item.path)"
        >
          <span class="ico">
            <span class="face">{{ item.emoji }}</span>
            <i class="ping" />
          </span>
          <span class="copy">
            <strong>{{ item.label }}</strong>
            <em>{{ item.hint }}</em>
          </span>
        </button>
      </nav>
    </aside>
    <section class="workspace">
      <header class="topbar">
        <div class="who">
          <span class="dot" />
          <div>
            <strong>{{ personaName }}</strong>
            <em>{{ personaMeta }}</em>
          </div>
        </div>
        <div>
          <el-button round @click="router.push('/persona')">改人设</el-button>
          <el-button round plain @click="logout">溜了</el-button>
        </div>
      </header>
      <main class="stage">
        <SparkleField />
        <img class="sticker s1" :src="stickers" alt="" />
        <div class="stage-inner">
          <router-view v-slot="{ Component }">
            <keep-alive :include="cachedViews">
              <component :is="Component" />
            </keep-alive>
          </router-view>
        </div>
      </main>
    </section>

    <!-- 手机端底部导航 -->
    <nav class="bottom-nav">
      <button
        v-for="item in navs"
        :key="item.path"
        class="bottom-tab"
        :class="{ on: route.path === item.path }"
        @click="go(item.path)"
      >
        <span class="face">{{ item.emoji }}</span>
        <i>{{ item.label }}</i>
      </button>
    </nav>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { useRoute, useRouter } from "vue-router";
import { personaApi } from "../api";
import { useAuthStore } from "../stores/auth";
import { useWorkspaceStore } from "../stores/workspace";
import SparkleField from "../components/SparkleField.vue";
import stickers from "../assets/kawaii-stickers.png";

const route = useRoute();
const router = useRouter();
const auth = useAuthStore();
const workspace = useWorkspaceStore();
const personaName = ref("人设待捏");
const personaMeta = ref("先去捏一个吧～");
const cachedViews = [
  "InspirationView",
  "TopicsView",
  "IdeasView",
  "ScriptView",
  "CalendarView",
  "SettingsView",
];

const navs = [
  { path: "/inspiration", label: "灵感采集", hint: "丢爆款，薅爆点", emoji: "✨" },
  { path: "/topics", label: "选题库", hint: "标记 · 标签 · 优先级", emoji: "📒" },
  { path: "/ideas", label: "编导创意", hint: "一发三连创意卡", emoji: "🪄" },
  { path: "/script", label: "大纲扩写", hint: "钩子 · 分镜 · 互动", emoji: "🎬" },
  { path: "/calendar", label: "热点日历", hint: "蹲点 · 可手改", emoji: "📅" },
  { path: "/settings", label: "设置", hint: "人设与模型", emoji: "⚙️" },
];

const activeId = computed(() => auth.user?.active_persona_id);

function go(path: string) {
  if (route.path !== path) router.push(path);
}

function warm(path: string) {
  if (path === "/topics") void workspace.refreshTopics();
  if (path === "/calendar") void workspace.refreshEvents();
}

onMounted(async () => {
  workspace.prefetch();
  const { data } = await personaApi.list();
  const current = data.find((item) => item.id === activeId.value);
  if (current) {
    personaName.value = current.name;
    personaMeta.value = [current.zone, current.content_style, current.update_freq]
      .filter(Boolean)
      .join(" · ");
  }
});

function logout() {
  auth.logout();
  router.push("/login");
}
</script>

<style scoped>
.studio {
  height: 100%;
  display: grid;
  grid-template-columns: 248px 1fr;
}

.rail {
  position: relative;
  display: flex;
  flex-direction: column;
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.92), rgba(255, 236, 245, 0.9)),
    #fff;
  border-right: 1px solid var(--line);
  overflow: hidden;
}

.brand {
  display: flex;
  gap: 10px;
  align-items: center;
  padding: 22px 18px 10px;
}

.logo {
  width: 38px;
  height: 38px;
  border-radius: 14px;
  background: linear-gradient(145deg, #ff9ec4, var(--accent));
  color: #fff;
  display: grid;
  place-items: center;
  font-weight: 800;
  box-shadow: 0 8px 18px rgba(255, 107, 157, 0.28);
  animation: pulse 2.8s ease-in-out infinite;
}

.brand b {
  display: block;
  letter-spacing: 0.08em;
}

.brand small {
  color: var(--muted);
  letter-spacing: 0.14em;
  font-size: 11px;
}

.side-nav {
  padding: 8px 12px;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.side-tab {
  appearance: none;
  border: 0;
  background: transparent;
  display: grid;
  grid-template-columns: 44px 1fr;
  gap: 10px;
  align-items: center;
  text-align: left;
  padding: 10px 10px;
  border-radius: 16px;
  cursor: pointer;
  color: var(--muted);
  transition: 0.22s ease;
}

.side-tab:hover {
  background: rgba(255, 107, 157, 0.08);
  color: var(--ink);
}

.side-tab:hover .face {
  animation: hop 0.45s ease;
}

.side-tab.on {
  background: linear-gradient(90deg, #ffe4ef, #fff);
  color: var(--ink);
  box-shadow: inset 3px 0 0 var(--accent);
}

.side-tab.on .face {
  animation: pop 0.55s ease, floaty 2.2s ease-in-out infinite 0.55s;
}

.ico {
  position: relative;
  width: 44px;
  height: 44px;
  display: grid;
  place-items: center;
}

.face {
  font-size: 24px;
  filter: drop-shadow(0 4px 0 rgba(255, 107, 157, 0.12));
}

.ping {
  position: absolute;
  inset: 6px;
  border-radius: 50%;
  border: 1px solid rgba(255, 107, 157, 0.25);
  opacity: 0;
}

.side-tab.on .ping {
  animation: ping 1.8s ease-out infinite;
}

.copy {
  min-width: 0;
}

.copy strong {
  display: block;
  font-size: 14px;
  letter-spacing: 0.04em;
}

.copy em {
  display: block;
  font-style: normal;
  font-size: 11px;
  color: var(--muted);
}

.mascot-card {
  margin: auto 14px 16px;
  text-align: center;
}

.mascot-card img {
  width: 100%;
  border-radius: 22px;
  object-fit: cover;
  max-height: 220px;
  animation: floaty 3.4s ease-in-out infinite;
}

.mascot-card p {
  margin: 8px 0 0;
  font-size: 12px;
  color: var(--accent);
  letter-spacing: 0.06em;
}

.workspace {
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.topbar {
  height: 64px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
  background: rgba(255, 255, 255, 0.72);
  backdrop-filter: blur(16px);
  border-bottom: 1px solid var(--line);
}

.who {
  display: flex;
  align-items: center;
  gap: 10px;
}

.who em {
  display: block;
  font-style: normal;
  color: var(--muted);
  font-size: 12px;
}

.dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--accent);
  box-shadow: 0 0 0 4px var(--accent-soft);
  animation: pulse 2s ease-in-out infinite;
}

.stage {
  position: relative;
  flex: 1;
  overflow: auto;
}

.stage-inner {
  position: relative;
  z-index: 1;
  padding: 28px 32px 48px;
}

.sticker {
  position: absolute;
  pointer-events: none;
  opacity: 0.22;
  width: 220px;
  right: 24px;
  bottom: 16px;
  z-index: 0;
  animation: floaty 5s ease-in-out infinite;
}

@keyframes hop {
  0% { transform: translateY(0) rotate(0); }
  40% { transform: translateY(-6px) rotate(-10deg) scale(1.12); }
  100% { transform: translateY(0) rotate(0); }
}

@keyframes pop {
  0% { transform: scale(0.7) rotate(-12deg); }
  60% { transform: scale(1.18) rotate(8deg); }
  100% { transform: scale(1); }
}

@keyframes floaty {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-6px); }
}

@keyframes ping {
  0% { transform: scale(0.7); opacity: 0.6; }
  100% { transform: scale(1.45); opacity: 0; }
}

@keyframes pulse {
  0%, 100% { transform: scale(1); box-shadow: 0 8px 18px rgba(255, 107, 157, 0.28); }
  50% { transform: scale(1.06); box-shadow: 0 10px 22px rgba(255, 107, 157, 0.4); }
}

@media (max-width: 900px) {
  .studio {
    grid-template-columns: 88px 1fr;
  }
  .copy,
  .mascot-card p,
  .brand div {
    display: none;
  }
  .side-tab {
    grid-template-columns: 1fr;
    justify-items: center;
  }
}

/* 手机：隐藏侧栏，用底部导航 */
.bottom-nav {
  display: none;
}

@media (max-width: 600px) {
  .studio {
    grid-template-columns: 1fr;
    grid-template-rows: 1fr;
  }
  .rail {
    display: none;
  }
  .bottom-nav {
    position: fixed;
    left: 0;
    right: 0;
    bottom: 0;
    z-index: 70;
    display: flex;
    background: rgba(255, 255, 255, 0.94);
    backdrop-filter: blur(16px);
    border-top: 1px solid var(--line);
    padding: 4px 4px calc(4px + env(safe-area-inset-bottom));
  }
  .bottom-tab {
    flex: 1;
    appearance: none;
    border: 0;
    background: transparent;
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 2px;
    padding: 6px 2px;
    border-radius: 12px;
    color: var(--muted);
    font-size: 10px;
    cursor: pointer;
  }
  .bottom-tab .face {
    font-size: 20px;
  }
  .bottom-tab i {
    font-style: normal;
    letter-spacing: 0.02em;
  }
  .bottom-tab.on {
    color: var(--accent);
    background: rgba(255, 107, 157, 0.08);
  }
  .topbar {
    height: auto;
    min-height: 52px;
    padding: 8px 14px;
    gap: 8px;
  }
  .who em {
    max-width: 150px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }
  .topbar > div:last-child {
    display: flex;
    gap: 6px;
  }
  .topbar .el-button {
    padding: 8px 10px;
  }
  .stage-inner {
    padding: 14px 12px calc(24px + 68px);
  }
  .sticker {
    display: none;
  }
}
</style>
