// pinia store setup
import { setActivePinia } from "pinia";
import pinia from "../store/index";
setActivePinia(pinia);

import { useEncryptionStore } from "../store/encryptionStore.js";
const encryption = useEncryptionStore(pinia);

import {
  getStationEncryption,
  setStationEncryptionEnabled,
  setStationEncryptionKey,
  deleteStationEncryptionKey,
} from "./api";

export async function loadEncryptionStatus(callsign) {
  if (!callsign) return null;
  const result = await getStationEncryption(callsign);
  if (result) encryption.status[callsign] = result;
  return result;
}

// Opens the encryption dialog for a station.
export function openEncryptionDialog(callsign, reason = "user") {
  encryption.dialogCallsign = callsign;
  encryption.dialogReason = reason;
  encryption.dialogRequest++;
}

// Each function returns {ok, data, error} and updates the stored status.
function storeResult(callsign, result) {
  if (result.ok) encryption.status[callsign] = result.data;
  return result;
}

export async function enableEncryption(callsign, key) {
  // check the key first, so encryption is never on with a rejected key
  const keyResult = await setStationEncryptionKey(callsign, key);
  if (!keyResult.ok) return keyResult;
  const result = storeResult(callsign, await setStationEncryptionEnabled(callsign, true));
  if (result.ok) {
    result.data = {
      ...result.data,
      decrypted: keyResult.data.decrypted,
      requeued: keyResult.data.requeued,
    };
  }
  return result;
}

export async function disableEncryption(callsign) {
  return storeResult(callsign, await setStationEncryptionEnabled(callsign, false));
}

export async function enterEncryptionKey(callsign, key) {
  return storeResult(callsign, await setStationEncryptionKey(callsign, key));
}

export async function forgetEncryptionKey(callsign) {
  return storeResult(callsign, await deleteStationEncryptionKey(callsign));
}

// Random 256 bit key as 64 hex characters, to share with the other operator.
export function generateEncryptionKey() {
  const bytes = new Uint8Array(32);
  crypto.getRandomValues(bytes);
  return Array.from(bytes, (b) => b.toString(16).padStart(2, "0")).join("");
}
