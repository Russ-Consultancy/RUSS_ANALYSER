/* ======================================================================
   RUSS Analyser - Unified Frontend Script
   Pages: index.html, dashboard.html, profile.html, admin.html
   ====================================================================== */

/* ----------------------------------------------------------------------
   Utilities
---------------------------------------------------------------------- */
function $(sel) {
  return document.querySelector(sel);
}
function $all(sel) {
  return Array.from(document.querySelectorAll(sel));
}
function pageIs(name) {
  const p = location.pathname.toLowerCase();
  return p.endsWith(`/${name}.html`) || p.endsWith(`${name}.html`) || p.includes(`/${name}`);
}
function toCSVRow(arr) {
  return arr
    .map((v) => {
      const s = v == null ? "" : String(v);
      if (/[,"\n]/.test(s)) return `"${s.replace(/"/g, '""')}"`;
      return s;
    })
    .join(",");
}

/* ======================================================================
   ✅ GLOBAL HEADER (profile icon, dropdown, logout, avatar)
====================================================================== */
document.addEventListener("DOMContentLoaded", () => {
  const user = JSON.parse(localStorage.getItem("russ_user"));
  const isLoginPage = pageIs("login");
  const isRegisterPage = pageIs("register");

  if (!user && !isLoginPage && !isRegisterPage) {
    location.href = "/frontend/login.html";
    return;
  }

  const profileMenu = $("#profileMenu");
  const profileIcon = $("#profileIcon");
  const logoutBtn = $("#logoutBtn");
  const headerImg = $("#user-avatar-img");
  const headerLetter = $("#user-avatar-letter");

  if (user && headerImg && headerLetter) {
    if (user.profile_image_url) {
      headerImg.src = user.profile_image_url + "?v=" + Date.now();
      headerImg.style.display = "block";
      headerLetter.style.display = "none";
    } else {
      headerImg.style.display = "none";
      headerLetter.style.display = "flex";
      headerLetter.textContent = (user.name?.[0] || "U").toUpperCase();
    }
  }

  if (profileIcon && profileMenu) {
    profileIcon.addEventListener("click", (e) => {
      e.stopPropagation();
      profileMenu.classList.toggle("active");
    });
    document.addEventListener("click", (e) => {
      if (!profileMenu.contains(e.target) && !profileIcon.contains(e.target)) {
        profileMenu.classList.remove("active");
      }
    });
  }

  logoutBtn?.addEventListener("click", (e) => {
    e.preventDefault();
    localStorage.removeItem("russ_user");
    location.href = "/frontend/login.html";
  });
});

/* ======================================================================
   ✅ INDEX (Main Tool) — Upload + Analyze  (UNCHANGED)
====================================================================== */
document.addEventListener("DOMContentLoaded", () => {
  if (!pageIs("index")) return;

  const user = JSON.parse(localStorage.getItem("russ_user") || "{}");

  const uploadForm = $("#uploadForm");
  const folderMode = $("#folderMode");
  const fileInput = $("#files");
  const manualToggle = $("#manualToggle");
  const manualSection = $("#manualSection");
  const status = $("#status-message");
  const progressBar = $("#progressBar");

  folderMode?.addEventListener("change", () => {
    if (folderMode.checked) {
      fileInput.setAttribute("webkitdirectory", "true");
      fileInput.removeAttribute("required");
    } else {
      fileInput.removeAttribute("webkitdirectory");
      fileInput.setAttribute("required", "true");
    }
  });

  manualToggle?.addEventListener("change", () => {
    manualSection.style.display = manualToggle.checked ? "block" : "none";
  });

  uploadForm?.addEventListener("submit", async (e) => {
    e.preventDefault();

    const cloud = $("#cloud").value;
    const files = fileInput.files;
    const isManual = manualToggle.checked;

    const vcpu = $("#manual-vcpu")?.value || "";
    const memory = $("#manual-memory")?.value || "";
    const iops = $("#manual-iops")?.value || "";
    const throughput = $("#manual-throughput")?.value || "";

    if (!cloud) {
      status.innerHTML = "⚠️ Please select a cloud platform.";
      return;
    }
    if (files.length === 0 && !isManual) {
      status.innerHTML = "⚠️ Please upload files or enable manual entry.";
      return;
    }

    const form = new FormData();
    form.append("cloud", cloud);
    if (user?.email) form.append("user_email", user.email);

    let jobType = "upload";
    if (files.length > 0) {
      for (const f of files) form.append("files", f);
    }
    if (isManual) {
      form.append("vcpu", vcpu);
      form.append("memory", memory);
      form.append("iops", iops);
      form.append("throughput", throughput);
      jobType = files.length > 0 ? "mixed" : "manual";
    }
    form.append("job_type", jobType);

    status.innerHTML = "⏳ Uploading and preparing analysis...";
    progressBar.style.width = "0%";

    try {
      const up = await fetch("/upload-awrs", { method: "POST", body: form });
      const upData = await up.json();
      if (!up.ok || upData.status !== "uploaded") {
        throw new Error(upData.message || "Upload failed");
      }

      status.innerHTML = "✅ Upload successful. Starting analysis...";

      const analyzeForm = new FormData();
      analyzeForm.append("cloud", cloud);
      analyzeForm.append("job_type", jobType);
      analyzeForm.append("user_email", user.email);

      if (user?.email) analyzeForm.append("user_email", user.email);

      const an = await fetch("/analyze", { method: "POST", body: analyzeForm });
      const anData = await an.json();
      if (anData.status !== "started") throw new Error("Failed to start analysis.");

      const interval = setInterval(async () => {
        try {
          const res = await fetch("/progress");
          if (!res.ok) return;
          const prog = await res.json();
          if (prog?.percent !== undefined) {
            progressBar.style.width = `${prog.percent}%`;
            status.innerHTML = `${prog.message} (${prog.percent}%)`;
          }
          if (prog?.percent >= 100) {
            clearInterval(interval);
            progressBar.style.width = "100%";
            status.innerHTML = "<span class='success'>✅ Analysis complete! Redirecting...</span>";
            setTimeout(() => (location.href = "/frontend/dashboard.html"), 1500);
          }
        } catch (err) {
          console.warn("Progress polling failed", err);
        }
      }, 2000);
    } catch (err) {
      status.innerHTML = `<span class='error'>❌ ${err.message}</span>`;
    }
  });
});

/* ======================================================================
   ✅ DASHBOARD — Load summary, table, pagination, exports, 8 charts
====================================================================== */
document.addEventListener("DOMContentLoaded", () => {
  if (!(typeof pageIs === "function" ? pageIs("dashboard") : location.pathname.toLowerCase().includes("dashboard"))) return;

  let allData = [];
  let filteredData = [];
  let currentPage = 1;
  const rowsPerPage = 10;

  const tbody = document.querySelector("#resultsTable tbody");
  const pageInfo = document.getElementById("pageInfo");
  const prevBtn = document.getElementById("prevBtn");
  const nextBtn = document.getElementById("nextBtn");

  // Chart instances so we can destroy/recreate
  let charts = [];

  function destroyCharts() {
    charts.forEach((c) => c && typeof c.destroy === "function" && c.destroy());
    charts = [];
  }

  function num(v) {
    const n = Number(v);
    return Number.isFinite(n) ? n : 0;
    }

  async function loadSummary() {
    try {
      const res = await fetch("/outputs/summary.json?ts=" + Date.now());
      if (!res.ok) throw new Error("summary.json not found");
      allData = await res.json();
      filteredData = [...allData];
      renderTable();
      renderCharts();
    } catch (err) {
      console.error("Failed to load summary:", err);
      tbody.innerHTML = `<tr><td colspan="12" style="text-align:center;color:#d93025;">summary.json not found</td></tr>`;
    }
  }

  function renderTable() {
    const start = (currentPage - 1) * rowsPerPage;
    const slice = filteredData.slice(start, start + rowsPerPage);

    tbody.innerHTML = slice.map((d) => {
      const cost = d["Monthly Cost (USD)"];
      return `
        <tr>
          <td>${d["Source"] || "-"}</td>
          <td>${d["DB Name"] || "-"}</td>
          <td>${d["Cloud"] || "-"}</td>
          <td>${d["Estimated vCPUs"] ?? "-"}</td>
          <td>${d["Memory (GB)"] ?? "-"}</td>
          <td>${d["Total IOPS"] ?? "-"}</td>
          <td>${d["Throughput (MB/s)"] ?? "-"}</td>
          <td>${d["Recommended VM"] || "-"}</td>
          <td>${d["VM vCPUs"] ?? "-"}</td>
          <td>${d["VM Memory (GB)"] ?? "-"}</td>
          <td>${d["Category"] || "-"}</td>
          <td>${cost != null && cost !== "-" ? `$${cost}` : "-"}</td>
        </tr>`;
    }).join("");

    const totalPages = Math.max(1, Math.ceil(filteredData.length / rowsPerPage));
    pageInfo.textContent = `Page ${currentPage} of ${totalPages}`;
    prevBtn.disabled = currentPage <= 1;
    nextBtn.disabled = currentPage >= totalPages;
  }

  prevBtn?.addEventListener("click", () => {
    if (currentPage > 1) { currentPage--; renderTable(); }
  });

  nextBtn?.addEventListener("click", () => {
    const totalPages = Math.ceil(filteredData.length / rowsPerPage);
    if (currentPage < totalPages) { currentPage++; renderTable(); }
  });

  // Filters
  document.getElementById("applyFilters")?.addEventListener("click", () => {
    const cloud = (document.getElementById("filter-cloud")?.value || "").trim();
    const source = (document.getElementById("filter-source")?.value || "").trim();
    const date = (document.getElementById("filter-date")?.value || "").trim();

    filteredData = allData.filter((d) => {
      const matchCloud = !cloud || String(d["Cloud"] || "").toUpperCase() === cloud.toUpperCase();
      const matchSource = !source || String(d["Source"] || "").toLowerCase() === source.toLowerCase();
      const matchDate = !date || String(d["Timestamp"] || "").startsWith(date);
      return matchCloud && matchSource && matchDate;
    });

    currentPage = 1;
    renderTable();
    renderCharts(true);
  });

  document.getElementById("clearFilters")?.addEventListener("click", () => {
    filteredData = [...allData];
    const fc = document.getElementById("filter-cloud");
    const fs = document.getElementById("filter-source");
    const fd = document.getElementById("filter-date");
    if (fc) fc.value = "";
    if (fs) fs.value = "";
    if (fd) fd.value = "";
    currentPage = 1;
    renderTable();
    renderCharts(true);
  });

  // Exports
  document.getElementById("exportCSV")?.addEventListener("click", () => {
    if (!filteredData.length) return alert("No data to export.");
    const headers = [
      "Source","DB Name","Cloud","Estimated vCPUs","Memory (GB)","Total IOPS",
      "Throughput (MB/s)","Recommended VM","VM vCPUs","VM Memory (GB)","Category","Monthly Cost (USD)"
    ];
    const toCSVRow = (arr) =>
      arr.map((v) => {
        const s = v == null ? "" : String(v);
        return /[,"\n]/.test(s) ? `"${s.replace(/"/g, '""')}"` : s;
      }).join(",");

    const rows = [toCSVRow(headers)];
    filteredData.forEach((d) => {
      rows.push(toCSVRow([
        d["Source"] ?? "-",
        d["DB Name"] ?? "-",
        d["Cloud"] ?? "-",
        d["Estimated vCPUs"] ?? "-",
        d["Memory (GB)"] ?? "-",
        d["Total IOPS"] ?? "-",
        d["Throughput (MB/s)"] ?? "-",
        d["Recommended VM"] ?? "-",
        d["VM vCPUs"] ?? "-",
        d["VM Memory (GB)"] ?? "-",
        d["Category"] ?? "-",
        d["Monthly Cost (USD)"] ?? "-"
      ]));
    });

    const blob = new Blob([rows.join("\n")], { type: "text/csv" });
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = "summary.csv";
    a.click();
  });

  document.getElementById("exportPDF")?.addEventListener("click", () => window.print());

  // ------------- Charts (8) -------------
  function renderCharts(refresh = false) {
    const data = filteredData.length ? filteredData : allData;
    if (!data.length) return;

    if (refresh) destroyCharts();

    // Helper aggregations
    const by = (key) => {
      const out = {};
      data.forEach((d) => {
        const k = (d[key] ?? "Unknown") + "";
        out[k] = (out[k] || 0) + 1;
      });
      return out;
    };
    const sumBy = (metric, group) => {
      const out = {};
      data.forEach((d) => {
        const g = (d[group] ?? "Unknown") + "";
        out[g] = (out[g] || 0) + num(d[metric]);
      });
      return out;
    };

    // 1) Cost trend line (by date)
    const costByDate = {};
    data.forEach((d) => {
      const day = String(d["Timestamp"] || "").split("T")[0] || "Unknown";
      costByDate[day] = (costByDate[day] || 0) + num(d["Monthly Cost (USD)"]);
    });
    const trendLabels = Object.keys(costByDate).sort();
    const trendVals = trendLabels.map((k) => costByDate[k]);

    charts.push(new Chart(document.getElementById("costTrendChart"), {
      type: "line",
      data: { labels: trendLabels, datasets: [{ label: "Total Monthly Cost (USD)", data: trendVals, borderWidth: 2, fill: false, tension: 0.3 }] },
      options: { responsive: true, plugins: { legend: { display: false } } }
    }));

    // 2) Workload count by cloud (doughnut)
    const countCloud = by("Cloud");
    charts.push(new Chart(document.getElementById("workloadByCloudChart"), {
      type: "doughnut",
      data: { labels: Object.keys(countCloud), datasets: [{ label: "Workloads", data: Object.values(countCloud) }] },
      options: { responsive: true }
    }));

    // 3) Category distribution (pie)
    const countCat = by("Category");
    charts.push(new Chart(document.getElementById("categoryPieChart"), {
      type: "pie",
      data: { labels: Object.keys(countCat), datasets: [{ label: "Workloads", data: Object.values(countCat) }] },
      options: { responsive: true }
    }));

    // 4) Top 10 costliest workloads (horizontal bar)
    const top = [...data].sort((a, b) => num(b["Monthly Cost (USD)"]) - num(a["Monthly Cost (USD)"])).slice(0, 10);
    charts.push(new Chart(document.getElementById("topCostChart"), {
      type: "bar",
      data: {
        labels: top.map((d) => d["DB Name"] || d["Source"] || "N/A"),
        datasets: [{ label: "Monthly Cost (USD)", data: top.map((d) => num(d["Monthly Cost (USD)"])) }]
      },
      options: { responsive: true, indexAxis: 'y', scales: { x: { beginAtZero: true } } }
    }));

    // 5) vCPU sum by category (bar)
    const vcpuCat = sumBy("Estimated vCPUs", "Category");
    charts.push(new Chart(document.getElementById("vcpuByCategoryChart"), {
      type: "bar",
      data: { labels: Object.keys(vcpuCat), datasets: [{ label: "vCPUs (sum)", data: Object.values(vcpuCat) }] },
      options: { responsive: true, scales: { y: { beginAtZero: true } } }
    }));

    // 6) Memory sum by category (bar)
    const memCat = sumBy("Memory (GB)", "Category");
    charts.push(new Chart(document.getElementById("memByCategoryChart"), {
      type: "bar",
      data: { labels: Object.keys(memCat), datasets: [{ label: "Memory (GB) (sum)", data: Object.values(memCat) }] },
      options: { responsive: true, scales: { y: { beginAtZero: true } } }
    }));

    // 7) IOPS by cloud (pie)
    const iopsCloud = sumBy("Total IOPS", "Cloud");
    charts.push(new Chart(document.getElementById("iopsByCloudPie"), {
      type: "pie",
      data: { labels: Object.keys(iopsCloud), datasets: [{ label: "IOPS (sum)", data: Object.values(iopsCloud) }] },
      options: { responsive: true }
    }));

    // 8) Throughput by cloud (pie)
    const tpCloud = sumBy("Throughput (MB/s)", "Cloud");
    charts.push(new Chart(document.getElementById("tpByCloudPie"), {
      type: "pie",
      data: { labels: Object.keys(tpCloud), datasets: [{ label: "Throughput (MB/s) (sum)", data: Object.values(tpCloud) }] },
      options: { responsive: true }
    }));
  }

  loadSummary();
});

