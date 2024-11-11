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
import "./styles.css"; // Import global styles
import "bootstrap/dist/css/bootstrap.css";
import "bootstrap-icons/font/bootstrap-icons.css";


import {defineAsyncComponent, onMounted} from 'vue';
import { Tooltip, Popover } from 'bootstrap'

// Lazy load FreeDATAMain
const FreeDATAMain = defineAsyncComponent(() =>
    import('./components/main_screen.vue')
);

// Import the loading screen
const LoadingScreen = defineAsyncComponent(() =>
    import('./components/main_loading_screen.vue')
);

onMounted(() => {
// Set attributes on the <html> element
  document.documentElement.setAttribute('lang', 'en');
  document.documentElement.setAttribute('data-bs-theme', 'light');

// Initialize Tooltips and Popovers
    new Tooltip(document.body, {
      selector: "[data-bs-toggle='tooltip']",
    })

  new Popover(document.body, {
      selector: "[data-bs-toggle='popover']",
    })

});


</script>
