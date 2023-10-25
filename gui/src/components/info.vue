<script setup lang="ts">
import { setActivePinia } from "pinia";
import pinia from "../store/index";
setActivePinia(pinia);

import { useStateStore } from "../store/stateStore.js";
const state = useStateStore(pinia);

const version = import.meta.env.PACKAGE_VERSION;

function openWebExternal(url) {
  open(url);
}
</script>


<template>
 <h3 class="m-2">
              <span class="badge bg-secondary">FreeDATA: {{ version }}</span>
              <span class="ms-2 badge bg-secondary">Modem: {{ state.modem_version }}</span>
            </h3>

            <div class="container-fluid">
              <div class="row mt-2">

<hr>
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
                      @click="
                        openWebExternal('https://statistics.freedata.app/')
                      "
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
                      @click="
                        openWebExternal('https://github.com/dj2ls/freedata')
                      "
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



<div class="row row-cols-1 row-cols-md-3 g-4 scrollable-row">
  <div class="col">
    <div class="card border-dark mb-3" style="max-width: 18rem;">
  <div class="card-header">DJ2LS</div>
  <div class="card-body">
    <h5 class="card-title">Dark card title</h5>
    <p class="card-text">Some quick example text to build on the card title and make up the bulk of the card's content.</p>
  </div>
  <div class="card-footer text-body-secondary">
    Core developer
  </div>
</div>
  </div>
  <div class="col">
    <div class="card border-dark mb-3" style="max-width: 18rem;">
  <div class="card-header">Header</div>
  <div class="card-body">
    <h5 class="card-title">Dark card title</h5>
    <p class="card-text">Some quick example text to build on the card title and make up the bulk of the card's content.</p>
  </div>
  <div class="card-footer text-body-secondary">
    2 days ago
  </div>
</div>
  </div>
  <div class="col">
    <div class="card border-dark mb-3" style="max-width: 18rem;">
  <div class="card-header">Header</div>
  <div class="card-body">
    <h5 class="card-title">Dark card title</h5>
    <p class="card-text">Some quick example text to build on the card title and make up the bulk of the card's content.</p>
  </div>
  <div class="card-footer text-body-secondary">
    2 days ago
  </div>
</div>
  </div>
  <div class="col">
    <div class="card border-dark mb-3" style="max-width: 18rem;">
  <div class="card-header">Header</div>
  <div class="card-body">
    <h5 class="card-title">Dark card title</h5>
    <p class="card-text">Some quick example text to build on the card title and make up the bulk of the card's content.</p>
  </div>
  <div class="card-footer text-body-secondary">
    2 days ago
  </div>
</div>
  </div>

  <div class="col">
    <div class="card border-dark mb-3" style="max-width: 18rem;">
  <div class="card-header">Header</div>
  <div class="card-body">
    <h5 class="card-title">Dark card title</h5>
    <p class="card-text">Some quick example text to build on the card title and make up the bulk of the card's content.</p>
  </div>
  <div class="card-footer text-body-secondary">
    2 days ago
  </div>
</div>
  </div>

    <div class="col">
    <div class="card border-dark mb-3" style="max-width: 18rem;">
  <div class="card-header">Header</div>
  <div class="card-body">
    <h5 class="card-title">Dark card title</h5>
    <p class="card-text">Some quick example text to build on the card title and make up the bulk of the card's content.</p>
  </div>
  <div class="card-footer text-body-secondary">
    2 days ago
  </div>
</div>
  </div>

    <div class="col">
    <div class="card border-dark mb-3" style="max-width: 18rem;">
  <div class="card-header">Header</div>
  <div class="card-body">
    <h5 class="card-title">Dark card title</h5>
    <p class="card-text">Some quick example text to build on the card title and make up the bulk of the card's content.</p>
  </div>
  <div class="card-footer text-body-secondary">
    2 days ago
  </div>
</div>
  </div>

    <div class="col">
    <div class="card border-dark mb-3" style="max-width: 18rem;">
  <div class="card-header">Header</div>
  <div class="card-body">
    <h5 class="card-title">Dark card title</h5>
    <p class="card-text">Some quick example text to build on the card title and make up the bulk of the card's content.</p>
  </div>
  <div class="card-footer text-body-secondary">
    2 days ago
  </div>
</div>
  </div>

    <div class="col">
    <div class="card border-dark mb-3" style="max-width: 18rem;">
  <div class="card-header">Header</div>
  <div class="card-body">
    <h5 class="card-title">Dark card title</h5>
    <p class="card-text">Some quick example text to build on the card title and make up the bulk of the card's content.</p>
  </div>
  <div class="card-footer text-body-secondary">
    2 days ago
  </div>
</div>
  </div>

    <div class="col">
    <div class="card border-dark mb-3" style="max-width: 18rem;">
  <div class="card-header">Header</div>
  <div class="card-body">
    <h5 class="card-title">Dark card title</h5>
    <p class="card-text">Some quick example text to build on the card title and make up the bulk of the card's content.</p>
  </div>
  <div class="card-footer text-body-secondary">
    2 days ago
  </div>
</div>
  </div>

    <div class="col">
    <div class="card border-dark mb-3" style="max-width: 18rem;">
  <div class="card-header">Header</div>
  <div class="card-body">
    <h5 class="card-title">Dark card title</h5>
    <p class="card-text">Some quick example text to build on the card title and make up the bulk of the card's content.</p>
  </div>
  <div class="card-footer text-body-secondary">
    2 days ago
  </div>
</div>
  </div>






</div>
            </div>
</template>



