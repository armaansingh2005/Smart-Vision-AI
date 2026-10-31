const form = document.querySelector("#detect-form");

if (form) {
  const fileInput = document.querySelector("#image-input");
  const dropzone = document.querySelector("#dropzone");
  const dropContent = document.querySelector("#drop-content");
  const previewWrap = document.querySelector("#preview-wrap");
  const previewImage = document.querySelector("#image-preview");
  const errorMessage = document.querySelector("#form-error");
  const confidence = document.querySelector("#confidence");
  const confidenceValue = document.querySelector("#confidence-value");
  const analyzeButton = document.querySelector("#analyze-button");
  let previewUrl = null;
  const maxBytes = 12 * 1024 * 1024;
  const allowedTypes = new Set(["image/jpeg", "image/png", "image/webp"]);

  function showError(message) {
    errorMessage.textContent = message;
    errorMessage.hidden = false;
  }

  function clearError() {
    errorMessage.textContent = "";
    errorMessage.hidden = true;
  }

  function showFile(file) {
    clearError();
    if (!file) return;
    if (!allowedTypes.has(file.type)) {
      fileInput.value = "";
      showError("Choose a JPG, PNG, or WEBP image.");
      return;
    }
    if (file.size > maxBytes) {
      fileInput.value = "";
      showError("This image is larger than 12 MB. Choose a smaller file.");
      return;
    }
    if (previewUrl) URL.revokeObjectURL(previewUrl);
    previewUrl = URL.createObjectURL(file);
    previewImage.src = previewUrl;
    dropContent.hidden = true;
    previewWrap.hidden = false;
  }

  fileInput.addEventListener("change", () => showFile(fileInput.files[0]));
  confidence.addEventListener("input", () => {
    confidenceValue.value = `${confidence.value}%`;
    confidenceValue.textContent = `${confidence.value}%`;
  });

  ["dragenter", "dragover"].forEach((eventName) => {
    dropzone.addEventListener(eventName, (event) => {
      event.preventDefault();
      dropzone.classList.add("is-dragging");
    });
  });
  ["dragleave", "drop"].forEach((eventName) => {
    dropzone.addEventListener(eventName, (event) => {
      event.preventDefault();
      dropzone.classList.remove("is-dragging");
    });
  });
  dropzone.addEventListener("drop", (event) => {
    const [file] = event.dataTransfer.files;
    if (!file) return;
    const transfer = new DataTransfer();
    transfer.items.add(file);
    fileInput.files = transfer.files;
    showFile(file);
  });

  form.addEventListener("submit", (event) => {
    clearError();
    if (!fileInput.files.length) {
      event.preventDefault();
      showError("Choose an image before starting detection.");
      return;
    }
    analyzeButton.disabled = true;
    analyzeButton.classList.add("is-loading");
  });

  window.addEventListener("beforeunload", () => {
    if (previewUrl) URL.revokeObjectURL(previewUrl);
  });
}
