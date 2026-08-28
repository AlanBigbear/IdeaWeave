<template>
  <div>
    <div class="page-head">
      <h2>设置</h2>
      <p>人设想改就改；模型走 OpenAI 兼容接口，Key 只待在你自己电脑里～</p>
    </div>
    <el-row :gutter="16">
      <el-col :md="12">
        <el-card header="当前人设">
          <div v-if="persona">
            <el-form label-position="top">
              <el-form-item label="名称"><el-input v-model="persona.name" /></el-form-item>
              <el-form-item label="分区"><el-input v-model="persona.zone" placeholder="生活区 / 美食区 / 科技区…" /></el-form-item>
              <el-form-item label="内容风格"><el-input v-model="persona.content_style" placeholder="探店、测评、Vlog…" /></el-form-item>
              <el-form-item label="更新节奏"><el-input v-model="persona.update_freq" /></el-form-item>
              <el-form-item label="评论互动"><el-input v-model="persona.comment_style" type="textarea" :rows="2" /></el-form-item>
              <el-form-item label="受众"><el-input v-model="persona.audience" /></el-form-item>
              <el-form-item label="禁忌"><el-input v-model="persona.taboos" /></el-form-item>
              <el-form-item label="口吻"><el-input v-model="persona.sample_tone" type="textarea" :rows="3" /></el-form-item>
              <el-button type="primary" round @click="savePersona">保存人设</el-button>
              <el-button round @click="router.push('/persona')">重走一遍选择</el-button>
            </el-form>
          </div>
        </el-card>
        <el-card v-if="persona" header="专属编导 Skill" style="margin-top: 16px">
          <PersonaSkillCard :persona="persona" @updated="persona = $event" />
        </el-card>
      </el-col>
      <el-col :md="12">
        <el-card header="大模型">
          <template v-if="auth.user?.is_trial">
            <p class="muted">公共体验空间使用服务端共享模型配置，无需也不支持自行修改～</p>
            <el-alert
              type="info"
              :closable="false"
              show-icon
              title="模型配置为只读"
              description="为了让大家体验一致，试用账号统一走系统预设的模型；注册自己的账号后即可自由配置。"
            />
          </template>
          <template v-else>
            <p class="muted">默认已接 DeepSeek（deepseek-v4-pro），想换成别的 OpenAI 兼容模型也随你～</p>
            <el-form label-position="top">
              <el-form-item label="Base URL">
                <el-input v-model="form.llm_base_url" placeholder="https://api.deepseek.com/v1" />
              </el-form-item>
              <el-form-item label="模型名">
                <el-input v-model="form.llm_model" placeholder="deepseek-v4-pro" />
              </el-form-item>
              <el-form-item :label="keyLabel">
                <el-input v-model="form.llm_api_key" type="password" show-password placeholder="留空则不修改已保存的 Key" />
              </el-form-item>
              <el-button type="primary" round :loading="saving" @click="save">保存</el-button>
            </el-form>
          </template>
        </el-card>
        <el-card header="桌面小猫" style="margin-top: 16px">
          <el-form label-position="top">
            <el-form-item label="让小猫在页面上乱跑">
              <el-switch
                :model-value="cat.roam"
                inline-prompt
                active-text="乱跑"
                inactive-text="坐好"
                @change="onCatRoam"
              />
            </el-form-item>
            <p class="muted">关掉后小猫会停在原地，仍可拖动。选择会记在本机。</p>
          </el-form>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from "vue";
import { useRouter } from "vue-router";
import { ElMessage } from "element-plus";
import { personaApi, settingsApi } from "../api";
import { useAuthStore } from "../stores/auth";
import { useCatStore } from "../stores/cat";
import PersonaSkillCard from "../components/PersonaSkillCard.vue";
import type { Persona } from "../types";

defineOptions({ name: "SettingsView" });

const router = useRouter();
const auth = useAuthStore();
const cat = useCatStore();
const saving = ref(false);
const hasKey = ref(false);
const persona = ref<Persona | null>(null);
const form = reactive({ llm_base_url: "", llm_model: "", llm_api_key: "" });
const keyLabel = computed(() => (hasKey.value ? "API Key（已配置，可覆盖）" : "API Key（尚未配置）"));

onMounted(async () => {
  const { data } = await settingsApi.get();
  form.llm_base_url = data.llm_base_url;
  form.llm_model = data.llm_model;
  hasKey.value = data.has_api_key;
  const personas = await personaApi.list();
  persona.value = personas.data.find((item) => item.id === auth.user?.active_persona_id) || null;
});

function onCatRoam(value: string | number | boolean) {
  cat.setRoam(Boolean(value));
}

async function save() {
  saving.value = true;
  try {
    const { data } = await settingsApi.update({
      llm_base_url: form.llm_base_url,
      llm_model: form.llm_model,
      llm_api_key: form.llm_api_key || undefined,
    });
    hasKey.value = data.has_api_key;
    form.llm_api_key = "";
    ElMessage.success("存好了～");
  } finally {
    saving.value = false;
  }
}

async function savePersona() {
  if (!persona.value) return;
  await personaApi.update(persona.value.id, persona.value);
  ElMessage.success("人设更新好了！分区/风格变化大的话，建议在下面重新套一次预置模板或 AI 生成");
}
</script>
