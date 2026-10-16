document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll("input[type=file]").forEach(input => {
    input.addEventListener("change", () => {
      const file = input.files && input.files[0];
      if (file && file.size > 5 * 1024 * 1024) {
        alert("Please choose a file smaller than 5 MB.");
        input.value = "";
      }
    });
  });
});
