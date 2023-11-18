import { getAudioDevices, getSerialDevices } from "./api";

let audioDevices = await getAudioDevices();
let serialDevices = await getSerialDevices();

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
  return audioDevices.in;
}

export function audioOutputOptions() {
  return audioDevices.out;
}

export function serialDeviceOptions() {
  return serialDevices;
}
