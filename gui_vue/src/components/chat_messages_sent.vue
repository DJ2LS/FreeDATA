<script>
export default {
  props: {
    message: Object, // Prop to receive the message content
  },
};



</script>

<template>
  <div class="row justify-content-end">
    <div class="col-auto">
      <div class="sent-message alert alert-info">
        <p><strong>{{message.timestamp}}</strong></p>
        <p>{{ message.msg }}</p>
      </div>
    </div>
  </div>
</template>



