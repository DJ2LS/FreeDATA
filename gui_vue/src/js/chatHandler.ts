const path = require("path");
const fs = require("fs");

const { v4: uuidv4 } = require("uuid");

// pinia store setup
import { setActivePinia } from "pinia";
import pinia from "../store/index";
setActivePinia(pinia);

import { useChatStore } from "../store/chatStore.js";
const chat = useChatStore(pinia);

import { useStateStore } from "../store/stateStore.js";
const state = useStateStore(pinia);

import { useSettingsStore } from "../store/settingsStore.js";
const settings = useSettingsStore(pinia);


import { sendMessage, sendBroadcastChannel } from "./sock.js";
import { displayToast } from "./popupHandler.js";


//const FD = require("./src/js/freedata.js");
import {btoa_FD} from "./freedata.js"


// split character
const split_char = "0;1;";

// define default message object
interface Attachment {
  content_type: string;
  data: string;
}

interface messageDefaultObject {
  command: string;
  hmac_signed: boolean;
  percent: number;
  bytesperminute: number;
  is_new: boolean;
  _id: string;
  timestamp: number;
  dxcallsign: string;
  dxgrid: string;
  msg: string;
  checksum: string;
  type: string;
  status: string;
  attempt: number;
  uuid: string;
  duration: number;
  nacks: number;
  speed_list: string;
  broadcast_sender?: string; // optional for broadcasts

  _attachments: {
    [filename: string]: Attachment;
  };
}


interface beaconDefaultObject{
  command: string;
  is_new: boolean;
  _id: string;
  timestamp: number;
  dxcallsign: string;
  dxgrid: string;
  type: string;
  status: string;
  uuid: string;
  snr: string;
}

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

// https://stackoverflow.com/a/26227660
if(typeof process.env["APPDATA"]  !== "undefined"){
    var appDataFolder = process.env["APPDATA"]
    console.log(appDataFolder)

} else {
    var appDataFolder: string;

    switch (process.platform) {
      case "darwin":
        appDataFolder = process.env["HOME"] + "/Library/Application Support";
        console.log(appDataFolder);
        break;
      case "linux":
        appDataFolder = process.env["HOME"] + "/.config";
        console.log(appDataFolder);
        break;
      case "win32":
        appDataFolder = "undefined";
        break;
      default:
        appDataFolder = "undefined";
        break;
    }
}
console.log("loading chat database...")
console.log("appdata folder:" + appDataFolder)
var configFolder = path.join(appDataFolder, "FreeDATA");
console.log("config folder:" + configFolder)

var chatDB = path.join(configFolder, "chatDB");
console.log("database path:" + chatDB)

var db = new PouchDB(chatDB);

/* -------- CREATE DATABASE INDEXES */
createChatIndex();

/* -------- RUN A DATABASE CLEANUP ON STARTUP */
//dbClean()

updateAllChat(true)


// create callsign set for storing unique callsigns
chat.callsign_list = new Set();

// function for creating a new broadcast
export function newBroadcast(broadcastChannel, chatmessage) {
  var mode = "";
  var frames = "";
  var data = "";

    var file = "";
    var filetype = "text";
    var filename = "";

  var file_checksum = ""; //crc32(file).toString(16).toUpperCase();
  var checksum = "";
  var message_type = "broadcast_transmit";
  var command = "";

  var timestamp = Math.floor(Date.now() / 1000);
  var uuid = uuidv4();
  // TODO: Not sure what this uuid part is needed for ...
  let uuidlast = uuid.lastIndexOf("-");
  uuidlast += 1;
  if (uuidlast > 0) {
    uuid = uuid.substring(uuidlast);
  }
  // slice uuid for reducing overhead
  uuid = uuid.slice(-4);


let newChatObj: messageDefaultObject = {
  command: "broadcast",
  hmac_signed: false,
  percent: 0,
  bytesperminute: 0,  // You need to assign a value here
  is_new: false,
  _id: uuid,
  timestamp: timestamp,
  dxcallsign: broadcastChannel,
  dxgrid: "null",
  msg: chatmessage,
  checksum: file_checksum,
  type: message_type,
  status: "transmitting",
  attempt: 1,
  uuid: uuid,
  duration: 0,
  nacks: 0,
  speed_list: "null",
  _attachments: {
    [filename]: {
      content_type: filetype,
      data: btoa_FD(file),
    }
  }
};


    //sendMessage(newChatObj)
    sendBroadcastChannel(newChatObj)

  addObjToDatabase(newChatObj);
}

