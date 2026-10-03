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


import {defineAsyncComponent, onMounted, onUnmounted} from 'vue';
import { Tooltip, Popover } from 'bootstrap'
import i18next from './js/i18n';

// Lazy load FreeDATAMain
const FreeDATAMain = defineAsyncComponent(() =>
    import('./components/main_screen.vue')
);

// Import the loading screen
const LoadingScreen = defineAsyncComponent(() =>
    import('./components/main_loading_screen.vue')
);

// Keep <html lang> in sync with the selected language
function setHtmlLang(lng) {
  document.documentElement.setAttribute('lang', lng || 'en');
}

onMounted(() => {
// Set attributes on the <html> element
  setHtmlLang(i18next.language);
  i18next.on('languageChanged', setHtmlLang);
  // Only set a default theme if none was applied yet (main.js applies the stored color mode)
  if (!document.documentElement.hasAttribute('data-bs-theme')) {
    document.documentElement.setAttribute('data-bs-theme', 'light');
  }

// Initialize Tooltips and Popovers
    new Tooltip(document.body, {
      selector: "[data-bs-toggle='tooltip']",
    })

  // Bootstrap allows one component instance per element: body already holds the
  // delegated Tooltip, so the delegated Popover lives on <html>
  new Popover(document.documentElement, {
      selector: "[data-bs-toggle='popover']",
    })

});

onUnmounted(() => {
  i18next.off('languageChanged', setHtmlLang);
});


</script>
