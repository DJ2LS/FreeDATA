<script setup lang="ts">
import { ref, onMounted, reactive, nextTick } from "vue";
import { Modal } from "bootstrap";
import { setActivePinia } from "pinia";
import pinia from "../store/index";
setActivePinia(pinia);
import "../../node_modules/gridstack/dist/gridstack.min.css";
import { GridStack } from "gridstack";
import { settingsStore as settings } from "../store/settingsStore.js";

import hsl from "./main_active_heard_stations.vue";
import stats from "./main_active_stats.vue";
import audio from "./main_active_audio_level.vue";
import rigctl from "./main_active_rig_control.vue";
import beacon from "./main_active_broadcasts.vue";
import { stateDispatcher } from "../js/eventHandler";
let count = ref(0);
let info = ref("");
let gridFloat = ref(false);
let color = ref("black");
let gridInfo = ref("");
let grid = null; // DO NOT use ref(null) as proxies GS will break all logic when comparing structures... see https://github.com/gridstack/gridstack.js/issues/2115
let items = ref([]);

onMounted(() => {
  grid = GridStack.init({
    // DO NOT user grid.value = GridStack.init(), see above
    float: true,
    cellHeight: "70px",
    minRow: 12,
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
  const node = items[count.value] || { x: 0, y: 0, w: 3, h: 3 };
  node.id = "w_" + count.value++;
  node.component2 = componentToAdd;
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
  addNewWidget2(hsl);
  addNewWidget2(stats);
  addNewWidget2(audio);
  addNewWidget2(rigctl);
  addNewWidget2(beacon);
}
</script>

<template>
  <button type="button" @click="showModal">Add Widget pos [0,0]</button>
  <button type="button" @click="quickfill">Quickfill</button>
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
        <button @click="remove(w)" class="btn-close grid-stack-floaty-btn">
          <i style="font-size: x-small" class="bi bi-trash3 h3"></i>
        </button>
        <component :is="w.component2" v-bind="w" />
      </div>
    </div>
  </div>
  <div class="modal fade" id="tileModal" tabindex="-1">
    <div class="modal-dialog">
      <div class="modal-content">
        <div class="modal-header">
          <h5 class="modal-title">Add grid tile</h5>
          <button
            type="button"
            class="btn-close"
            data-bs-dismiss="modal"
            aria-label="Close"
          ></button>
        </div>
        <div class="modal-body">
          <div
            class="btn-group"
            role="group"
            aria-label="Basic outlined example"
          >
            <button
              type="button"
              @click="addNewWidget2(hsl)"
              class="btn btn-outline-secondary"
              data-bs-dismiss="modal"
            >
              Heard station list
            </button>
            <button
              type="button"
              @click="addNewWidget2(stats)"
              class="btn btn-outline-secondary"
              data-bs-dismiss="modal"
            >
              Stats (waterfall, etc)
            </button>
            <button
              type="button"
              @click="addNewWidget2(audio)"
              class="btn btn-outline-secondary"
              data-bs-dismiss="modal"
            >
              Audio
            </button>
            <button
              type="button"
              @click="addNewWidget2(beacon)"
              class="btn btn-outline-secondary"
              data-bs-dismiss="modal"
            >
              Broadcasts
            </button>
            <button
              type="button"
              @click="addNewWidget2(rigctl)"
              class="btn btn-outline-secondary"
              data-bs-dismiss="modal"
            >
              Rig Control
            </button>
          </div>
        </div>
        <div class="modal-footer">
          <button
            type="button"
            class="btn btn-secondary"
            data-bs-dismiss="modal"
          >
            Close
          </button>
          <button type="button" class="btn btn-primary">Save changes</button>
        </div>
      </div>
    </div>
  </div>
</template>
<style>
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
  top: 3px;
  opacity: 50%;
}
</style>
