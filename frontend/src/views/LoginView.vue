<template>
  <div class="landing">
    <SparkleField />
    <section class="hero">
      <div class="brand-row">
        <span class="logo">I</span>
        <span>IdeaWeave</span>
      </div>
      <h1>把收藏夹里的灵感<br />织成一期能拍的脚本</h1>
      <p class="lead">
        小团队 UP 主的前期创作工作台。丢进爆款、选好人设，从选题织到分镜脚本。
      </p>
      <div class="hero-art">
        <img class="hero-img" :src="hero" alt="编导娘" />
        <img class="sticker" :src="stickers" alt="" />
      </div>
    </section>

    <section class="panel">
      <div class="panel-card">
        <img class="mini-mascot" :src="mascot" alt="" />
        <h2>{{ mode === "login" ? "欢迎回来～" : "成为新 UP 主" }}</h2>
        <p class="sub">登录后花 30 秒捏一个人设 ★</p>
        <div class="switch seg-tabs">
          <button class="seg-tab" :class="{ on: mode === 'login' }" @click="mode = 'login'">登录</button>
          <button class="seg-tab" :class="{ on: mode === 'register' }" @click="mode = 'register'">注册</button>
        </div>
        <el-form @submit.prevent="submit">
          <el-form-item>
            <el-input v-model="username" placeholder="用户名" size="large" />
          </el-form-item>
          <el-form-item>
            <el-input v-model="password" type="password" placeholder="密码（至少 6 位）" size="large" show-password />
          </el-form-item>
          <el-button
            class="go"
            type="primary"
            size="large"
            :loading="loading"
            :disabled="loading || trialLoading"
            @click="submit"
          >
            {{ mode === "login" ? "开工！" : "去捏人设！" }}
          </el-button>
        </el-form>
        <div class="trial-entry">
          <p class="trial-title">免注册体验完整工作台</p>
          <div class="pick-grid trial-picks">
            <button
              v-for="t in trialAccounts"
              :key="t.key"
              type="button"
              class="pick-card"
              :class="{ active: selectedTrial === t.key }"
              :aria-pressed="selectedTrial === t.key"
              :disabled="loading || trialLoading"
              @click="selectedTrial = t.key"
            >
              <i class="emoji">{{ t.emoji }}</i>
              <b>{{ t.label }}</b>
              <span>{{ t.desc }}</span>
            </button>
          </div>
          <el-button
            class="trial-go"
            size="large"
            :loading="trialLoading"
            :disabled="loading || trialLoading"
            @click="startTrial"
          >
            进入所选体验空间
          </el-button>
          <p class="trial-note">
            共享体验账号，操作对其他访客可见，数据会定期重置。
          </p>
        </div>
        <p class="hint">今天也要更新哦 · 先把这一期想清楚再拍</p>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { ref } from "vue";
import { useRouter } from "vue-router";
import { ElMessage } from "element-plus";
import { authApi, type TrialAccountKey } from "../api";
import SparkleField from "../components/SparkleField.vue";
import hero from "../assets/login-hero.webp";
import stickers from "../assets/kawaii-stickers.webp";
import { useAuthStore } from "../stores/auth";

const mascot = "/pets/calico-sit-clear.webp";

const router = useRouter();
const auth = useAuthStore();
const mode = ref<"login" | "register">("login");
const username = ref("");
const password = ref("");
const loading = ref(false);
const trialLoading = ref(false);
const selectedTrial = ref<TrialAccountKey>("tech");
const trialAccounts = [
  { key: "tech", emoji: "📱", label: "科技数码", desc: "实测不盲吹" },
  { key: "anime", emoji: "🎀", label: "二次元收藏", desc: "开箱验货 · 避坑" },
  { key: "pet", emoji: "🐾", label: "萌宠动物", desc: "萌系日常 · 科学养宠" },
] as const;

async function submit() {
  if (!username.value.trim() || password.value.length < 6) {
    ElMessage.warning("用户名不能为空，密码至少 6 位");
    return;
  }
  loading.value = true;
  try {
    const api = mode.value === "login" ? authApi.login : authApi.register;
    const { data } = await api(username.value, password.value);
    await auth.setToken(data.access_token);
    ElMessage.success(mode.value === "login" ? "欢迎回来，今天也要爆更哦" : "账号捏好了！");
    await router.push(auth.hasPersona ? "/inspiration" : "/persona");
  } finally {
    loading.value = false;
  }
}

async function startTrial() {
  trialLoading.value = true;
  try {
    const { data } = await authApi.trial(selectedTrial.value);
    await auth.setToken(data.access_token);
    await router.push("/inspiration");
  } finally {
    trialLoading.value = false;
  }
}
</script>

