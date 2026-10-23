<script setup>
// Dialog to turn encryption for a station on or off and to enter its key.
// Opened from the lock button in the chat header, or by the server when a
// key is needed to send or decrypt a message (see encryptionHandler.js).
import { ref, computed, watch, onMounted } from "vue";
import { Modal } from "bootstrap/dist/js/bootstrap.esm.min.js";

import { setActivePinia } from "pinia";
import pinia from "../store/index";
import { useEncryptionStore } from "../store/encryptionStore.js";
import {
  loadEncryptionStatus,
  enableEncryption,
  disableEncryption,
  enterEncryptionKey,
  forgetEncryptionKey,
  generateEncryptionKey,
} from "../js/encryptionHandler";

setActivePinia(pinia);
const encryption = useEncryptionStore(pinia);

const modalElement = ref(null);
let modal = null;

const keyInput = ref("");
const showKey = ref(false);
const legalConfirmed = ref(false);
const error = ref("");
const notice = ref("");
const busy = ref(false);

const callsign = computed(() => encryption.dialogCallsign);
const status = computed(() => encryption.status[callsign.value] || null);
const enabled = computed(() => !!status.value?.enabled);
const keyLoaded = computed(() => !!status.value?.key_loaded);

function resetForm() {
  keyInput.value = "";
  showKey.value = false;
  legalConfirmed.value = false;
  error.value = "";
  notice.value = "";
}

onMounted(() => {
  modal = new Modal(modalElement.value, {});
});

watch(
  () => encryption.dialogRequest,
  async () => {
    resetForm();
    await loadEncryptionStatus(callsign.value);
    modal?.show();
  },
);

function generateKey() {
  keyInput.value = generateEncryptionKey();
  showKey.value = true;
}

async function run(action, successNotice) {
  busy.value = true;
  error.value = "";
  notice.value = "";
  try {
    const result = await action();
    if (!result.ok) {
      error.value = result.error;
      return;
    }
    keyInput.value = "";
    showKey.value = false;
    notice.value = successNotice(result.data);
  } finally {
    busy.value = false;
  }
}

// notice lines are [translation key, parameters]
function keyResultNotice(data) {
  const lines = [["chat.encryption.keysaved", {}]];
  if (data?.decrypted) lines.push(["chat.encryption.decrypted", { n: data.decrypted }]);
  if (data?.requeued) lines.push(["chat.encryption.requeued", { n: data.requeued }]);
  return lines;
}

function enable() {
  run(() => enableEncryption(callsign.value, keyInput.value), keyResultNotice);
}

function saveKey() {
  run(() => enterEncryptionKey(callsign.value, keyInput.value), keyResultNotice);
}

function forgetKey() {
  run(() => forgetEncryptionKey(callsign.value), () => [["chat.encryption.keyforgotten", {}]]);
}

function disable() {
  run(() => disableEncryption(callsign.value), () => [["chat.encryption.disabled", {}]]);
}
</script>

