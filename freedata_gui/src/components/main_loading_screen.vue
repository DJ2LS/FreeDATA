<!-- src/components/main_loading_screen.vue -->
<template>
  <div class="loading-screen">
    <div class="spinner" />
    <p>Loading...</p>
  </div>
</template>

<script>
export default {
  name: "LoadingScreen",
};
</script>

<style scoped>
.loading-screen {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100vh;
  background-color: #f0f0f0;
  flex-direction: column;
}

.spinner {
  width: 50px;
  height: 50px;
  border: 5px solid rgba(0, 0, 0, 0.1);
  border-top-color: #3498db;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

p {
  margin-top: 10px;
  font-size: 1.2rem;
  color: #333;
}
</style>
