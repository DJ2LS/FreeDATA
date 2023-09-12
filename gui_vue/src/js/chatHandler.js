const path = require("path");
const fs = require("fs");

// pinia store setup
import { setActivePinia } from 'pinia';
import pinia from '../store/index';
setActivePinia(pinia);

import { useChatStore } from '../store/chatStore.js';
const chat = useChatStore(pinia);


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



function sortChatList(){

    // Create an empty object to store the reordered data dynamically
    const reorderedData = {};
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


          // handle result async
        

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
        "new",
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
