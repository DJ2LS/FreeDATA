import { reactive } from "vue";

import { getConfig } from "../js/api";

export const settingsStore = reactive({
  local: {
    host: "127.0.0.1",
    port: "5000",
  },
  remote: {},
});

export function getRemote() {
  getConfig().then((conf) => {
    settingsStore.remote = conf;
  });
}

getRemote();
