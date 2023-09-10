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
        <div class=" mb-3">
                 <div class="card mb-1">
              <div class="card-header p-1">



              <div class="container">
                  <div class="row">
                    <div class="col-1">
                      <i class="bi bi-house-door" style="font-size: 1.2rem"></i>
                    </div>
                    <div class="col-10">
              <strong class="fs-5">Radio control</strong>
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
    <span class="input-group-text">Frequency</span>
    <input type="text" class="form-control" v-model="state.frequency" style="max-width: 8rem;"
                        pattern="[0-9]*">
        <span class="input-group-text" >Hz</span>

  </div>
</div>

                <div class="me-2">
  <div class="input-group">
    <span class="input-group-text" >Mode</span>
<select class="form-control"  v-model="settings.hamlib_rigctld_ip">
  <option value="USB">USB</option>
  <option value="LSB">LSB</option>
  <option value="AM">AM</option>
  <option value="FM">FM</option>
</select>

  </div>
</div>



                <div class="me-2">
  <div class="input-group">
    <span class="input-group-text" >Bandwidth</span>
<select class="form-control">
  <option>500</option>
  <option>1000</option>
  <option>1500</option>
  <option>2000</option>
</select>
    <span class="input-group-text" >Hz</span>

  </div>
</div>

                <div class="me-2">
  <div class="input-group">
    <span class="input-group-text" >Power</span>
<select class="form-control">
  <option>10</option>
  <option>20</option>
  <option>30</option>
  <option>40</option>
  <option>50</option>
  <option>60</option>
  <option>70</option>
  <option>80</option>
  <option>90</option>
  <option>100</option>




</select>
    <span class="input-group-text" >%</span>


  </div>
</div>






            </div>



























                 </div>
                 </div></div>
</template>