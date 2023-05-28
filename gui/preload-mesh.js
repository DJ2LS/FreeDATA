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
  document
    .getElementById("enable_mesh")
    .addEventListener("click", () => {
      if (document.getElementById("enable_mesh").checked) {
        display_class("table-info", true);
      } else {
        display_class("table-info", false);
      }
    });


});


ipcRenderer.on("action-update-mesh-table", (event, arg) => {
  var routes = arg.routing_table;
    var tbl = document.getElementById("mesh-table");
      tbl.innerHTML = "";


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

  var timestamp = document.createElement("td");
  var timestampText = document.createElement("span");
  timestampText.innerText = routes[i]["timestamp"];
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


  // scroll to bottom of page
  // https://stackoverflow.com/a/11715670
  window.scrollTo(0, document.body.scrollHeight);
});
