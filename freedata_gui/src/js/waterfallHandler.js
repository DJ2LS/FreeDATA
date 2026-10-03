import { Spectrum } from "../assets/waterfall/spectrum.js";

import { setActivePinia } from "pinia";
import pinia from "../store/index";
setActivePinia(pinia);

import { settingsStore as settings } from "../store/settingsStore.js";

var spectrums = [];

/**
 * Create a Spectrum for the canvas with the given id and register it so it
 * receives FFT data. Returns the instance; pass it to removeWaterfall() when
 * the canvas goes away.
 * @param {string} id canvas element id
 */
export function initWaterfall(id) {
  const spectrum = new Spectrum(id, {
    spectrumPercent: 0,
    wf_rows: 1024, //Assuming 1 row = 1 pixe1, 192 is the height of the spectrum container
    wf_size: 1024,
  });
  spectrum.setColorMap(settings.local.wf_theme);
  spectrums.push(spectrum);
  return spectrum;
}

/**
 * Unregister a Spectrum created by initWaterfall() so it stops receiving data.
 * @param {object} spectrum instance returned by initWaterfall()
 */
export function removeWaterfall(spectrum) {
  const index = spectrums.indexOf(spectrum);
  if (index !== -1) spectrums.splice(index, 1);
}

export function addDataToWaterfall(data) {
  data = JSON.parse(data);
  if (data.constructor !== Array) return;
  spectrums.forEach((element) => {
    //console.log(element);
    element.addData(data);
  });
  //window.dispatchEvent(new CustomEvent("wf-data-avail", {bubbles:true, detail: data }));
}

/**
 * Setwaterfall colormap array by index
 * @param {number} index colormap index to use
 */
export function setColormap() {
  let index = settings.local.wf_theme;
  if (isNaN(index)) index = 0;
  console.log("Setting waterfall colormap to " + index);
  spectrums.forEach((element) => {
    //console.log(element);
    element.setColorMap(index);
  });
}
