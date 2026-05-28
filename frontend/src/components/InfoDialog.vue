<script setup lang="ts">
defineProps<{
  title: string;
  message: string;
  variant?: "info" | "error" | "confirm";
  confirmLabel?: string;
  cancelLabel?: string;
}>();

const emit = defineEmits<{
  (e: "confirm"): void;
  (e: "close"): void;
}>();
</script>

<template>
  <div class="dialog-backdrop" @click.self="emit('close')">
    <div class="dialog info-dialog" :class="variant">
      <div class="dialog-title">{{ title }}</div>
      <div class="message" v-html="message"></div>
      <div class="dialog-actions">
        <button v-if="variant === 'confirm'" @click="emit('confirm')">
          {{ confirmLabel ?? "確定" }}
        </button>
        <button @click="emit('close')">
          {{ variant === "confirm" ? (cancelLabel ?? "取消") : "確定" }}
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.info-dialog {
  min-width: 360px;
}
.info-dialog.error .message {
  color: #c0392b;
}
.message {
  font-size: 15px;
  white-space: pre-wrap;
  line-height: 1.6;
}
</style>
