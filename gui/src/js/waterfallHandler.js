import { Spectrum } from "../assets/waterfall/spectrum.js";

import { setActivePinia } from "pinia";
import pinia from "../store/index";
setActivePinia(pinia);

import { settingsStore as settings } from "../store/settingsStore.js";

var spectrum = new Object();

export function initWaterfall(id) {
  spectrum = new Spectrum(id, {
    spectrumPercent: 0,
    wf_rows: 1024, //Assuming 1 row = 1 pixe1, 192 is the height of the spectrum container
    wf_size: 1024,
  });
  spectrum.setColorMap(settings.local.wf_theme);
  return spectrum;
}

export function addDataToWaterfall(data) {
  data = JSON.parse(data);
  window.dispatchEvent(new CustomEvent("wf-data-avail", { detail: data }));
}
/**
 * Setwaterfall colormap array by index
 * @param {number} index colormap index to use
 */
export function setColormap(index) {
  if (isNaN(index)) index = 0;
  //console.log("Setting waterfall colormap to " + index)
  spectrum.setColorMap(index);
}
