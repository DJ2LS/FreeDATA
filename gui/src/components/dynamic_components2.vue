<script setup lang="ts">
import { ref, onMounted, reactive, nextTick, shallowRef } from "vue";
import { Modal } from "bootstrap";
import { setActivePinia } from "pinia";
import pinia from "../store/index";
setActivePinia(pinia);
import "../../node_modules/gridstack/dist/gridstack.min.css";
import { GridStack } from "gridstack";
import { settingsStore as settings } from "../store/settingsStore.js";

import active_heard_stations from "./grid_active_heard_stations.vue";
import mini_heard_stations from "./grid_active_heard_stations_mini.vue";
import active_stats from "./grid_active_stats.vue";
import active_audio_level from "./grid_active_audio.vue";
import active_rig_control from "./grid_active_rig_control.vue";
import active_broadcats from "./grid_active_broadcasts.vue";
import s_meter from "./grid_s-meter.vue";
import dbfs_meter from "./grid_dbfs.vue";
import grid_activities from "./grid_activities.vue";
import { stateDispatcher } from "../js/eventHandler";

let count = ref(0);
let info = ref("");
let gridFloat = ref(false);
let color = ref("black");
let gridInfo = ref("");
let grid = null; // DO NOT use ref(null) as proxies GS will break all logic when comparing structures... see https://github.com/gridstack/gridstack.js/issues/2115
let items = ref([]);
class gridWidget {
  component2;
  size;
  text;
  constructor(component, size, text) {
    this.component2 = component;
    this.size = size;
    this.text = text;
  }
}
const gridWidgets = [
  new gridWidget(
    active_heard_stations,
    { x: 0, y: 0, w: 7, h: 20 },
    "Heard stations",
  ),
  new gridWidget(
    active_stats,
    { x: 0, y: 0, w: 4, h: 35 },
    "Stats (waterfall, etc)",
  ),
  new gridWidget(active_audio_level, { x: 0, y: 0, w: 4, h: 13 }, "Audio"),
  new gridWidget(
    active_rig_control,
    { x: 0, y: 0, w: 6, h: 12 },
    "Rig control",
  ),
  new gridWidget(active_broadcats, { x: 1, y: 1, w: 4, h: 12 }, "Broadcats"),
  new gridWidget(
    mini_heard_stations,
    { x: 1, y: 1, w: 3, h: 27 },
    "Mini Heard stations",
  ),
  new gridWidget(s_meter, { x: 1, y: 1, w: 2, h: 4 }, "S-Meter"),
  new gridWidget(dbfs_meter, { x: 1, y: 1, w: 2, h: 4 }, "Dbfs Meter"),
  new gridWidget(grid_activities, { x: 1, y: 1, w: 3, h: 27 }, "Activities"),
];
onMounted(() => {
  grid = GridStack.init({
    // DO NOT user grid.value = GridStack.init(), see above
    float: true,
    cellHeight: "10px",
    minRow: 50,
    margin: 5,
    draggable: {
      scroll: true,
    },
    resizable: {
      handles: "se,sw",
    },
  });

  grid.on("dragstop", function (event, element) {
    const node = element.gridstackNode;
    info.value = `you just dragged node #${node.id} to ${node.x},${node.y} – good job!`;
  });

  grid.on("change", onChange);
  // gridFloat.value = grid.float();
});

function changeFloat() {
  gridFloat.value = !gridFloat.value;
  grid.float(gridFloat.value);
}

function onChange(event, changeItems) {
  updateInfo();
  // update item position
  changeItems.forEach((item) => {
    var widget = items.value.find((w) => w.id == item.id);
    if (!widget) {
      alert("Widget not found: " + item.id);
      return;
    }
    widget.x = item.x;
    widget.y = item.y;
    widget.w = item.w;
    widget.h = item.h;
  });
}
function addNewWidget2(componentToAdd) {
  const node = items[count.value] || { ...componentToAdd.size };
  node.id = "w_" + count.value++;
  node.component2 = shallowRef({ ...componentToAdd.component2 });
  items.value.push(node);
  nextTick(() => {
    grid.makeWidget(node.id);
    updateInfo();
  });
}

