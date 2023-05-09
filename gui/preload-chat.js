const path = require("path");
const { ipcRenderer } = require("electron");
const { v4: uuidv4 } = require("uuid");
const imageCompression = require("browser-image-compression");
const blobUtil = require("blob-util");
const FD = require("./freedata");
const fs = require("fs");

// https://stackoverflow.com/a/26227660
var appDataFolder =
  process.env.APPDATA ||
  (process.platform == "darwin"
    ? process.env.HOME + "/Library/Application Support"
    : process.env.HOME + "/.config");
var configFolder = path.join(appDataFolder, "FreeDATA");
var configPath = path.join(configFolder, "config.json");
var config = require(configPath);
// set date format
const dateFormat = new Intl.DateTimeFormat(navigator.language, {
  timeStyle: "long",
  dateStyle: "short",
});
// set date format information
const dateFormatShort = new Intl.DateTimeFormat(navigator.language, {
  year: "numeric",
  month: "numeric",
  day: "numeric",
  hour: "numeric",
  minute: "numeric",
  second: "numeric",
  hour12: false,
});

const dateFormatHours = new Intl.DateTimeFormat(navigator.language, {
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
var defaultUserIcon =
  "data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIxNiIgaGVpZ2h0PSIxNiIgZmlsbD0iY3VycmVudENvbG9yIiBjbGFzcz0iYmkgYmktcGVyc29uLWJvdW5kaW5nLWJveCIgdmlld0JveD0iMCAwIDE2IDE2Ij4KICA8cGF0aCBkPSJNMS41IDFhLjUuNSAwIDAgMC0uNS41djNhLjUuNSAwIDAgMS0xIDB2LTNBMS41IDEuNSAwIDAgMSAxLjUgMGgzYS41LjUgMCAwIDEgMCAxaC0zek0xMSAuNWEuNS41IDAgMCAxIC41LS41aDNBMS41IDEuNSAwIDAgMSAxNiAxLjV2M2EuNS41IDAgMCAxLTEgMHYtM2EuNS41IDAgMCAwLS41LS41aC0zYS41LjUgMCAwIDEtLjUtLjV6TS41IDExYS41LjUgMCAwIDEgLjUuNXYzYS41LjUgMCAwIDAgLjUuNWgzYS41LjUgMCAwIDEgMCAxaC0zQTEuNSAxLjUgMCAwIDEgMCAxNC41di0zYS41LjUgMCAwIDEgLjUtLjV6bTE1IDBhLjUuNSAwIDAgMSAuNS41djNhMS41IDEuNSAwIDAgMS0xLjUgMS41aC0zYS41LjUgMCAwIDEgMC0xaDNhLjUuNSAwIDAgMCAuNS0uNXYtM2EuNS41IDAgMCAxIC41LS41eiIvPgogIDxwYXRoIGQ9Ik0zIDE0cy0xIDAtMS0xIDEtNCA2LTQgNiAzIDYgNC0xIDEtMSAxSDN6bTgtOWEzIDMgMCAxIDEtNiAwIDMgMyAwIDAgMSA2IDB6Ii8+Cjwvc3ZnPg==";

// -----------------------------------
// Initially fill sharedFolderFileList
//TODO: Make this automatically ever N seconds
var sharedFolderFileList = "";
ipcRenderer.send("read-files-in-folder", {
  folder: config.shared_folder_path,
});

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
PouchDB.plugin(require("pouchdb-upsert"));

var db = new PouchDB(chatDB);
var users = new PouchDB(userDB);

/* -------- CREATE DATABASE INDEXES */
createChatIndex();
createUserIndex();

// REMOTE SYNC ATTEMPTS

//var remoteDB = new PouchDB('http://172.20.10.4:5984/chatDB')
/*
// we need express packages for running pouchdb sync "express-pouchdb"
var express = require('express');
var app = express();
app.use('/chatDB', require('express-pouchdb')(PouchDB));
app.listen(5984);




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

//Set default chat filter
var chatFilter = [
  { type: "newchat" },
  { type: "received" },
  { type: "transmit" },
  { type: "ping-ack" },
  //{ type: "request" },
  //{ type: "response" },
];

updateAllChat(false);

// WINDOW LISTENER
window.addEventListener("DOMContentLoaded", () => {
  // theme selector
  changeGuiDesign(config.theme);

  const userInfoFields = [
    "user_info_image",
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
      console.log(result);
      if (typeof result.docs[0] !== "undefined") {
        // handle result
        userInfoFields.forEach(function (elem) {
          if (elem !== "user_info_image") {
            document.getElementById(elem).value = result.docs[0][elem];
          } else {
            document.getElementById(elem).src = result.docs[0][elem];
          }
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

  //save user info
  document.getElementById("userInfoSave").addEventListener("click", () => {
    let obj = new Object();
    userInfoFields.forEach(function (subelem) {
      if (subelem !== "user_info_image") {
        obj[subelem] = document.getElementById(subelem).value;
      } else {
        obj[subelem] = document.getElementById(subelem).src;
      }
    });
    addUserToDatabaseIfNotExists(obj);
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
    if (document.getElementById("chkRequest").checked == true)
      chatFilter.push({ type: "request" });
    if (document.getElementById("chkResponse").checked == true)
      chatFilter.push({ type: "response" });
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

  document.getElementById("requestUserInfo").addEventListener("click", () => {
    ipcRenderer.send("run-tnc-command", {
      command: "requestUserInfo",
      dxcallsign: selected_callsign,
    });

    pauseButton(document.getElementById("requestUserInfo"), 60000);
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
    if (lastIsWritingBroadcast < new Date().getTime() - 5 * 2000) {
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

  // open file selector for user image
  document.getElementById("userImageSelector").addEventListener("click", () => {
    ipcRenderer.send("select-user-image", {
      title: "Title",
    });
  });

  // open file selector for shared folder
  document
    .getElementById("sharedFolderButton")
    .addEventListener("click", () => {
      ipcRenderer.send("read-files-in-folder", {
        folder: config.shared_folder_path,
      });
    });

  document
    .getElementById("openSharedFilesFolder")
    .addEventListener("click", () => {
      ipcRenderer.send("open-folder", {
        path: config.shared_folder_path,
      });
    });

  document
    .getElementById("requestSharedFolderList")
    .addEventListener("click", () => {
      ipcRenderer.send("run-tnc-command", {
        command: "requestSharedFolderList",
        dxcallsign: selected_callsign,
      });

      pauseButton(document.getElementById("requestSharedFolderList"), 60000);
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
      command: "msg",
      dxcallsign: dxcallsign,
      mode: 255,
      frames: 5,
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
      attempt: 1,
      uuid: uuid,
      _attachments: {
        [filename]: {
          content_type: filetype,
          //data: btoa(file)
          data: FD.btoa_FD(file),
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

ipcRenderer.on("return-shared-folder-files", (event, arg) => {
  console.log(arg);
  sharedFolderFileList = arg.files;

  var tbl = document.getElementById("sharedFolderTable");
  if (tbl == undefined) return;
  tbl.innerHTML = "";
  let counter = 0;
  arg.files.forEach((file) => {
    //console.log(file["name"]);
    var row = document.createElement("tr");

    let id = document.createElement("td");
    let idText = document.createElement("span");
    idText.innerText = counter += 1;
    id.appendChild(idText);
    row.appendChild(id);

    let filename = document.createElement("td");
    let filenameText = document.createElement("span");
    filenameText.innerText = file["name"];
    filename.appendChild(filenameText);
    row.appendChild(filename);

    let filetype = document.createElement("td");
    let filetypeText = document.createElement("span");
    filetypeText.innerHTML = `
                <i class="bi bi-filetype-${file["extension"]}" style="font-size: 1.8rem"></i>
                `;
    filetype.appendChild(filetypeText);
    row.appendChild(filetype);

    let filesize = document.createElement("td");
    let filesizeText = document.createElement("span");
    filesizeText.innerText = formatBytes(file["size"], 2);
    filesize.appendChild(filesizeText);
    row.appendChild(filesize);

    tbl.appendChild(row);
  });
});

ipcRenderer.on("return-select-user-image", (event, arg) => {
  let imageFiletype = arg.mime;
  let imageFile = arg.data;

  imageFile = blobUtil.base64StringToBlob(imageFile, imageFiletype);

  var options = {
    maxSizeMB: 0.01,
    maxWidthOrHeight: 125,
    useWebWorker: false,
  };

  imageCompression(imageFile, options)
    .then(function (compressedFile) {
      console.log(
        "compressedFile instanceof Blob",
        compressedFile instanceof Blob
      ); // true
      console.log(
        `compressedFile size ${compressedFile.size / 1024 / 1024} MB`
      ); // smaller than maxSizeMB

      console.log(compressedFile.size);

      blobUtil
        .blobToBase64String(compressedFile)
        .then(function (base64String) {
          // update image

          document.getElementById("user_info_image").src =
            "data:" + imageFiletype + ";base64," + base64String;
        })
        .catch(function (err) {
          document.getElementById("user_info_image").src = "img/icon.png";
        });
    })
    .catch(function (error) {
      console.log(error.message);
    });
});

ipcRenderer.on("action-update-transmission-status", (event, arg) => {
  var data = arg["data"][0];
  console.log(data.status);
  if (data.uuid !== "no-uuid") {
    db.get(data.uuid, {
      attachments: true,
    })
      .then(function (doc) {
        return db.put({
          _id: doc.uuid.toString(),
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
  }
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
      var encoded_data = FD.atob_FD(item.data);
      var splitted_data = encoded_data.split(split_char);

      console.log(splitted_data);

      if (splitted_data[1] == "msg") {
        obj.timestamp = parseInt(splitted_data[4]);
        obj.dxcallsign = item.dxcallsign;
        obj.dxgrid = item.dxgrid;
        obj.command = splitted_data[1];
        obj.checksum = splitted_data[2];
        obj.uuid = splitted_data[3];
        obj.msg = splitted_data[5];
        obj.status = "null";
        obj.snr = "null";
        obj.type = "received";
        obj.filename = splitted_data[6];
        obj.filetype = splitted_data[7];
        //obj.file = btoa(splitted_data[8]);
        obj.file = FD.btoa_FD(splitted_data[8]);
      } else if (splitted_data[1] == "req" && splitted_data[2] == "0") {
        obj.uuid = uuidv4().toString();
        obj.timestamp = Math.floor(Date.now() / 1000);
        obj.dxcallsign = item.dxcallsign;
        obj.command = splitted_data[1];
        obj.type = "request";
        obj.status = "received";
        obj.snr = "null";
        obj.msg = "Request for station info";
        obj.filename = "null";
        obj.filetype = "null";
        obj.file = "null";

        if (config.enable_request_profile == "True") {
          sendUserData(item.dxcallsign);
        }
      } else if (splitted_data[1] == "req" && splitted_data[2] == "1") {
        obj.uuid = uuidv4().toString();
        obj.timestamp = Math.floor(Date.now() / 1000);
        obj.dxcallsign = item.dxcallsign;
        obj.command = splitted_data[1];
        obj.type = "request";
        obj.status = "received";
        obj.snr = "null";
        obj.msg = "Request for shared folder list";
        obj.filename = "null";
        obj.filetype = "null";
        obj.file = "null";

        if (config.enable_request_shared_folder == "True") {
          sendSharedFolderList(item.dxcallsign);
        }
      } else if (
        splitted_data[1] == "req" &&
        splitted_data[2].substring(0, 1) == "2"
      ) {
        let name = splitted_data[2].substring(1);
        //console.log("In handle req for shared folder file");
        obj.uuid = uuidv4().toString();
        obj.timestamp = Math.floor(Date.now() / 1000);
        obj.dxcallsign = item.dxcallsign;
        obj.command = splitted_data[1];
        obj.type = "request";
        obj.status = "received";
        obj.snr = "null";
        obj.msg = "Request for shared file " + name;
        obj.filename = "null";
        obj.filetype = "null";
        obj.file = "null";

        if (config.enable_request_shared_folder == "True") {
          sendSharedFolderFile(item.dxcallsign, name);
        }
      } else if (splitted_data[1] == "res-0") {
        obj.uuid = uuidv4().toString();
        obj.timestamp = Math.floor(Date.now() / 1000);
        obj.dxcallsign = item.dxcallsign;
        obj.command = splitted_data[1];
        obj.type = "response";
        obj.status = "received";
        obj.snr = "null";
        obj.msg = "Response for station info";
        obj.filename = "null";
        obj.filetype = "null";
        obj.file = "null";

        console.log(splitted_data);
        let userData = new Object();
        userData.user_info_image = splitted_data[2];
        userData.user_info_callsign = splitted_data[3];
        userData.user_info_gridsquare = splitted_data[4];
        userData.user_info_name = splitted_data[5];
        userData.user_info_age = splitted_data[6];
        userData.user_info_location = splitted_data[7];
        userData.user_info_radio = splitted_data[8];
        userData.user_info_antenna = splitted_data[9];
        userData.user_info_email = splitted_data[10];
        userData.user_info_website = splitted_data[11];
        userData.user_info_comments = splitted_data[12];

        addUserToDatabaseIfNotExists(userData);
        getSetUserInformation(splitted_data[3]);
      } else if (splitted_data[1] == "res-1") {
        obj.uuid = uuidv4().toString();
        obj.timestamp = Math.floor(Date.now() / 1000);
        obj.dxcallsign = item.dxcallsign;
        obj.command = splitted_data[1];
        obj.type = "response";
        obj.status = "received";
        obj.snr = "null";
        obj.msg = "Response for shared file list";
        obj.filename = "null";
        obj.filetype = "null";
        obj.file = "null";

        console.log(splitted_data);

        let userData = new Object();

        userData.user_info_callsign = obj.dxcallsign;
        let filelist = JSON.parse(splitted_data[3]);
        console.log(filelist);
        userData.user_shared_folder = filelist;
        addFileListToUserDatabaseIfNotExists(userData);
        getSetUserSharedFolder(obj.dxcallsign);

        //getSetUserInformation(selected_callsign);
      } else if (splitted_data[1] == "res-2") {
        console.log("In received respons-2");
        let sharedFileInfo = splitted_data[2].split("/", 2);

        obj.uuid = uuidv4().toString();
        obj.timestamp = Math.floor(Date.now() / 1000);
        obj.dxcallsign = item.dxcallsign;
        obj.command = splitted_data[1];
        obj.type = "received";
        obj.status = "received";
        obj.snr = "null";
        obj.msg = "Response for shared file download";
        obj.filename = sharedFileInfo[0];
        obj.filetype = "application/octet-stream";
        obj.file = FD.btoa_FD(sharedFileInfo[1]);
      } else {
        console.log("no rule matched for handling received data!");
      }

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

  // check if obj.attempt exists
  if (typeof obj.attempt == "undefined") {
    db.upsert(obj._id, function (doc) {
      if (!doc.attempt) {
        doc.attempt = 1;
      }
      return doc;
    });
    obj.attempt = 1;
  }

  // define attempts
  if (typeof obj.attempt == "undefined") {
    var attempt = 1;
  } else {
    var attempt = obj.attempt;
  }

  if (typeof config.max_retry_attempts == "undefined") {
    var max_retry_attempts = 3;
  } else {
    var max_retry_attempts = parseInt(config.max_retry_attempts);
  }

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
          Math.ceil(FD.atob_FD(obj._attachments[filename]["data"]).length) +
          " Bytes";
      }

      // check if image, then display it
      if (filetype == "image/png" || filetype == "png") {
        var fileheader = `
        <div class="card-header border-0 bg-transparent text-end p-0 mb-0 hover-overlay">
        <img class="w-100 rounded-2" src="data:image/png;base64,${FD.atob(
          obj._attachments[filename]["data"]
        )}">
       <p class="text-right mb-0 p-1" style="text-align: right; font-size : 1rem">
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
       <p class="text-right mb-0 p-1" style="text-align: right; font-size : 1rem">
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
                <button class="btn bg-transparent p-1 m-1"><i class="bi bi-arrow-repeat link-secondary" id="retransmit-msg-${obj._id}" style="font-size: 1.2rem;"></i></button>
                <button class="btn bg-transparent p-1 m-1"><i class="bi bi-download link-secondary" id="save-file-msg-${obj._id}" style="font-size: 1.2rem;"></i></button>
                <button class="btn bg-transparent p-1 m-1"><i class="bi bi-trash link-secondary" id="del-msg-${obj._id}" style="font-size: 1.2rem;"></i></button>
             </div>

        `;

      var controlarea_receive = `

             <div class="me-auto" id="msg-${obj._id}-control-area">
                <button class="btn bg-transparent p-1 m-1"><i class="bi bi-download link-secondary" id="save-file-msg-${obj._id}" style="font-size: 1.2rem;"></i></button>
                <button class="btn bg-transparent p-1 m-1"><i class="bi bi-trash link-secondary" id="del-msg-${obj._id}" style="font-size: 1.2rem;"></i></button>
             </div>

        `;
    } else {
      var filename = "";
      var fileheader = "";
      var filetype = "text/plain";
      var controlarea_transmit = `
<div class="ms-auto" id="msg-${obj._id}-control-area">
                <button class="btn bg-transparent p-1 m-1"><i class="bi bi-arrow-repeat link-secondary" id="retransmit-msg-${obj._id}" style="font-size: 1.2rem;"></i></button>
                <button class="btn bg-transparent p-1 m-1"><i class="bi bi-trash link-secondary" id="del-msg-${obj._id}" style="font-size: 1.2rem;"></i></button>
             </div>
        `;
      var controlarea_receive = `
      <div class="float-start" id="msg-${obj._id}-control-area">
                      <button class="btn bg-transparent p-1 m-1"><i class="bi bi-trash link-secondary" id="del-msg-${obj._id}" style="font-size: 1.2rem;"></i></button>
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
    dxcallsigns.add(dxcallsign);
    if (
      (callsign_counter == 1 && selected_callsign == "") ||
      selected_callsign == dxcallsign
    ) {
      var callsign_selected = "active show";
      //document.getElementById('chatModuleDxCall').value = dxcallsign;
      selected_callsign = dxcallsign;
    }

    getSetUserInformation(dxcallsign);
    getSetUserSharedFolder(dxcallsign);

    var new_callsign = `
            <a class="list-group-item list-group-item-action rounded-4 rounded-top rounded-bottom border-1 mb-2 ${callsign_selected}" id="chat-${dxcallsign}-list" data-bs-toggle="list" href="#chat-${dxcallsign}" role="tab" aria-controls="chat-${dxcallsign}">

                      <div class="d-flex w-100 justify-content-between">
                          <div class="rounded-circle p-0">
                            <img id="user-image-${dxcallsign}" class="p-1 rounded-circle" src="data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIxNiIgaGVpZ2h0PSIxNiIgZmlsbD0iY3VycmVudENvbG9yIiBjbGFzcz0iYmkgYmktcGVyc29uLWNpcmNsZSIgdmlld0JveD0iMCAwIDE2IDE2Ij4KICA8cGF0aCBkPSJNMTEgNmEzIDMgMCAxIDEtNiAwIDMgMyAwIDAgMSA2IDB6Ii8+CiAgPHBhdGggZmlsbC1ydWxlPSJldmVub2RkIiBkPSJNMCA4YTggOCAwIDEgMSAxNiAwQTggOCAwIDAgMSAwIDh6bTgtN2E3IDcgMCAwIDAtNS40NjggMTEuMzdDMy4yNDIgMTEuMjI2IDQuODA1IDEwIDggMTBzNC43NTcgMS4yMjUgNS40NjggMi4zN0E3IDcgMCAwIDAgOCAxeiIvPgo8L3N2Zz4="></img>
                            <!--<i class="bi bi-person-circle p-1" style="font-size:2rem;"></i>-->
                          </div>

                        <span style="font-size:1.2rem;"><strong>${dxcallsign}</strong></span>
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

    // finally get and set user information to first selected item
    getSetUserInformation(selected_callsign);
    getSetUserSharedFolder(selected_callsign);

    // create eventlistener for listening on clicking on a callsign
    document
      .getElementById("chat-" + dxcallsign + "-list")
      .addEventListener("click", function () {
        //document.getElementById('chatModuleDxCall').value = dxcallsign;
        selected_callsign = dxcallsign;
        setTimeout(scrollMessagesToBottom, 200);

        //get user information
        getSetUserInformation(selected_callsign);
        getSetUserSharedFolder(selected_callsign);
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
      // check for messages which failed and try to transmit them
      if (config.enable_auto_retry.toUpperCase() == "TRUE") {
        checkForWaitingMessages(obj.dxcallsign);
      }

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
      // check for messages which failed and try to transmit them
      if (config.enable_auto_retry.toUpperCase() == "TRUE") {
        checkForWaitingMessages(obj.dxcallsign);
      }
      var new_message = `
                <div class="p-0 rounded m-auto mt-1 w-50 bg-info bg-gradient" id="msg-${obj._id}">
                    <p class="text-small text-white text-break" style="font-size: 0.7rem;"><i class="m-3 bi bi-broadcast"></i>snr: ${obj.snr} - ${timestamp}     </p>
                </div>
            `;
    }
    if (obj.type == "request") {
      var new_message = `
                <div class="p-0 rounded m-auto mt-1 w-50 bg-warning bg-gradient" id="msg-${obj._id}">
                    <p class="text-small text-white text-break" style="font-size: 0.7rem;"><i class="m-3 bi bi-info"></i>${obj.msg} - ${timestamp}     </p>
                </div>
            `;
    }
    if (obj.type == "response") {
      var new_message = `
                <div class="p-0 rounded m-auto mt-1 w-50 bg-warning bg-gradient" id="msg-${obj._id}">
                    <p class="text-small text-white text-break" style="font-size: 0.7rem;"><i class="m-3 bi bi-info"></i>Response - ${timestamp}     </p>
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
        var percent_value = "TRANSMISSION FAILED";
      } else if (obj.status == "transmitted") {
        var progressbar_bg = "bg-success";
        var percent_value = "TRANSMITTED";
      } else {
        var progressbar_bg = "bg-primary";
        var percent_value = obj.percent;
      }

      //Sneak in low graphics mode if so enabled for progress bars
      if (config.high_graphics.toString().toUpperCase() != "TRUE") {
        progressbar_bg += " disable-effects";
        //console.log("Low graphics enabled for chat module");
      }

      var new_message = `
        <div class="d-flex align-items-center">
            ${controlarea_transmit}
            <div class="rounded-3 mt-3 mb-0 me-2" style="max-width: 75%;">
                <div class="card border-primary bg-primary" id="msg-${obj._id}">
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
                        </p>
                        <span id="msg-${
                          obj._id
                        }-attempts-badge" class="position-absolute top-0 start-100 translate-middle badge rounded-1 bg-primary border border-white">

                            <span id="msg-${
                              obj._id
                            }-attempts" class="">${attempt}/${max_retry_attempts}</span>
                            <span class="visually-hidden">retries</span>
                        </span>
                        <div class="progress p-0 m-0 rounded-0 rounded-bottom bg-secondary" style="height: 10px;">
                            <div class="progress-bar progress-bar-striped ${progressbar_bg} p-0 m-0 rounded-0 force-gpu" id="msg-${
        obj._id
      }-progress" role="progressbar" style="width: ${
        obj.percent
      }%;" aria-valuenow="${
        obj.percent
      }" aria-valuemin="0" aria-valuemax="100"></div>
                            <p class="justify-content-center d-flex position-absolute m-0 p-0 w-100 text-white" style="font-size: xx-small" id="msg-${
                              obj._id
                            }-progress-information">${percent_value} % - ${
        obj.bytesperminute
      } Bpm</p>
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

    document.getElementById("msg-" + obj._id + "-attempts").innerHTML =
      obj.attempt + "/" + max_retry_attempts;

    if (obj.status == "transmitted") {
      //document.getElementById('msg-' + obj._id + '-progress').classList.remove("progress-bar-striped");
      document
        .getElementById("msg-" + obj._id + "-progress")
        .classList.remove("progress-bar-animated");
      document
        .getElementById("msg-" + obj._id + "-progress")
        .classList.remove("bg-danger");
      document
        .getElementById("msg-" + obj._id + "-progress")
        .classList.add("bg-success");

      document.getElementById("msg-" + obj._id + "-progress").innerHTML = "";
      document.getElementById(
        "msg-" + obj._id + "-progress-information"
      ).innerHTML = "TRANSMITTED - " + obj.bytesperminute + " Bpm";
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

      document.getElementById(
        "msg-" + obj._id + "-progress-information"
      ).innerHTML = "TRANSMISSION FAILED - " + obj.bytesperminute + " Bpm";
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

        // stop transmission if deleted message is still in progress
        if (obj.status == "transmitting") {
          let Data = {
            command: "stop_transmission",
          };
          ipcRenderer.send("run-tnc-command", Data);
        }
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
        // increment attempt
        db.upsert(obj._id, function (doc) {
          if (!doc.attempt) {
            doc.attempt = 1;
          }
          doc.attempt++;
          return doc;
        })
          .then(function (res) {
            // success, res is {rev: '1-xxx', updated: true, id: 'myDocId'}
            console.log(res);
            update_chat_obj_by_uuid(obj.uuid);
          })
          .catch(function (err) {
            // error
            console.log(err);
          });

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
              var binaryString = FD.atob_FD(data);

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
                command: "msg",
                dxcallsign: doc.dxcallsign,
                mode: 255,
                frames: 5,
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
                                command: "msg",
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
  console.log(obj);
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
    attempt: obj.attempt,
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
      console.log("already exists");
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
      console.log(result);
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
            user_info_image: obj.user_info_image,
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

addFileListToUserDatabaseIfNotExists = function (obj) {
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
            user_shared_folder: obj.user_shared_folder,
            user_info_callsign: result.docs[0].user_info_callsign,
            user_info_gridsquare: result.docs[0].user_info_gridsquare,
            user_info_name: result.docs[0].user_info_name,
            user_info_age: result.docs[0].user_info_age,
            user_info_location: result.docs[0].user_info_location,
            user_info_radio: result.docs[0].user_info_radio,
            user_info_antenna: result.docs[0].user_info_antenna,
            user_info_email: result.docs[0].user_info_email,
            user_info_website: result.docs[0].user_info_website,
            user_info_comments: result.docs[0].user_info_comments,
          })
          .then(function (response) {
            console.log("File List:  UPDATED USER");
            console.log(response);
            console.log(obj);
            getSetUserSharedFolder(obj.user_info_callsign);
          })
          .catch(function (err) {
            console.log(err);
          });
      } else {
        users
          .post({
            user_info_callsign: obj.user_info_callsign,
            user_shared_folder: obj.user_shared_folder,
          })
          .then(function (response) {
            console.log("File List:  NEW USER ADDED");
            getSetUserSharedFolder(obj.user_info_callsign);
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

function returnObjFromCallsign(database, callsign) {
  return new Promise((resolve, reject) => {
    users
      .find({
        selector: {
          user_info_callsign: callsign,
        },
      })
      .then(function (result) {
        //return new Promise((resolve, reject) => {
        if (typeof result.docs[0] !== "undefined") {
          resolve(result.docs[0]);
        } else {
          reject("Promise rejected");
        }

        /*
      if (typeof result.docs[0] !== "undefined") {
        return result.docs[0];




      } else {
        return false;
      }

      */
      })
      .catch(function (err) {
        console.log(err);
      });
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
        "attempt",
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
          "user_info_image",
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

