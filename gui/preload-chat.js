const path = require("path");
const { ipcRenderer } = require("electron");
const { v4: uuidv4 } = require("uuid");
// https://stackoverflow.com/a/26227660
var appDataFolder =
  process.env.APPDATA ||
  (process.platform == "darwin"
    ? process.env.HOME + "/Library/Application Support"
    : process.env.HOME + "/.config");
var configFolder = path.join(appDataFolder, "FreeDATA");
var configPath = path.join(configFolder, "config.json");
const config = require(configPath);
// set date format
const dateFormat = new Intl.DateTimeFormat("en-GB", {
  timeStyle: "long",
  dateStyle: "short",
});
// set date format information
const dateFormatShort = new Intl.DateTimeFormat("en-GB", {
  year: "numeric",
  month: "numeric",
  day: "numeric",
  hour: "numeric",
  minute: "numeric",
  second: "numeric",
  hour12: false,
});

const dateFormatHours = new Intl.DateTimeFormat("en-GB", {
  hour: "numeric",
  minute: "numeric",
  hour12: false,
});
// split character
const split_char = "\0;\1;";
// global for our selected file we want to transmit
// ----------------- some chat globals
var filetype = "";
var file = "";
var filename = "";
var callsign_counter = 0;
var selected_callsign = "";
var lastIsWritingBroadcast = new Date().getTime();
// -----------------------------------

var chatDB = path.join(configFolder, "chatDB");
var userDB = path.join(configFolder, "userDB");
// ---- MessageDB
try {
  var PouchDB = require("pouchdb");
} catch (err) {
  console.log(err);

  /*
    This is a fix for raspberryPi where we get an error when loading pouchdb because of
    leveldown package isnt running on ARM devices.
    pouchdb-browser does not depend on leveldb and seems to be working.
    */
  console.log("using pouchdb-browser fallback");
  var PouchDB = require("pouchdb-browser");
}

PouchDB.plugin(require("pouchdb-find"));
//PouchDB.plugin(require('pouchdb-replication'));

var db = new PouchDB(chatDB);
var users = new PouchDB(userDB);

/* -------- CREATE DATABASE INDEXES */
createChatIndex();
createUserIndex();

/*
// REMOTE SYNC ATTEMPTS


var remoteDB = new PouchDB('http://172.20.10.4:5984/chatDB')

// we need express packages for running pouchdb sync "express-pouchdb"
var express = require('express');
var app = express();
//app.use('/chatDB', require('express-pouchdb')(PouchDB));
//app.listen(5984);

app.use('/chatDB', require('pouchdb-express-router')(PouchDB));
app.listen(5984);



db.sync('http://172.20.10.4:5984/jojo', {
//var sync = PouchDB.sync('chatDB', 'http://172.20.10.4:5984/chatDB', {
  live: true,
  retry: false
}).on('change', function (change) {
  // yo, something changed!
  console.log(change)
}).on('paused', function (err) {
  // replication was paused, usually because of a lost connection
  console.log(err)
}).on('active', function (info) {
  // replication was resumed
  console.log(info)
}).on('error', function (err) {
  // totally unhandled error (shouldn't happen)
  console.log(err)
}).on('denied', function (err) {
  // a document failed to replicate (e.g. due to permissions)
  console.log(err)
}).on('complete', function (info) {
  // handle complete;
  console.log(info)
});
*/

var dxcallsigns = new Set();
var chatFilter = [
  { type: "newchat" },
  { type: "received" },
  { type: "transmit" },
  { type: "ping-ack" },
];

updateAllChat(false);

