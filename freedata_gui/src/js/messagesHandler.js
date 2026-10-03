import { setActivePinia } from "pinia";
import pinia from "../store/index";
setActivePinia(pinia);

import { useChatStore } from "../store/chatStore.js";
const chatStore = useChatStore(pinia);

import {
  sendFreedataMessage,
  deleteFreedataMessage,
  retransmitFreedataMessage,
  getFreedataAttachmentBySha512,
  getFreedataMessageById,
  postFreedataMessageADIF,
  getBeaconDataByCallsign,
} from "./api";
import { displayToast, escapeHtml } from "./popupHandler";
import { useIsMobile } from "@/js/mobile_devices";
const { isMobile } = useIsMobile(768);

// Statuses for which the server refuses to delete a message (HTTP 409)
const UNDELETABLE_STATUSES = ["queued", "transmitting"];

/**
 * Process FreeDATA messages and update chat store.
 * Accepts the API response object, or a Promise resolving to it. Anything
 * else (undefined, a Promise resolving to undefined, ...) is ignored.
 * @param {Object|Promise<Object>} data - The data object containing messages.
 */
export async function processFreedataMessages(data) {
  try {
    data = await data;
  } catch (error) {
    console.error("Error resolving messages:", error);
    return;
  }
  if (!data || !Array.isArray(data.messages)) return;

  chatStore.callsign_list = createCallsignListFromAPI(data);
  chatStore.sorted_chat_list = createSortedMessagesList(data);

  // On desktop, auto-select the most recent conversation
  if (!chatStore.selectedCallsign && !isMobile.value) {
    const first = Object.keys(chatStore.callsign_list)[0];
    if (first) {
      chatStore.selectedCallsign = first;
      loadBeaconData(first);
    }
  }
}

/**
 * Create a list of callsigns from the API data.
 * @param {Object} data - The data object containing messages.
 * @returns {Object} - The callsign list.
 */
function createCallsignListFromAPI(data) {
  const callsignList = {};
  chatStore.totalUnreadMessages = 0;

  data.messages.forEach((message) => {
    const callsign =
      message.direction === "receive" ? message.origin : message.destination;

    // Increment global unread count if the message is not read.
    if (!message.is_read) {
      chatStore.totalUnreadMessages++;
    }

    // Create or update the callsign entry.
    if (!callsignList[callsign]) {
      callsignList[callsign] = {
        timestamp: message.timestamp,
        body: message.body,
        unread_messages: !message.is_read ? 1 : 0,
      };
    } else {
      // Update the unread count if the message is unread.
      if (!message.is_read) {
        callsignList[callsign].unread_messages++;
      }
      // Update stored details if this message is newer.
      if (
        new Date(message.timestamp) > new Date(callsignList[callsign].timestamp)
      ) {
        callsignList[callsign].timestamp = message.timestamp;
        callsignList[callsign].body = message.body;
      }
    }
  });

  // Get the keys sorted in descending order by timestamp.
  const sortedKeys = Object.keys(callsignList).sort(
    (a, b) =>
      new Date(callsignList[b].timestamp) - new Date(callsignList[a].timestamp),
  );

  // Rebuild the object with keys in sorted order.
  const sortedCallsignList = {};
  sortedKeys.forEach((key) => {
    sortedCallsignList[key] = callsignList[key];
  });

  return sortedCallsignList;
}

/**
 * Create a sorted list of messages by callsign.
 * @param {Object} data - The data object containing messages.
 * @returns {Object} - The sorted messages list.
 */
function createSortedMessagesList(data) {
  const callsignMessages = {};

  data.messages.forEach((message) => {
    // Determine the callsign based on message direction.
    const callsign =
      message.direction === "receive" ? message.origin : message.destination;

    if (!callsignMessages[callsign]) {
      callsignMessages[callsign] = [];
    }

    callsignMessages[callsign].push(message);
  });

  return callsignMessages;
}

