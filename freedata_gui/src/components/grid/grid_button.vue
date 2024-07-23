<script setup>
import { defineProps } from 'vue';

const props = defineProps(['btnText', 'btnID']);
//const emit = defineEmits();

function emitClick() {
  window.dispatchEvent(new CustomEvent('add-widget', { detail: props.btnID }));
}
</script>

<template>
  <button
    class="btn btn-small btn-outline-secondary mb-1"
    @click="emitClick"
  >
    {{ props.btnText }}
  </button>
</template>
