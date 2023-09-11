<script setup lang="ts">

import {saveSettingsToFile} from '../js/settingsHandler'

import { setActivePinia } from 'pinia';
import pinia from '../store/index';
setActivePinia(pinia);

import { useSettingsStore } from '../store/settingsStore.js';
const settings = useSettingsStore(pinia);

import { useStateStore } from '../store/stateStore.js';
const state = useStateStore(pinia);

import {set_frequency, set_mode} from '../js/sock.js'


function set_hamlib_frequency(){
    set_frequency(state.new_frequency)
}

function set_hamlib_mode(){
    set_mode(state.mode)
}

function set_hamlib_rf_level(){
    set_rf_level(state.rf_level)
}

</script>


<template>
        <div class=" mb-3">
                 <div class="card mb-1">
              <div class="card-header p-1">



              <div class="container">
                  <div class="row">
                    <div class="col-1">
                      <i class="bi bi-house-door" style="font-size: 1.2rem"></i>
                    </div>
                    <div class="col-10">
              <strong class="fs-5 me-2">Radio control</strong> <span class="badge" v-bind:class="{ 'text-bg-success' : state.hamlib_status === 'connected',
                                'text-bg-danger disabled' : state.hamlib_status === 'disconnected'}">{{state.hamlib_status}}</span>
                    </div>
                    <div class="col-1 text-end">
                      <button
                        type="button"
                        id="openHelpModalStation"
                        data-bs-toggle="modal"
                        data-bs-target="#stationHelpModal"
                        class="btn m-0 p-0 border-0"
                        disabled
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
                 <div class="card-body p-2">




                <div class="input-group bottom-0 m-0">


                <div class="me-2">
  <div class="input-group">
    <span class="input-group-text">QRG</span>
    <span class="input-group-text">{{state.frequency}} Hz</span>
    <span class="input-group-text">QSY</span>
    <input type="text" class="form-control" v-model="state.new_frequency" style="max-width: 8rem;"
                        pattern="[0-9]*" list="frequencyDataList" v-bind:class="{ 'disabled' : state.hamlib_status === 'disconnected'}">

                  <datalist id="frequencyDataList">
                    <option selected value="7053000">40m | USB | EU, US</option>
                    <option value="14093000">20m | USB | EU, US</option>
                    <option value="21093000">15m | USB | EU, US</option>
                    <option value="24908000">12m | USB | EU, US</option>
                    <option value="28093000">10m | USB | EU, US</option>
                    <option value="50308000">6m | USB | US</option>
                    <option value="50616000">6m | USB | EU, US</option>
                   </datalist>
    <button class="btn btn-sm btn-outline-success" type="button" @click="set_hamlib_frequency" v-bind:class="{ 'disabled' : state.hamlib_status === 'disconnected'}">Apply</button>
  </div>
</div>

                <div class="me-2">
  <div class="input-group">
    <span class="input-group-text" >Mode</span>
<select class="form-control"  v-model="state.mode" @click="set_hamlib_mode()" v-bind:class="{ 'disabled' : state.hamlib_status === 'disconnected'}">
  <option value="USB">USB</option>
  <option value="LSB">LSB</option>
  <option value="AM">AM</option>
  <option value="FM">FM</option>
</select>

  </div>
</div>




                <div class="me-2">
  <div class="input-group">
    <span class="input-group-text" >Power</span>
        <select class="form-control" v-model="state.rf_level" @click="set_hamlib_rf_level()" v-bind:class="{ 'disabled' : state.hamlib_status === 'disconnected'}">
          <option value="0">-</option>
          <option value="10">10</option>
          <option value="20">20</option>
          <option value="30">30</option>
          <option value="40">40</option>
          <option value="50">50</option>
          <option value="60">60</option>
          <option value="70">70</option>
          <option value="80">80</option>
          <option value="90">90</option>
          <option value="100">100</option>
        </select>
    <span class="input-group-text" >%</span>


  </div>
</div>






            </div>



























                 </div>
                 </div></div>
</template>