/**
 * Send a new FreeDATA message.
 * @param {string} dxcall - The callsign to send the message to.
 * @param {string} body - The message body.
 * @param {Array} attachments - The message attachments.
 */
export function newMessage(dxcall, body, attachments) {
  const result = sendFreedataMessage(dxcall, body, attachments);
  chatStore.triggerScrollToBottom();
  return result;
}

/**
 * Repeat the transmission of a message by its ID.
 * @param {string} id - The ID of the message.
 */
export function repeatMessageTransmission(id) {
  return retransmitFreedataMessage(id);
}

/**
 * Delete all messages associated with a callsign from the database.
 * Messages that are queued or transmitting cannot be deleted (the server
 * answers 409); they are skipped and the user is told about them.
 * @param {string} callsign - The callsign to delete messages for.
 */
export async function deleteCallsignFromDB(callsign) {
  const messages = chatStore.sorted_chat_list?.[callsign] || [];
  const deletable = messages.filter(
    (message) => !UNDELETABLE_STATUSES.includes(message.status),
  );
  const skipped = messages.length - deletable.length;

  if (skipped > 0) {
    displayToast(
      "warning",
      "bi-exclamation-triangle",
      `${skipped} message(s) to ${escapeHtml(callsign)} are queued or being transmitted and were not deleted.`,
      7000,
    );
  }

  await Promise.all(
    deletable.map((message) => deleteFreedataMessage(message.id)),
  );
}

/**
 * Delete a specific message by its ID from the database.
 * @param {string} id - The ID of the message.
 */
export function deleteMessageFromDB(id) {
  return deleteFreedataMessage(id);
}

/**
 * Send a specific message by its ID via ADIF UDP.
 * @param {string} id - The ID of the message.
 */
export function sendADIFviaUDP(id) {
  return postFreedataMessageADIF(id);
}

/**
 * Request information about a message by its ID and store it in
 * chatStore.messageInfoById (null if unknown or on error).
 * The server returns the message as a JSON object (404 for unknown ids,
 * which getFreedataMessageById turns into undefined).
 * @param {string} id - The ID of the message.
 * @returns {Promise<Object|null>} - The message info.
 */
export async function requestMessageInfo(id) {
  let info = null;
  try {
    info = (await getFreedataMessageById(id)) ?? null;
  } catch (error) {
    console.error("Error fetching message info:", error);
    info = null;
  }
  chatStore.messageInfoById = info;
  return info;
}

/**
 * Parse a message timestamp from the server. P2P message timestamps are UTC
 * but come back from the database without a timezone designator
 * (e.g. "2024-04-04T17:22:14.002502"), which JavaScript would read as local
 * time, so a missing designator is treated as UTC. Numbers are Unix seconds.
 * @param {string|number} input
 * @returns {Date}
 */
export function parseServerTimestamp(input) {
  if (typeof input === "number") return new Date(input * 1000);
  if (typeof input === "string" && !/(Z|[+-]\d{2}:?\d{2})$/i.test(input)) {
    return new Date(input + "Z");
  }
  return new Date(input);
}

/**
 * Load the beacon history of a callsign into the chat store (beacon histogram).
 * @param {string} callsign - The callsign to load beacons for.
 */
export async function loadBeaconData(callsign) {
  if (!callsign) return;
  const beacons = await getBeaconDataByCallsign(callsign);
  const list = Array.isArray(beacons) ? beacons : [];
  chatStore.beaconLabelArray = list.map((entry) => entry.timestamp);
  chatStore.beaconDataArray = list.map((entry) => entry.snr);
}

/**
 * Retrieve an attachment by its SHA-512 hash.
 * @param {string} data_sha512 - The SHA-512 hash of the attachment.
 * @returns {Promise<Object>} - The attachment data.
 */
export async function getMessageAttachment(data_sha512) {
  return await getFreedataAttachmentBySha512(data_sha512);
}
