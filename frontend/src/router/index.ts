import { createRouter, createWebHistory } from "vue-router";
import { useAuthStore } from "../stores/auth";

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: "/login", name: "login", component: () => import("../views/LoginView.vue") },
    {
      path: "/persona",
      name: "persona",
      component: () => import("../views/PersonaSelectView.vue"),
      meta: { auth: true },
    },
    {
      path: "/",
      component: () => import("../views/LayoutView.vue"),
      meta: { auth: true, persona: true },
      children: [
        { path: "", redirect: "/inspiration" },
        { path: "inspiration", name: "inspiration", component: () => import("../views/InspirationView.vue") },
        { path: "topics", name: "topics", component: () => import("../views/TopicsView.vue") },
        { path: "ideas", name: "ideas", component: () => import("../views/IdeasView.vue") },
        { path: "script", name: "script", component: () => import("../views/ScriptView.vue") },
        { path: "calendar", name: "calendar", component: () => import("../views/CalendarView.vue") },
        { path: "settings", name: "settings", component: () => import("../views/SettingsView.vue") },
      ],
    },
  ],
});

router.beforeEach(async (to) => {
  const auth = useAuthStore();
  if (to.meta.auth && !auth.isLoggedIn) return { name: "login" };
  if (auth.isLoggedIn && !auth.user) {
    try {
      await auth.fetchMe();
    } catch {
      auth.logout();
      return { name: "login" };
    }
  }
  if (to.meta.persona && !auth.hasPersona) return { name: "persona" };
  if (to.name === "login" && auth.isLoggedIn) {
    return auth.hasPersona ? { name: "inspiration" } : { name: "persona" };
  }
  return true;
});

export default router;
