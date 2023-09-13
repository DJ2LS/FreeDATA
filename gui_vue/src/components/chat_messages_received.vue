<script>
export default {
  props: {
    message: Object, // Prop to receive the message content
  },
};


</script>



<template>
  <div class="row justify-content-start">
    <div class="col-auto">
      <div class="received-message alert alert-light">
        <p><strong>{{ message.timestamp }}</strong></p>
        <p>{{ message.msg }}</p>
      </div>
    </div>
  </div>
</template>