async function updateAllChat(clear) {
  if (clear == true) {
    filetype = "";
    file = "";
    filename = "";
    callsign_counter = 0;
    //selected_callsign = "";
    dxcallsigns.clear();
    document.getElementById("list-tab").innerHTML = "";
    document.getElementById("nav-tabContent").innerHTML = "";
    //document.getElementById("list-tab").childNodes.remove();
    //document.getElementById("nav-tab-content").childrenNodes.remove();
  }
  //Ensure we create an index before running db.find
  //We can't rely on the default index existing before we get here...... :'(
  await db
    .createIndex({
      index: {
        fields: [{ timestamp: "asc" }],
      },
    })
    .then(async function (result) {
      // handle result
      await db
        .find({
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
          //document.getElementById("blurOverlay").classList.add("bg-primary");

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
  if (clear == true && dxcallsigns.has(selected_callsign) == false) {
    //Selected call sign is not visible, reset to first call sign
    let tmp = dxcallsigns.entries().next().value[0];
    selected_callsign = tmp;
    document
      .getElementById("chat-" + tmp + "-list")
      .classList.add("active", "show");
    document.getElementById("chat-" + tmp).classList.add("active", "show");
    scrollMessagesToBottom();
  }
}

function getSetUserSharedFolder(selected_callsign) {
  // TODO: This is a dirty hotfix for avoiding, this function is canceld too fast.
  console.log("get set user information:" + selected_callsign);

  if (
    selected_callsign == "" ||
    selected_callsign == null ||
    typeof selected_callsign == "undefined"
  ) {
    console.log("return triggered");
    return;
  }
  returnObjFromCallsign(users, selected_callsign)
    .then(function (data) {
      console.log(data);

      console.log(data.user_shared_folder);

      if (typeof data.user_shared_folder !== "undefined") {
        // shared folder table
        var icons = [
          "aac",
          "ai",
          "bmp",
          "cs",
          "css",
          "csv",
          "doc",
          "docx",
          "exe",
          "gif",
          "heic",
          "html",
          "java",
          "jpg",
          "js",
          "json",
          "jsx",
          "key",
          "m4p",
          "md",
          "mdx",
          "mov",
          "mp3",
          "mp4",
          "otf",
          "pdf",
          "php",
          "png",
          "ppt",
          "pptx",
          "psd",
          "py",
          "raw",
          "rb",
          "sass",
          "scss",
          "sh",
          "sql",
          "svg",
          "tiff",
          "tsx",
          "ttf",
          "txt",
          "wav",
          "woff",
          "xls",
          "xlsx",
          "xml",
          "yml",
        ];
        var tbl = document.getElementById("sharedFolderTableDX");
        tbl.innerHTML = "";
        let counter = 0;
        data.user_shared_folder.forEach((file) => {
          var row = document.createElement("tr");

          let dxcall = selected_callsign;
          let name = file["name"];
          let type = file["extension"];

          if (icons.indexOf(type) == -1) {
            type = "bi-file-earmark";
          } else {
            type = "bi-filetype-" + type;
          }

          let id = document.createElement("td");
          let idText = document.createElement("span");
          counter += 1;
          idText.innerHTML +=
            '<i class="bi bi-file-earmark-arrow-down" style="font-size: 1.8rem;cursor: pointer"></i> ' +
            counter;
          id.appendChild(idText);
          row.appendChild(id);

          let filename = document.createElement("td");
          let filenameText = document.createElement("span");
          filenameText.innerText = file["name"];
          filename.appendChild(filenameText);
          row.appendChild(filename);

          let filetype = document.createElement("td");
          let filetypeText = document.createElement("span");
          filetypeText.innerHTML = `<i class="bi ${type}" style="font-size: 1.8rem"></i>`;
          filetype.appendChild(filetypeText);
          row.appendChild(filetype);

          let filesize = document.createElement("td");
          let filesizeText = document.createElement("span");
          filesizeText.innerText = formatBytes(file["size"], 2);
          filesize.appendChild(filesizeText);
          row.appendChild(filesize);
          id.addEventListener("click", function () {
            //console.log(name," clicked");
            sendFileReq(dxcall, name);
          });
          tbl.appendChild(row);
        });
      } else {
        document.getElementById("sharedFolderTableDX").innerHTML = "no data";
      }
    })
    .catch(function (err) {
      console.log(err);
      document.getElementById("sharedFolderTableDX").innerHTML = "no data";
    });
}

function getSetUserInformation(selected_callsign) {
  //Get user information
  console.log("get set user information:" + selected_callsign);

  if (
    selected_callsign == "" ||
    selected_callsign == null ||
    typeof selected_callsign == "undefined"
  ) {
    console.log("return triggered");
    return;
  }
  document.getElementById("dx_user_info_callsign").innerHTML =
    selected_callsign;

  returnObjFromCallsign(users, selected_callsign)
    .then(function (data) {
      console.log(data);

      // image
      if (typeof data.user_info_image !== "undefined") {
        try {
          console.log("try checking for image if base64 data");
          // determine if we have a base64 encoded image
          console.log(data.user_info_image);
          console.log(data.user_info_image.split(";base64,")[1]);
          // split data string by "base64" for separating image type from base64 string
          atob(data.user_info_image.split(";base64,")[1]);

          document.getElementById("dx_user_info_image").src =
            data.user_info_image;
          document.getElementById("user-image-" + selected_callsign).src =
            data.user_info_image;
        } catch (e) {
          console.log(e);
          console.log("corrupted image data");
          document.getElementById("user-image-" + selected_callsign).src =
            defaultUserIcon;
          document.getElementById("dx_user_info_image").src = defaultUserIcon;
        }
      } else {
        // throw error and use placeholder data
        // throw new Error("Data not available or corrupted");
        document.getElementById("dx_user_info_image").src = defaultUserIcon;
        document.getElementById("user-image-" + selected_callsign).src =
          defaultUserIcon;
      }

      // Callsign list elements
      document.getElementById(
        "chat-" + selected_callsign + "-list-dxgrid"
      ).innerHTML = "<small>" + data.user_info_gridsquare + "</small>";
      document.getElementById("user-image-" + selected_callsign).className =
        "p-1 rounded-circle";
      document.getElementById("user-image-" + selected_callsign).style =
        "width: 60px";

      // DX Station tab
      document.getElementById("dx_user_info_name").innerHTML =
        data.user_info_name;
      document.getElementById("dx_user_info_age").innerHTML =
        data.user_info_age;
      document.getElementById("dx_user_info_gridsquare").innerHTML =
        data.user_info_gridsquare;
      document.getElementById("dx_user_info_location").innerHTML =
        data.user_info_location;
      document.getElementById("dx_user_info_email").innerHTML =
        data.user_info_email;
      document.getElementById("dx_user_info_website").innerHTML =
        data.user_info_website;
      document.getElementById("dx_user_info_radio").innerHTML =
        data.user_info_radio;
      document.getElementById("dx_user_info_antenna").innerHTML =
        data.user_info_antenna;
      document.getElementById("dx_user_info_comments").innerHTML =
        data.user_info_comments;

      document.getElementById("dx_user_info_gridsquare").className = "";
      document.getElementById("dx_user_info_name").className =
        "badge bg-secondary";
      document.getElementById("dx_user_info_age").className =
        "badge bg-secondary";
      document.getElementById("dx_user_info_gridsquare").className = "";
      document.getElementById("dx_user_info_location").className = "";
      document.getElementById("dx_user_info_email").className = "";
      document.getElementById("dx_user_info_website").className = "";
      document.getElementById("dx_user_info_radio").className = "";
      document.getElementById("dx_user_info_antenna").className = "";
      document.getElementById("dx_user_info_comments").className = "";
    })
    .catch(function (err) {
      console.log("writing user info to modal failed");
      console.log(err);

      // Callsign list elements
      document.getElementById("user-image-" + selected_callsign).src =
        defaultUserIcon;
      document.getElementById("user-image-" + selected_callsign).className =
        "p-1 rounded-circle w-100";
      document.getElementById("user-image-" + selected_callsign).style =
        "height:60px";
      document.getElementById(
        "chat-" + selected_callsign + "-list-dxgrid"
      ).innerHTML = "<small>no grid</small>";

      // DX Station tab

      document.getElementById("dx_user_info_image").src = defaultUserIcon;
      document.getElementById("dx_user_info_gridsquare").className =
        "placeholder col-4";
      document.getElementById("dx_user_info_name").className =
        "placeholder col-4";
      document.getElementById("dx_user_info_age").className =
        "placeholder col-2";
      document.getElementById("dx_user_info_gridsquare").className =
        "placeholder col-3";
      document.getElementById("dx_user_info_location").className =
        "placeholder col-3";
      document.getElementById("dx_user_info_email").className =
        "placeholder col-7";
      document.getElementById("dx_user_info_website").className =
        "placeholder col-7";
      document.getElementById("dx_user_info_radio").className =
        "placeholder col-4";
      document.getElementById("dx_user_info_antenna").className =
        "placeholder col-4";
      document.getElementById("dx_user_info_comments").className =
        "placeholder col-7";
    });
}

function sendSharedFolderList(dxcallsign) {
  ipcRenderer.send("read-files-in-folder", {
    folder: config.shared_folder_path,
  });

  console.log(sharedFolderFileList);
  let fileListWithCallsign = "";
  fileListWithCallsign += dxcallsign;
  fileListWithCallsign += split_char;
  fileListWithCallsign += JSON.stringify(sharedFolderFileList);

  console.log(fileListWithCallsign);

  ipcRenderer.send("run-tnc-command", {
    command: "responseSharedFolderList",
    dxcallsign: dxcallsign,
    folderFileList: fileListWithCallsign,
  });
}

function sendSharedFolderFile(dxcallsign, filename) {
  let filePath = path.join(config.shared_folder_path, filename);
  console.log("In function sendSharedFolderFile ", filePath);

  //Make sure nothing sneaky is going on
  if (!filePath.startsWith(config.shared_folder_path)) {
    console.error("File is outside of shared folder path!");
    return;
  }

  if (!fs.existsSync(filePath)) {
    console.warn("File doesn't seem to exist");
    return;
  }

  //Read file's data
  let fileData = null;
  try {
    //Has to be binary
    let data = fs.readFileSync(filePath);
    fileData = data.toString("utf-8");
  } catch (err) {
    console.log(err);
    return;
  }

  ipcRenderer.send("run-tnc-command", {
    command: "responseSharedFile",
    dxcallsign: dxcallsign,
    file: filename,
    filedata: fileData,
  });
}

function sendUserData(dxcallsign) {
  const userInfoFields = [
    "user_info_image",
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

  let info = "";
  userInfoFields.forEach(function (subelem) {
    if (subelem !== "user_info_image") {
      info += document.getElementById(subelem).value;
      info += split_char;
    } else {
      info += document.getElementById(subelem).src;
      info += split_char;
    }
  });

  console.log(info);

  ipcRenderer.send("run-tnc-command", {
    command: "responseUserInfo",
    dxcallsign: selected_callsign,
    userinfo: info,
  });
}

//Temporarily disable a button with timeout
function pauseButton(btn, timems) {
  btn.disabled = true;
  var curText = btn.innerHTML;
  if (config.high_graphics.toUpperCase() == "TRUE") {
    btn.innerHTML =
      '<span class="spinner-grow spinner-grow-sm force-gpu" role="status" aria-hidden="true">';
  }
  setTimeout(() => {
    btn.innerHTML = curText;
    btn.disabled = false;
  }, timems);
}
ipcRenderer.on("update-config", (event, data) => {
  config = data;
});

// https://stackoverflow.com/a/18650828
function formatBytes(bytes, decimals = 2) {
  if (!+bytes) return "0 Bytes";

  const k = 1024;
  const dm = decimals < 0 ? 0 : decimals;
  const sizes = ["Bytes", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB"];

  const i = Math.floor(Math.log(bytes) / Math.log(k));

  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(dm))} ${sizes[i]}`;
}
function sendFileReq(dxcall, file) {
  //console.log(file," clicked");
  ipcRenderer.send("run-tnc-command", {
    command: "requestSharedFile",
    dxcallsign: dxcall,
    file: file,
  });
}

function changeGuiDesign(design) {
  console.log(design);
  if (
    design != "default" &&
    design != "default_light" &&
    design != "default_dark" &&
    design != "default_auto"
  ) {
    var theme_path =
      "../node_modules/bootswatch/dist/" + design + "/bootstrap.min.css";
    document.getElementById("bootstrap_theme").href = escape(theme_path);
  } else if (design == "default" || design == "default_light") {
    var theme_path = "../node_modules/bootstrap/dist/css/bootstrap.min.css";
    document.getElementById("bootstrap_theme").href = escape(theme_path);
    document.documentElement.setAttribute("data-bs-theme", "light");
  } else if (design == "default_dark") {
    var theme_path = "../node_modules/bootstrap/dist/css/bootstrap.min.css";
    document.getElementById("bootstrap_theme").href = escape(theme_path);
    document.querySelector("html").setAttribute("data-bs-theme", "dark");
  } else if (design == "default_auto") {
    var theme_path = "../node_modules/bootstrap/dist/css/bootstrap.min.css";
    document.getElementById("bootstrap_theme").href = escape(theme_path);

    // https://stackoverflow.com/a/57795495
    // check if dark mode or light mode used in OS
    if (
      window.matchMedia &&
      window.matchMedia("(prefers-color-scheme: dark)").matches
    ) {
      // dark mode
      document.documentElement.setAttribute("data-bs-theme", "dark");
    } else {
      document.documentElement.setAttribute("data-bs-theme", "light");
    }

    // also register event listener for automatic change
    window
      .matchMedia("(prefers-color-scheme: dark)")
      .addEventListener("change", (event) => {
        let newColorScheme = event.matches ? "dark" : "light";
        if (newColorScheme == "dark") {
          document.documentElement.setAttribute("data-bs-theme", "dark");
        } else {
          document.documentElement.setAttribute("data-bs-theme", "light");
        }
      });
  } else {
    var theme_path = "../node_modules/bootstrap/dist/css/bootstrap.min.css";
    document.getElementById("bootstrap_theme").href = escape(theme_path);
    document.documentElement.setAttribute("data-bs-theme", "light");
  }

  //update path to css file
  document.getElementById("bootstrap_theme").href = escape(theme_path);
}

function checkForWaitingMessages(dxcall) {
  console.log(dxcall);
  db.find({
    selector: {
      dxcallsign: dxcall,
      type: "transmit",
      status: "failed",
      //attempt: { $lt: parseInt(config.max_retry_attempts) }
    },
  })
    .then(function (result) {
      // handle result
      if (result.docs.length > 0) {
        // only want to process the first available item object, then return
        // this ensures, we are only sending one message at once

        if (typeof result.docs[0].attempt == "undefined") {
          db.upsert(result.docs[0]._id, function (doc) {
            if (!doc.attempt) {
              doc.attempt = 1;
            }
            doc.attempt++;
            return doc;
          });
          console.log("old message found - adding attempt field");
          result.docs[0].attempt = 1;
        }

        if (result.docs[0].attempt < config.max_retry_attempts) {
          console.log("RESENDING MESSAGE TRIGGERED BY BEACON OR PING");
          console.log(result.docs[0]);
          document
            .getElementById("retransmit-msg-" + result.docs[0]._id)
            .click();
        } else {
          console.log("max retries reached...can't auto repeat");
          document
            .getElementById("msg-" + result.docs[0]._id + "-attempts-badge")
            .classList.remove("bg-primary");
          document
            .getElementById("msg-" + result.docs[0]._id + "-attempts-badge")
            .classList.add("bg-danger");
        }
        return;
      } else {
        console.log("nope");
      }
    })
    .catch(function (err) {
      console.log(err);
    });
}
