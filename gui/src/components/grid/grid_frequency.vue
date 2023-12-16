<script setup lang="ts">
import { setActivePinia } from "pinia";
import pinia from "../../store/index";
setActivePinia(pinia);

import { useStateStore } from "../../store/stateStore.js";
const state = useStateStore(pinia);
</script>
<template>
<div class="w-100">
  <div class="input-group input-group-sm" style="width: calc(100% - 24px);">
  
 
  <span class="input-group-text">Hz</span>
  
  
               <input type="text" class="form-control" style="min-width: 3em;" placeholder="mycall" v-model=state.frequency readonly>
               <a class="btn btn-secondary dropdown-toggle"               v-bind:class="{
                disabled: state.hamlib_status === 'disconnected',
              }" type="button" data-bs-toggle="offcanvas" data-bs-target="#offcanvasFrequency"></a>

 </div>
</div>
</template>
