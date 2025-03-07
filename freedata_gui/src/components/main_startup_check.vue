<template>
   <div
      class="modal modal-lg fade"
      id="modemCheck"
      data-bs-backdrop="static"
      data-bs-keyboard="false"
      tabindex="-1"
      aria-hidden="true"
      >
      <div class="modal-dialog modal-dialog-scrollable">
         <div class="modal-content">
            <div class="modal-header">
               <h1 class="modal-title fs-5">{{ $t('modals.systemcheck') }}</h1>
               <button
                  type="button"
                  class="ms-5 btn btn-secondary"
                  aria-label="Reload GUI"
                  @click="reloadGUI"
                  >
               {{ $t('modals.reloadgui') }}
               </button>
               <button
                  type="button"
                  class="btn-close me-2"
                  data-bs-dismiss="modal"
                  aria-label="Close"
                  ></button>
            </div>
            <div class="modal-body">
               <div class="accordion" id="startupCheckAccordion">
                  <!-- Network Section -->
                  <div class="accordion-item">
                     <h2 class="accordion-header">
                        <button
                           class="accordion-button collapsed"
                           type="button"
                           data-bs-target="#networkStatusCollapse"
                           data-bs-toggle="collapse"
                           >
                        {{ $t('modals.network') }}
                        <span
                           class="badge ms-2"
                           :class="state.modem_connection === 'connected' ? 'bg-success' : 'bg-danger'"
                           >
                        {{ getNetworkState() }}
                        </span>
                        </button>
                     </h2>
                     <div id="networkStatusCollapse" class="accordion-collapse collapse" data-bs-parent="#startupCheckAccordion">
                        <div class="accordion-body">


                        <div class="alert alert-info" role="alert">
                          {{ $t('modals.remoteinfo') }}

</div>

                           <div class="input-group input-group-sm mb-1">
                              <span class="input-group-text w-25">{{ $t('modals.apiurl') }}</span>
                              <input
                                 type="text"
                                 class="form-control"
                                 :value="apiUrl"
                                 disabled
                                 />
                           </div>
                        </div>
                     </div>
                  </div>
                  <!-- Modem Section -->
                  <div class="accordion-item">
                     <h2 class="accordion-header">
                        <button
                           class="accordion-button collapsed"
                           type="button"
                           data-bs-target="#modemStatusCollapse"
                           data-bs-toggle="collapse"
                           >
                        {{ $t('general.modem') }}
                        <span
                           class="badge ms-2"
                           :class="state.is_modem_running ? 'bg-success' : 'bg-danger'"
                           >
                        {{ getModemStateLocal() }}
                        </span>
                        </button>
                     </h2>
                     <div id="modemStatusCollapse" class="accordion-collapse collapse" data-bs-parent="#startupCheckAccordion">
                        <div class="accordion-body">

                          <div class="alert alert-info" role="alert">
                            {{ $t('modals.furthersettings') }}

</div>


                           <!-- Audio Input Device -->
                           <div class="input-group input-group-sm mb-1">
                              <label class="input-group-text w-50">{{ $t('settings.modem.audioinputdevice') }}</label>
                              <select
                                 class="form-select form-select-sm"
                                 aria-label=".form-select-sm"
                                 @change="onChange"
                                 v-model="settings.remote.AUDIO.input_device"
                                 >
                                 <option
                                    v-for="device in audioStore.audioInputs"
                                    :value="device.id"
                                    :key="device.id"
                                    >
                                    {{ device.name }} [{{ device.api }}]
                                 </option>
                              </select>
                           </div>
                           <!-- Audio Output Device -->
                           <div class="input-group input-group-sm mb-1">
                              <label class="input-group-text w-50">{{ $t('settings.modem.audiooutputdevice') }}</label>
                              <select
                                 class="form-select form-select-sm"
                                 aria-label=".form-select-sm"
                                 @change="onChange"
                                 v-model="settings.remote.AUDIO.output_device"
                                 >
                                 <option
                                    v-for="device in audioStore.audioOutputs"
                                    :value="device.id"
                                    :key="device.id"
                                    >
                                    {{ device.name }} [{{ device.api }}]
                                 </option>
                              </select>
                           </div>


                          <div class="alert alert-warning mt-3" role="alert">
{{ $t('modals.restartserveronproblem') }}

