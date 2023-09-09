<script setup lang="ts">

import {saveSettingsToFile} from '../js/settingsHandler'

import { setActivePinia } from 'pinia';
import pinia from '../store/index';
setActivePinia(pinia);

import { useSettingsStore } from '../store/settingsStore.js';
const settings = useSettingsStore(pinia);

import { useStateStore } from '../store/stateStore.js';
const state = useStateStore(pinia);

</script>
<template>

<div class="card mb-1" style="height: 240px">
              <!--325px-->
              <div class="card-header p-1">
                <div class="container">
                  <div class="row">
                    <div class="col-auto">
                      <i
                        class="bi bi-list-columns-reverse"
                        style="font-size: 1.2rem"
                      ></i>
                    </div>
                    <div class="col-10">
                      <strong class="fs-5">Heard stations</strong>
                    </div>
                    <div class="col-1 text-end">
                      <button
                        type="button"
                        id="openHelpModalHeardStations"
                        data-bs-toggle="modal"
                        data-bs-target="#heardStationsHelpModal"
                        class="btn m-0 p-0 border-0"
                      >
                        <i
                          class="bi bi-question-circle"
                          style="font-size: 1rem"
                        ></i>
                      </button>
                    </div>
                  </div>
                </div>
              </div>
              <div class="card-body p-0" style="overflow-y: overlay">
                <div class="table-responsive">
                  <!-- START OF TABLE FOR HEARD STATIONS -->
                  <table class="table table-sm" id="tblHeardStationList">
                    <thead>
                      <tr>
                        <th scope="col" id="thTime">
                          <i id="hslSort" class="bi bi-sort-up"></i>Time
                        </th>
                        <th scope="col" id="thFreq">Frequency</th>
                        <th>&nbsp;</th>
                        <th scope="col" id="thDxcall">DXCall</th>
                        <th scope="col" id="thDxgrid">DXGrid</th>
                        <th scope="col" id="thDist">Distance</th>
                        <th scope="col" id="thType">Type</th>
                        <th scope="col" id="thSnr">SNR (rx/dx)</th>
                        <!--<th scope="col">Off</th>-->
                      </tr>
                    </thead>
                    <tbody id="heardstations">
                    <!--https://vuejs.org/guide/essentials/list.html-->
                     <tr v-for="item in state.heard_stations" :key="item.timestamp">
                        <td>{{ item.timestamp }}</td>
                        <td>{{ item.frequency }}</td>
                        <td>&nbsp;</td>
                        <td>{{ item.dxcallsign }}</td>
                        <td>{{ item.dxgrid }}</td>
                        <td>{{ item.distance }}</td>
                        <td>{{ item.datatype }}</td>
                        <td>{{ item.snr }}</td>
                        <!--<td>{{ item.offset }}</td>-->
                    </tr>
                    </tbody>
                  </table>
                </div>
                <!-- END OF HEARD STATIONS TABLE -->
              </div>
            </div>

</template>