function removeLastWidget() {
  if (count.value == 0) return;
  var id = `w_${count.value - 1}`;
  var index = items.value.findIndex((w) => w.id == id);
  if (index < 0) return;
  var removed = items.value[index];
  remove(removed);
}

function remove(widget) {
  var index = items.value.findIndex((w) => w.id == widget.id);
  items.value.splice(index, 1);
  const selector = `#${widget.id}`;
  grid.removeWidget(selector, false);
  updateInfo();
}

function updateInfo() {
  color.value =
    grid.engine.nodes.length == items.value.length ? "black" : "red";
  gridInfo.value = `Grid engine: ${grid.engine.nodes.length}, widgets: ${items.value.length}`;
}
function showModal() {
  new Modal("#tileModal", {}).show();
}
function quickfill() {
  gridWidgets.forEach(async (gw) => {
    await addNewWidget2(gw);
  });
}
</script>

<template>
<button class="btn btn-secondary fixed-middle-right rounded-0 rounded-start-4 p-1 pt-4 pb-4" type="button" data-bs-toggle="offcanvas" data-bs-target="#offcanvasGridItems" aria-controls="offcanvasGridItems"><i class="bi bi-grip-vertical h1"></i></button>

  <div class="grid-container vh-100">
    <div class="grid-stack">
      <div
        v-for="(w, indexs) in items"
        class="grid-stack-item"
        :gs-x="w.x"
        :gs-y="w.y"
        :gs-w="w.w"
        :gs-h="w.h"
        :gs-id="w.id"
        :id="w.id"
        :key="w.id"
        :gs-auto-position="true"
      >
        <div class="grid-stack-item-content">
          <button
            @click="remove(w)"
            class="btn-close grid-stack-floaty-btn"
          ></button>
          <component :is="w.component2" />
        </div>
      </div>
    </div>
  </div>

<div class="offcanvas offcanvas-end" data-bs-scroll="true" data-bs-backdrop="true" tabindex="-1" id="offcanvasGridItems" aria-labelledby="offcanvasGridItemsLabel">
  <div class="offcanvas-header">
    <h5 class="offcanvas-title" id="offcanvasGridItemsLabel">
      <button class="btn btn-secondary" type="button" @click="quickfill">Quickfill grid</button>

    </h5>
    <button type="button" class="btn-close" data-bs-dismiss="offcanvas" aria-label="Close"></button>
  </div>
  <div class="offcanvas-body">
