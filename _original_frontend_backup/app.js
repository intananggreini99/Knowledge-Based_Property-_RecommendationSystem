const $ = (id) => document.getElementById(id);

const formatRupiah = (value) => {
  if (value === null || value === undefined || Number.isNaN(Number(value))) return "-";
  return "Rp " + Number(value).toLocaleString("id-ID");
};

const renderCard = (item) => {
  const template = $("cardTemplate");
  const node = template.content.cloneNode(true);
  const typeLabel = item.property_label || (item.property_type === "rumah" ? "Rumah" : "Apartemen");
  const txnLabel = item.transaction_label || (item.transaction_type === "jual" ? "Jual Beli" : "Sewa");
  node.querySelector(".typeBadge").textContent = typeLabel;
  node.querySelector(".transactionBadge").textContent = txnLabel;
  node.querySelector(".title").textContent = item.title || `${typeLabel} — ${txnLabel}`;
  node.querySelector(".location").textContent = [item.city, item.district, item.address].filter(Boolean).join(" • ");
  node.querySelector(".score").textContent = Number(item.score).toFixed(2);
  node.querySelector(".summary").textContent = item.feature_summary || "-";
  node.querySelector(".price").textContent = `Harga: ${item.price_label || formatRupiah(item.price_rp)}`;
  node.querySelector(".source").textContent = `Sumber: ${item.source_dataset}`;
  node.querySelector(".furnish").textContent = `Furnishing: ${item.furnishing || "-"}`;

  const reasons = node.querySelector(".reasons");
  (item.matched_reasons || []).forEach((reason) => {
    const span = document.createElement("span");
    span.className = "tag";
    span.textContent = reason;
    reasons.appendChild(span);
  });

  return node;
};

const collectQuery = () => {
  const swimPoolValue = $("swim_pool").value;
  return {
    property_type: $("property_type").value || null,
    transaction_type: $("transaction_type").value || null,
    budget_max: $("budget_max").value ? Number($("budget_max").value) : null,
    city: $("city").value.trim() || null,
    district: $("district").value.trim() || null,
    bedrooms_min: $("bedrooms_min").value ? Number($("bedrooms_min").value) : null,
    bathrooms_min: $("bathrooms_min").value ? Number($("bathrooms_min").value) : null,
    furnishing: $("furnishing").value || null,
    swim_pool: swimPoolValue === "" ? null : swimPoolValue === "true",
    max_watt_min: $("max_watt_min").value ? Number($("max_watt_min").value) : null,
    size_min: $("size_min").value ? Number($("size_min").value) : null,
    top_k: Number($("top_k").value || 8),
    explain: true,
  };
};

const loadStats = async () => {
  try {
    const [healthRes, evalRes] = await Promise.all([
      fetch("/api/health"),
      fetch("/api/evaluate?sample_size=50&top_k=10"),
    ]);
    const health = await healthRes.json();
    const metrics = await evalRes.json();

    $("statsRecords").textContent = health.records?.toLocaleString("id-ID") || "—";
    $("statsValid").textContent = `${Math.round((metrics.valid_recommendation_rate || 0) * 100)}%`;
  } catch (e) {
    console.error(e);
  }
};

$("top_k").addEventListener("input", (e) => {
  $("topkLabel").textContent = e.target.value;
});

$("searchForm").addEventListener("submit", async (e) => {
  e.preventDefault();
  $("results").innerHTML = '<p class="text-slate-400">Memproses rekomendasi...</p>';
  $("resultMeta").textContent = "Menjalankan hard constraint filtering → soft ranking → constraint relaxation.";
  try {
    const payload = collectQuery();
    const res = await fetch("/api/recommend", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    const data = await res.json();
    $("stageBadge").textContent = `Stage: ${data.relaxation_stage}`;
    $("resultMeta").textContent = `${data.returned} properti ditemukan dari ${data.total_candidates} kandidat setelah penyaringan.`;

    const results = $("results");
    results.innerHTML = "";
    if (!data.results || data.results.length === 0) {
      results.innerHTML = '<p class="text-slate-400">Tidak ada hasil yang cocok.</p>';
      return;
    }
    data.results.forEach((item) => results.appendChild(renderCard(item)));
  } catch (err) {
    console.error(err);
    $("results").innerHTML = '<p class="text-rose-300">Terjadi kesalahan saat mengambil rekomendasi.</p>';
  }
});

loadStats();
