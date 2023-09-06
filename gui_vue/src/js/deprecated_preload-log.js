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
    .getElementById("enable_filter_info")
    .addEventListener("click", () => {
      if (document.getElementById("enable_filter_info").checked) {
        display_class("table-info", true);
      } else {
        display_class("table-info", false);
      }
    });

  document
    .getElementById("enable_filter_debug")
    .addEventListener("click", () => {
      if (document.getElementById("enable_filter_debug").checked) {
        display_class("table-debug", true);
      } else {
        display_class("table-debug", false);
      }
    });

  document
    .getElementById("enable_filter_warning")
    .addEventListener("click", () => {
      if (document.getElementById("enable_filter_warning").checked) {
        display_class("table-warning", true);
      } else {
        display_class("table-warning", false);
      }
    });

  document
    .getElementById("enable_filter_error")
    .addEventListener("click", () => {
      if (document.getElementById("enable_filter_error").checked) {
        display_class("table-danger", true);
      } else {
        display_class("table-danger", false);
      }
    });
});

function display_class(class_name, state) {
  var collection = document.getElementsByClassName(class_name);
  console.log(collection);
  for (let i = 0; i < collection.length; i++) {
    if (state == true) {
      collection[i].style.display = "table-row";
    } else {
      collection[i].style.display = "None";
    }
  }
}

ipcRenderer.on("action-update-log", (event, arg) => {
  var entry = arg.entry;

  // remove ANSI characters from string, caused by color logging
  // https://stackoverflow.com/a/29497680
  entry = entry.replace(
    /[\u001b\u009b][[()#;?]*(?:[0-9]{1,4}(?:;[0-9]{0,4})*)?[0-9A-ORZcf-nqry=><]/g,
    "",
  );

  var tbl = document.getElementById("log");
  var row = document.createElement("tr");

  var timestamp = document.createElement("td");
  var timestampText = document.createElement("span");

  //datetime = new Date();
  //timestampText.innerText = datetime.toISOString();
  timestampText.innerText = entry.slice(0, 19);
  timestamp.appendChild(timestampText);

  var type = document.createElement("td");
  var typeText = document.createElement("span");
  // typeText.innerText = entry.slice(10, 30).match(/[\[](.*)[^\]]/g);
  console.log(entry.match(/\[[^\]]+\]/g));

  try {
    typeText.innerText = entry.match(/\[[^\]]+\]/g)[0];
  } catch (e) {
    typeText.innerText = "-";
  }

  //    let res = str.match(/[\[](.*)[^\]]/g);

  type.appendChild(typeText);

  var area = document.createElement("td");
  var areaText = document.createElement("span");
  //areaText.innerText = entry.slice(10, 50).match(/[\] \[](.*)[^\]]/g);
  //areaText.innerText = entry.match(/\[[^\]]+\]/g)[1];

  try {
    areaText.innerText = entry.match(/\[[^\]]+\]/g)[1];
  } catch (e) {
    areaText.innerText = "-";
  }
  area.appendChild(areaText);

  var logEntry = document.createElement("td");
  var logEntryText = document.createElement("span");
  try {
    logEntryText.innerText = entry.split("]")[2];
  } catch (e) {
    logEntryText.innerText = "-";
  }
  logEntry.appendChild(logEntryText);

  row.appendChild(timestamp);
  row.appendChild(type);
  row.appendChild(area);
  row.appendChild(logEntry);

  //row.classList.add("table-blablubb");
  /*
    if (logEntryText.innerText.includes('ALSA lib pcm')) {
        row.classList.add("table-secondary");
    }
  */
  if (typeText.innerText.includes("info")) {
    row.classList.add("table-info");
  }
  if (typeText.innerText.includes("debug")) {
    row.classList.add("table-secondary");
  }

  if (typeText.innerText.includes("warning")) {
    row.classList.add("table-warning");
  }

  if (typeText.innerText.includes("error")) {
    row.classList.add("table-danger");
  }

  if (document.getElementById("enable_filter_info").checked) {
    row.style.display = "table-row";
    display_class("table-info", true);
  } else {
    row.style.display = "None";
    display_class("table-info", false);
  }
  if (document.getElementById("enable_filter_debug").checked) {
    row.style.display = "table-row";
    display_class("table-secondary", true);
  } else {
    row.style.display = "None";
    display_class("table-secondary", false);
  }
  if (document.getElementById("enable_filter_warning").checked) {
    row.style.display = "table-row";
    display_class("table-warning", true);
  } else {
    row.style.display = "None";
    display_class("table-warning", false);
  }
  if (document.getElementById("enable_filter_error").checked) {
    row.style.display = "table-row";
    display_class("table-danger", true);
  } else {
    row.style.display = "None";
    display_class("table-danger", false);
  }

  tbl.appendChild(row);

  // scroll to bottom of page
  // https://stackoverflow.com/a/11715670
  window.scrollTo(0, document.body.scrollHeight);
});
