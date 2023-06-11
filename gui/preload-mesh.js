const path = require("path");
const { ipcRenderer } = require("electron");

// https://stackoverflow.com/a/26227660
var appDataFolder =
  process.env.APPDATA ||
  (process.platform == "darwin"
    ? process.env.HOME + "/Library/Application Support"
    : process.env.HOME + "/.config");
var configFolder = path.join(appDataFolder, "FreeDATA");
var configPath = path.join(configFolder, "config.json");
const config = require(configPath);

// WINDOW LISTENER
window.addEventListener("DOMContentLoaded", () => {

  // startPing button clicked
  document.getElementById("transmit_mesh_ping").addEventListener("click", () => {
    var dxcallsign = document.getElementById("dxCallMesh").value.toUpperCase();
    if (dxcallsign == "" || dxcallsign == null || dxcallsign == undefined)
      return;
    //pauseButton(document.getElementById("transmit_mesh_ping"), 2000);
    ipcRenderer.send("run-tnc-command", {
      command: "mesh_ping",
      dxcallsign: dxcallsign,
    });
  });



  document
    .getElementById("enable_mesh")
    .addEventListener("click", () => {
      if (document.getElementById("enable_mesh").checked) {


        let Data = {
      type: "set",
      command: "enable_mesh",
    };
    ipcRenderer.send("run-tnc-command", Data);


      } else {
let Data = {
      type: "set",
      command: "disable_mesh",
    };
    ipcRenderer.send("run-tnc-command", Data);

      }
    });


});


ipcRenderer.on("action-update-mesh-table", (event, arg) => {
  var routes = arg.routing_table;

if (typeof routes == "undefined") {
    return;
  }


    var tbl = document.getElementById("mesh-table");
if (tbl !== null) {
      tbl.innerHTML = "";

  }


for (i = 0; i < routes.length; i++) {


      /*
      var myGrid = document.getElementById("myGrid").value;
      try {
        var dist = parseInt(distance(myGrid, dxGrid)) + " km";
        document.getElementById("dataModalPingDistance").textContent = dist;
      } catch {
        document.getElementById("dataModalPingDistance").textContent = "---";
      }
      document.getElementById("dataModalPingDB").textContent =
        arg.stations[i]["snr"];
    }
    */



  var row = document.createElement("tr");
    var datetime = new Date(routes[i]["timestamp"] * 1000).toLocaleString(
      navigator.language,{
        hourCycle: 'h23',
        year: "numeric",
        month: "2-digit",
        day: "2-digit",
        hour: "2-digit",
        minute: "2-digit",
        second: "2-digit"
    }
    );
  var timestamp = document.createElement("td");
  var timestampText = document.createElement("span");
  timestampText.innerText = datetime;
  timestamp.appendChild(timestampText);

  var dxcall = document.createElement("td");
  var dxcallText = document.createElement("span");
  dxcallText.innerText = routes[i]["dxcall"];
  dxcall.appendChild(dxcallText);

  var router = document.createElement("td");
  var routerText = document.createElement("span");
  routerText.innerText = routes[i]["router"];
  router.appendChild(routerText);

  var hops = document.createElement("td");
  var hopsText = document.createElement("span");
  hopsText.innerText = routes[i]["hops"];
  hops.appendChild(hopsText);

    var score = document.createElement("td");
  var scoreText = document.createElement("span");
  scoreText.innerText = routes[i]["score"];
  score.appendChild(scoreText);

    var snr = document.createElement("td");
  var snrText = document.createElement("span");
  snrText.innerText = routes[i]["snr"];
  snr.appendChild(snrText);

  row.appendChild(timestamp);
  row.appendChild(dxcall);
  row.appendChild(router);
  row.appendChild(hops);
  row.appendChild(score);
  row.appendChild(snr);



  tbl.appendChild(row);
}


if (tbl !== null) {

  // scroll to bottom of page
  // https://stackoverflow.com/a/11715670
  window.scrollTo(0, document.body.scrollHeight);
  }
});
