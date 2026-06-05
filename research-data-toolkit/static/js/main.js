document.addEventListener("DOMContentLoaded", function () {
  const buttons = document.querySelectorAll("button[type='submit']");
  buttons.forEach((button) => {
    button.addEventListener("click", () => {
      button.classList.add("disabled");
      button.textContent = "Processing...";
    });
  });
});
