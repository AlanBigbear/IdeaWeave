import { defineStore } from "pinia";
import { ref } from "vue";
import { calendarApi, topicApi } from "../api";
import type { CalendarEvent, Topic } from "../types";

/** 工作台列表缓存：公网 RTT 高时先出旧数据，后台再刷新。 */
export const useWorkspaceStore = defineStore("workspace", () => {
  const topics = ref<Topic[]>([]);
  const events = ref<CalendarEvent[]>([]);
  let topicsTask: Promise<Topic[]> | null = null;
  let eventsTask: Promise<CalendarEvent[]> | null = null;

  async function refreshTopics() {
    if (topicsTask) return topicsTask;
    topicsTask = topicApi
      .list()
      .then(({ data }) => {
        topics.value = data;
        return data;
      })
      .finally(() => {
        topicsTask = null;
      });
    return topicsTask;
  }

  async function refreshEvents() {
    if (eventsTask) return eventsTask;
    eventsTask = calendarApi
      .list()
      .then(({ data }) => {
        events.value = data;
        return data;
      })
      .finally(() => {
        eventsTask = null;
      });
    return eventsTask;
  }

  function prefetch() {
    void refreshTopics();
    void refreshEvents();
  }

  return { topics, events, refreshTopics, refreshEvents, prefetch };
});