// WINDOW LISTENER
window.addEventListener("DOMContentLoaded", () => {
  // theme selector
  if (config.theme != "default") {
    var theme_path =
      "../node_modules/bootswatch/dist/" + config.theme + "/bootstrap.min.css";
    document.getElementById("bootstrap_theme").href = theme_path;
  } else {
    var theme_path = "../node_modules/bootstrap/dist/css/bootstrap.min.css";
    document.getElementById("bootstrap_theme").href = theme_path;
  }

  const userInfoFields = [
    "user_info_callsign",
    "user_info_gridsquare",
    "user_info_name",
    "user_info_age",
    "user_info_location",
    "user_info_radio",
    "user_info_antenna",
    "user_info_email",
    "user_info_website",
    "user_info_comments",
  ];

  users
    .find({
      selector: {
        user_info_callsign: config.mycall,
      },
    })
    .then(function (result) {
      if (typeof result.docs[0] !== "undefined") {
        // handle result
        userInfoFields.forEach(function (elem) {
          document.getElementById(elem).value = result.docs[0][elem];
        });
      } else {
        console.log(
          config.mycall + " not found in user db - creating new entry"
        );
        // add initial entry for own callsign and grid
        let obj = new Object();
        obj.user_info_callsign = config.mycall;
        obj.user_info_gridsquare = config.mygrid;
        addUserToDatabaseIfNotExists(obj);

        document.getElementById("user_info_callsign").value = config.mycall;
        document.getElementById("user_info_gridsquare").value = config.mygrid;
      }
    })
    .catch(function (err) {
      console.log(err);
    });

  // user info bulk event listener for saving settings
  userInfoFields.forEach(function (elem) {
    try {
      document.getElementById(elem).addEventListener("change", function () {
        //config[elem] = document.getElementById(elem).value;

        let obj = new Object();
        userInfoFields.forEach(function (subelem) {
          obj[subelem] = document.getElementById(subelem).value;
        });
        console.log(obj);
        addUserToDatabaseIfNotExists(obj);
      });
    } catch (e) {
      console.log(e);
      console.log(elem);
    }
  });

  //Add event listener for filter apply button
  document.getElementById("btnFilter").addEventListener("click", () => {
    chatFilter = [{ type: "newchat" }];
    if (document.getElementById("chkMessage").checked == true)
      chatFilter.push({ type: "received" }, { type: "transmit" });
    if (document.getElementById("chkPing").checked == true)
      chatFilter.push({ type: "ping" });
    if (document.getElementById("chkPingAck").checked == true)
      chatFilter.push({ type: "ping-ack" });
    if (document.getElementById("chkBeacon").checked == true)
      chatFilter.push({ type: "beacon" });
    updateAllChat(true);
  });

  document
    .querySelector("emoji-picker")
    .addEventListener("emoji-click", (event) => {
      var msg = document.getElementById("chatModuleMessage");
      //Convert to utf-8--so we can just use utf-8 everywhere
      msg.setRangeText(event.detail.emoji.unicode.toString("utf-8"));
      //console.log(event.detail);
      //msg.focus();
    });
  document.getElementById("emojipickerbutton").addEventListener("click", () => {
    var element = document.getElementById("emojipickercontainer");
    console.log(element.style.display);
    if (element.style.display === "none") {
      element.style.display = "block";
    } else {
      element.style.display = "none";
    }
  });
  document
    .getElementById("delete_selected_chat")
    .addEventListener("click", () => {
      db.find({
        selector: {
          dxcallsign: selected_callsign,
        },
      })
        .then(function (result) {
          // handle result
          if (typeof result !== "undefined") {
            result.docs.forEach(function (item) {
              console.log(item);
              db.get(item._id)
                .then(function (doc) {
                  db.remove(doc)
                    .then(function (doc) {
                      return location.reload();
                    })
                    .catch(function (err) {
                      console.log(err);
                    });
                })
                .catch(function (err) {
                  console.log(err);
                });
            });
          }
        })
        .catch(function (err) {
          console.log(err);
        });
    });
  document.getElementById("selectFilesButton").addEventListener("click", () => {
    //document.getElementById('selectFiles').click();
    ipcRenderer.send("select-file", {
      title: "Title",
    });
  });

  document.getElementById("ping").addEventListener("click", () => {
    ipcRenderer.send("run-tnc-command", {
      command: "ping",
      dxcallsign: selected_callsign,
    });
  });

  document.addEventListener("keyup", function (event) {
    // Number 13 == Enter
    if (
      event.keyCode === 13 &&
      !event.shiftKey &&
      document.activeElement.id == "chatModuleMessage"
    ) {
      // Cancel the default action, if needed
      event.preventDefault();
      // Trigger the button element with a click
      document.getElementById("sendMessage").click();
    }
  });

  // ADJUST TEXTAREA SIZE
  document.getElementById("chatModuleMessage").addEventListener("input", () => {
    var textarea = document.getElementById("chatModuleMessage");
    var text = textarea.value;

    if (document.getElementById("expand_textarea").checked) {
      var lines = 6;
    } else {
      var lines = text.split("\n").length;

      if (lines >= 6) {
        lines = 6;
      }
    }
    var message_container_height_offset = 130 + 20 * lines;
    var message_container_height = `calc(100% - ${message_container_height_offset}px)`;
    document.getElementById("message-container").style.height =
      message_container_height;
    textarea.rows = lines;

    console.log(textarea.value);
    if (lastIsWritingBroadcast < new Date().getTime() - 5 * 1000) {
      //console.log("Sending FECIsWriting");
      console.log(config.enable_is_writing);
      if (config.enable_is_writing == "True") {
        ipcRenderer.send("tnc-fec-iswriting");
      }
      lastIsWritingBroadcast = new Date().getTime();
    }
  });

  document.getElementById("expand_textarea").addEventListener("click", () => {
    var textarea = document.getElementById("chatModuleMessage");

    if (document.getElementById("expand_textarea").checked) {
      var lines = 6;
      document.getElementById("expand_textarea_button").className =
        "bi bi-chevron-compact-down";
    } else {
      var lines = 1;
      document.getElementById("expand_textarea_button").className =
        "bi bi-chevron-compact-up";
    }

    var message_container_height_offset = 130 + 20 * lines;
    //var message_container_height_offset = 90 + (23*lines);
    var message_container_height = `calc(100% - ${message_container_height_offset}px)`;
    document.getElementById("message-container").style.height =
      message_container_height;
    textarea.rows = lines;
    console.log(textarea.rows);
  });

  // NEW CHAT

  document
    .getElementById("createNewChatButton")
    .addEventListener("click", () => {
      var dxcallsign = document.getElementById("chatModuleNewDxCall").value;
      var uuid = uuidv4();
      db.post({
        _id: uuid,
        timestamp: Math.floor(Date.now() / 1000),
        dxcallsign: dxcallsign.toUpperCase(),
        dxgrid: "---",
        msg: "null",
        checksum: "null",
        type: "newchat",
        status: "null",
        uuid: uuid,
      })
        .then(function (response) {
          // handle response
          console.log("new database entry");
          console.log(response);
        })
        .catch(function (err) {
          console.log(err);
        });
      update_chat_obj_by_uuid(uuid);
    });

  // SEND MSG
  document.getElementById("sendMessage").addEventListener("click", () => {
    document.getElementById("emojipickercontainer").style.display = "none";

    var dxcallsign = selected_callsign.toUpperCase();
    var textarea = document.getElementById("chatModuleMessage");
    var chatmessage = textarea.value;
    //Remove non-printable chars from begining and end of string--should save us a byte here and there
    chatmessage = chatmessage.toString().trim();
    // reset textarea size
    var message_container_height_offset = 150;
    var message_container_height = `calc(100% - ${message_container_height_offset}px)`;
    document.getElementById("message-container").style.height =
      message_container_height;
    textarea.rows = 1;
    document.getElementById("expand_textarea_button").className =
      "bi bi-chevron-compact-up";
    document.getElementById("expand_textarea").checked = false;

    console.log(file);
    console.log(filename);
    console.log(filetype);
    if (filetype == "") {
      filetype = "plain/text";
    }
    var timestamp = Math.floor(Date.now() / 1000);

    var file_checksum = crc32(file).toString(16).toUpperCase();
    console.log(file_checksum);
    var data_with_attachment =
      timestamp +
      split_char +
      chatmessage +
      split_char +
      filename +
      split_char +
      filetype +
      split_char +
      file;

    document.getElementById("selectFilesButton").innerHTML = ``;
    var uuid = uuidv4();
    let uuidlast = uuid.lastIndexOf("-");
    uuidlast += 1;
    if (uuidlast > 0) {
      uuid = uuid.substring(uuidlast);
    }
    console.log(data_with_attachment);
    let Data = {
      command: "send_message",
      dxcallsign: dxcallsign,
      mode: 255,
      frames: 1,
      data: data_with_attachment,
      checksum: file_checksum,
      uuid: uuid,
    };
    ipcRenderer.send("run-tnc-command", Data);
    db.post({
      _id: uuid,
      timestamp: timestamp,
      dxcallsign: dxcallsign,
      dxgrid: "null",
      msg: chatmessage,
      checksum: file_checksum,
      type: "transmit",
      status: "transmit",
      uuid: uuid,
      _attachments: {
        [filename]: {
          content_type: filetype,
          //data: btoa(file)
          data: btoa_FD(file),
        },
      },
    })
      .then(function (response) {
        // handle response
        console.log("new database entry");
        console.log(response);
      })
      .catch(function (err) {
        console.log(err);
      });
    update_chat_obj_by_uuid(uuid);

    // clear input
    document.getElementById("chatModuleMessage").value = "";

    // after adding file data to our attachment variable, delete it from global
    filetype = "";
    file = "";
    filename = "";
  });
  // cleanup after transmission
  filetype = "";
  file = "";
  filename = "";
});
ipcRenderer.on("return-selected-files", (event, arg) => {
  filetype = arg.mime;
  console.log(filetype);

  file = arg.data;
  filename = arg.filename;
  document.getElementById("selectFilesButton").innerHTML = `
     <span class="position-absolute top-0 start-85 translate-middle p-2 bg-danger border border-light rounded-circle">
        <span class="visually-hidden">New file selected</span>
     </span>
    `;
});
ipcRenderer.on("action-update-transmission-status", (event, arg) => {
  var data = arg["data"][0];
  console.log(data.status);
  db.get(data.uuid, {
    attachments: true,
  })
    .then(function (doc) {
      return db.put({
        _id: data.uuid,
        _rev: doc._rev,
        timestamp: doc.timestamp,
        dxcallsign: doc.dxcallsign,
        dxgrid: doc.dxgrid,
        msg: doc.msg,
        checksum: doc.checksum,
        type: "transmit",
        status: data.status,
        percent: data.percent,
        bytesperminute: data.bytesperminute,
        uuid: doc.uuid,
        _attachments: doc._attachments,
      });
    })
    .then(function (response) {
      update_chat_obj_by_uuid(data.uuid);
    })
    .catch(function (err) {
      console.log(err);
      console.log(data);
    });
});