// function for creating a new message
export function newMessage(
  dxcallsign,
  chatmessage,
  chatFile,
  chatFileName,
  chatFileSize,
  chatFileType,
) {
  var mode = "";
  var frames = "";
  var data = "";
  var filename = "";
  var filetype = "";
  var file=""
  if (typeof chatFile !== "undefined") {
    file = chatFile;
    filetype = chatFileType;
    filename = chatFileName;
  } else {
    file = "";
    filetype = "text";
    filename = "";
  }
  var file_checksum = ""; //crc32(file).toString(16).toUpperCase();
  var checksum = "";
  var message_type = "transmit";
  var command = "";

  var timestamp = Math.floor(Date.now() / 1000);
  var uuid = uuidv4();
  // TODO: Not sure what this uuid part is needed for ...
  let uuidlast = uuid.lastIndexOf("-");
  uuidlast += 1;
  if (uuidlast > 0) {
    uuid = uuid.substring(uuidlast);
  }
  // slice uuid for reducing overhead
  uuid = uuid.slice(-8);


let newChatObj: messageDefaultObject = {
  command: "msg",
  hmac_signed: false,
  percent: 0,
  bytesperminute: 0, // You need to assign a value here
  is_new: false,
  _id: uuid,
  timestamp: timestamp,
  dxcallsign: dxcallsign,
  dxgrid: "null",
  msg: chatmessage,
  checksum: file_checksum,
  type: message_type,
  status: "transmitting",
  attempt: 1,
  uuid: uuid,
  duration: 0,
  nacks: 0,
  speed_list: "null",
  _attachments: {
    [filename]: {
      content_type: filetype,
      data: btoa_FD(file)
    }
  }
};

  sendMessage(newChatObj);
  addObjToDatabase(newChatObj);
}

// function for creating a list, accessible by callsign
function sortChatList() {
  // Create an empty object to store the reordered data dynamically
  var reorderedData = {};
  var jsonObjects = chat.unsorted_chat_list;
  // Iterate through the list of JSON objects and reorder them dynamically
  jsonObjects.forEach((obj) => {
    var dxcallsign = obj.dxcallsign;
    if (dxcallsign) {
      if (!reorderedData[dxcallsign]) {
        reorderedData[dxcallsign] = [];
      }
      reorderedData[dxcallsign].push(obj);

      reorderedData[dxcallsign] = reorderedData[dxcallsign].sort(sortByProperty("timestamp"));
    }
  });
  //console.log(reorderedData["2LS-0"])
  return reorderedData;
}

//https://medium.com/@asadise/sorting-a-json-array-according-one-property-in-javascript-18b1d22cd9e9
function sortByProperty(property){  
  return function(a,b){  
     if(a[property] > b[property])  
        return 1;  
     else if(a[property] < b[property])  
        return -1;  
 
     return 0;  
  }  
}


export function getMessageAttachment(id) {
  return new Promise(async (resolve, reject) => {
    try {
      const findResult = await db.find({
        selector: {
          _id: id,
        },
      });

      const getResult = await db.get(findResult.docs[0]._id, {
        attachments: true,
      });

      let obj = getResult;
      let filename = Object.keys(obj._attachments)[0];
      let filetype = obj._attachments[filename].content_type;
      let file = obj._attachments[filename].data;
      resolve([filename, filetype, file]);
    } catch (err) {
      console.log(err);
      reject(false); // Reject the Promise if there's an error
    }
  });
}


