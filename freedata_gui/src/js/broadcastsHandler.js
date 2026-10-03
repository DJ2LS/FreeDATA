import { setActivePinia } from "pinia";
import pinia from "../store/index";
setActivePinia(pinia);

import { useBroadcastStore } from "../store/broadcastStore.js";
import {
  deleteFreedataBroadcastDomain,
  deleteFreedataBroadcastMessage,
  retransmitFreedataBroadcast,
  sendFreedataBroadcastMessage,
} from "@/js/api";
const broadcast = useBroadcastStore(pinia);

/**
 * Maximum broadcast payload in bytes. The server base64-decodes `data` and
 * truncates it to 15 bursts * 26 bytes (freedata_server/command_norm.py),
 * so anything longer would be cut off, possibly in the middle of a tag or a
 * multi-byte UTF-8 character.
 */
export const BROADCAST_MAX_BYTES = 15 * 26; // 390

/**
 * Encode a string as UTF-8 and return the bytes.
 * @param {string} text
 * @returns {Uint8Array}
 */
export function utf8Bytes(text) {
  return new TextEncoder().encode(text || "");
}

/**
 * Encode a (possibly non-Latin-1) string as UTF-8 and return it as base64.
 * btoa() alone throws InvalidCharacterError for characters outside Latin-1.
 * @param {string} text
 * @returns {string}
 */
export function encodeBroadcastText(text) {
  const bytes = utf8Bytes(text);
  let binary = "";
  for (let i = 0; i < bytes.length; i++) {
    binary += String.fromCharCode(bytes[i]);
  }
  return btoa(binary);
}

/**
 * Decode a base64 broadcast payload as UTF-8. Legacy messages that were sent
 * with plain btoa() and are not valid UTF-8 fall back to the latin-1 result.
 * Throws if the input is not valid base64.
 * @param {string} b64
 * @returns {string}
 */
export function decodeBroadcastText(b64) {
  const binary = atob(b64);
  const bytes = new Uint8Array(binary.length);
  for (let i = 0; i < binary.length; i++) {
    bytes[i] = binary.charCodeAt(i);
  }
  try {
    return new TextDecoder("utf-8", { fatal: true }).decode(bytes);
  } catch {
    return binary;
  }
}

export async function processFreedataBroadcastsPerDomain(data) {
  console.log(data);
  broadcast.setBroadcastsForDomain(data);
}

export async function processFreedataDomains(data) {
  console.log(data);

  broadcast.setDomains(data);

  // sum of unread_count
  broadcast.totalUnreadMessages = Object.values(data).reduce(
    (sum, domain) => sum + (domain.unread_count || 0),
    0,
  );
}

export function newBroadcastMessage(params) {
  const result = sendFreedataBroadcastMessage(params);
  broadcast.triggerScrollToBottom();
  return result;
}

export function repeatBroadcastTransmission(id) {
  return retransmitFreedataBroadcast(id);
}

export function deleteBroadcastDomainFromDB(domain) {
  const result = deleteFreedataBroadcastDomain(domain);
  broadcast.selectedDomain = "";
  return result;
}

// Note: there is no ADIF export for broadcasts. The server only offers
// POST /freedata/messages/{id}/adif for P2P messages, so the former
// sendBroadcastADIFviaUDP() (which called a non-existent
// /freedata/broadcasts/{id}/adif) has been removed together with its buttons.

export function deleteBroadcastMessageFromDB(id) {
  return deleteFreedataBroadcastMessage(id);
}
