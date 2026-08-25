import { createRouter, createWebHistory } from "vue-router";
import { useAuthStore } from "../stores/auth";
import LayoutView from "../views/LayoutView.vue";
import InspirationView from "../views/InspirationView.vue";
import TopicsView from "../views/TopicsView.vue";
import IdeasView from "../views/IdeasView.vue";
import ScriptView from "../views/ScriptView.vue";
import CalendarView from "../views/CalendarView.vue";
import SettingsView from "../views/SettingsView.vue";

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
      component: LayoutView,
      meta: { auth: true, persona: true },
      children: [
        { path: "", redirect: "/inspiration" },
        { path: "inspiration", name: "inspiration", component: InspirationView },
        { path: "topics", name: "topics", component: TopicsView },
        { path: "ideas", name: "ideas", component: IdeasView },
        { path: "script", name: "script", component: ScriptView },
        { path: "calendar", name: "calendar", component: CalendarView },
        { path: "settings", name: "settings", component: SettingsView },
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