//repeat a message
export function repeatMessageTransmission(id) {
  // 1. get message object by ID
  // 2. Upsert Attempts
  // 3. send message

db.find({
    selector: {
      _id: id,
    },
  }).then(function (result){
    console.log(result)
    let obj = result.docs[0]
    console.log(obj)
    obj.attempt += 1
    databaseUpsert(obj.uuid, "attempt", obj.attempt);
    updateUnsortedChatListEntry(obj.uuid, "attempt", obj.attempt);
    sendMessage(obj)
  }).catch(function (err) {
                  console.log(err);
                });
}

// delete a message from databse and gui
export function deleteMessageFromDB(id) {
  console.log("deleting: " + id);
  db.get(id).then(function (doc) {
    db.remove(doc);
  });

  // overwrote unsorted chat list  by filtering if not ID
  chat.unsorted_chat_list = chat.unsorted_chat_list.filter(
    (entry) => entry.uuid !== id,
  );

  // and finally generate our sorted chat list, which is the key store for chat gui rendering
  // the removed entry should be removed now from gui
  chat.sorted_chat_list = sortChatList();
}


//Function to clean old beacons and optimize database
async function dbClean() {
  //Only keep the most x latest days of beacons
  let beaconKeep = 4;
  let itemCount = 0;
  let timestampPurge = Math.floor(
    (Date.now() - beaconKeep * 24 * 60 * 60 * 1000) / 1000,
  );


  //Items to purge from database
  var purgeFilter = [
    { type: "beacon" },
    { type: "ping-ack" },
    { type: "ping" },
    { type: "request" },
    { type: "response" },
  ];

  await db
    .find({
      selector: {
        $and: [{ timestamp: { $lt: timestampPurge } }, { $or: purgeFilter }],
      },
    })
    .then(async function (result) {
      //console.log("Purging " + result.docs.length + " beacons received before " + timestampPurge);
      itemCount = result.docs.length;
      result.docs.forEach(async function (item) {
           await deleteMessageFromDB(item._id)
      });
    })
    .catch(function (err) {
      console.log(err);
    });

  //Compact database
  await db.compact();



 let message = "Database maintenance is complete"
              displayToast("info", "bi bi-info-circle", message, 5000);

 message = "Removed "+itemCount+" items from database"
              displayToast("info", "bi bi-info-circle", message, 5000);


}




// function to update transmission status
export function updateTransmissionStatus(obj) {
  // update database entries
  databaseUpsert(obj.uuid, "percent", obj.percent);
  databaseUpsert(obj.uuid, "bytesperminute", obj.bytesperminute);
  databaseUpsert(obj.uuid, "status", obj.status);


  // update screen rendering / messages
  updateUnsortedChatListEntry(obj.uuid, "percent", obj.percent);
  updateUnsortedChatListEntry(obj.uuid, "bytesperminute", obj.bytesperminute);
  updateUnsortedChatListEntry(obj.uuid, "status", obj.status);

}

export function updateUnsortedChatListEntry(uuid, object, value) {

  var data = getFromUnsortedChatListByUUID(uuid)
  if(data){
    data[object] = value;
    console.log("Entry updated:", data[object]);
    chat.sorted_chat_list = sortChatList();
    return data;

  }

  /*
  for (const entry of chat.unsorted_chat_list) {
    if (entry.uuid === uuid) {
      entry[object] = value;
      console.log("Entry updated:", entry[object]);
      chat.sorted_chat_list = sortChatList();
      return entry;
    }
  }
  */

  console.log("Entry not updated:", object);
  return null; // Return null if not found
}

function getFromUnsortedChatListByUUID(uuid){
    for (const entry of chat.unsorted_chat_list) {
        if (entry.uuid === uuid) {
            return entry;
        }
    }
    return false;
}