//Render is typing message in correct chat window
ipcRenderer.on("action-show-feciswriting", (event, arg) => {
  //console.log("In action-show-feciswriting");
  //console.log(arg);
  let uuid = uuidv4.toString();
  let dxcallsign = arg["data"][0]["dxcallsign"];
  var new_message = `
            <div class="m-auto mt-1 p-0 w-25 rounded bg-secondary bg-gradient" id="msg-${uuid}">
                <p class="text-white mb-0 text-break" style="font-size: 0.7rem;"><i class="m-1 bi bi-pencil"></i><i id="msg-${uuid}-icon" class="m-1 bi bi-wifi-1"></i>${dxcallsign} is typing....</p>

            </div>
        `;
  var id = "chat-" + dxcallsign;
  let chatwin = document.getElementById(id);
  if (chatwin == undefined) {
    //console.log("Element not found!!!!! :(");
    return;
  }
  chatwin.insertAdjacentHTML("beforeend", new_message);
  scrollMessagesToBottom();
  let animIcon = document.getElementById("msg-" + uuid + "-icon");
  //Remove notification after about 4.5 seconds hopefully enough time before a second notification can come in
  setTimeout(function () {
    animIcon.classList = "m-1 bi bi-wifi-2";
  }, 1000);
  setTimeout(function () {
    animIcon.classList = "m-1 bi bi-wifi";
  }, 2000);
  setTimeout(function () {
    animIcon.classList = "m-1 bi bi-wifi-2";
  }, 3000);
  setTimeout(function () {
    animIcon.classList = "m-1 bi bi-wifi-1";
  }, 4000);
  setTimeout(() => {
    let feciw = document.getElementById("msg-" + uuid);
    feciw.remove();
  }, 4500);
});

ipcRenderer.on("action-new-msg-received", (event, arg) => {
  console.log(arg.data);

  var new_msg = arg.data;
  new_msg.forEach(function (item) {
    console.log(item.status);
    let obj = new Object();

    //handle ping
    if (item.ping == "received") {
      obj.timestamp = parseInt(item.timestamp);
      obj.dxcallsign = item.dxcallsign;
      obj.dxgrid = item.dxgrid;
      obj.uuid = item.uuid;
      obj.command = "ping";
      obj.checksum = "null";
      obj.msg = "null";
      obj.status = item.status;
      obj.snr = item.snr;
      obj.type = "ping";
      obj.filename = "null";
      obj.filetype = "null";
      obj.file = "null";

      add_obj_to_database(obj);
      update_chat_obj_by_uuid(obj.uuid);

      // handle beacon
    } else if (item.ping == "acknowledge") {
      obj.timestamp = parseInt(item.timestamp);
      obj.dxcallsign = item.dxcallsign;
      obj.dxgrid = item.dxgrid;
      obj.uuid = item.uuid;
      obj.command = "ping-ack";
      obj.checksum = "null";
      obj.msg = "null";
      obj.status = item.status;
      obj.snr = item.dxsnr + "/" + item.snr;
      obj.type = "ping-ack";
      obj.filename = "null";
      obj.filetype = "null";
      obj.file = "null";

      add_obj_to_database(obj);
      update_chat_obj_by_uuid(obj.uuid);

      // handle beacon
    } else if (item.beacon == "received") {
      obj.timestamp = parseInt(item.timestamp);
      obj.dxcallsign = item.dxcallsign;
      obj.dxgrid = item.dxgrid;
      obj.uuid = item.uuid;
      obj.command = "beacon";
      obj.checksum = "null";
      obj.msg = "null";
      obj.status = item.status;
      obj.snr = item.snr;
      obj.type = "beacon";
      obj.filename = "null";
      obj.filetype = "null";
      obj.file = "null";

      add_obj_to_database(obj);
      update_chat_obj_by_uuid(obj.uuid);

      // handle ARQ transmission
    } else if (item.arq == "transmission" && item.status == "received") {
      //var encoded_data = atob(item.data);
      //var encoded_data = Buffer.from(item.data,'base64').toString('utf-8');
      var encoded_data = atob_FD(item.data);
      var splitted_data = encoded_data.split(split_char);

      console.log(splitted_data);

      obj.timestamp = parseInt(splitted_data[4]);
      obj.dxcallsign = item.dxcallsign;
      obj.dxgrid = item.dxgrid;
      obj.command = splitted_data[1];
      obj.checksum = splitted_data[2];
      // convert message to unicode from utf8 because of emojis
      //No, don't convert; we're already UTF-8!!!!!
      obj.uuid = splitted_data[3];
      obj.msg = splitted_data[5];
      obj.status = "null";
      obj.snr = "null";
      obj.type = "received";
      obj.filename = splitted_data[6];
      obj.filetype = splitted_data[7];
      //obj.file = btoa(splitted_data[8]);
      obj.file = btoa_FD(splitted_data[8]);

      add_obj_to_database(obj);
      update_chat_obj_by_uuid(obj.uuid);
    }
  });
  //window.location = window.location;
});

