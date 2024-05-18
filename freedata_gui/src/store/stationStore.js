import { defineStore } from "pinia";
import { ref } from "vue";
import * as bootstrap from "bootstrap";
export const useStationStore = defineStore("stationStore", () => {
  const stationInfo = ref({
    callsign: "N/A", // Default value for callsign
    location: {
      gridsquare: "N/A", // Default value for gridsquare
    },
    info: {
      name: "",
      city: "",
      age: "",
      radio: "",
      antenna: "",
      email: "",
      website: "",
      socialMedia: {
        facebook: "",
        "twitter-x": "", // Use twitter-x to correspond to the Twitter X icon
        mastodon: "",
        instagram: "",
        linkedin: "",
        youtube: "",
        tiktok: "",
      },
      comments: "",
    },
  });
  return {
    stationInfo,
  };
});
