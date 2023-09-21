<template>
  <div class="row justify-content-end mb-2">
    <div :class="messageWidthClass">
      <div class="card bg-primary text-white">

        <div class="card-header" v-if="getFileContent['filesize'] !== 0">
          <p class="card-text">{{ getFileContent["filename"] }} | {{ getFileContent["filesize"] }} Bytes | {{ getFileContent["filetype"] }}</p>
        </div>


        <div class="card-body">
          <p class="card-text">{{ message.msg }}</p>
        </div>

        <div class="card-footer p-0 bg-primary border-top-0">
                  <p class="text p-0 m-0 me-1 text-end">{{ getDateTime }}</p> <!-- Display formatted timestamp in card-footer -->
        </div>




        <div class="card-footer p-0 border-top-0" v-if="message.percent < 100">
          <div class="progress  bg-secondary  "  :style="{height: 10 + 'px'}">
            <div
              class="progress-bar progress-bar-striped overflow-visible"
              role="progressbar"
              :style="{ width: message.percent + '%', height: 10 + 'px'}"
              :aria-valuenow="message.percent"
              aria-valuemin="0"
              aria-valuemax="100"
            >
                {{ message.percent }} % with {{ message.bytesperminute }} bpm
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  props: {
    message: Object,
  },
  computed: {
    getFileContent(){
        var filename = Object.keys(this.message._attachments)[0]
        var filesize = this.message._attachments[filename]["length"]
        var filetype = filename.split(".")[1]

        return {filename: filename, filesize: filesize, filetype: filetype}
    },
    messageWidthClass() {
      // Calculate a Bootstrap grid class based on message length
      // Adjust the logic as needed to fit your requirements
      if (this.message.msg.length <= 50) {
        return 'col-4';
      } else if (this.message.msg.length <= 100) {
        return 'col-6';
      } else {
        return 'col-9';
      }
    },
    getDateTime() {
      var datetime = new Date(this.message.timestamp * 1000).toLocaleString(
        navigator.language,
        {

          hour: '2-digit',
          minute: '2-digit',
        }
      );
      return datetime;
    },
  },
};
</script>