// Update chat list
update_chat = function (obj) {
  var dxcallsign = obj.dxcallsign;
  var timestamp = dateFormat.format(obj.timestamp * 1000);
  //var timestampShort = dateFormatShort.format(obj.timestamp * 1000);
  var timestampHours = dateFormatHours.format(obj.timestamp * 1000);

  var dxgrid = obj.dxgrid;

  // define shortmessage
  if (obj.msg == "null" || obj.msg == "NULL") {
    var shortmsg = obj.type;
  } else {
    var shortmsg = obj.msg;
    var maxlength = 30;
    var shortmsg =
      shortmsg.length > maxlength
        ? shortmsg.substring(0, maxlength - 3) + "..."
        : shortmsg;
  }
  try {
    //console.log(Object.keys(obj._attachments)[0].length)
    if (
      typeof obj._attachments !== "undefined" &&
      Object.keys(obj._attachments)[0].length > 0
    ) {
      //var filename = obj._attachments;
      var filename = Object.keys(obj._attachments)[0];
      var filetype = filename.split(".")[1];
      var filesize = obj._attachments[filename]["length"] + " Bytes";
      if (filesize == "undefined Bytes") {
        // get filesize of new submitted data
        // not that nice....
        // we really should avoid converting back from base64 for performance reasons...
        //var filesize = Math.ceil(atob(obj._attachments[filename]["data"]).length) + "Bytes";
        var filesize =
          Math.ceil(atob_FD(obj._attachments[filename]["data"]).length) +
          " Bytes";
      }

      // check if image, then display it
      if (filetype == "image/png" || filetype == "png") {
        var fileheader = `
        <div class="card-header border-0 bg-transparent text-end p-0 mb-0 hover-overlay">
        <img class="w-100 rounded-2" src="data:image/png;base64,${atoa_FD(obj._attachments[filename]["data"])}">
       <p class="text-right mb-0 p-1 text-black" style="text-align: right; font-size : 1rem">
                    <span class="p-1" style="text-align: right; font-size : 0.8rem">${filename}</span>
                    <span class="p-1" style="text-align: right; font-size : 0.8rem">${filesize}</span>
                            <i class="bi bi-filetype-${filetype}" style="font-size: 2rem;"></i>
                        </p>
        </div>
        <hr class="m-0 p-0">
        `;
      } else {
        var fileheader = `
        <div class="card-header border-0 bg-transparent text-end p-0 mb-0 hover-overlay">
       <p class="text-right mb-0 p-1 text-black" style="text-align: right; font-size : 1rem">
                    <span class="p-1" style="text-align: right; font-size : 0.8rem">${filename}</span>
                    <span class="p-1" style="text-align: right; font-size : 0.8rem">${filesize}</span>
                            <i class="bi bi-filetype-${filetype}" style="font-size: 2rem;"></i>
                        </p>
        </div>
        <hr class="m-0 p-0">
        `;
      }

      var controlarea_transmit = `
        <div class="ms-auto" id="msg-${obj._id}-control-area">
                <button class="btn bg-transparent p-1 m-1"><i class="bi bi-arrow-repeat" id="retransmit-msg-${obj._id}" style="font-size: 1.2rem; color: grey;"></i></button>
                <button class="btn bg-transparent p-1 m-1"><i class="bi bi-download" id="save-file-msg-${obj._id}" style="font-size: 1.2rem; color: grey;"></i></button>
                <button class="btn bg-transparent p-1 m-1"><i class="bi bi-trash" id="del-msg-${obj._id}" style="font-size: 1.2rem; color: grey;"></i></button>
             </div>

        `;

      var controlarea_receive = `

             <div class="me-auto" id="msg-${obj._id}-control-area">
                <button class="btn bg-transparent p-1 m-1"><i class="bi bi-download" id="save-file-msg-${obj._id}" style="font-size: 1.2rem; color: grey;"></i></button>
                <button class="btn bg-transparent p-1 m-1"><i class="bi bi-trash" id="del-msg-${obj._id}" style="font-size: 1.2rem; color: grey;"></i></button>
             </div>

        `;
    } else {
      var filename = "";
      var fileheader = "";
      var filetype = "text/plain";
      var controlarea_transmit = `
<div class="ms-auto" id="msg-${obj._id}-control-area">
                <button class="btn bg-transparent p-1 m-1"><i class="bi bi-arrow-repeat" id="retransmit-msg-${obj._id}" style="font-size: 1.2rem; color: grey;"></i></button>
                <button class="btn bg-transparent p-1 m-1"><i class="bi bi-trash" id="del-msg-${obj._id}" style="font-size: 1.2rem; color: grey;"></i></button>
             </div>
        `;
      var controlarea_receive = `
      <div class="float-start" id="msg-${obj._id}-control-area">
                      <button class="btn bg-transparent p-1 m-1"><i class="bi bi-trash" id="del-msg-${obj._id}" style="font-size: 1.2rem; color: grey;"></i></button>
                   </div>
              `;
    }
  } catch (err) {
    console.log("error with database parsing...");
    console.log(err);
  }
  // CALLSIGN LIST
  if (!document.getElementById("chat-" + dxcallsign + "-list")) {
    // increment callsign counter
    callsign_counter++;
    if (callsign_counter == 1) {
      var callsign_selected = "active show";
      //document.getElementById('chatModuleDxCall').value = dxcallsign;
      selected_callsign = dxcallsign;
    }

    var new_callsign = `
            <a class="list-group-item list-group-item-action rounded-4 rounded-top rounded-bottom border-1 mb-2 ${callsign_selected}" id="chat-${dxcallsign}-list" data-bs-toggle="list" href="#chat-${dxcallsign}" role="tab" aria-controls="chat-${dxcallsign}">

                      <div class="d-flex w-100 justify-content-between">
                          <div class="rounded-circle p-0">
                            <i class="bi bi-person-circle p-1" style="font-size:2rem;"></i>
                          </div>

                        <h5 class="mb-1">${dxcallsign}</h5>
                        <span class="badge bg-secondary text-white p-1 h-100" id="chat-${dxcallsign}-list-dxgrid"><small>${dxgrid}</small></span>
                        <span style="font-size:0.8rem;" id="chat-${dxcallsign}-list-time">${timestampHours}</span>
                        <span class="position-absolute m-2 bottom-0 end-0" style="font-size:0.8rem;" id="chat-${dxcallsign}-list-shortmsg">${shortmsg}</span>
                      </div>

                  </a>

            `;
    document
      .getElementById("list-tab")
      .insertAdjacentHTML("beforeend", new_callsign);
    var message_area = `
            <div class="tab-pane fade ${callsign_selected}" id="chat-${dxcallsign}" role="tabpanel" aria-labelledby="chat-${dxcallsign}-list"></div>
            `;
    document
      .getElementById("nav-tabContent")
      .insertAdjacentHTML("beforeend", message_area);
    // create eventlistener for listening on clicking on a callsign
    document
      .getElementById("chat-" + dxcallsign + "-list")
      .addEventListener("click", function () {
        //document.getElementById('chatModuleDxCall').value = dxcallsign;
        selected_callsign = dxcallsign;

        setTimeout(scrollMessagesToBottom, 200);
      });

    // if callsign entry already exists - update
  } else {
    // gridsquare - update only on receive
    if (obj.type !== "transmit") {
      document.getElementById("chat-" + dxcallsign + "-list-dxgrid").innerHTML =
        dxgrid;
    }
    // time
    document.getElementById("chat-" + dxcallsign + "-list-time").innerHTML =
      timestampHours;
    // short message
    document.getElementById("chat-" + dxcallsign + "-list-shortmsg").innerHTML =
      shortmsg;
  }
  // APPEND MESSAGES TO CALLSIGN

  if (!document.getElementById("msg-" + obj._id)) {
    if (obj.type == "ping") {
      var new_message = `
                <div class="m-auto mt-1 p-0 w-50 rounded bg-secondary bg-gradient" id="msg-${obj._id}">
                    <p class="text-small text-white mb-0 text-break" style="font-size: 0.7rem;"><i class="m-3 bi bi-arrow-left-right"></i>snr: ${obj.snr} - ${timestamp}     </p>
                </div>
            `;
    }
    if (obj.type == "ping-ack") {
      var new_message = `
                <div class="m-auto mt-1 p-0 w-50 rounded bg-secondary bg-gradient" id="msg-${obj._id}">
                    <p class="text-small text-white mb-0 text-break" style="font-size: 0.7rem;"><i class="m-3 bi bi-check-lg"></i>Ping ack dx/mine snr: ${obj.snr} - ${timestamp}     </p>
                </div>
            `;
    }
    if (obj.type == "beacon") {
      var new_message = `
                <div class="p-0 rounded m-auto mt-1 w-50 bg-info bg-gradient" id="msg-${obj._id}">
                    <p class="text-small text-white text-break" style="font-size: 0.7rem;"><i class="m-3 bi bi-broadcast"></i>snr: ${obj.snr} - ${timestamp}     </p>
                </div>
            `;
    }

    if (obj.type == "newchat") {
      var new_message = `
                <div class="p-0 rounded m-auto mt-1 w-50 bg-light bg-gradient" id="msg-${obj._id}">
                    <p class="text-small text-dark text-break" style="font-size: 0.7rem;"><i class="m-3 bi bi-file-earmark-plus"></i> new chat opened - ${timestamp}     </p>
                </div>
            `;
    }

    // CHECK FOR NEW LINE AND REPLACE WITH <br>
    var message_html = obj.msg.replaceAll(/\n/g, "<br>");

    if (obj.type == "received") {
      var new_message = `
             <div class="d-flex align-items-center" style="margin-left: auto;"> <!-- max-width: 75%;  -->

                    <div class="mt-3 rounded-3 mb-0" style="max-width: 75%;" id="msg-${obj._id}">
                    <!--<p class="font-monospace text-small mb-0 text-muted text-break">${timestamp}</p>-->
                    <div class="card border-light bg-light" id="msg-${obj._id}">
                      ${fileheader}

                      <div class="card-body rounded-3 p-0">
                        <p class="card-text p-2 mb-0 text-break text-wrap">${message_html}</p>
                        <p class="text-right mb-0 p-1 text-white" style="text-align: left; font-size : 0.9rem">
                            <span class="badge bg-light text-muted">${timestamp}</span>

                        </p>
                      </div>
                    </div>
                </div>
                ${controlarea_receive}
                </div>
                `;
    }

    if (obj.type == "transmit") {
      //console.log('msg-' + obj._id + '-status')

      if (obj.status == "failed") {
        var progressbar_bg = "bg-danger";
      } else {
        var progressbar_bg = "bg-primary";
      }

      //Sneak in low graphics mode if so enabled for progress bars
      if (config.high_graphics.toString().toUpperCase() != "TRUE") {
        progressbar_bg += " disable-effects";
        //console.log("Low graphics enabled for chat module");
      }
      var new_message = `

            <div class="d-flex align-items-center"> <!-- max-width: 75%;  w-75 -->

            ${controlarea_transmit}

            <div class="rounded-3 mt-2 mb-0" style="max-width: 75%;" > <!-- w-100 style="margin-left: auto;"-->

                    <!--<p class="font-monospace text-right mb-0 text-muted" style="text-align: right;">${timestamp}</p>-->
                    <div class="card border-primary  bg-primary" id="msg-${
                      obj._id
                    }">
                    ${fileheader}

                      <div class="card-body rounded-3 p-0 text-right bg-primary">
                        <p class="card-text p-1 mb-0 text-white text-break text-wrap">${message_html}</p>
                        <p class="text-right mb-0 p-1 text-white" style="text-align: right; font-size : 0.9rem">
                            <span class="text-light" style="font-size: 0.7rem;">${timestamp} - </span>

                            <span class="text-white" id="msg-${
                              obj._id
                            }-status" style="font-size:0.8rem;">${get_icon_for_state(
        obj.status
      )}</span>

                            <!--<button type="button" id="retransmit-msg-${
                              obj._id
                            }" class="btn btn-sm btn-light p-0" style="height:20px;width:30px"><i class="bi bi-arrow-repeat" style="font-size: 0.9rem; color: black;"></i></button>-->

                        </p>

                       <div class="progress p-0 m-0 rounded-0 rounded-bottom bg-secondary" style="height: 10px;">
                            <div class="progress-bar progress-bar-striped ${progressbar_bg} p-0 m-0 rounded-0 force-gpu" id="msg-${
        obj._id
      }-progress" role="progressbar" style="width: ${
        obj.percent
      }%;" aria-valuenow="${obj.percent}" aria-valuemin="0" aria-valuemax="100">
							 </div>


							<p class="justify-content-center d-flex position-absolute m-0 p-0 w-100 text-white" style="font-size: xx-small" id="msg-${
                obj._id
              }-progress-information">
							    ${obj.percent} % - ${obj.bytesperminute} Bpm

							</p>




                            </div>
                      </div>
                    </div>

                </div>

                </div>

                `;
    }
    // CHECK CHECK CHECK --> This could be done better
    var id = "chat-" + obj.dxcallsign;
    document.getElementById(id).insertAdjacentHTML("beforeend", new_message);

    /* UPDATE EXISTING ELEMENTS */
  } else if (document.getElementById("msg-" + obj._id)) {
    console.log("element already exists......");
    console.log(obj);

    console.log(
      document
        .getElementById("msg-" + obj._id + "-progress")
        .getAttribute("aria-valuenow")
    );

    document.getElementById("msg-" + obj._id + "-status").innerHTML =
      get_icon_for_state(obj.status);

    document
      .getElementById("msg-" + obj._id + "-progress")
      .setAttribute("aria-valuenow", obj.percent);
    document
      .getElementById("msg-" + obj._id + "-progress")
      .setAttribute("style", "width:" + obj.percent + "%;");
    document.getElementById(
      "msg-" + obj._id + "-progress-information"
    ).innerHTML = obj.percent + "% - " + obj.bytesperminute + " Bpm";

    if (obj.percent >= 100) {
      //document.getElementById('msg-' + obj._id + '-progress').classList.remove("progress-bar-striped");
      document
        .getElementById("msg-" + obj._id + "-progress")
        .classList.remove("progress-bar-animated");
      document
        .getElementById("msg-" + obj._id + "-progress")
        .classList.remove("bg-danger");
      document
        .getElementById("msg-" + obj._id + "-progress")
        .classList.add("bg-primary");

      document.getElementById("msg-" + obj._id + "-progress").innerHTML = "";
    } else {
      document
        .getElementById("msg-" + obj._id + "-progress")
        .classList.add("progress-bar-striped");
      document
        .getElementById("msg-" + obj._id + "-progress")
        .classList.add("progress-bar-animated");
    }

    if (obj.status == "failed") {
      //document.getElementById('msg-' + obj._id + '-progress').classList.remove("progress-bar-striped");
      document
        .getElementById("msg-" + obj._id + "-progress")
        .classList.remove("progress-bar-animated");
      document
        .getElementById("msg-" + obj._id + "-progress")
        .classList.remove("bg-primary");
      document
        .getElementById("msg-" + obj._id + "-progress")
        .classList.add("bg-danger");
    }

    //document.getElementById(id).className = message_class;
  }

  //Delete message event listener
  if (
    document.getElementById("del-msg-" + obj._id) &&
    !document
      .getElementById("del-msg-" + obj._id)
      .hasAttribute("listenerOnClick")
  ) {
    // set Attribute to determine if we already created an EventListener for this element
    document
      .getElementById("del-msg-" + obj._id)
      .setAttribute("listenerOnClick", "true");
    document
      .getElementById("del-msg-" + obj._id)
      .addEventListener("click", () => {
        db.get(obj._id, {
          attachments: true,
        })
          .then(function (doc) {
            db.remove(doc._id, doc._rev, function (err) {
              if (err) console.log("Error removing item " + err);
            });
          })
          .catch(function (err) {
            console.log(err);
          });

        document.getElementById("msg-" + obj._id).remove();
        document.getElementById("msg-" + obj._id + "-control-area").remove();
        console.log("Removed message " + obj._id.toString());
      });
    //scrollMessagesToBottom();
  }

  // CREATE SAVE TO FOLDER EVENT LISTENER
  if (
    document.getElementById("save-file-msg-" + obj._id) &&
    !document
      .getElementById("save-file-msg-" + obj._id)
      .hasAttribute("listenerOnClick")
  ) {
    // set Attribute to determine if we already created an EventListener for this element
    document
      .getElementById("save-file-msg-" + obj._id)
      .setAttribute("listenerOnClick", "true");

    document
      .getElementById("save-file-msg-" + obj._id)
      .addEventListener("click", () => {
        saveFileToFolder(obj._id);
      });
  }
  // CREATE RESEND MSG EVENT LISTENER

  // check if element exists and if we already created NOT created an event listener
  if (
    document.getElementById("retransmit-msg-" + obj._id) &&
    !document
      .getElementById("retransmit-msg-" + obj._id)
      .hasAttribute("listenerOnClick")
  ) {
    // set Attribute to determine if we already created an EventListener for this element
    document
      .getElementById("retransmit-msg-" + obj._id)
      .setAttribute("listenerOnClick", "true");
    document
      .getElementById("retransmit-msg-" + obj._id)
      .addEventListener("click", () => {
        db.get(obj._id, {
          attachments: true,
        })
          .then(function (doc) {
            // handle doc
            console.log(doc);

            var filename = Object.keys(obj._attachments)[0];
            var filetype = filename.content_type;

            console.log(filename);
            console.log(filetype);
            var file = obj._attachments[filename].data;
            console.log(file);
            console.log(Object.keys(obj._attachments)[0].data);

            //var file = atob(obj._attachments[filename]["data"])
            db.getAttachment(obj._id, filename).then(function (data) {
              console.log(data);
              //Rewrote this part to use buffers to ensure encoding is corect -- n1qm
              var binaryString = atob_FD(data);

              console.log(binaryString);
              var data_with_attachment =
                doc.timestamp +
                split_char +
                doc.msg +
                split_char +
                filename +
                split_char +
                filetype +
                split_char +
                binaryString;
              let Data = {
                command: "send_message",
                dxcallsign: doc.dxcallsign,
                mode: 255,
                frames: 1,
                data: data_with_attachment,
                checksum: doc.checksum,
                uuid: doc.uuid,
              };
              console.log(Data);
              ipcRenderer.send("run-tnc-command", Data);
            });
            /*
                    // convert blob data to binary string
                    blobUtil.blobToBinaryString(data).then(function (binaryString) {
                        console.log(binaryString)
                    }).catch(function (err) {
                      // error
                      console.log(err);
                      binaryString = blobUtil.arrayBufferToBinaryString(data);

                    }).then(function(){

                        console.log(binaryString)
                        console.log(binaryString.length)

                        var data_with_attachment = doc.timestamp + split_char + utf8.encode(doc.msg) + split_char + filename + split_char + filetype + split_char + binaryString;
                            let Data = {
                                command: "send_message",
                                dxcallsign: doc.dxcallsign,
                                mode: 255,
                                frames: 1,
                                data: data_with_attachment,
                                checksum: doc.checksum,
                                uuid: doc.uuid
                            };
                            console.log(Data)
                            ipcRenderer.send('run-tnc-command', Data);

                    });
                });
                */
          })
          .catch(function (err) {
            console.log(err);
          });
      });
  }
  //window.location = window.location

  // scroll to bottom on new message
  scrollMessagesToBottom();
};

