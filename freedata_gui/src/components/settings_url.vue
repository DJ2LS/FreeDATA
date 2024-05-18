<script setup lang="ts">
import { setActivePinia } from "pinia";
import pinia from "../store/index";
setActivePinia(pinia);

function openWebExternal(url:string) {
  open(url);
}
</script>

<template>
  <div class="input-group input-group-sm mb-1">
    <div
        class="btn-toolbar mx-auto"
        role="toolbar"
        aria-label="Toolbar with button groups"
      >
      <div class="btn-group">
          <button
            class="btn btn-secondary bi bi-bookmarks me-2 mt-1"
            id="fdWww"
            data-bs-toggle="tooltip"
            data-bs-trigger="hover"
            title="FreeDATA website"
            role="button"
            @click="openWebExternal('https://freedata.app')"
          >
            FD Website
          </button>
        </div>
        <div class="btn-group">
          <button
            class="btn btn-secondary bi bi-wikipedia me-2 mt-1"
            id="wikiUrl"
            data-bs-toggle="tooltip"
            data-bs-trigger="hover"
            title="Wiki"
            role="button"
            @click="openWebExternal('https://wiki.freedata.app')"
          >
            FD Wiki
          </button>
        </div>
        <div class="btn-group">
          <button
            class="btn btn-sm bi bi-geo-alt btn-secondary me-2 mt-1"
            id="openExplorer"
            type="button"
            data-bs-placement="bottom"
            @click="openWebExternal('https://explorer.freedata.app')"
          >
            FD Explorer map
          </button>
        </div>
        <div class="btn-group">
          <button
            class="btn btn-sm btn-secondary me-2 bi bi-graph-up mt-1"
            id="btnStats"
            type="button"
            data-bs-placement="bottom"
            @click="openWebExternal('https://statistics.freedata.app/')"
          >
            FD Statistics
          </button>
        </div>

        <div class="btn-group">
          <button
            class="btn btn-secondary bi bi-github me-2 mt-1"
            id="ghUrl"
            data-bs-toggle="tooltip"
            data-bs-trigger="hover"
            title="Github"
            role="button"
            @click="openWebExternal('https://github.com/dj2ls')"
          >
            DJ2LS's Github
          </button>
        </div>

        <div class="btn-group">
          <button
            class="btn btn-secondary bi bi-discord mt-1"
            id="discordUrl"
            data-bs-toggle="tooltip"
            data-bs-trigger="hover"
            title="Discord"
            role="button"
            @click="openWebExternal('https://discord.freedata.app')"
          >
            FD Discord
          </button>
        </div>
      </div>
  </div>
</template>