/* ======================================================================
   ✅ PROFILE PAGE — Info + Image Upload Button (minor fix)
====================================================================== */
document.addEventListener("DOMContentLoaded", () => {
  if (!pageIs("profile")) return;

  const user = JSON.parse(localStorage.getItem("russ_user") || "{}");
  if (!user?.email || !user?.license_key) {
    return (location.href = "/frontend/login.html");
  }

  const avatarImg = $("#avatarImage");
  const avatarLetter = $("#avatarInitial");
  const profileName = $("#profile-name");
  const profileEmail = $("#profile-email");
  const oldPassword = $("#old-password");
  const newPassword = $("#new-password");
  const fileInput = $("#profileImageInput");
  const uploadBtn = $("#uploadImageBtn");

  (async () => {
    try {
      const res = await fetch(`/api/profile?email=${encodeURIComponent(user.email)}&license_key=${encodeURIComponent(user.license_key)}`);
      const data = await res.json();
      if (data?.name) profileName.value = data.name;
      if (data?.email) profileEmail.value = data.email;

      if (data?.profile_image_url) {
        const url = data.profile_image_url + "?v=" + Date.now();
        avatarImg.src = url;
        avatarImg.style.display = "block";
        avatarLetter.style.display = "none";
      } else {
        avatarImg.style.display = "none";
        avatarLetter.style.display = "flex";
        avatarLetter.textContent = (data?.name?.[0] || "U").toUpperCase();
      }
    } catch (e) {
      console.warn("Profile load failed", e);
    }
  })();

  $("#saveProfileBtn")?.addEventListener("click", async () => {
    const form = new FormData();
    form.append("email", user.email);
    form.append("license_key", user.license_key);
    form.append("new_name", profileName.value);
    form.append("new_email", profileEmail.value);

    if (newPassword.value) {
      form.append("old_password", oldPassword.value);
      form.append("new_password", newPassword.value);
    }

    const res = await fetch("/api/profile", { method: "POST", body: form });
    const data = await res.json();

    if (data?.error) return alert("❌ " + data.error);

    alert("✅ Profile updated!");

    const newUser = {
      ...user,
      name: data.name || profileName.value || user.name,
      email: data.email || profileEmail.value || user.email,
      profile_image_url: data.profile_image_url || user.profile_image_url,
    };
    localStorage.setItem("russ_user", JSON.stringify(newUser));

    const headerImg = $("#user-avatar-img");
    const headerLetter = $("#user-avatar-letter");
    if (newUser.profile_image_url) {
      const u = newUser.profile_image_url + "?v=" + Date.now();
      if (headerImg) {
        headerImg.src = u;
        headerImg.style.display = "block";
      }
      if (headerLetter) headerLetter.style.display = "none";
    } else if (headerLetter) {
      headerLetter.textContent = (newUser.name?.[0] || "U").toUpperCase();
    }
  });

  uploadBtn?.addEventListener("click", (e) => {
    e.preventDefault();
    fileInput?.click();
  });

  fileInput?.addEventListener("change", async () => {
    if (!fileInput.files?.length) return;
    const form = new FormData();
    form.append("email", user.email);
    form.append("license_key", user.license_key);
    form.append("file", fileInput.files[0]);

    try {
      const res = await fetch("/api/profile/image", { method: "POST", body: form });
      const data = await res.json();
      if (!data?.profile_image_url) return alert("❌ Image upload failed.");

      const newUrl = data.profile_image_url + "?v=" + Date.now();

      avatarImg.src = newUrl;
      avatarImg.style.display = "block";
      avatarLetter.style.display = "none";

      const headerImg = $("#user-avatar-img");
      const headerLetter = $("#user-avatar-letter");
      if (headerImg && headerLetter) {
        headerImg.src = newUrl;
        headerImg.style.display = "block";
        headerLetter.style.display = "none";
      }

      const updated = { ...user, profile_image_url: newUrl };
      localStorage.setItem("russ_user", JSON.stringify(updated));

      alert("✅ Profile image updated!");
    } catch (e) {
      console.error("Upload error:", e);
      alert("❌ Error uploading image.");
    }
  });
});