function saveFileToFolder(id) {
  db.get(id, {
    attachments: true,
  })
    .then(function (obj) {
      console.log(obj);
      console.log(Object.keys(obj._attachments)[0].content_type);
      var filename = Object.keys(obj._attachments)[0];
      var filetype = filename.content_type;
      var file = filename.data;
      console.log(file);
      console.log(filename.data);
      db.getAttachment(id, filename)
        .then(function (data) {
          // handle result
          console.log(data.length);
          //data = new Blob([data.buffer], { type: 'image/png' } /* (1) */)
          console.log(data);
          // we need to encode data because of error "an object could not be cloned"
          let Data = {
            file: data,
            filename: filename,
            filetype: filetype,
          };
          console.log(Data);
          ipcRenderer.send("save-file-to-folder", Data);
        })
        .catch(function (err) {
          console.log(err);
          return false;
        });
    })
    .catch(function (err) {
      console.log(err);
    });
}

// function for setting an ICON to the corresponding state
function get_icon_for_state(state) {
  if (state == "transmit") {
    var status_icon = '<i class="bi bi-check" style="font-size:1rem;"></i>';
  } else if (state == "transmitting") {
    //var status_icon = '<i class="bi bi-arrow-left-right" style="font-size:0.8rem;"></i>';
    var status_icon = `
            <i class="spinner-border ms-auto" style="width: 0.8rem; height: 0.8rem;" role="status" aria-hidden="true"></i>
        `;
  } else if (state == "failed") {
    var status_icon =
      '<i class="bi bi-exclamation-circle" style="font-size:1rem;"></i>';
  } else if (state == "transmitted") {
    var status_icon = '<i class="bi bi-check-all" style="font-size:1rem;"></i>';
  } else {
    var status_icon = '<i class="bi bi-question" style="font-size:1rem;"></i>';
  }
  return status_icon;
}

