<template>
  <FreeDATAMain />
</template>

<script setup>
import FreeDATAMain from './components/main_screen.vue';
import { onMounted } from 'vue';
onMounted(() => {
  // Set attributes on the <html> element
  document.documentElement.setAttribute('lang', 'en');
  document.documentElement.setAttribute('data-bs-theme', 'light');
});
</script>