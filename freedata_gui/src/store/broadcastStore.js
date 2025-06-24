import { defineStore } from "pinia";
import { ref } from "vue";


export const useBroadcastStore = defineStore("broadcastStore", () => {

  // Indicator if we are loading data
  var loading = ref(false);

  /* ------------------------------------------------ */
  // Scroll to bottom functions
  const scrollTrigger = ref(0);

  // domains
  const domains = ref({});
  const selectedDomain = ref({});

  // broadcasts per domain
  const domainBroadcasts = ref({});

  // input text
  const inputText = ref("");

  function triggerScrollToBottom() {
    scrollTrigger.value++;
  }

  function setDomains(data){
    domains.value = data;
  }

  function setBroadcastsForDomain(data){
    domainBroadcasts.value = data;
  }

  return {
    scrollTrigger,
    triggerScrollToBottom,
    loading,
    domains,
    setDomains,
    selectedDomain,
    domainBroadcasts,
    setBroadcastsForDomain,
    inputText,
  };
})