update_chat_obj_by_uuid = function (uuid) {
  db.get(uuid, {
    attachments: true,
  })
    .then(function (doc) {
      update_chat(doc);
      //return doc
    })
    .catch(function (err) {
      console.log(err);
    });
};

add_obj_to_database = function (obj) {
  db.put({
    _id: obj.uuid,
    timestamp: parseInt(obj.timestamp),
    uuid: obj.uuid,
    dxcallsign: obj.dxcallsign,
    dxgrid: obj.dxgrid,
    msg: obj.msg,
    checksum: obj.checksum,
    type: obj.type,
    command: obj.command,
    status: obj.status,
    snr: obj.snr,
    _attachments: {
      [obj.filename]: {
        content_type: obj.filetype,
        data: obj.file,
      },
    },
  })
    .then(function (response) {
      console.log("new database entry");
      console.log(response);
    })
    .catch(function (err) {
      console.log(err);
    });
};

/* users database functions */
addUserToDatabaseIfNotExists = function (obj) {
  /*
    "user_info_callsign",
    "user_info_gridsquare",
    "user_info_name",
    "user_info_age",
    "user_info_location",
    "user_info_radio",
    "user_info_antenna",
    "user_info_email",
    "user_info_website",
    "user_info_comments",
*/
  console.log(obj);
  users
    .find({
      selector: {
        user_info_callsign: obj.user_info_callsign,
      },
    })
    .then(function (result) {
      // handle result
      if (result.docs.length > 0) {
        users
          .put({
            _id: result.docs[0]._id,
            _rev: result.docs[0]._rev,
            user_info_callsign: obj.user_info_callsign,
            user_info_gridsquare: obj.user_info_gridsquare,
            user_info_name: obj.user_info_name,
            user_info_age: obj.user_info_age,
            user_info_location: obj.user_info_location,
            user_info_radio: obj.user_info_radio,
            user_info_antenna: obj.user_info_antenna,
            user_info_email: obj.user_info_email,
            user_info_website: obj.user_info_website,
            user_info_comments: obj.user_info_comments,
          })
          .then(function (response) {
            console.log("UPDATED USER");
            console.log(response);
            console.log(obj);
          })
          .catch(function (err) {
            console.log(err);
          });
      } else {
        users
          .post({
            user_info_callsign: obj.user_info_callsign,
            user_info_gridsquare: obj.user_info_gridsquare,
            user_info_name: obj.user_info_name,
            user_info_age: obj.user_info_age,
            user_info_location: obj.user_info_location,
            user_info_radio: obj.user_info_radio,
            user_info_antenna: obj.user_info_antenna,
            user_info_email: obj.user_info_email,
            user_info_website: obj.user_info_website,
            user_info_comments: obj.user_info_comments,
          })
          .then(function (response) {
            console.log("NEW USER ADDED");
          })
          .catch(function (err) {
            console.log(err);
          });
      }
    })
    .catch(function (err) {
      console.log(err);
    });
};

