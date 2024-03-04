import { defineStore } from "pinia";
import { getSerialDevices } from "../js/api"; // Make sure this points to the correct file
import { ref } from "vue";

// Define "skel" fallback data for serial devices
const skelSerial = [{
  "description": "No devices received from modem",
  "port": "ignore" // Using "ignore" as a placeholder value
}];

export const useSerialStore = defineStore("serialStore", () => {
  const serialDevices = ref([]);

  const loadSerialDevices = async () => {
    try {
      const devices = await getSerialDevices();
      // Check if devices are valid and have entries, otherwise use skelSerial
      serialDevices.value = devices && devices.length > 0 ? devices : skelSerial;
    } catch (error) {
      console.error("Failed to load serial devices:", error);
      // Use skelSerial as fallback in case of error
      serialDevices.value = skelSerial;
    }

    // Ensure the "-- ignore --" option is always available
    if (!serialDevices.value.some(device => device.port === "ignore")) {
      serialDevices.value.push({ description: "-- ignore --", port: "ignore" });
    }
  };

  return {
    serialDevices,
    loadSerialDevices,
  };
});
