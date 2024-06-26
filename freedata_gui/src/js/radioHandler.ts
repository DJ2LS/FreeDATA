// pinia store setup
import { setActivePinia } from "pinia";
import pinia from "../store/index";
setActivePinia(pinia);

import { settingsStore as settings, onChange } from "../store/settingsStore.js";

import { useStateStore } from "../store/stateStore";
const stateStore = useStateStore(pinia);

import { getRadioStatus } from "./api";

export async function processRadioStatus() {
  let result = await getRadioStatus();
  stateStore.mode = result.radio_mode;
  stateStore.frequency = result.radio_frequency;
  stateStore.rf_level = Math.round(result.radio_rf_level / 5) * 5; // round to 5er steps
  stateStore.tuner = result.radio_tuner;
}
