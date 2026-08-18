import { defineStore } from "pinia";
import { computed, ref } from "vue";
import { authApi } from "../api";
import type { User } from "../types";

export const useAuthStore = defineStore("auth", () => {
  const token = ref(localStorage.getItem("bstar_token") || "");
  const user = ref<User | null>(null);

  const isLoggedIn = computed(() => Boolean(token.value));
  const hasPersona = computed(() => Boolean(user.value?.active_persona_id));

  async function setToken(value: string) {
    token.value = value;
    localStorage.setItem("bstar_token", value);
    await fetchMe();
  }

  async function fetchMe() {
    if (!token.value) return;
    const { data } = await authApi.me();
    user.value = data;
  }

  function logout() {
    token.value = "";
    user.value = null;
    localStorage.removeItem("bstar_token");
  }

  return { token, user, isLoggedIn, hasPersona, setToken, fetchMe, logout };
});
