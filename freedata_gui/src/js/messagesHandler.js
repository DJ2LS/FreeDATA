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
  postFreedataMessageADIF
} from "./api";

/**
 * Process FreeDATA messages and update chat store.
 * @param {Object} data - The data object containing messages.
 */
export async function processFreedataMessages(data) {
  if (data && Array.isArray(data.messages)) {
    chatStore.callsign_list = createCallsignListFromAPI(data);
    chatStore.sorted_chat_list = createSortedMessagesList(data);

    if (!chatStore.selectedCallsign) {
      chatStore.selectedCallsign = Object.keys(chatStore.sorted_chat_list)[0];
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
    let callsign =
      message.direction === "receive" ? message.origin : message.destination;

    if (
      !callsignList[callsign] ||
      callsignList[callsign].timestamp < message.timestamp
    ) {
      let unreadCounter = 0;

      if (callsignList[callsign]) {
        unreadCounter = callsignList[callsign].unread_messages;
      }

      if (!message.is_read) {
        unreadCounter++;
        chatStore.totalUnreadMessages++;
      }

      callsignList[callsign] = {
        timestamp: message.timestamp,
        body: message.body,
        unread_messages: unreadCounter,
      };
    } else if (!message.is_read) {
      chatStore.totalUnreadMessages++;
    }
  });

  return callsignList;
}

/**
 * Create a sorted list of messages by callsign.
 * @param {Object} data - The data object containing messages.
 * @returns {Object} - The sorted messages list.
 */
function createSortedMessagesList(data) {
  const callsignMessages = {};

  data.messages.forEach((message) => {
    let callsign =
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
  sendFreedataMessage(dxcall, body, attachments);
  chatStore.triggerScrollToBottom();
}

/**
 * Repeat the transmission of a message by its ID.
 * @param {string} id - The ID of the message.
 */
export function repeatMessageTransmission(id) {
  retransmitFreedataMessage(id);
}

/**
 * Delete all messages associated with a callsign from the database.
 * @param {string} callsign - The callsign to delete messages for.
 */
export function deleteCallsignFromDB(callsign) {
  for (const message of chatStore.sorted_chat_list[callsign]) {
    deleteFreedataMessage(message.id);
  }
}

/**
 * Delete a specific message by its ID from the database.
 * @param {string} id - The ID of the message.
 */
export function deleteMessageFromDB(id) {
  deleteFreedataMessage(id);
}

/**
 * Send a specific message by its ID via ADIF UDP.
 * @param {string} id - The ID of the message.
 */
export function sendADIFviaUDP(id) {
  postFreedataMessageADIF(id);
}

/**
 * Request information about a message by its ID
 * @param {string} id - The ID of the message.
 */
export function requestMessageInfo(id) {
  return getFreedataMessageById(id)
    .then((result) => {
      console.log(result);

      try {
        chatStore.messageInfoById = JSON.parse(result);
      } catch (error) {
        console.error("Error parsing JSON:", error);
        chatStore.messageInfoById = null;
      }

      return result;
    })
    .catch((error) => {
      console.error("Error fetching message:", error);
    });
}

/**
 * Retrieve an attachment by its SHA-512 hash.
 * @param {string} data_sha512 - The SHA-512 hash of the attachment.
 * @returns {Promise<Object>} - The attachment data.
 */
export async function getMessageAttachment(data_sha512) {
  return await getFreedataAttachmentBySha512(data_sha512);
}
