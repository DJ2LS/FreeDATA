const path = require("path");
const fs = require("fs");

const { v4: uuidv4 } = require("uuid");


// pinia store setup
import { setActivePinia } from 'pinia';
import pinia from '../store/index';
setActivePinia(pinia);

import { useChatStore } from '../store/chatStore.js';
const chat = useChatStore(pinia);

import { sendMessage } from './sock.js';

const FD = require("./src/js/freedata.js");

// split character
const split_char = "0;1;";




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
var appDataFolder =
  process.env.APPDATA ||
  (process.platform == "darwin"
    ? process.env.HOME + "/Library/Application Support"
    : process.env.HOME + "/.config");
var configFolder = path.join(appDataFolder, "FreeDATA");




var chatDB = path.join(configFolder, "chatDB");
var db = new PouchDB(chatDB);

/* -------- CREATE DATABASE INDEXES */
createChatIndex();






chat.callsign_list = new Set()




export function newMessage(dxcallsign, chatmessage){
    var mode = ''
    var frames = ''
    var data = ''
    var file = ''
    var file_checksum = crc32(file).toString(16).toUpperCase();
    var checksum = ''
    var message_type = 'transmit'
    var command = ''
    var filetype = "plain/text"
    var filename = ''
    var timestamp = Math.floor(Date.now() / 1000)
    var uuid = uuidv4();
    let uuidlast = uuid.lastIndexOf("-");
    console.log(uuidlast)
    uuidlast += 1;
    if (uuidlast > 0) {
        uuid = uuid.substring(uuidlast);
    }
    // slice uuid for reducing overhead
    uuid = uuid.slice(-4);


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
      var tnc_command = "msg";

    sendMessage(
        dxcallsign,
        data_with_attachment,
        checksum,
        uuid,
        tnc_command
    )

    let newChatObj = new Object();

        newChatObj.command = "msg"
        newChatObj.hmac_signed = false
        newChatObj.percent = 0
        newChatObj.bytesperminute
        newChatObj.is_new = false
        newChatObj._id = uuid
        newChatObj.timestamp = timestamp
        newChatObj.dxcallsign = dxcallsign
        newChatObj.dxgrid = "null"
        newChatObj.msg = chatmessage
        newChatObj.checksum = file_checksum
        newChatObj.type = message_type
        newChatObj.status = "transmitting"
        newChatObj.attempt = 1
        newChatObj.uuid = uuid
        newChatObj._attachments = {
            [filename]: {
              content_type: filetype,
              data: FD.btoa_FD(file),
            },
        }

    addObjToDatabase(newChatObj)

}




function sortChatList(){

    // Create an empty object to store the reordered data dynamically
    var reorderedData = {};
    var jsonObjects = chat.unsorted_chat_list
    // Iterate through the list of JSON objects and reorder them dynamically
    jsonObjects.forEach(obj => {
        var dxcallsign = obj.dxcallsign;
        if (dxcallsign) {
            if (!reorderedData[dxcallsign]) {
                reorderedData[dxcallsign] = [];
            }
            reorderedData[dxcallsign].push(obj);
        }
    });
    //console.log(reorderedData["DJ2LS-0"])
    return reorderedData
}


export async function updateAllChat() {

  //Ensure we create an index before running db.find
  //We can't rely on the default index existing before we get here...... :'(
  await db
    .createIndex({
      index: {
        fields: [{ dxcallsign: "asc" }, { timestamp: "asc" }],
      },
    })
    .then(async function (result) {
      // handle result
      await db
        .find({
          selector: {
            $and: [
              { dxcallsign: { $exists: true } },
              { timestamp: { $exists: true } },
              { $or: chat.chat_filter },
            ],
            //$or: chat.chat_filter
          },
          sort: [{ dxcallsign: "asc" }, { timestamp: "asc" }],
        })
        .then(async function (result) {
          console.log(result);
          for (var item of result.docs) {
            chat.callsign_list.add(item.dxcallsign)
            chat.unsorted_chat_list.push(item)
          }

            chat.sorted_chat_list = sortChatList()

          /*
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
          */


        })
        .catch(function (err) {
          console.log(err);
        });
    })
    .catch(function (err) {
      console.log(err);
    });

}

function addObjToDatabase(newobj){
        console.log(newobj)
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
            })
            .catch(function (err) {
              console.log(err);
            });

            chat.unsorted_chat_list.push(newobj)
            chat.sorted_chat_list = sortChatList()


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


export function deleteChatByCallsign(callsign){
   chat.callsign_list.delete(callsign)
   delete chat.unsorted_chat_list.callsign
   delete chat.sorted_chat_list.callsign

   deleteFromDatabaseByCallsign(callsign)


}

function deleteFromDatabaseByCallsign(callsign){
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
                      updateAllChat(true);
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