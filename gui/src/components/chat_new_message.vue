<script setup lang="ts">
// @ts-nocheck

import { setActivePinia } from 'pinia';
import pinia from '../store/index';
setActivePinia(pinia);


import { useStateStore } from '../store/stateStore.js';
const state = useStateStore(pinia);

import { useChatStore } from '../store/chatStore.js';
const chat = useChatStore(pinia);


import chat_navbar from './chat_navbar.vue'
import chat_conversations from './chat_conversations.vue'
import chat_messages from './chat_messages.vue'

import {updateAllChat, newMessage, newBroadcast} from '../js/chatHandler'


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


import { VuemojiPicker, EmojiClickEventDetail } from 'vuemoji-picker'

const handleEmojiClick = (detail: EmojiClickEventDetail) => {
chat.inputText += detail.unicode

}


const chatModuleMessage=ref(null);




function transmitNewMessage(){

    chat.inputText = chat.inputText.trim();
    if (chat.inputText.length==0)
      return;
    if (chat.selectedCallsign.startsWith("BC-")) {

        newBroadcast(chat.selectedCallsign, chat.inputText)

    } else {
        newMessage(chat.selectedCallsign, chat.inputText, chat.inputFile, chat.inputFileName, chat.inputFileSize, chat.inputFileType)
    }
    // finally do a cleanup
    //chatModuleMessage.reset();
    chat.inputText = '';
    chatModuleMessage.value="";
    // @ts-expect-error
    resetFile()
}

function resetFile(event){
    chat.inputFileName = '-'
    chat.inputFileSize = '-'
    chat.inputFileType = '-'

}


function readFile(event) {
    const reader = new FileReader();

    reader.onload = () => {
        console.log(reader.result);
        chat.inputFileName = event.target.files[0].name
        chat.inputFileSize = event.target.files[0].size
        chat.inputFileType = event.target.files[0].type

        chat.inputFile = reader.result
        calculateTimeNeeded()

//        String.fromCharCode.apply(null, Array.from(chatFile))


      };

    reader.readAsArrayBuffer(event.target.files[0]);

}



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

                            <button type="button" class="btn btn-outline-secondary border-0 rounded-pill me-1"
                            data-bs-toggle="modal" data-bs-target="#emojiPickerModal"
                            data-bs-backdrop="false"
                            >
                                <i
                                  id="emojipickerbutton"
                                  class="bi bi-emoji-smile p-0"
                                  style="font-size: 1rem"
                                ></i>
                            </button>



                                        <!-- trigger file selection modal -->
                            <button type="button" class="btn btn-outline-secondary border-0 rounded-pill me-1" data-bs-toggle="modal" data-bs-target="#fileSelectionModal">
                              <i class="bi bi-paperclip" style="font-size: 1.2rem"></i>
                            </button>


                          <textarea
                            class="form-control border rounded-pill"
                            rows="1"
                            ref="chatModuleMessage"
                            placeholder="Message - Send with [Enter]"
                            v-model="chat.inputText"
                            @keyup.enter.exact="transmitNewMessage()"
                          ></textarea>




                            <button
                              class="btn btn-sm btn-secondary ms-1 me-2 rounded-pill"
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
        <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close" @click="resetFile"></button>
      </div>
      <div class="modal-body">


     <div class="alert alert-warning d-flex align-items-center" role="alert">
 <i class="bi bi-exclamation-triangle-fill ms-2 me-2"></i>
  <div>
    Transmission speed over HF channels is very limited!
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

<Line :data="speedChartData" />

      </div>
      <div class="modal-footer">
        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal" @click="resetFile">Reset</button>
        <button type="button" class="btn btn-primary" data-bs-dismiss="modal">Append</button>
      </div>
    </div>
  </div>
                </div>

<!-- Emoji Picker Modal -->
<div class="modal fade" id="emojiPickerModal" tabindex="-1" aria-hidden="true">
  <div class="modal-dialog modal-dialog-centered modal-sm">
    <div class="modal-content">
      <div class="modal-body p-0">
        <VuemojiPicker @emojiClick="handleEmojiClick" />
      </div>
    </div>
  </div>
</div>





</template>

