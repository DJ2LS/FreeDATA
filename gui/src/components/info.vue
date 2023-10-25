<script setup lang="ts">
import { ref, onMounted } from "vue";

import { setActivePinia } from "pinia";
import pinia from "../store/index";
setActivePinia(pinia);

import { useStateStore } from "../store/stateStore.js";
const state = useStateStore(pinia);

const version = import.meta.env.PACKAGE_VERSION;

function openWebExternal(url) {
  open(url);
}
const cards = ref([
  {
    title: "Simon - DJ2LS",
    role: "Founder & Core developer",
    imgSrc: "dj2ls.png",
  },
  { title: "Alan - N1QM", role: "developer", imgSrc: "" },
  { title: "Stefan - DK5SM", role: "tester", imgSrc: "" },
  { title: "Wolfgang - DL4IAZ", role: "supporter", imgSrc: "" },
  { title: "David - VK5DGR", role: "codec2 founder", imgSrc: "" },
  { title: "John - EI7IG", role: "tester", imgSrc: "" },
  { title: "John - N2KIQ", role: "developer", imgSrc: "" },
  { title: "Trip - KT4WO", role: "tester", imgSrc: "" },
  { title: "Manuel - DF7MH", role: "tester", imgSrc: "" },
  { title: "Darren - G0HWW", role: "tester", imgSrc: "" },
  { title: "Kai - LA3QMA", role: "developer", imgSrc: "" },
]);

// Shuffle cards
function shuffleCards() {
  cards.value = cards.value.sort(() => Math.random() - 0.5);
}

onMounted(shuffleCards);
</script>

<template>
  <h3 class="m-2">
    <span class="badge bg-secondary">FreeDATA: {{ version }}</span>
    <span class="ms-2 badge bg-secondary"
      >Modem: {{ state.modem_version }}</span
    >
  </h3>

  <div class="container-fluid">
    <div class="row mt-2">
      <hr />
      <h6>Important URLs</h6>

      <div
        class="btn-toolbar mx-auto"
        role="toolbar"
        aria-label="Toolbar with button groups"
      >
        <div class="btn-group">
          <button
            class="btn btn-sm bi bi-geo-alt btn-secondary me-2"
            id="openExplorer"
            type="button"
            data-bs-placement="bottom"
            @click="openWebExternal('https://explorer.freedata.app')"
          >
            Explorer map
          </button>
        </div>
        <div class="btn-group">
          <button
            class="btn btn-sm btn-secondary me-2 bi bi-graph-up"
            id="btnStats"
            type="button"
            data-bs-placement="bottom"
            @click="openWebExternal('https://statistics.freedata.app/')"
          >
            Statistics
          </button>
        </div>
        <div class="btn-group">
          <button
            class="btn btn-secondary bi bi-bookmarks me-2"
            id="fdWww"
            data-bs-toggle="tooltip"
            data-bs-trigger="hover"
            title="FreeDATA website"
            role="button"
            @click="openWebExternal('https://freedata.app')"
          >
            Website
          </button>
        </div>
        <div class="btn-group">
          <button
            class="btn btn-secondary bi bi-github me-2"
            id="ghUrl"
            data-bs-toggle="tooltip"
            data-bs-trigger="hover"
            title="Github"
            role="button"
            @click="openWebExternal('https://github.com/dj2ls/freedata')"
          >
            Github
          </button>
        </div>
        <div class="btn-group">
          <button
            class="btn btn-secondary bi bi-wikipedia me-2"
            id="wikiUrl"
            data-bs-toggle="tooltip"
            data-bs-trigger="hover"
            title="Wiki"
            role="button"
            @click="openWebExternal('https://wiki.freedata.app')"
          >
            Wiki
          </button>
        </div>
        <div class="btn-group">
          <button
            class="btn btn-secondary bi bi-discord"
            id="discordUrl"
            data-bs-toggle="tooltip"
            data-bs-trigger="hover"
            title="Discord"
            role="button"
            @click="openWebExternal('https://discord.freedata.app')"
          >
            Discord
          </button>
        </div>
      </div>
    </div>
    <div class="row mt-5">
      <hr />
      <h6>Special thanks to</h6>
    </div>

    <div class="d-flex flex-nowrap overflow-x-auto">
      <div class="row row-cols-1 row-cols-md-3 g-4">
        <div class="d-inline-block" v-for="card in cards" :key="card.title">
          <div class="col">
            <div
              class="card border-dark mb-3 ms-1 me-1"
              style="max-width: 15rem"
            >
              <img :src="card.imgSrc" class="card-img-top" />
              <div class="card-body">
                <p class="card-text text-center">{{ card.role }}</p>
              </div>
              <div class="card-footer text-body-secondary text-center">
                <strong>{{ card.title }}</strong>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