// Scroll to bottom of message-container
function scrollMessagesToBottom() {
  var messageBody = document.getElementById("message-container");
  messageBody.scrollTop = messageBody.scrollHeight - messageBody.clientHeight;
}

// CRC CHECKSUMS
// https://stackoverflow.com/a/50579690
// crc32 calculation
//console.log(crc32('abc'));
//var crc32=function(r){for(var a,o=[],c=0;c<256;c++){a=c;for(var f=0;f<8;f++)a=1&a?3988292384^a>>>1:a>>>1;o[c]=a}for(var n=-1,t=0;t<r.length;t++)n=n>>>8^o[255&(n^r.charCodeAt(t))];return(-1^n)>>>0};
//console.log(crc32('abc').toString(16).toUpperCase()); // hex

var makeCRCTable = function () {
  var c;
  var crcTable = [];
  for (var n = 0; n < 256; n++) {
    c = n;
    for (var k = 0; k < 8; k++) {
      c = c & 1 ? 0xedb88320 ^ (c >>> 1) : c >>> 1;
    }
    crcTable[n] = c;
  }
  return crcTable;
};

var crc32 = function (str) {
  var crcTable = window.crcTable || (window.crcTable = makeCRCTable());
  var crc = 0 ^ -1;

  for (var i = 0; i < str.length; i++) {
    crc = (crc >>> 8) ^ crcTable[(crc ^ str.charCodeAt(i)) & 0xff];
  }

  return (crc ^ -1) >>> 0;
};
/**
 * Binary to ASCII replacement
 * @param {string} data in normal/usual utf-8 format
 * @returns base64 encoded string
 */
