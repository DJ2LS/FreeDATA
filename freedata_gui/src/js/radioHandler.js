// pinia store setup
import { setActivePinia } from "pinia";
import pinia from "../store/index";
setActivePinia(pinia);

import { useStateStore } from "../store/stateStore";
const stateStore = useStateStore(pinia);

import { getRadioStatus } from "./api";

export async function processRadioStatus() {
  try {
    let result = await getRadioStatus();

    if (!result || typeof result !== "object") {
      throw new Error("Invalid radio status");
    }

    stateStore.mode = result.radio_mode;
    stateStore.frequency = result.radio_frequency;
    stateStore.rf_level = Math.round(result.radio_rf_level / 5) * 5; // round to 5er steps
    stateStore.tuner = result.radio_tuner;
  } catch (error) {
    console.error("Error fetching radio status:", error);
    // Handle the error appropriately
    // For example, you can set default values or update the UI to indicate an error
    stateStore.mode = "unknown";
    stateStore.frequency = 0;
    stateStore.rf_level = 0;
    stateStore.tuner = "unknown";
  }
}
