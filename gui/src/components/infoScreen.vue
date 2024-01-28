<script setup lang="ts">
import { ref, onMounted } from "vue";

import { setActivePinia } from "pinia";
import pinia from "../store/index";
setActivePinia(pinia);

import infoScreen_updater from "./infoScreen_updater.vue";

function openWebExternal(url) {
  open(url);
}
const cards = ref([
  {
    titleName: "Simon",
    titleCall: "DJ2LS",
    role: "Founder & Core Developer",
    imgSrc: "dj2ls.png",
  },
  {
    titleName: "Alan",
    titleCall: "N1QM",
    role: "Developer",
    imgSrc: "person-fill.svg",
  },
  {
    titleName: "Stefan",
    titleCall: "DK5SM",
    role: "Tester",
    imgSrc: "person-fill.svg",
  },
  {
    titleName: "Wolfgang",
    titleCall: "DL4IAZ",
    role: "Supporter",
    imgSrc: "person-fill.svg",
  },
  {
    titleName: "David",
    titleCall: "VK5DGR",
    role: "Codec 2 Founder",
    imgSrc: "vk5dgr.jpeg",
  },
  {
    titleName: "John",
    titleCall: "EI7IG",
    role: "Tester",
    imgSrc: "ei7ig.jpeg",
  },
  {
    titleName: "Paul",
    titleCall: "N2KIQ",
    role: "Developer",
    imgSrc: "person-fill.svg",
  },
  {
    titleName: "Trip",
    titleCall: "KT4WO",
    role: "Tester",
    imgSrc: "kt4wo.png",
  },
  {
    titleName: "Manuel",
    titleCall: "DF7MH",
    role: "Tester",
    imgSrc: "person-fill.svg",
  },
  {
    titleName: "Darren",
    titleCall: "G0HWW",
    role: "Tester",
    imgSrc: "person-fill.svg",
  },
  {
    titleName: "Kai",
    titleCall: "LA3QMA",
    role: "Developer",
    imgSrc: "person-fill.svg",
  },
  {
    titleName: "Pedro",
    titleCall: "F4JAW",
    role: "Core Developer",
    imgSrc: "person-fill.svg",
  },
]);

// Shuffle cards
function shuffleCards() {
  cards.value = cards.value.sort(() => Math.random() - 0.5);
}

onMounted(shuffleCards);
</script>

<template>
  <!--<infoScreen_updater />-->
  <div class="container-fluid">
    <div class="row">
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
    <hr />
    <div class="row">
      <h6>We would like to especially thank the following</h6>
    </div>

    <div
      class="d-flex flex-nowrap overflow-y-auto w-100"
      style="height: calc(100vh - 170px); overflow-x: hidden"
    >
      <div class="row row-cols-1 row-cols-sm-2 row-cols-md-4 row-cols-lg-6">
        <div class="d-inline-block" v-for="card in cards" :key="card.titleName">
          <div class="col">
            <div class="card border-dark m-1" style="max-width: 10rem">
              <img :src="card.imgSrc" class="card-img-top grayscale" />
              <div class="card-body">
                <p class="card-text text-center">{{ card.role }}</p>
              </div>
              <div class="card-footer text-body-secondary text-center">
                <strong>{{ card.titleCall }}</strong>
              </div>
              <div class="card-footer text-body-secondary text-center">
                <strong>{{ card.titleName }}</strong>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style>
.grayscale {
  filter: grayscale(100%);
  transition: filter 0.3s ease-in-out;
}

.grayscale:hover {
  filter: grayscale(0);
}
</style>
