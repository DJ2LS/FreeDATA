<script setup lang="ts">
import { setActivePinia } from "pinia";
import pinia from "../store/index";
setActivePinia(pinia);

import { settingsStore as settings } from "../store/settingsStore.js";


</script>

<template>
  <div class="card mb-1">
    <div class="card-header p-1">
      <div class="container">
        <div class="row">
          <div class="col-1">
            <i class="bi bi-house-door" style="font-size: 1.2rem"></i>
          </div>
          <div class="col-10">
            <strong class="fs-5">My station</strong>
          </div>
          <div class="col-1 text-end">
            <button
              type="button"
              id="openHelpModalStation"
              data-bs-toggle="modal"
              data-bs-target="#stationHelpModal"
              class="btn m-0 p-0 border-0"
            >
              <i class="bi bi-question-circle" style="font-size: 1rem"></i>
            </button>
          </div>
        </div>
      </div>
    </div>
    <div class="card-body p-2">
      <div class="row">
        <div class="col-md-auto">
          <div
            class="input-group input-group-sm mb-0"
            data-bs-placement="bottom"
            data-bs-toggle="tooltip"
            data-bs-trigger="hover"
            data-bs-html="false"
            title="Enter your callsign and save it"
          >
            <span class="input-group-text">
              <i class="bi bi-person-bounding-box" style="font-size: 1rem"></i>
            </span>
            <input
              type="text"
              class="form-control"
              style="width: 5rem; text-transform: uppercase"
              placeholder="callsign"
              pattern="[A-Z]*"
              id="myCall"
              maxlength="8"
              aria-label="Input group"
              aria-describedby="btnGroupAddon"
              v-model="settings.remote.STATION.mycall"
            />
            <select
              class="form-select form-select-sm"
              aria-label=".form-select-sm"
              id="myCallSSID"
              v-model="settings.remote.STATION.myssid"
            >
              <option selected value="0">0</option>
              <option value="1">1</option>
              <option value="2">2</option>
              <option value="3">3</option>
              <option value="4">4</option>
              <option value="5">5</option>
              <option value="6">6</option>
              <option value="7">7</option>
              <option value="8">8</option>
              <option value="9">9</option>
              <option value="10">10</option>
              <option value="11">11</option>
              <option value="12">12</option>
              <option value="13">13</option>
              <option value="14">14</option>
              <option value="15">15</option>
            </select>
          </div>
        </div>
        <div class="col-md-auto">
          <div
            class="input-group input-group-sm mb-0"
            data-bs-placement="bottom"
            data-bs-toggle="tooltip"
            data-bs-trigger="hover"
            data-bs-html="false"
            title="Enter your gridsquare and save it"
          >
            <span class="input-group-text">
              <i class="bi bi-house-fill" style="font-size: 1rem"></i>
            </span>
            <input
              type="text"
              class="form-control mr-1"
              style="max-width: 6rem"
              placeholder="locator"
              id="myGrid"
              maxlength="6"
              aria-label="Input group"
              aria-describedby="btnGroupAddon"
              v-model="settings.remote.STATION.mygrid"
            />
          </div>
        </div>
      </div>
      <!-- end of row-->
    </div>
  </div>
</template>
