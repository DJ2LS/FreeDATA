import { useStationStore } from "../store/stationStore.js";
const station = useStationStore();

import { getStationInfo, setStationInfo } from "../js/api";

export async function getStationInfoByCallsign(callsign) {
  try {
    const result = await getStationInfo(callsign);
    console.log(result);

    station.stationInfo.callsign = result.callsign || "N/A";
    station.stationInfo.location.gridsquare =
      result.location?.gridsquare || "N/A";
    // Check if info is null and assign default values if it is
if (result == null || result.info == null) {
      station.stationInfo.info = {
        name: "",
        city: "",
        age: "",
        radio: "",
        antenna: "",
        email: "",
        website: "",
        socialMedia: {
          facebook: "",
          "twitter-x": "",
          mastodon: "",
          instagram: "",
          linkedin: "",
          youtube: "",
          tiktok: "",
        },
        comments: "",
      };
    } else {
      station.stationInfo.info = {
        name: result.info.name || "",
        city: result.info.city || "",
        age: result.info.age || "",
        radio: result.info.radio || "",
        antenna: result.info.antenna || "",
        email: result.info.email || "",
        website: result.info.website || "",
        socialMedia: {
          facebook: result.info.socialMedia.facebook || "",
          "twitter-x": result.info.socialMedia["twitter-x"] || "",
          mastodon: result.info.socialMedia.mastodon || "",
          instagram: result.info.socialMedia.instagram || "",
          linkedin: result.info.socialMedia.linkedin || "",
          youtube: result.info.socialMedia.youtube || "",
          tiktok: result.info.socialMedia.tiktok || "",
        },
        comments: result.info.comments || "",
      };
    }
  } catch (error) {
    console.error("Error fetching station info:", error);
  }
}

export async function setStationInfoByCallsign(callsign) {
  console.log(station.stationInfo);
  setStationInfo(callsign, station.stationInfo);
}