</div>
                          <div class="input-group input-group-sm">
                              <label class="input-group-text w-50">{{ $t('modals.manualmodemrestart') }}</label>
                              <label class="input-group-text w-50">
                              <button
                                 type="button"
                                 id="startModem"
                                 class="btn btn-sm btn-outline-secondary w-100"
                                 data-bs-toggle="tooltip"
                                 data-bs-trigger="hover"
                                 data-bs-html="false"
                                 :title=" $t('modals.manualmodemrestart_help')"
                                 @click="reloadModem"
                                 >
                              <i class="bi bi-arrow-clockwise"></i>
                              </button>
                              </label>

                           </div>


                        </div>
                     </div>
                  </div>
                  <!-- Radio Control Section -->
                  <div class="accordion-item">
                     <h2 class="accordion-header">
                        <button
                           class="accordion-button collapsed"
                           type="button"
                           data-bs-target="#radioControlCollapse"
                           data-bs-toggle="collapse"
                           data-bs-parent="#startupCheckAccordion"
                           >
                        {{ $t('modals.radiocontrol') }}
                        <span
                           class="badge ms-2"
                           :class="getRigControlStatus() ? 'bg-success' : 'bg-danger'"
                           >
                        {{ getRigControlStatus() ? i18next.t('grid.components.online') : i18next.t('grid.components.offline') }}
                        </span>
                        </button>
                     </h2>
                     <div id="radioControlCollapse" class="accordion-collapse collapse" data-bs-parent="#startupCheckAccordion">
                        <div class="accordion-body">

                           <div class="alert alert-info" role="alert">
                             {{ $t('modals.radiocontrolinfo') }}
</div>

                           <div class="input-group input-group-sm mb-1">
                              <span class="input-group-text" style="width: 180px">{{ $t('modals.rigcontrolmethod') }}</span>
                              <select
                                 class="form-select form-select-sm"
                                 aria-label=".form-select-sm"
                                 id="rigcontrol_radiocontrol_healthcheck"
                                 @change="onChange"
                                 v-model="settings.remote.RADIO.control"
                                 >
                                 <option value="disabled">Disabled (no rig control; use with VOX)</option>
                                 <option value="serial_ptt">Serial PTT via DTR/RTS</option>
                                 <option value="rigctld">Rigctld (external Hamlib)</option>
                                 <option value="rigctld_bundle">Rigctld (internal Hamlib)</option>
                                 <option value="tci">TCI</option>
                              </select>
                           </div>
                           <!-- Shown when rigctld_bundle is selected -->
                           <div :class="{ 'd-none': settings.remote.RADIO.control !== 'rigctld_bundle' }">
                              <div class="input-group input-group-sm mb-1">
                                 <span class="input-group-text" style="width: 180px"
                                    >{{ $t('modals.radioport') }}</span
                                    >
                                 <select
                                    @change="onChange"
                                    v-model="settings.remote.RADIO.serial_port"
                                    class="form-select form-select-sm"
                                    >
                                    <option
                                       v-for="device in serialStore.serialDevices"
                                       :value="device.port"
                                       :key="device.port"
                                       >
                                       {{ device.description }}
                                    </option>
                                 </select>
                              </div>
                              <!-- Test Hamlib Button -->
                              <div class="input-group input-group-sm mb-1">
                                 <button
                                    type="button"
                                    class="btn btn-sm btn-outline-secondary"
                                    @click="testHamlib"
                                    >
                                 {{ $t('modals.testhamlib') }}
                                 </button>
                              </div>
                           </div>
                        </div>
                     </div>
                  </div>
                  <!-- Info Section -->
                  <div class="accordion-item">
                     <h2 class="accordion-header">
                        <button
                           class="accordion-button collapsed"
                           type="button"
                           data-bs-target="#systemStatusCollapse"
                           data-bs-toggle="collapse"
                           >

                        {{ $t('modals.systeminfo') }}
                        <!--
                        <button type="button" class="btn btn-sm btn-outline-secondary" @click="copyToClipboard">Copy</button>
                        -->

                                                </button>

                     </h2>
                     <div id="systemStatusCollapse" class="accordion-collapse collapse" data-bs-parent="#startupCheckAccordion">
                        <div class="accordion-body">

                           <div class="alert alert-info" role="alert">
                             {{ $t('modals.systeminfoalert') }}

