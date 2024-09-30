<template>
  <Suspense>
    <template #default>
      <!-- Lazy load FreeDATAMain -->
      <FreeDATAMain />
    </template>
    <template #fallback>
      <!-- Show loading screen while the component is loading -->
      <LoadingScreen />
    </template>
  </Suspense>
</template>

<script setup>
import { defineAsyncComponent, onMounted } from 'vue';

// Lazy load FreeDATAMain
const FreeDATAMain = defineAsyncComponent(() =>
  import('./components/main_screen.vue')
);

// Import the loading screen
const LoadingScreen = defineAsyncComponent(() =>
  import('./components/main_loading_screen.vue')
);

// Set attributes on the <html> element
onMounted(() => {
  document.documentElement.setAttribute('lang', 'en');
  document.documentElement.setAttribute('data-bs-theme', 'light');
});
</script>