<style scoped>
.landing {
  min-height: 100%;
  display: grid;
  grid-template-columns: 1.15fr 0.85fr;
  position: relative;
  overflow: hidden;
  background:
    radial-gradient(circle at 12% 18%, #ffd0e4 0%, transparent 32%),
    radial-gradient(circle at 78% 88%, #ffc2dc 0%, transparent 28%),
    linear-gradient(160deg, #fff4f8, #ffe4ef 55%, #fff 100%);
}

.hero,
.panel {
  position: relative;
  z-index: 1;
}

.hero {
  padding: 56px 64px;
  display: flex;
  flex-direction: column;
}

.brand-row {
  display: flex;
  align-items: center;
  gap: 10px;
  font-weight: 700;
  letter-spacing: 0.04em;
}

.logo {
  width: 32px;
  height: 32px;
  border-radius: 10px;
  background: var(--accent);
  color: #fff;
  display: grid;
  place-items: center;
  font-weight: 800;
}

h1 {
  margin: 28px 0 12px;
  font-size: 52px;
  line-height: 1.12;
  letter-spacing: -0.04em;
}

.lead {
  max-width: 460px;
  color: var(--muted);
  font-size: 16px;
}

.hero-art {
  margin-top: auto;
  position: relative;
}

.hero-img {
  width: min(560px, 100%);
  border-radius: 28px;
  box-shadow: 0 24px 50px rgba(255, 107, 157, 0.22);
  animation: floaty 4s ease-in-out infinite;
}

.sticker {
  position: absolute;
  width: 150px;
  right: 8%;
  bottom: -18px;
  opacity: 0.85;
  animation: floaty 3.2s ease-in-out infinite reverse;
}

.mini-mascot {
  width: 86px;
  height: 86px;
  object-fit: contain;
  background: transparent;
  margin: -8px 0 12px;
  animation: floaty 3s ease-in-out infinite;
}

@keyframes floaty {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-8px); }
}

.panel {
  display: grid;
  place-items: center;
  padding: 32px;
}

.panel-card {
  width: min(420px, 100%);
  background: rgba(255, 255, 255, 0.88);
  backdrop-filter: blur(16px);
  border: 1px solid var(--line);
  border-radius: 28px;
  padding: 36px 32px 28px;
  box-shadow: 0 24px 60px rgba(255, 107, 157, 0.14);
}

.panel-card h2 {
  margin: 0;
  font-size: 28px;
}

.sub {
  color: var(--muted);
  margin: 8px 0 20px;
}

.switch {
  width: 100%;
  margin-bottom: 18px;
}

.switch .seg-tab {
  flex: 1;
}

.go {
  width: 100%;
  height: 46px;
  border-radius: 999px !important;
  font-weight: 700;
}

.trial-entry {
  margin-top: 14px;
  padding-top: 14px;
  border-top: 1px solid rgba(255, 107, 157, 0.16);
}

.trial-title {
  margin: 0 0 10px;
  color: var(--muted);
  font-size: 12px;
  font-weight: 600;
  text-align: center;
}

.trial-picks {
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 10px;
  margin-bottom: 12px;
}

.trial-picks .pick-card {
  min-height: 92px;
  padding: 12px 8px 10px;
  border-radius: 16px;
  text-align: center;
}

.trial-picks .pick-card .emoji {
  font-size: 22px;
  margin-bottom: 6px;
}

.trial-picks .pick-card b {
  font-size: 13px;
  margin-bottom: 3px;
}

.trial-picks .pick-card span {
  font-size: 10.5px;
  line-height: 1.35;
}

.trial-picks .pick-card:disabled {
  cursor: not-allowed;
  opacity: 0.55;
  transform: none;
}

.trial-go {
  width: 100%;
  height: 44px;
  border-radius: 999px !important;
  border-color: rgba(255, 107, 157, 0.5);
  background: rgba(255, 255, 255, 0.72);
  color: var(--accent);
  font-weight: 700;
  transition: transform 0.2s ease, box-shadow 0.2s ease, border-color 0.2s ease;
}

.trial-go:not(.is-disabled):hover,
.trial-go:not(.is-disabled):focus-visible {
  border-color: var(--accent);
  background: #fff7fa;
  color: var(--accent);
  box-shadow: 0 8px 20px rgba(255, 107, 157, 0.14);
  transform: translateY(-1px);
}

.trial-note {
  margin: 9px 8px 0;
  color: var(--muted);
  font-size: 11px;
  line-height: 1.55;
  text-align: center;
}

.hint {
  text-align: center;
  color: #c48aa3;
  font-size: 12px;
  margin: 16px 0 0;
}

@media (max-width: 960px) {
  .landing {
    grid-template-columns: 1fr;
  }
  .hero {
    padding: 32px 24px 8px;
  }
  h1 {
    font-size: 36px;
  }
  .hero-art {
    display: none;
  }
}

@media (max-width: 480px) {
  h1 {
    font-size: 28px;
  }
  .hero {
    padding: 24px 16px 4px;
  }
  .panel {
    padding: 16px;
  }
  .panel-card {
    padding: 24px 18px 22px;
    border-radius: 22px;
  }
}
</style>