export function getNewMessagesByDXCallsign(dxcallsign): [number, number, any]{
let new_counter = 0
let total_counter = 0
let item_array = []
if (typeof dxcallsign !== 'undefined'){
    for (const key in chat.sorted_chat_list[dxcallsign]){
        //console.log(chat.sorted_chat_list[dxcallsign][key])
        //item_array.push(chat.sorted_chat_list[dxcallsign][key])
      if(chat.sorted_chat_list[dxcallsign][key].is_new){
            item_array.push(chat.sorted_chat_list[dxcallsign][key])
            new_counter += 1

      }
      total_counter += 1
    }
}

    return [total_counter, new_counter, item_array];
}


export function resetIsNewMessage(uuid, value){
    databaseUpsert(uuid, "is_new", value)
    updateUnsortedChatListEntry(uuid, "is_new", value);
}



export function databaseUpsert(id, object, value) {
  db.upsert(id, function (doc) {
    if (!doc[object]) {
      doc[object] = value;
    }
    doc[object] = value;
    return doc;
  })
    .then(function (res) {
      // success, res is {rev: '1-xxx', updated: true, id: 'myDocId'}
      console.log(res);
    })
    .catch(function (err) {
      // error
      console.log(err);
    });
}

// function for fetching all messages from chat / updating chat
export async function updateAllChat(cleanup) {

    // run cleanup if requested
    if (cleanup) {
        await dbClean()
    }

  let filter = {
          selector: {
            $and: [
              { dxcallsign: { $exists: true } },
              { timestamp: { $exists: true } },
              //{ $or: chat.chat_filter },
            ],
          },
          sort: [{ dxcallsign: "asc" }, { timestamp: "asc" }],
        }
  getFromDBByFilter(filter)
    .then(async function (result) {
          for (var item of result.docs) {
            const dxcallsign = item.dxcallsign;
            // Check if dxcallsign already exists as a property in the result object
            if (!chat.sorted_beacon_list[dxcallsign]) {
              // If not, initialize it with an empty array for snr values
              chat.sorted_beacon_list[dxcallsign] = {
                dxcallsign,
                snr: [],
                timestamp: [],
              };
              chat.callsign_list.add(dxcallsign);
            }

            if (item.type === "beacon") {
              //console.log(item);

              // TODO: sort beacon list .... maybe a part for a separate function
              const jsonData = [item];
              
              // Process each JSON item step by step
              jsonData.forEach((jsonitem) => {
                const { snr, timestamp } = item;

                // Push the snr value to the corresponding dxcallsign's snr array
                chat.sorted_beacon_list[dxcallsign].snr.push(snr);
                chat.sorted_beacon_list[dxcallsign].timestamp.push(timestamp);
              });
            } else {
              
              chat.unsorted_chat_list.push(item);
              chat.sorted_chat_list = sortChatList();
              
            }
           
          }

        })
        .catch(function (err) {
          console.log(err);
        });

}

