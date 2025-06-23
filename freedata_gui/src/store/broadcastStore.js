import { defineStore } from "pinia";
import { ref } from "vue";


export const useBroadcastStore = defineStore("broadcastStore", () => {

  // Indicator if we are loading data
  var loading = ref(false);

  /* ------------------------------------------------ */
  // Scroll to bottom functions
  const scrollTrigger = ref(0);

  function triggerScrollToBottom() {
    scrollTrigger.value++;
  }


  return {
    scrollTrigger,
    triggerScrollToBottom,
    loading,
  };
});
