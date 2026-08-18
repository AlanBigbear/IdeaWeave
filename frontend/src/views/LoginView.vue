<template>
  <div class="landing">
    <SparkleField />
    <section class="hero">
      <div class="brand-row">
        <span class="logo">B</span>
        <span>B-Star 编导台</span>
      </div>
      <h1>把脑子里的灵感<br />变成能拍的脚本</h1>
      <p class="lead">
        面向小团队 UP 主的前期创作工作台。粘贴爆款、选好人设，AI 当你的虚拟编导。
      </p>
      <div class="hero-art">
        <img class="hero-img" :src="hero" alt="编导娘" />
        <img class="sticker" :src="stickers" alt="" />
      </div>
    </section>

    <section class="panel">
      <div class="panel-card">
        <img class="mini-mascot" :src="mascot" alt="" />
        <h2>{{ mode === "login" ? "欢迎回来" : "创建创作者账号" }}</h2>
        <p class="sub">先登录，再花 30 秒选分区和风格 ★</p>
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
          <el-button class="go" type="primary" size="large" :loading="loading" @click="submit">
            {{ mode === "login" ? "进入工作台" : "开始完善人设" }}
          </el-button>
        </el-form>
        <p class="hint">本地账号 · 数据存在你电脑里</p>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { ref } from "vue";
import { useRouter } from "vue-router";
import { ElMessage } from "element-plus";
import { authApi } from "../api";
import SparkleField from "../components/SparkleField.vue";
import hero from "../assets/login-hero.png";
import stickers from "../assets/kawaii-stickers.png";
import { useAuthStore } from "../stores/auth";

const mascot = "/pets/calico-sit-clear.png";

const router = useRouter();
const auth = useAuthStore();
const mode = ref<"login" | "register">("login");
const username = ref("");
const password = ref("");
const loading = ref(false);

async function submit() {
  if (username.value.length < 3 || password.value.length < 6) {
    ElMessage.warning("用户名至少 3 位，密码至少 6 位");
    return;
  }
  loading.value = true;
  try {
    const api = mode.value === "login" ? authApi.login : authApi.register;
    const { data } = await api(username.value, password.value);
    await auth.setToken(data.access_token);
    ElMessage.success(mode.value === "login" ? "欢迎回来" : "账号已创建");
    await router.push(auth.hasPersona ? "/inspiration" : "/persona");
  } finally {
    loading.value = false;
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
</style>