function addObjToDatabase(newobj) {
  console.log(newobj);
  /*
        db.upsert(newobj._id, function (doc) {
          if (!doc._id) {
            console.log("upsert")
            console.log(doc)
            doc = newobj
          } else {
                        console.log("new...")
            */
  db.post(newobj)
    .then(function (response) {
      // handle response
      console.log("new database entry");
      console.log(response);


      if (newobj.command === "msg") {
        chat.unsorted_chat_list.push(newobj);
        chat.sorted_chat_list = sortChatList();
      }

    })
    .catch(function (err) {
      console.log(err);
      console.log(newobj);

      // try upserting status in case we tried sending a message to our selfes
      databaseUpsert(newobj.uuid, "status", newobj.status);
      updateUnsortedChatListEntry(newobj.uuid, "status", newobj.status);


    });


  /*
// upsert footer ...

          }
          return doc;
        })
*/
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
        "hmac_signed",
        "bytesperminute",
        "_attachments",
        "is_new",
        "nacks",
        "duration",
        "speed_list"
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

export function deleteChatByCallsign(callsign) {
  chat.callsign_list.delete(callsign);
  // @ts-expect-error
  delete chat.unsorted_chat_list.callsign;
  delete chat.sorted_chat_list.callsign;

  deleteFromDatabaseByCallsign(callsign);
}



function deleteFromDatabaseByCallsign(callsign) {
  db.find({
    selector: {
      dxcallsign: callsign,
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
                  updateAllChat(false);
                  return true;
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
}

// function for handling a received beacon
export function newBeaconReceived(obj) {
  /*
{
    "freedata": "modem-message",
    "beacon": "received",
    "uuid": "12741312-3dbb-4a53-b0cc-100f6c930ab8",
    "timestamp": 1696076869,
    "dxcallsign": "DJ2LS-0",
    "dxgrid": "JN48CS",
    "snr": "-2.8",
    "mycallsign": "DJ2LS-0"
}
*/
let newChatObj: beaconDefaultObject = {
  command: "beacon",
  is_new: false,
  _id: obj["uuid"],
  timestamp: obj["timestamp"],
  dxcallsign: obj["dxcallsign"],
  dxgrid: obj["dxgrid"],
  type: "beacon",
  status: obj["beacon"],
  uuid: obj["uuid"],
  snr: obj["snr"], // adding the new field
};

  addObjToDatabase(newChatObj);

  console.log(obj);

  const jsonData = [obj];
  const dxcallsign = obj.dxcallsign;
  // Process each JSON item step by step
  jsonData.forEach((item) => {
    const { snr, timestamp } = obj;

    // Check if dxcallsign already exists as a property in the result object
    if (!chat.sorted_beacon_list[dxcallsign]) {
      // If not, initialize it with an empty array for snr values
      chat.sorted_beacon_list[dxcallsign] = {
        dxcallsign,
        snr: [],
        timestamp: [],
      };
    }

    // Push the snr value to the corresponding dxcallsign's snr array
    chat.sorted_beacon_list[dxcallsign].snr.push(snr);
    chat.sorted_beacon_list[dxcallsign].timestamp.push(timestamp);
  });

  // check if auto retry enabled
  console.log("-----------------------------------------")
  console.log(settings.enable_auto_retry.toUpperCase())
    if (settings.enable_auto_retry.toUpperCase() == "TRUE") {
    checkForWaitingMessages(dxcallsign);
  }


}

// function for handling a received message
export function newMessageReceived(message, protocol) {
  /*

    PROTOCOL
{
    "freedata": "modem-message",
    "arq": "transmission",
    "status": "received",
    "uuid": "5a3caa57-7feb-4436-853d-e341b085350f",
    "percent": 100,
    "bytesperminute": 206,
    "compression": 0.5833333333333334,
    "timestamp": 1697048385,
    "finished": 0,
    "mycallsign": "DJ2LS-0",
    "dxcallsign": "DJ2LS-0",
    "dxgrid": "------",
    "data": "bTA7MTttc2cwOzE7MDsxOzBlNGE3YjQ2MDsxOzE2OTcwNDgzMTkwOzE7dGVzdDMwOzE7MDsxO3RleHQwOzE7",
    "irs": "False",
    "hmac_signed": "False",
    "duration": 44.385897636413574,
    "nacks": 1,
    "speed_list": [
        {
            "snr": 0,
            "bpm": 106,
            "timestamp": 1697048362
        },
        {
            "snr": -6,
            "bpm": 104,
            "timestamp": 1697048370
        },
        {
            "snr": -6,
            "bpm": 81,
            "timestamp": 1697048370
        },
        {
            "snr": -5.7,
            "bpm": 161,
            "timestamp": 1697048378
        },
        {
            "snr": -5.7,
            "bpm": 133,
            "timestamp": 1697048379
        },
        {
            "snr": -5.4,
            "bpm": 206,
            "timestamp": 1697048385
        },
        {
            "snr": -5.8,
            "bpm": 179,
            "timestamp": 1697048391
        }
    ]
}

    MESSAGE; decoded from "data"
    [
    0 - protocol type message   -     "m",
    1 - type             -     "msg",
    2 - checksum     "",
    3 - uuid -     "07e2",
    4 - timestamp -    "1695203833",
    5 - message      -    "test",
    6 - file name    -   "",
    7 - mime         -    "plain/text",
    8 - file         -    ""
    ]


    */
  console.log(protocol);

let newChatObj: messageDefaultObject = {
  command: "msg",
  hmac_signed: protocol["hmac_signed"],
  percent: 100,
  bytesperminute: protocol["bytesperminute"],
  is_new: true,
  _id: message[3],
  timestamp: message[4],
  dxcallsign: protocol["dxcallsign"],
  dxgrid: protocol["dxgrid"],
  msg: message[5],
  checksum: message[2],
  type: protocol["status"],
  status: protocol["status"],
  attempt: 1,
  uuid: message[3],
  duration: protocol["duration"],
  nacks: protocol["nacks"],
  speed_list: protocol["speed_list"],
  _attachments: {
    [message[6]]: {
      content_type: message[7],
      data: btoa_FD(message[8])
    }
  }
};


  // some tweaks for broadcasts
  if (protocol.fec == "broadcast") {
    newChatObj.broadcast_sender = protocol["dxcallsign"];
    newChatObj.type = "broadcast_received";
  }

  addObjToDatabase(newChatObj);
}

export function setStateFailed() {
  state.arq_seconds_until_finish = 0;
  state.arq_seconds_until_timeout = 180;
  state.arq_seconds_until_timeout_percent = 100;
}

export function setStateSuccess() {
  state.arq_seconds_until_finish = 0;
  state.arq_seconds_until_timeout = 180;
  state.arq_seconds_until_timeout_percent = 100;
}

export function requestMessageInfo(id){

console.log(id)
// id and uuid are the same
var data = getFromUnsortedChatListByUUID(id)
console.log(data)
    chat.selectedMessageObject = data


}

function getFromDBByFilter(filter) {
/*
USAGE:

let filter = {
    selector: {
      dxcallsign: dxcall,
      type: "transmit",
      status: "failed",
      //attempt: { $lt: parseInt(config.max_retry_attempts) }
    },
  }

getFromDBByFilter(filter)
  .then(result => {
    console.log(result)
  })
  .catch(err => {
    console.log(err)
  });

*/
  return new Promise((resolve, reject) => {
    console.log(filter);

    db.createIndex({
      index: {
        fields: [{ dxcallsign: "asc" }, { type: "asc" }, { status: "asc" }, { timestamp: "asc" }],
      },
    })
    .then(result => {
      return db.find(filter);
    })
    .then(result => {
      console.log(result);
      resolve(result);
    })
    .catch(err => {
      console.log(err);
      reject(err);
    });
  });
}



async function checkForWaitingMessages(dxcall) {

let filter = {
    selector: {
      dxcallsign: dxcall,
      type: "transmit",
      status: "failed",
      //attempt: { $lt: parseInt(config.max_retry_attempts) }
    },
  }

getFromDBByFilter(filter)
  .then(result => {
       let message = "Found " + result.docs.length + " waiting messages for " + dxcall
        console.log(message);
       displayToast("info", "bi bi-info-circle", message, 5000);

      // handle result
      if (result.docs.length > 0) {
        // only want to process the first available item object, then return
        // this ensures, we are only sending one message at once

        if (result.docs[0].attempt < config.max_retry_attempts) {
          repeatMessageTransmission(result.docs[0].uuid)
        }
        return;
      }

  })
  .catch(err => {
    console.log(err)
  });
}