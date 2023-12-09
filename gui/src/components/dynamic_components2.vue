<script setup lang="ts">
import { ref, onMounted, nextTick, shallowRef, render, h } from "vue";
import { Modal } from "bootstrap";
import { setActivePinia } from "pinia";
import pinia from "../store/index";
setActivePinia(pinia);
import "../../node_modules/gridstack/dist/gridstack.min.css";
import { GridStack } from "gridstack";
import { settingsStore as settings } from "../store/settingsStore.js";

import active_heard_stations from "./grid/grid_active_heard_stations.vue";
import mini_heard_stations from "./grid/grid_active_heard_stations_mini.vue";
import active_stats from "./grid/grid_active_stats.vue";
import active_audio_level from "./grid/grid_active_audio.vue";
import active_rig_control from "./grid/grid_active_rig_control.vue";
import active_broadcats from "./grid/grid_active_broadcasts.vue";
import s_meter from "./grid/grid_s-meter.vue";
import dbfs_meter from "./grid/grid_dbfs.vue";
import grid_activities from "./grid/grid_activities.vue";
import grid_button from "./grid/button.vue";
import { stateDispatcher } from "../js/eventHandler";

let count = ref(0);
let grid = null; // DO NOT use ref(null) as proxies GS will break all logic when comparing structures... see https://github.com/gridstack/gridstack.js/issues/2115
let items = ref([]);
class gridWidget {
  //Contains the vue component
  component2;
  //Initial size and location if autoplace is false
  size;
  //Text for dynamic button
  text;
  //if true add when quick fill button is clicked
  quickFill;
  //Auto place; true to add where ever it fits; false uses position information
  autoPlace;
  //Category to place in widget picker
  category;
  constructor(component, size, text, quickfill, autoPlace, category) {
    this.component2 = component;
    this.size = size;
    this.text = text;
    this.quickFill = quickfill;
    this.autoPlace = autoPlace;
    this.category = category;
  }
}
const gridWidgets = [
  new gridWidget(
    active_heard_stations,
    { x: 0, y: 0, w: 16, h: 40 },
    "Detailed heard stations list",
    true,
    true,"Activity"
  ),
  new gridWidget(
    active_stats,
    { x: 16, y: 26, w: 8, h: 69 },
    "Stats (waterfall, etc)",
    true,
    true,
    "Stats"
  ),
  new gridWidget(
    active_audio_level,
    { x: 16, y: 0, w: 8, h: 26 },
    "Audio main",
    true,
    true,
    "Audio",
  ),
  new gridWidget(
    active_rig_control,
    { x: 6, y: 40, w: 10, h: 30 },
    "Rig control main",
    true,
    true,
    "Rig"
  ),
  new gridWidget(
    active_broadcats,
    { x: 6, y: 70, w: 10, h: 25 },
    "Broadcats main",
    true,
    true,
    "Broadcasts"
  ),
  new gridWidget(
    mini_heard_stations,
    { x: 1, y: 1, w: 6, h: 54 },
    "Mini heard stations list",
    false,
    true,
    "Activity"
  ),
  new gridWidget(s_meter, { x: 1, y: 1, w: 4, h: 8 }, "S-Meter", false, true, "Rig"),
  new gridWidget(
    dbfs_meter,
    { x: 1, y: 1, w: 4, h: 8 },
    "Dbfs Meter",
    false,
    true,
    "Audio"
  ),
  new gridWidget(
    grid_activities,
    { x: 0, y: 40, w: 6, h: 55 },
    "Activities list",
    true,
    true,
    "Activity",
  ),
  
];
onMounted(() => {
  grid = GridStack.init({
    // DO NOT use grid.value = GridStack.init(), see above
    float: true,
    cellHeight: "5px",
    minRow: 50,
    margin: 5,
    column: 24,
    draggable: {
      scroll: true,
    },
    resizable: {
      handles: "se,sw",
    },
  });

  grid.on("dragstop", function (event, element) {
    const node = element.gridstackNode;
    console.info(
      `Moved #${node.id} to ${node.x}.${node.y}.  Dimensions:  ${node.w}x${node.h}`,
    );
  });

  grid.on("change", onChange);

  gridWidgets.forEach((gw) =>{
    //Dynamically add widgets to widget menu
    let dom = document.getElementById("otherBod");
    switch (gw.category) {
      case "Activity":
        dom = document.getElementById("actBody");
        break;
        case "Stats":
        dom = document.getElementById("statsBody");
        break;
        case "Audio":
        dom = document.getElementById("audioBody");
        break;
        case "Rig":
        dom = document.getElementById("rigBody");
        break;
        case "Broadcasts":
        dom = document.getElementById("bcBody");
        break;
      default:
        console.error("Uknown widget category:  " + gw.category);
        break;
    }
    var index = gridWidgets.findIndex((w) => gw.text == w.text);
    dom.insertAdjacentHTML("beforeend",`<div id="gridbtn-${index}""></div>`);
    let dom2 = document.getElementById(`gridbtn-${index}`);
    let vueComponent = h(grid_button,{btnText: gw.text,btnID:index});
    render(vueComponent,dom2);
  })
  window.addEventListener(
      "add-widget",
      function (eventdata) {
        let data = eventdata.detail;
        addNewWidget2(gridWidgets[data]);
      },
      false,
    );
});
function onChange(event, changeItems) {
  // update item position
  changeItems.forEach((item) => {
    var widget = items.value.find((w) => w.id == item.id);
    if (!widget) {
      console.error("Widget not found: " + item.id);
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
  node.autoPlace = componentToAdd.autoPlace;
  items.value.push(node);
  nextTick(() => {
    grid.makeWidget(node.id);
  });
}

function remove(widget) {
  var index = items.value.findIndex((w) => w.id == widget.id);
  items.value.splice(index, 1);
  const selector = `#${widget.id}`;
  grid.removeWidget(selector, false);
}

function clearAllItems() {
  grid.removeAll(false);
  count.value = 0;
  items.value = [];
}
function quickfill() {
  gridWidgets.forEach(async (gw) => {
    if (gw.quickFill === true) {
      gw.autoPlace = false;
      await addNewWidget2(gw);
      //Reset autoplace value
      gw.autoPlace = true;
    }
  });
}
</script>

<template>
  <button
    class="btn btn-secondary fixed-middle-right rounded-0 rounded-start-4 p-1 pt-4 pb-4"
    type="button"
    data-bs-toggle="offcanvas"
    data-bs-target="#offcanvasGridItems"
    aria-controls="offcanvasGridItems"
  >
    <i class="bi bi-grip-vertical h5"></i>
  </button>

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
        :gs-auto-position="w.autoPlace"
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

  <div
    class="offcanvas offcanvas-end"
    data-bs-scroll="true"
    data-bs-backdrop="true"
    tabindex="-1"
    id="offcanvasGridItems"
    aria-labelledby="offcanvasGridItemsLabel"
  >
    <div class="offcanvas-header">
      <h5 class="offcanvas-title" id="offcanvasGridItemsLabel">
        Manage grid widgets
      </h5>
      
      <button
        type="button"
        class="btn-close"
        data-bs-dismiss="offcanvas"
        aria-label="Close"
      ></button>
    </div>
    <div class="offcanvas-body">
      <p>Grid widgets allow you to customize the display for your own usage.  Here you may add additional widgets to fit your needs.
        You can move and resize the individual widgets!
      </p>
      <div>
        <button
          class="btn btn-sm btn-outline-primary"
          type="button"
          @click="quickfill"
        >
          Fill grid with common widgets
        </button>


      </div>
      <hr>
      <!-- Begin widget selector -->
      <div class="accordion" id="accordionExample">
        <!-- Heard Stations -->
        <div class="accordion-item">
          <h2 class="accordion-header" id="headingHeardStations">
            <button
              class="accordion-button"
              type="button"
              data-bs-toggle="collapse"
              data-bs-target="#collapseHeardStations"
              aria-expanded="true"
              aria-controls="collapseHeardStations"
            >
              <strong>Activity</strong>
            </button>
          </h2>
          <div
            id="collapseHeardStations"
            class="accordion-collapse collapse show"
            aria-labelledby="headingHeardStations"
            data-bs-parent="#accordionExample"
          >
            <div class="accordion-body" id="actBody">

            </div>
          </div>
        </div>

        <!-- Activities -->
        <div class="accordion-item">
          <h2 class="accordion-header" id="headingActivities">
            <button
              class="accordion-button collapsed"
              type="button"
              data-bs-toggle="collapse"
              data-bs-target="#collapseActivities"
              aria-expanded="false"
              aria-controls="collapseActivities"
            >
              <strong>Audio</strong>
            </button>
          </h2>
          <div
            id="collapseActivities"
            class="accordion-collapse collapse"
            aria-labelledby="headingActivities"
            data-bs-parent="#accordionExample"
          >
            <div class="accordion-body" id="audioBody">
              
            </div>
          </div>
        </div>
        <!-- Broadcasts -->
        <div class="accordion-item">
          <h2 class="accordion-header" id="headingBroadcasts">
            <button
              class="accordion-button collapsed"
              type="button"
              data-bs-toggle="collapse"
              data-bs-target="#collapseBroadcasts"
              aria-expanded="false"
              aria-controls="collapseBroadcasts"
            >
              <strong>Broadcasts</strong>
            </button>
          </h2>
          <div
            id="collapseBroadcasts"
            class="accordion-collapse collapse"
            aria-labelledby="headingBroadcasts"
            data-bs-parent="#accordionExample"
          >
            <div class="accordion-body" id="bcBody">

            </div>
          </div>
        </div>
        <!-- Radio Control -->
        <div class="accordion-item">
          <h2 class="accordion-header" id="headingRadioControl">
            <button
              class="accordion-button collapsed"
              type="button"
              data-bs-toggle="collapse"
              data-bs-target="#collapseRadioControl"
              aria-expanded="false"
              aria-controls="collapseRadioControl"
            >
              <strong>Radio Control</strong>
            </button>
          </h2>
          <div
            id="collapseRadioControl"
            class="accordion-collapse collapse"
            aria-labelledby="headingRadioControl"
            data-bs-parent="#accordionExample"
          >
            <div class="accordion-body" id="rigBody">

            </div>
          </div>
        </div>

        <!-- Audio Control -->
        <div class="accordion-item">
          <h2 class="accordion-header" id="headingAudioControl">
            <button
              class="accordion-button collapsed"
              type="button"
              data-bs-toggle="collapse"
              data-bs-target="#collapseAudioControl"
              aria-expanded="false"
              aria-controls="collapseAudioControl"
            >
              <strong>Statistics</strong>
            </button>
          </h2>
          <div
            id="collapseAudioControl"
            class="accordion-collapse collapse"
            aria-labelledby="headingAudioControl"
            data-bs-parent="#accordionExample"
          >
            <div class="accordion-body" id="statsBody">
              
            </div>
          </div>
        </div>

        <!-- Statistics -->
        <div class="accordion-item">
          <h2 class="accordion-header" id="headingStatistics">
            <button
              class="accordion-button collapsed"
              type="button"
              data-bs-toggle="collapse"
              data-bs-target="#collapseStatistics"
              aria-expanded="false"
              aria-controls="collapseStatistics"
            >
              <strong>Other</strong>
            </button>
          </h2>
          <div
            id="collapseStatistics"
            class="accordion-collapse collapse"
            aria-labelledby="headingStatistics"
            data-bs-parent="#accordionExample"
          >
            <div class="accordion-body" id="otherBod">
              
            </div>
          </div>
        </div>
      </div>
      <hr>
      <button
          class="btn btn-sm btn-outline-warning"
          type="button"
          @click="clearAllItems"
        >
          Clear grid
        </button>
    </div>
  </div>
</template>

<style>
.fixed-middle-right {
  position: fixed; /* Fixed/sticky position */
  top: 50%; /* Position at the middle of the viewport */
  right: 0px; /* Place the button 20px from the right */
  transform: translateY(-50%); /* Adjust for exact vertical centering */
  z-index: 999; /* Ensure it's on top of other elements */
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
.gs-24 > .grid-stack-item {
  width: 4.167%;
}
.gs-24 > .grid-stack-item[gs-x="1"] {
  left: 4.167%;
}
.gs-24 > .grid-stack-item[gs-w="2"] {
  width: 8.333%;
}
.gs-24 > .grid-stack-item[gs-x="2"] {
  left: 8.333%;
}
.gs-24 > .grid-stack-item[gs-w="3"] {
  width: 12.5%;
}
.gs-24 > .grid-stack-item[gs-x="3"] {
  left: 12.5%;
}
.gs-24 > .grid-stack-item[gs-w="4"] {
  width: 16.667%;
}
.gs-24 > .grid-stack-item[gs-x="4"] {
  left: 16.667%;
}
.gs-24 > .grid-stack-item[gs-w="5"] {
  width: 20.833%;
}
.gs-24 > .grid-stack-item[gs-x="5"] {
  left: 20.833%;
}
.gs-24 > .grid-stack-item[gs-w="6"] {
  width: 25%;
}
.gs-24 > .grid-stack-item[gs-x="6"] {
  left: 25%;
}
.gs-24 > .grid-stack-item[gs-w="7"] {
  width: 29.167%;
}
.gs-24 > .grid-stack-item[gs-x="7"] {
  left: 29.167%;
}
.gs-24 > .grid-stack-item[gs-w="8"] {
  width: 33.333%;
}
.gs-24 > .grid-stack-item[gs-x="8"] {
  left: 33.333%;
}
.gs-24 > .grid-stack-item[gs-w="9"] {
  width: 37.5%;
}
.gs-24 > .grid-stack-item[gs-x="9"] {
  left: 37.5%;
}
.gs-24 > .grid-stack-item[gs-w="10"] {
  width: 41.667%;
}
.gs-24 > .grid-stack-item[gs-x="10"] {
  left: 41.667%;
}
.gs-24 > .grid-stack-item[gs-w="11"] {
  width: 45.833%;
}
.gs-24 > .grid-stack-item[gs-x="11"] {
  left: 45.833%;
}
.gs-24 > .grid-stack-item[gs-w="12"] {
  width: 50%;
}
.gs-24 > .grid-stack-item[gs-x="12"] {
  left: 50%;
}
.gs-24 > .grid-stack-item[gs-w="13"] {
  width: 54.167%;
}
.gs-24 > .grid-stack-item[gs-x="13"] {
  left: 54.167%;
}
.gs-24 > .grid-stack-item[gs-w="14"] {
  width: 58.333%;
}
.gs-24 > .grid-stack-item[gs-x="14"] {
  left: 58.333%;
}
.gs-24 > .grid-stack-item[gs-w="15"] {
  width: 62.5%;
}
.gs-24 > .grid-stack-item[gs-x="15"] {
  left: 62.5%;
}
.gs-24 > .grid-stack-item[gs-w="16"] {
  width: 66.667%;
}
.gs-24 > .grid-stack-item[gs-x="16"] {
  left: 66.667%;
}
.gs-24 > .grid-stack-item[gs-w="17"] {
  width: 70.833%;
}
.gs-24 > .grid-stack-item[gs-x="17"] {
  left: 70.833%;
}
.gs-24 > .grid-stack-item[gs-w="18"] {
  width: 75%;
}
.gs-24 > .grid-stack-item[gs-x="18"] {
  left: 75%;
}
.gs-24 > .grid-stack-item[gs-w="19"] {
  width: 79.167%;
}
.gs-24 > .grid-stack-item[gs-x="19"] {
  left: 79.167%;
}
.gs-24 > .grid-stack-item[gs-w="20"] {
  width: 83.333%;
}
.gs-24 > .grid-stack-item[gs-x="20"] {
  left: 83.333%;
}
.gs-24 > .grid-stack-item[gs-w="21"] {
  width: 87.5%;
}
.gs-24 > .grid-stack-item[gs-x="21"] {
  left: 87.5%;
}
.gs-24 > .grid-stack-item[gs-w="22"] {
  width: 91.667%;
}
.gs-24 > .grid-stack-item[gs-x="22"] {
  left: 91.667%;
}
.gs-24 > .grid-stack-item[gs-w="23"] {
  width: 95.833%;
}
.gs-24 > .grid-stack-item[gs-x="23"] {
  left: 95.833%;
}
.gs-24 > .grid-stack-item[gs-w="24"] {
  width: 100%;
}
</style>
