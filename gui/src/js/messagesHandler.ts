// pinia store setup
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
} from "./api";

interface Message {
  id: string;
  timestamp: string;
  origin: string;
  destination: string;
  direction: string;
  body: string;
  attachments: any[];
  status: any;
  statistics: any;
}

export async function processFreedataMessages(data) {
  if (
    typeof data !== "undefined" &&
    typeof data.messages !== "undefined" &&
    Array.isArray(data.messages)
  ) {
    chatStore.callsign_list = createCallsignListFromAPI(data);
    chatStore.sorted_chat_list = createSortedMessagesList(data);
  }
}

function createCallsignListFromAPI(data: {
  total_messages: number;
  messages: Message[];
}): { [key: string]: { timestamp: string; body: string } } {
  const callsignList: { [key: string]: { timestamp: string; body: string } } =
    {};

  data.messages.forEach((message) => {
    let callsign =
      message.direction === "receive" ? message.origin : message.destination;

    if (
      !callsignList[callsign] ||
      callsignList[callsign].timestamp < message.timestamp
    ) {
      callsignList[callsign] = {
        timestamp: message.timestamp,
        body: message.body,
      };
    }
  });

  return callsignList;
}

function createSortedMessagesList(data: {
  total_messages: number;
  messages: Message[];
}): { [key: string]: Message[] } {
  const callsignMessages: { [key: string]: Message[] } = {};

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

export function newMessage(dxcall, body, attachments) {
  sendFreedataMessage(dxcall, body, attachments);
  chatStore.triggerScrollToBottom();
}

/* ------ TEMPORARY DUMMY FUNCTIONS --- */
export function repeatMessageTransmission(id) {
  retransmitFreedataMessage(id);
}

export function deleteCallsignFromDB(callsign) {
  for (var message of chatStore.sorted_chat_list[callsign]) {
    deleteFreedataMessage(message["id"]);
  }
}

export function deleteMessageFromDB(id) {
  deleteFreedataMessage(id);
}

export function requestMessageInfo(id) {
  return;
}

export async function getMessageAttachment(data_sha512) {
  return await getFreedataAttachmentBySha512(data_sha512);
}
