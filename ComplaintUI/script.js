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

  const requiredFields = ["reference", "summary", "details"];

  requiredFields.forEach((id) => {
    const input = document.getElementById(id);
    if (!input.value.trim()) {
      setError(id, "This field is required.");
      hasError = true;
    }
  });

  const consent = document.getElementById("consent");
  if (!consent.checked) {
    setError("consent", "Please confirm before submitting.");
    hasError = true;
  }

  if (hasError) {
    showToast("Please complete required fields.");
    return;
  }

  const payload = {
    complaintType: complaintType.value,
    reference: document.getElementById("reference").value.trim(),
    summary: document.getElementById("summary").value.trim(),
    details: document.getElementById("details").value.trim(),
    attachment: attachment.files?.[0]?.name || null,
  };

  console.log("Complaint submitted", payload);

  showToast(`Complaint sent. Case ref: CMP-${Math.floor(100000 + Math.random() * 900000)}`);
  form.reset();
  chips.forEach((chip) => chip.classList.remove("selected"));
  chips[0].classList.add("selected");
  complaintType.value = chips[0].dataset.value;
  fileName.textContent = "No file selected";
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
