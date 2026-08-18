import { defineStore } from "pinia";
import { ref, watch } from "vue";

const KEY = "bstar_cat_roam";

export const useCatStore = defineStore("cat", () => {
  const roam = ref(localStorage.getItem(KEY) !== "0");

  watch(roam, (value) => {
    localStorage.setItem(KEY, value ? "1" : "0");
  });

  function setRoam(value: boolean) {
    roam.value = value;
  }

  function toggle() {
    roam.value = !roam.value;
  }

  return { roam, setRoam, toggle };
});
