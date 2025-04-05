<template>
  <div class="message-actions-menu">
    <button @click="onDelete">
      Delete
    </button>
    <button @click="onCopy">
      Copy
    </button>
    <button @click="onQuote">
      Quote
    </button>
  </div>
</template>

<script>
export default {
  methods: {
    onDelete() {
      // Implement delete action
      this.$emit("delete");
    },
    onCopy() {
      // Implement copy action
      this.$emit("copy");
    },
    onQuote() {
      // Implement quote action
      this.$emit("quote");
    },
  },
};
</script>

<style scoped>
/* Style the message actions menu as needed */
.message-actions-menu {
  position: absolute;
  top: 50%;
  transform: translateY(-50%);
  display: none; /* Initially hidden */
  /* Add styling for buttons and menu */
}

/* Style individual action buttons */
.message-actions-menu button {
  /* Add button styles here */
}

/* Style menu display on hover */
.card:hover .message-actions-menu {
  display: block;
}
</style>
