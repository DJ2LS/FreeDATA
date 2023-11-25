<script setup lang="ts">
import { ref, onMounted, reactive, nextTick } from "vue";
import { setActivePinia } from "pinia";
import pinia from "../store/index";
setActivePinia(pinia);
import "../../node_modules/gridstack/dist/gridstack.min.css"
import { GridStack } from "gridstack";
import { settingsStore as settings } from "../store/settingsStore.js";

import hsl from "./main_active_heard_stations.vue"
import stats from "./main_active_stats.vue"
import audio from "./main_active_audio_level.vue"
import rigctl from "./main_active_rig_control.vue"
import beacon from "./main_active_broadcasts.vue"
let count = ref(0);

let info = ref("");
let grid = null; // DO NOT use ref(null) as proxies GS will break all logic when comparing structures... see https://github.com/gridstack/gridstack.js/issues/2115
const items = [
{ x: 0, y: 1, h: 2 },
{ x: 0, y: 2, w: 3 },
{ x: 0, y: 7 },
{ x: 3, y: 1, h: 2 },
{ x: 0, y: 6, w: 2, h: 2 },
];
let components = reactive({
      yourRandomComponent1: {
        name: hsl, props: {}, gridPos: { x: 0, y: 1, w: 8, h: 13 }
      },
      yourRandomComponent2: {
        name: stats, props: {}, gridPos: { x: 9, y: 1, w: 4, h: 13 }
      },
      yourRandomComponent5: {
        name: beacon, props: {}, gridPos: { x: 0, y: 15, w: 4, h: 5 },
      },
      yourRandomComponent4: {
        name: rigctl, props: {}, gridPos: {  x: 5, y: 15, w: 4, h: 5},
      },
      yourRandomComponent3: {
        name: audio, props: {}, gridPos: {  x: 14, y: 15, w: 4, h: 5},
      },
      

    });
onMounted(() => {
  grid = GridStack.init({ // DO NOT use grid.value = GridStack.init(), see above
    float: true,
    cellHeight: "25px",
    minRow: 24,
  });

  grid.on("dragstop", function (event, element) {
    const node = element.gridstackNode;
    info.value = `you just dragged node #${node.id} to ${node.x},${node.y} – good job!`;
  });
});

function addNewWidget() {
components.yourRandomComponent3= {
name: rigctl, props: {}, gridPos: {x: 14, y: 15, w: 4, h: 5 }
}

  // we have to wait for vue to update v-for, 
  // until then the querySelector wont find the element
  nextTick(() => {
    console.log(grid);
    let compEl = document.querySelector('[gs-id="yourRandomComponent3"]');
    console.log(compEl);
    grid.makeWidget(compEl);
  });
  //console.warn("i will only work once, fix my inputs to reuse me");
}

</script>

<template>
  <!--
<button @click="addNewWidget()">Add Widget</button> {{ info }}
  -->

<section class="grid-stack">
  <div 
    v-for="(component, key, index) in components" 
    :key="'component'+index" 
    :gs-id="key" 
    class="grid-stack-item"
    :gs-x="component.gridPos.x" 
    :gs-y="component.gridPos.y" 
    :gs-h="component.gridPos.h" 
    :gs-w="component.gridPos.w"
    gs-auto-position="true"
  >
    <div class="grid-stack-item-content">
      <component :is="component.name" v-bind="component.props" />
    </div>
  </div>
</section>
</template>
<style>

.grid-stack-item {
  color: #2c3e50;
  text-align: center;
  
  overflow: auto;
  z-index: 50;
}
</style>