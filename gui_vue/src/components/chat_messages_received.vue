<template>
  <div class="row justify-content-start mb-2">
    <div :class="messageWidthClass">
      <div class="card bg-light border-0 text-dark">

        <div class="card-header" v-if="getFileContent['filesize'] !== 0">
          <p class="card-text">{{ getFileContent["filename"] }} | {{ getFileContent["filesize"] }} Bytes | {{ getFileContent["filetype"] }}</p>
        </div>

        <div class="card-body">
          <p class="card-text">{{ message.msg }}</p>
        </div>
        <div class="card-footer p-0 bg-light border-top-0">
          <p class="text-muted p-0 m-0 me-1 text-end">{{ getDateTime }}</p> <!-- Display formatted timestamp in card-footer -->
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
        try{
        var filename = Object.keys(this.message._attachments)[0]
        var filesize = this.message._attachments[filename]["length"]
        var filetype = filename.split(".")[1]

        return {filename: filename, filesize: filesize, filetype: filetype}
        } catch (e){
            console.log("file not loaded from database - empty?")
            // we are only checking against filesize for displaying attachments
            return {filesize: 0}
        }
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
