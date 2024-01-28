// pinia store setup
import { setActivePinia } from "pinia";
import pinia from "../store/index";
setActivePinia(pinia);

import { useChatStore } from "../store/chatStore.js";
const chatStore = useChatStore(pinia);

import { sendFreedataMessage, deleteFreedataMessage } from "./api"

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


export function processFreedataMessages(data){
    let jsondata = JSON.parse(data);
    console.log(jsondata)
    chatStore.callsign_list = createCallsignListFromAPI(jsondata)
    chatStore.sorted_chat_list = createSortedMessagesList(jsondata)
}

function createCallsignListFromAPI(data: { total_messages: number, messages: Message[] }): {[key: string]: {timestamp: string, body: string}} {
  const callsignList: {[key: string]: {timestamp: string, body: string}} = {};

  data.messages.forEach(message => {
    let callsign = message.direction === 'receive' ? message.origin : message.destination;

    if (!callsignList[callsign] || callsignList[callsign].timestamp < message.timestamp) {
      callsignList[callsign] = { timestamp: message.timestamp, body: message.body };
    }
  });

  return callsignList;
}



function createSortedMessagesList(data: { total_messages: number, messages: Message[] }): {[key: string]: Message[]} {
  const callsignMessages: {[key: string]: Message[]} = {};

  data.messages.forEach(message => {
    let callsign = message.direction === 'receive' ? message.origin : message.destination;

    if (!callsignMessages[callsign]) {
      callsignMessages[callsign] = [];
    }

    callsignMessages[callsign].push(message);
  });

  return callsignMessages;
}



export function newMessage(dxcall, body){
    sendFreedataMessage(dxcall, body)
}


/* ------ TEMPORARY DUMMY FUNCTIONS --- */
export function repeatMessageTransmission(id){
    return
}

export function deleteCallsignFromDB(callsign){
    for (var message of chatStore.sorted_chat_list[callsign]) {
          deleteFreedataMessage(message["id"]);
    }

}

export function deleteMessageFromDB(id){
    deleteFreedataMessage(id);
}

export function requestMessageInfo(id){
    return
}

export function getMessageAttachment(id){
    return
}
