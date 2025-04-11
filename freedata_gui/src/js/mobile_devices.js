import { ref, computed, onMounted, onUnmounted } from "vue";

export function useIsMobile(breakpoint = 720) {
  const windowWidth = ref(window.innerWidth);

  const updateWidth = () => {
    windowWidth.value = window.innerWidth;
  };

  onMounted(() => window.addEventListener("resize", updateWidth));
  onUnmounted(() => window.removeEventListener("resize", updateWidth));

  const isMobile = computed(() => windowWidth.value < breakpoint);
  return { isMobile, windowWidth };
}
