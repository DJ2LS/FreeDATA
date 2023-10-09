import {Spectrum} from "../assets/waterfall/spectrum.js"


var spectrum = new Object

export function initWaterfall(){
    spectrum = new Spectrum("waterfall", {
        spectrumPercent: 0,
        wf_rows: 192, //Assuming 1 row = 1 pixe1, 192 is the height of the spectrum container
      });

        //spectrum.setColorMap(config.wftheme);

}

export function addDataToWaterfall(data){
    //console.log(spectrum)
    try {
          spectrum.addData(data);
        } catch (e) {
          console.log(e);
        }

}