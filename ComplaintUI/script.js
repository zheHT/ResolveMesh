const form = document.getElementById("complaintForm");
const chips = Array.from(document.querySelectorAll(".chip"));
const complaintType = document.getElementById("complaintType");
const attachment = document.getElementById("attachment");
const fileName = document.getElementById("fileName");
const toast = document.getElementById("toast");

chips.forEach((chip) => {
  chip.addEventListener("click", () => {
    chips.forEach((item) => item.classList.remove("selected"));
    chip.classList.add("selected");
    complaintType.value = chip.dataset.value;
  });
});

attachment.addEventListener("change", (event) => {
  const file = event.target.files?.[0];
  fileName.textContent = file ? `Selected: ${file.name}` : "No file selected";
});

form.addEventListener("submit", (event) => {
  event.preventDefault();
  clearErrors();

  let hasError = false;

  const requiredFields = ["transactionId", "details"];

  requiredFields.forEach((id) => {
    const input = document.getElementById(id);
    if (!input.value.trim()) {
      setError(id, "This field is required.");
      hasError = true;
    }
  });

  if (hasError) {
    showToast("Please complete required fields.");
    return;
  }

  const formData = new FormData();
  formData.append("platform", complaintType.value);
  formData.append("transactionId", document.getElementById("transactionId").value.trim());
  formData.append("summary", document.getElementById("summary").value.trim());
  formData.append("details", document.getElementById("details").value.trim());
  
  if (attachment.files?.[0]) {
    formData.append("attachment", attachment.files[0]);
  }

  fetch("https://unemployed.app.n8n.cloud/webhook-test/userComplaint", {
    method: "POST",
    body: formData,
  })
    .then((response) => {
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      return response.json();
    })
    .then((data) => {
      console.log("Complaint submitted successfully", data);
      showToast("Complaint submitted successfully");
      form.reset();
      chips.forEach((chip) => chip.classList.remove("selected"));
      chips[0].classList.add("selected");
      complaintType.value = chips[0].dataset.value;
      fileName.textContent = "No file selected";
      attachment.value = "";
    })
    .catch((error) => {
      console.error("Error submitting complaint:", error);
      showToast("Failed to submit complaint. Please try again.");
    });
});

function setError(fieldId, message) {
  const errorNode = document.querySelector(`.error[data-for=\"${fieldId}\"]`);
  if (errorNode) {
    errorNode.textContent = message;
  }
}

function clearErrors() {
  document.querySelectorAll(".error").forEach((node) => {
    node.textContent = "";
  });
}

function showToast(message) {
  toast.textContent = message;
  toast.classList.add("show");
  window.setTimeout(() => {
    toast.classList.remove("show");
  }, 2200);
}
