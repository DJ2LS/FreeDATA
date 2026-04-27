import { setActivePinia } from 'pinia';
import pinia from '../store/index';
setActivePinia(pinia);

import { useBroadcastStore } from '../store/broadcastStore.js';
import {
  deleteFreedataBroadcastDomain,
  deleteFreedataBroadcastMessage,
  postFreedataBroadcastADIF,
  retransmitFreedataBroadcast,
  sendFreedataBroadcastMessage
} from "@/js/api";
const broadcast = useBroadcastStore(pinia);

export async function processFreedataBroadcastsPerDomain(data) {
  console.log(data)
  broadcast.setBroadcastsForDomain(data);
}

export async function processFreedataDomains(data) {
  console.log(data);

  broadcast.setDomains(data);

  // sum of unread_count
  broadcast.totalUnreadMessages = Object.values(data).reduce(
    (sum, domain) => sum + (domain.unread_count || 0),
    0
  );
}



export function newBroadcastMessage(params) {
  sendFreedataBroadcastMessage(params);
  broadcast.triggerScrollToBottom();
}

export function repeatBroadcastTransmission(id) {
  retransmitFreedataBroadcast(id);
}

export function deleteBroadcastDomainFromDB(domain) {
  deleteFreedataBroadcastDomain(domain);
  broadcast.selectedDomain = '';
}

export function sendBroadcastADIFviaUDP(domain) {
  const messages = broadcastStore.sorted_broadcast_list[domain] || [];
  for (const message of messages) {
    postFreedataBroadcastADIF(message.id);
  }
}

export function deleteBroadcastMessageFromDB(id) {
  deleteFreedataBroadcastMessage(id);
}
