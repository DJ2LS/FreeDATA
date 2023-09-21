<script setup lang="ts">


import {saveSettingsToFile} from '../js/settingsHandler';

import { setActivePinia } from 'pinia';
import pinia from '../store/index';
setActivePinia(pinia);

import { useSettingsStore } from '../store/settingsStore.js';
const settings = useSettingsStore(pinia);

import { useStateStore } from '../store/stateStore.js';
const state = useStateStore(pinia);

import { useChatStore } from '../store/chatStore.js';
const chat = useChatStore(pinia);


import chat_navbar from './chat_navbar.vue'
import chat_conversations from './chat_conversations.vue'
import chat_messages from './chat_messages.vue'

import {updateAllChat, newMessage} from '../js/chatHandler'






function transmitNewMessage(){
    newMessage(chat.selectedCallsign, chat.inputText)

    // finally do a cleanup
    chat.inputText = ''

    chat.inputFileName = ''
    chat.inputFileSize = ''
    chat.inputFileType = ''

    const reader = new FileReader();
    chat.inputFile = reader.readAsArrayBuffer(event.target.files[0]);

}


function readFile(event) {

    console.log(event.target.files);
    chat.inputFileName = event.target.files[0].name
    chat.inputFileSize = event.target.files[0].size
    chat.inputFileType = event.target.files[0].type

    const reader = new FileReader();
    chat.inputFile = reader.readAsArrayBuffer(event.target.files[0]);

    calculateTimeNeeded()


  reader.onload = function() {
    console.log(reader.result);
  };

  reader.onerror = function() {
    console.log(reader.error);
  };
}



</script>

<script lang="ts">

import { setActivePinia } from 'pinia';
import pinia from '../store/index';
setActivePinia(pinia);

import { useSettingsStore } from '../store/settingsStore.js';
const settings = useSettingsStore(pinia);

import { useStateStore } from '../store/stateStore.js';
const state = useStateStore(pinia);

import { useChatStore } from '../store/chatStore.js';
const chat = useChatStore(pinia);


import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend
} from 'chart.js'
import { Line } from 'vue-chartjs'

import { ref, computed } from 'vue';



ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend
)




// calculate time needed for transmitting a file
function calculateTimeNeeded(){

    var calculatedSpeedPerMinutePER0 = []
    var calculatedSpeedPerMinutePER25 = []
    var calculatedSpeedPerMinutePER75 = []

    // bpm vs snr with PER == 0
    var snrList = [
       {snr: -10, bpm: 100},
       {snr: -5, bpm: 300},
       {snr: 0, bpm: 800},
       {snr: 5, bpm: 2500},
       {snr: 10, bpm: 5300}
    ];

    for (let i = 0; i < snrList.length; i++) {

          var result = snrList.find(obj => {
            return obj.snr === snrList[i].snr
          })

        calculatedSpeedPerMinutePER0.push(chat.inputFileSize / result.bpm)
        calculatedSpeedPerMinutePER25.push(chat.inputFileSize / (result.bpm * 0.75))
        calculatedSpeedPerMinutePER75.push(chat.inputFileSize / (result.bpm * 0.25))

    }

    chat.chartSpeedPER0 = calculatedSpeedPerMinutePER0
    chat.chartSpeedPER25 = calculatedSpeedPerMinutePER25
    chat.chartSpeedPER75 = calculatedSpeedPerMinutePER75

}


const speedChartData = computed(() => ({
 labels: ['-10', '-5', '0', '5', '10'],
  datasets: [
    { data: chat.chartSpeedPER0, label: 'PER 0%' ,tension: 0.1, borderColor: 'rgb(0, 255, 0)' },
    { data: chat.chartSpeedPER25, label: 'PER 25%' ,tension: 0.1, borderColor: 'rgb(255, 255, 0)'},
    { data: chat.chartSpeedPER75, label: 'PER 75%' ,tension: 0.1, borderColor: 'rgb(255, 0, 0)' }
  ]
}


));
</script>


<template>

<div class="container-fluid mt-2 p-0">
                        <input
                          type="checkbox"
                          id="expand_textarea"
                          class="btn-check"
                          autocomplete="off"
                        />
                        <label
                          class="btn d-flex justify-content-center"
                          id="expand_textarea_label"
                          for="expand_textarea"
                          ><i
                            id="expand_textarea_button"
                            class="bi bi-chevron-compact-up"
                          ></i
                        ></label>

                        <div class="input-group bottom-0 ms-2">
                          <!--<input class="form-control" maxlength="8" style="max-width: 6rem; text-transform:uppercase; display:none" id="chatModuleDxCall" placeholder="DX CALL"></input>-->
                          <!--<button class="btn btn-sm btn-primary me-2" id="emojipickerbutton" type="button">-->
                          <div class="input-group-text">
                            <i
                              id="emojipickerbutton"
                              class="bi bi-emoji-smile p-0"
                              style="font-size: 1rem"
                            ></i>
                          </div>

                          <textarea
                            class="form-control"
                            rows="1"
                            id="chatModuleMessage"
                            placeholder="Message - Send with [Enter]"
                            v-model="chat.inputText"
                          ></textarea>


                            <!-- trigger file selection modal -->
                            <button type="button" class="btn btn-outline-secondary" data-bs-toggle="modal" data-bs-target="#fileSelectionModal">
                              <i class="bi bi-paperclip" style="font-size: 1.2rem"></i>
                            </button>


                            <button
                              class="btn btn-sm btn-secondary me-2"
                              @click="transmitNewMessage()"
                              type="button"
                            >
                              <i
                                class="bi bi-send ms-4 me-4"
                                style="font-size: 1.2rem"
                              ></i>
                            </button>

                        </div>
                      </div>




                      <!-- select file modal -->

                <div
                  class="modal fade"
                  id="fileSelectionModal"
                  tabindex="-1"
                  aria-labelledby="fileSelectionModalLabel"
                  aria-hidden="true"
                >

                <div class="modal-dialog">
    <div class="modal-content">
      <div class="modal-header">
        <h5 class="modal-title" id="staticBackdropLabel">File Attachment</h5>
        <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
      </div>
      <div class="modal-body">


     <div class="alert alert-warning d-flex align-items-center" role="alert">
 <i class="bi bi-exclamation-triangle-fill ms-2 me-2"></i>
  <div>
    Please keep in mind, transmission speed is limited on HF channels when selecting a file.
  </div>
</div>

           <div class="input-group-text mb-3">
                <input class="" type="file" ref="doc" @change="readFile" />
           </div>



<div class="btn-group me-2" role="group" aria-label="Basic outlined example">
  <button type="button" class="btn btn-secondary">Type</button>
  <button type="button" class="btn btn-secondary disabled">{{chat.inputFileType}}</button>
</div>

<div class="btn-group me-2" role="group" aria-label="Basic outlined example">
  <button type="button" class="btn btn-secondary">Size</button>
  <button type="button" class="btn btn-secondary disabled">{{chat.inputFileSize}}</button>
</div>

<Line :data="speedChartData" :options="speedChartOptions" />

      </div>
      <div class="modal-footer">
        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Reset</button>
        <button type="button" class="btn btn-primary">Append</button>
      </div>
    </div>
  </div>
                </div>


</template>