<template>
  <div
    id="encryptionModal"
    ref="modalElement"
    class="modal fade"
    tabindex="-1"
    aria-labelledby="encryptionModalLabel"
    aria-hidden="true"
  >
    <div class="modal-dialog modal-dialog-scrollable">
      <div class="modal-content">
        <div class="modal-header">
          <h1
            id="encryptionModalLabel"
            class="modal-title fs-5"
          >
            <i class="bi bi-lock me-1" />
            {{ $t('chat.encryption.title') }} – {{ callsign }}
          </h1>
          <button
            type="button"
            class="btn-close"
            data-bs-dismiss="modal"
            aria-label="Close"
          />
        </div>

        <div class="modal-body">
          <!-- why the dialog was opened by the server -->
          <div
            v-if="['send', 'receive', 'wrong_key'].includes(encryption.dialogReason) && !notice"
            class="alert alert-warning py-2"
          >
            {{ $t(`chat.encryption.reason_${encryption.dialogReason}`) }}
          </div>

          <!-- status -->
          <ul
            v-if="status"
            class="list-group mb-3"
          >
            <li class="list-group-item d-flex justify-content-between">
              {{ $t('chat.encryption.state') }}
              <span
                class="badge"
                :class="enabled ? 'text-bg-success' : 'text-bg-secondary'"
              >
                {{ enabled ? $t('chat.encryption.on') : $t('chat.encryption.off') }}
              </span>
            </li>
            <li class="list-group-item d-flex justify-content-between">
              {{ $t('chat.encryption.key') }}
              <span
                v-if="keyLoaded"
                class="font-monospace"
                :title="$t('chat.encryption.fingerprint_help')"
              >
                <i class="bi bi-fingerprint" /> {{ status.fingerprint }}
              </span>
              <span
                v-else
                class="badge text-bg-warning"
              >{{ $t('chat.encryption.nokey') }}</span>
            </li>
            <li
              v-if="status.pending_received"
              class="list-group-item d-flex justify-content-between"
            >
              {{ $t('chat.encryption.pending_received') }}
              <span class="badge text-bg-warning">{{ status.pending_received }}</span>
            </li>
            <li
              v-if="status.waiting_to_send"
              class="list-group-item d-flex justify-content-between"
            >
              {{ $t('chat.encryption.waiting_to_send') }}
              <span class="badge text-bg-warning">{{ status.waiting_to_send }}</span>
            </li>
          </ul>

          <!-- legal warning, always shown before turning encryption on -->
          <div
            v-if="!enabled"
            class="alert alert-danger"
          >
            <strong><i class="bi bi-exclamation-triangle-fill me-1" />{{ $t('chat.encryption.legal_title') }}</strong>
            <p class="mb-2 mt-1 small">
              {{ $t('chat.encryption.legal_text') }}
            </p>
            <div class="form-check">
              <input
                id="encryptionLegalConfirm"
                v-model="legalConfirmed"
                class="form-check-input"
                type="checkbox"
              >
              <label
                class="form-check-label small"
                for="encryptionLegalConfirm"
              >
                {{ $t('chat.encryption.legal_confirm') }}
              </label>
            </div>
          </div>

          <!-- key entry -->
          <div v-if="!enabled || !keyLoaded || status?.pending_received">
            <label
              for="encryptionKeyInput"
              class="form-label"
            >{{ $t('chat.encryption.keylabel') }}</label>
            <div class="input-group">
              <input
                id="encryptionKeyInput"
                v-model="keyInput"
                :type="showKey ? 'text' : 'password'"
                class="form-control font-monospace"
                autocomplete="off"
                spellcheck="false"
                :placeholder="$t('chat.encryption.keyplaceholder')"
                @keyup.enter="enabled || status?.pending_received ? saveKey() : (legalConfirmed && enable())"
              >
              <button
                class="btn btn-outline-secondary"
                type="button"
                :title="$t('chat.encryption.showkey')"
                @click="showKey = !showKey"
              >
                <i :class="showKey ? 'bi bi-eye-slash' : 'bi bi-eye'" />
              </button>
              <button
                v-if="!enabled"
                class="btn btn-outline-secondary"
                type="button"
                @click="generateKey"
              >
                <i class="bi bi-shuffle me-1" />{{ $t('chat.encryption.generate') }}
              </button>
            </div>
            <div class="form-text">
              {{ $t('chat.encryption.keyhelp') }}
            </div>
          </div>

          <div
            v-if="error"
            class="alert alert-danger py-2 mt-3 mb-0"
          >
            {{ error }}
          </div>
          <div
            v-if="notice"
            class="alert alert-success py-2 mt-3 mb-0"
          >
            <span
              v-for="[line, params] in notice"
              :key="line"
              class="d-block"
            >{{ $t(line, params) }}</span>
          </div>
        </div>

        <div class="modal-footer">
          <button
            v-if="enabled && keyLoaded"
            type="button"
            class="btn btn-outline-secondary me-auto"
            :disabled="busy"
            @click="forgetKey"
          >
            {{ $t('chat.encryption.forgetkey') }}
          </button>
          <button
            v-if="enabled"
            type="button"
            class="btn btn-outline-danger"
            :disabled="busy"
            @click="disable"
          >
            <i class="bi bi-unlock me-1" />{{ $t('chat.encryption.disable') }}
          </button>
          <!-- decrypting received messages works without turning on encrypted sending -->
          <button
            v-if="status?.pending_received || (enabled && !keyLoaded)"
            type="button"
            class="btn btn-primary"
            :disabled="busy || !keyInput"
            @click="saveKey"
          >
            {{ $t('chat.encryption.savekey') }}
          </button>
          <button
            v-if="!enabled"
            type="button"
            class="btn btn-danger"
            :disabled="busy || !keyInput || !legalConfirmed"
            @click="enable"
          >
            <i class="bi bi-lock-fill me-1" />{{ $t('chat.encryption.enable') }}
          </button>
          <button
            type="button"
            class="btn btn-secondary"
            data-bs-dismiss="modal"
          >
            {{ $t('chat.encryption.close') }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>
