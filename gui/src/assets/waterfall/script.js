"use strict";
/*
function connectWebSocket(spectrum) {
//    var ws = new WebSocket("ws://" + window.location.host + "/websocket");
    var ws = new WebSocket("ws://192.168.178.163:3000");
    
    
    ws.onopen = function(evt) {
        console.log("connected!");
    }
    ws.onclose = function(evt) {
        console.log("closed");
        setTimeout(function() {
            connectWebSocket(spectrum);
        }, 1000);
    }
    ws.onerror = function(evt) {
        console.log("error: " + evt.message);
    }
    ws.onmessage = function (evt) {
        var data = JSON.parse(evt.data);
        if (data.s) {
            spectrum.addData(data.s);
        } else {
            if (data.center) {
                spectrum.setCenterHz(data.center);
            }
            if (data.span) {
                spectrum.setSpanHz(data.span);
            }
        }
    }
}
*/

function main() {
  // Create spectrum object on canvas with ID "waterfall"
  var spectrum = new Spectrum("waterfall", {
    spectrumPercent: 20,
  });

  // Connect to websocket
  //connectWebSocket(spectrum);

  //spectrum.setCenterHz("2000");
  //spectrum.setSpanHz("1");

  /*    
for (var i = 0; i < 1000; i++) {
    var randomstring = Math.floor(Math.random())
    spectrum.addData(randomstring.toString());
   // more statements
}
*/

  // Bind keypress handler
  window.addEventListener("keydown", function (e) {
    spectrum.onKeypress(e);
  });
}

window.onload = main;