<div class="accordion" id="accordionExample">
  <!-- Heard Stations -->
  <div class="accordion-item">
    <h2 class="accordion-header" id="headingHeardStations">
      <button class="accordion-button" type="button" data-bs-toggle="collapse" data-bs-target="#collapseHeardStations" aria-expanded="true" aria-controls="collapseHeardStations">
        <strong>Heard Stations</strong>
      </button>
    </h2>
    <div id="collapseHeardStations" class="accordion-collapse collapse show" aria-labelledby="headingHeardStations" data-bs-parent="#accordionExample">
      <div class="accordion-body">
        <button type="button" @click="addNewWidget2(gridWidgets[0])" class="btn btn-outline-secondary" data-bs-dismiss="modal">Heard station list</button>
      </div>
    </div>
  </div>

  <!-- Activities -->
  <div class="accordion-item">
    <h2 class="accordion-header" id="headingActivities">
      <button class="accordion-button collapsed" type="button" data-bs-toggle="collapse" data-bs-target="#collapseActivities" aria-expanded="false" aria-controls="collapseActivities">
        <strong>Activities</strong>
      </button>
    </h2>
    <div id="collapseActivities" class="accordion-collapse collapse" aria-labelledby="headingActivities" data-bs-parent="#accordionExample">
      <div class="accordion-body">
        <!-- Content for Activities -->
      </div>
    </div>
  </div>

  <!-- Radio Control -->
  <div class="accordion-item">
    <h2 class="accordion-header" id="headingRadioControl">
      <button class="accordion-button collapsed" type="button" data-bs-toggle="collapse" data-bs-target="#collapseRadioControl" aria-expanded="false" aria-controls="collapseRadioControl">
        <strong>Radio Control</strong>
      </button>
    </h2>
    <div id="collapseRadioControl" class="accordion-collapse collapse" aria-labelledby="headingRadioControl" data-bs-parent="#accordionExample">
      <div class="accordion-body">
        <button type="button" @click="addNewWidget2(gridWidgets[3])" class="btn btn-outline-secondary" data-bs-dismiss="modal">Rig Control</button>
      </div>
    </div>
  </div>

  <!-- Audio Control -->
  <div class="accordion-item">
    <h2 class="accordion-header" id="headingAudioControl">
      <button class="accordion-button collapsed" type="button" data-bs-toggle="collapse" data-bs-target="#collapseAudioControl" aria-expanded="false" aria-controls="collapseAudioControl">
        <strong>Audio Control</strong>
      </button>
    </h2>
    <div id="collapseAudioControl" class="accordion-collapse collapse" aria-labelledby="headingAudioControl" data-bs-parent="#accordionExample">
      <div class="accordion-body">
        <button type="button" @click="addNewWidget2(gridWidgets[2])" class="btn btn-outline-secondary" data-bs-dismiss="modal">Audio</button>
      </div>
    </div>
  </div>

  <!-- Statistics -->
  <div class="accordion-item">
    <h2 class="accordion-header" id="headingStatistics">
      <button class="accordion-button collapsed" type="button" data-bs-toggle="collapse" data-bs-target="#collapseStatistics" aria-expanded="false" aria-controls="collapseStatistics">
        <strong>Statistics</strong>
      </button>
    </h2>
    <div id="collapseStatistics" class="accordion-collapse collapse" aria-labelledby="headingStatistics" data-bs-parent="#accordionExample">
      <div class="accordion-body">
        <button type="button" @click="addNewWidget2(gridWidgets[1])" class="btn btn-outline-secondary" data-bs-dismiss="modal">Stats (waterfall, etc)</button>
      </div>
    </div>
  </div>

  <!-- Broadcasts -->
  <div class="accordion-item">
    <h2 class="accordion-header" id="headingBroadcasts">
      <button class="accordion-button collapsed" type="button" data-bs-toggle="collapse" data-bs-target="#collapseBroadcasts" aria-expanded="false" aria-controls="collapseBroadcasts">
        <strong>Broadcasts</strong>
      </button>
    </h2>
    <div id="collapseBroadcasts" class="accordion-collapse collapse" aria-labelledby="headingBroadcasts" data-bs-parent="#accordionExample">
      <div class="accordion-body">
        <button type="button" @click="addNewWidget2(gridWidgets[4])" class="btn btn-outline-secondary" data-bs-dismiss="modal">Broadcasts</button>
      </div>
    </div>
  </div>
</div>






  </div>
</div>


</template>

<style>
.fixed-middle-right {
    position: fixed; /* Fixed/sticky position */
    top: 50%;        /* Position at the middle of the viewport */
    right: 0px;     /* Place the button 20px from the right */
    transform: translateY(-50%); /* Adjust for exact vertical centering */
    z-index: 999;    /* Ensure it's on top of other elements */
}

.grid-stack-item {
  text-align: center;
  overflow: auto;
  z-index: 50;
}
.grid-stack-floaty-btn {
  position: absolute;
  right: 0px;
  z-index: 1000;
  float: right;
  top: 6px;
}
.grid-container {
  overflow-y: auto;
}
</style>
