<script setup lang="ts">
const props = defineProps(["btnText", "btnID"]);

function emitClick() {
  window.dispatchEvent(new CustomEvent("add-widget", { detail: props.btnID }));
}
</script>
<template>
  <button class="btn btn-small btn-outline-secondary" v-on:click="emitClick">
    {{ btnText }}
  </button>
</template>