</div>

                            <h3>{{ $t('modals.apiinformation') }}</h3>
                            <p><strong>{{ $t('modals.apiversion') }}:</strong> {{ state.api_version }}</p>
                            <p><strong>{{ $t('modals.modemversion') }}:</strong> {{ state.modem_version }}</p>

                            <h3>{{ $t('modals.osinfo') }}</h3>
                            <p><strong>{{ $t('modals.system') }}:</strong> {{ state.os_info.system }}</p>
                            <p><strong>{{ $t('modals.node') }}:</strong> {{ state.os_info.node }}</p>
                            <p><strong>{{ $t('modals.release') }}:</strong> {{ state.os_info.release }}</p>
                            <p><strong>{{ $t('modals.version') }}:</strong> {{ state.os_info.version }}</p>
                            <p><strong>{{ $t('modals.machine') }}:</strong> {{ state.os_info.machine }}</p>
                            <p><strong>{{ $t('modals.processor') }}:</strong> {{ state.os_info.processor }}</p>

                            <h3>{{ $t('modals.pythoninformation') }}</h3>
                            <p><strong>{{ $t('modals.build') }}:</strong> {{ state.python_info.build.join(' ') }}</p>
                            <p><strong>{{ $t('modals.compiler') }}:</strong> {{ state.python_info.compiler }}</p>
                            <p><strong>{{ $t('modals.branch') }}:</strong> {{ state.python_info.branch || 'N/A' }}</p>
                            <p><strong>{{ $t('modals.implementation') }}:</strong> {{ state.python_info.implementation }}</p>
                            <p><strong>{{ $t('modals.revision') }}:</strong> {{ state.python_info.revision || 'N/A' }}</p>
                            <p><strong>{{ $t('modals.version') }}:</strong> {{ state.python_info.version }}</p>
                        </div>
                     </div>
                  </div>
               </div>
            </div>
         </div>
      </div>
   </div>
</template>

<script setup>
import { Modal } from 'bootstrap/dist/js/bootstrap.esm.min.js';
import { onMounted } from 'vue';

// Pinia setup
import { setActivePinia } from 'pinia';
import pinia from '../store/index';
setActivePinia(pinia);

// Store imports
import { settingsStore as settings, onChange } from '../store/settingsStore.js';
import { sendModemCQ, startModem, stopModem } from '../js/api.js';
import { useStateStore } from '../store/stateStore.js';
import { useAudioStore } from '../store/audioStore';
import { useSerialStore } from '../store/serialStore.js';

// API imports
import { getVersion, getSysInfo } from '../js/api';
import i18next from "@/js/i18n";

// Reactive state
const state = useStateStore(pinia);
const audioStore = useAudioStore(pinia);
const serialStore = useSerialStore(pinia);

// Get the full API URL
const apiUrl = `${window.location.protocol}//${window.location.hostname}:${window.location.port}`;

// Initialize modal on mount
onMounted(() => {
  getSysInfo().then((res) => {
    if (res) {
      state.api_version = res.api_version;
      state.modem_version = res.modem_version;
      state.os_info = res.os_info;
      state.python_info = res.python_info;
    }
  });

  getVersion().then((res) => {
    state.modem_version = res;
  });

  new Modal('#modemCheck', {}).show();
});

/*
const copyToClipboard = () => {
  const info = `
    API Version: ${state.api_version}
    Modem Version: ${state.modem_version}

    Operating System Information:
    System: ${state.os_info.system}
    Node: ${state.os_info.node}
    Release: ${state.os_info.release}
    Version: ${state.os_info.version}
    Machine: ${state.os_info.machine}
    Processor: ${state.os_info.processor}

    Python Information:
    Build: ${state.python_info.build.join(' ')}
    Compiler: ${state.python_info.compiler}
    Branch: ${state.python_info.branch || 'N/A'}
    Implementation: ${state.python_info.implementation}
    Revision: ${state.python_info.revision || 'N/A'}
    Version: ${state.python_info.version}
  `;

  navigator.clipboard.writeText(info).then(() => {
    alert('Information copied to clipboard!');
  });

};
*/

// Helper functions
function getModemStateLocal() {
  return state.is_modem_running ? i18next.t('grid.components.active') : i18next.t('grid.components.inactive')
}

function getNetworkState() {
  return state.modem_connection === 'connected' ? i18next.t('grid.components.connected') : i18next.t('grid.components.disconnected');
}

function getRigControlStatus() {
  switch (settings.remote.RADIO.control) {
    case 'disabled':
      return true;
    case 'serial_ptt':
    case 'rigctld':
    case 'rigctld_bundle':
    case 'tci':
      return state.radio_status;
    default:
      console.error('Unknown radio control mode ' + settings.remote.RADIO.control);
      return 'Unknown control type' + settings.remote.RADIO.control;
  }
}

function testHamlib() {
  sendModemCQ();
}

function reloadGUI() {
  location.reload();
}

function reloadModem(){
  stopModem();
  setTimeout(startModem, 5000); // Executes startModem after 5000 milliseconds as server needs to shutdown first
}

</script>
