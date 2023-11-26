import { getAudioDevices, getSerialDevices } from "./api";

let audioDevices = await getAudioDevices();
let serialDevices = await getSerialDevices();

//Dummy device data sent if unable to get devices from modem to prevent GUI crash
const skel = JSON.parse(`
  [{
    "api": "MME",
    "id": "0000",
    "name": "No devices received from modem",
    "native_index": 0
}]`);
export function loadAudioDevices() {
  getAudioDevices().then((devices) => {
    audioDevices = devices;
  });
}

export function loadSerialDevices() {
  getSerialDevices().then((devices) => {
    serialDevices = devices;
  });
}

export function audioInputOptions() {
  if (audioDevices === undefined) {
    return skel;
  }
  return audioDevices.in;
}

export function audioOutputOptions() {
  if (audioDevices === undefined) {
    return skel;
  }
  return audioDevices.out;
}

export function serialDeviceOptions() {
  return serialDevices;
}
