document.getElementById("uploadForm").addEventListener("submit", async (e) => {
  e.preventDefault();
  const status = document.getElementById("status");
  const cloud = document.getElementById("cloud").value;
  const files = document.getElementById("files").files;

  if (!cloud || files.length === 0) {
    status.innerHTML = "⚠️ Please select a cloud and upload files.";
    return;
  }

  const formData = new FormData();
  formData.append("cloud", cloud);
  for (const file of files) {
    formData.append("files", file);
  }

  status.innerHTML = "⏳ Uploading...";
  try {
    const uploadResponse = await fetch("/upload-awrs", { method: "POST", body: formData });
    const uploadData = await uploadResponse.json();

    if (uploadData.status !== "uploaded") {
      status.innerHTML = "❌ Upload failed. Please try again.";
      return;
    }

    status.innerHTML = "✅ Uploaded successfully. Starting analysis...";
    const analyzeForm = new FormData();
    analyzeForm.append("cloud", cloud);

    const analyzeResponse = await fetch("/analyze", { method: "POST", body: analyzeForm });
    const analyzeData = await analyzeResponse.json();

    if (analyzeData.status === "ok") {
      status.innerHTML = "✅ Analysis completed! Redirecting to dashboard...";
      setTimeout(() => {
        window.location.href = "/dashboard.html";
      }, 2000);
    } else {
      status.innerHTML = `❌ Analysis failed: ${analyzeData.message}`;
    }
  } catch (err) {
    status.innerHTML = "❌ Error connecting to the backend.";
    console.error(err);
  }
});