function btoa_FD(data) {
  return Buffer.from(data, "utf-8").toString("base64");
}
/**
 * ASCII to Binary replacement
 * @param {string} data in base64 encoding
 * @returns utf-8 normal/usual string
 */
function atob_FD(data) {
  return Buffer.from(data, "base64").toString("utf-8");
}
/**
 * UTF8 to ASCII btoa
 * @param {string} data in base64 encoding
 * @returns base64 bota compatible data
 */
function atoa_FD(data) {
  return window.btoa(Buffer.from(data,"base64").toString("utf8"));
}
function returnObjFromCallsign(database, callsign) {
  users
    .find({
      selector: {
        user_info_callsign: callsign,
      },
    })
    .then(function (result) {
      if (typeof result.docs[0] !== "undefined") {
        return result.docs[0];
      } else {
        return false;
      }
    })
    .catch(function (err) {
      console.log(err);
    });
}

function createChatIndex() {
  db.createIndex({
    index: {
      fields: [
        "timestamp",
        "uuid",
        "dxcallsign",
        "dxgrid",
        "msg",
        "checksum",
        "type",
        "command",
        "status",
        "percent",
        "bytesperminute",
        "_attachments",
      ],
    },
  })
    .then(function (result) {
      // handle result
      console.log(result);
    })
    .catch(function (err) {
      console.log(err);
    });
}

function createUserIndex() {
  users
    .createIndex({
      index: {
        fields: [
          "timestamp",
          "user_info_callsign",
          "user_info_gridsquare",
          "user_info_name",
          "user_info_age",
          "user_info_location",
          "user_info_radio",
          "user_info_antenna",
          "user_info_email",
          "user_info_website",
          "user_info_comments",
          "_attachments",
        ],
      },
    })
    .then(function (result) {
      // handle result
      console.log(result);
      return true;
    })
    .catch(function (err) {
      console.log(err);
      return false;
    });
}

function updateAllChat(clear) {
  if (clear == true) {
    filetype = "";
    file = "";
    filename = "";
    callsign_counter = 0;
    selected_callsign = "";
    dxcallsigns = new Set();
    document.getElementById("list-tab").innerHTML = "";
    document.getElementById("nav-tabContent").innerHTML = "";
    //document.getElementById("list-tab").childNodes.remove();
    //document.getElementById("nav-tab-content").childrenNodes.remove();
  }
  //Ensure we create an index before running db.find
  //We can't rely on the default index existing before we get here...... :'(
  db.createIndex({
    index: {
      fields: [{ timestamp: "asc" }],
    },
  })
    .then(function (result) {
      // handle result
      db.find({
        selector: {
          $and: [{ timestamp: { $exists: true } }, { $or: chatFilter }],
          //$or: chatFilter
        },
        sort: [
          {
            timestamp: "asc",
          },
        ],
      })
        .then(async function (result) {
          // handle result async
          if (typeof result !== "undefined") {
            for (const item of result.docs) {
              //await otherwise history will not be in chronological order
              await db
                .get(item._id, {
                  attachments: true,
                })
                .then(function (item_with_attachments) {
                  update_chat(item_with_attachments);
                });
            }
          }
        })
        .catch(function (err) {
          console.log(err);
        });
    })
    .catch(function (err) {
      console.log(err);
    });
}