/* ======================================================================
   ✅ ADMIN PAGE — User Management + Reports (UNCHANGED)
====================================================================== */
document.addEventListener("DOMContentLoaded", () => {
  if (!pageIs("admin")) return;

  const tabUsers = $("#tab-users");
  const tabReports = $("#tab-reports");
  const userTab = $("#user-tab");
  const reportsTab = $("#reports-tab");

  tabUsers?.addEventListener("click", () => {
    tabUsers.classList.add("active");
    tabReports.classList.remove("active");
    userTab.classList.remove("hidden");
    reportsTab.classList.add("hidden");
  });
  tabReports?.addEventListener("click", () => {
    tabReports.classList.add("active");
    tabUsers.classList.remove("active");
    reportsTab.classList.remove("hidden");
    userTab.classList.add("hidden");
    loadReports();
  });

  const loadBtn = $("#admin-load-users");
  loadBtn?.addEventListener("click", async () => {
    const adminEmail = $("#admin-email").value;
    const adminPassword = $("#admin-password").value;
    if (!adminEmail || !adminPassword) return alert("Admin email & password required");

    const res = await fetch(`/api/admin/users?email=${encodeURIComponent(adminEmail)}&password=${encodeURIComponent(adminPassword)}`);
    const data = await res.json();
    if (!res.ok) return alert("Error: " + (data.detail || "Failed to load users."));

    const tbody = $("#admin-users-table tbody");
    tbody.innerHTML = "";
    (data.users || []).forEach((u) => {
      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td>${u.id}</td>
        <td><input type="text" id="name-${u.id}" value="${u.name || ""}"></td>
        <td><input type="email" id="email-${u.id}" value="${u.email || ""}"></td>
        <td>${u.is_admin ? "<strong style='color:green;'>Admin</strong>" : "User"}</td>
        <td>
          <button class="btn" data-action="save" data-id="${u.id}">Save</button>
          <button class="btn-delete" data-action="delete" data-id="${u.id}">Delete</button>
          ${
            u.is_admin
              ? `<button class="btn-remove-admin" data-action="toggleAdmin" data-id="${u.id}" data-val="0">Remove Admin</button>`
              : `<button class="btn-admin" data-action="toggleAdmin" data-id="${u.id}" data-val="1">Make Admin</button>`
          }
        </td>`;
      tbody.appendChild(tr);
    });

    tbody.addEventListener("click", async (e) => {
      const btn = e.target.closest("button");
      if (!btn) return;
      const id = btn.getAttribute("data-id");
      const action = btn.getAttribute("data-action");

      if (action === "save") {
        const form = new FormData();
        form.append("admin_email", adminEmail);
        form.append("admin_password", adminPassword);
        form.append("name", $(`#name-${id}`).value || "");
        form.append("email", $(`#email-${id}`).value || "");
        await fetch(`/api/admin/users/${id}`, { method: "POST", body: form });
        loadBtn.click();
      } else if (action === "delete") {
        if (!confirm("Delete this user?")) return;
        await fetch(`/api/admin/users/${id}?admin_email=${encodeURIComponent(adminEmail)}&admin_password=${encodeURIComponent(adminPassword)}`, { method: "DELETE" });
        loadBtn.click();
      } else if (action === "toggleAdmin") {
        const val = btn.getAttribute("data-val");
        const form = new FormData();
        form.append("admin_email", adminEmail);
        form.append("admin_password", adminPassword);
        form.append("is_admin", val);
        await fetch(`/api/admin/users/${id}`, { method: "POST", body: form });
        loadBtn.click();
      }
    });
  });

  const reportBody = $("#report-table tbody");
  async function loadReports(filters = {}) {
    const params = new URLSearchParams(filters);
    const res = await fetch(`/api/reports?${params.toString()}`);
    const payload = await res.json();
    const reports = payload?.reports || [];

    if (!reports.length) {
      reportBody.innerHTML = `<tr><td colspan="13" style="text-align:center;color:#555;">No report records found</td></tr>`;
      return;
    }

    reportBody.innerHTML = reports
      .map((r) => {
        const cost = r.monthly_cost;
        return `
        <tr>
          <td>${r.timestamp ? new Date(r.timestamp).toLocaleString() : "-"}</td>
          <td>${r.user_email || "-"}</td>
          <td>${r.cloud || "-"}</td>
          <td>${r.source || "-"}</td>
          <td>${r.vcpus ?? "-"}</td>
          <td>${r.memory ?? "-"}</td>
          <td>${r.iops ?? "-"}</td>
          <td>${r.throughput ?? "-"}</td>
          <td>${r.recommended_vm || "-"}</td>
          <td>${r.vm_vcpus ?? "-"}</td>
          <td>${r.vm_memory ?? "-"}</td>
          <td>${r.category || "-"}</td>
          <td>${cost != null && cost !== "-" ? `$${cost}` : "-"}</td>
        </tr>`;
      })
      .join("");
  }

  $("#apply-report-filters")?.addEventListener("click", () => {
    loadReports({ email: $("#filter-email")?.value || "", cloud: $("#filter-cloud")?.value || "" });
  });
  $("#clear-report-filters")?.addEventListener("click", () => {
    if ($("#filter-email")) $("#filter-email").value = "";
    if ($("#filter-cloud")) $("#filter-cloud").value = "";
    loadReports();
  });

  // If Reports tab opens first, auto-load:
  if (reportsTab && !reportsTab.classList.contains("hidden")) loadReports();
});
