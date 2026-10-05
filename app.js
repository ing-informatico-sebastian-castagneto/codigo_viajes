const DEFAULT_API_URL = "http://127.0.0.1:8000";
const state = { packages: [], destinations: [], selectedPackage: null, toastTimer: null };

const elements = {
  apiUrl: document.querySelector("#api-url"),
  apiForm: document.querySelector("#api-form"),
  statusDot: document.querySelector("#api-status-dot"),
  statusText: document.querySelector("#api-status-text"),
  packageGrid: document.querySelector("#package-grid"),
  packageEmpty: document.querySelector("#package-empty"),
  packageSearch: document.querySelector("#package-search"),
  destinationList: document.querySelector("#destination-list"),
  bookingDialog: document.querySelector("#booking-dialog"),
  bookingForm: document.querySelector("#booking-form"),
  bookingMessage: document.querySelector("#booking-message"),
  toast: document.querySelector("#toast"),
};

function apiBaseUrl() {
  return elements.apiUrl.value.trim().replace(/\/+$/, "");
}

async function apiRequest(path, options = {}) {
  const response = await fetch(`${apiBaseUrl()}${path}`, {
    ...options,
    headers: { Accept: "application/json", ...options.headers },
  });
  const contentType = response.headers.get("content-type") || "";
  const body = contentType.includes("application/json")
    ? await response.json()
    : await response.text();

  if (!response.ok) {
    const detail = typeof body === "object" ? body.detail : body;
    throw new Error(detail || `Error HTTP ${response.status}`);
  }
  return body;
}

function setConnection(online, message) {
  elements.statusDot.classList.toggle("online", online);
  elements.statusDot.classList.toggle("offline", !online);
  elements.statusText.textContent = message;
}

function formatPrice(value) {
  return new Intl.NumberFormat("es-CL", {
    style: "currency",
    currency: "CLP",
    maximumFractionDigits: 0,
  }).format(Number(value) || 0);
}

function formatDate(value) {
  if (!value) return "Fecha por confirmar";
  const date = new Date(`${value}T12:00:00`);
  if (Number.isNaN(date.getTime())) return value;
  return new Intl.DateTimeFormat("es-CL", {
    day: "numeric",
    month: "short",
    year: "numeric",
  }).format(date);
}

function showToast(message) {
  elements.toast.textContent = message;
  elements.toast.classList.add("visible");
  window.clearTimeout(state.toastTimer);
  state.toastTimer = window.setTimeout(() => {
    elements.toast.classList.remove("visible");
  }, 3600);
}

function setIndicator(id, value) {
  document.querySelector(id).textContent = new Intl.NumberFormat("es-CL").format(value);
}

function renderIndicators(data) {
  setIndicator("#stat-destinations", data.destinos?.disponibles ?? data.destinos?.total ?? 0);
  setIndicator("#stat-packages", data.paquetes?.total ?? 0);
  setIndicator("#stat-travelers", data.reservas?.personas ?? 0);
}

function imageForPackage(packageData, index) {
  const photos = [
    "photo-1519681393784-d120267933ba",
    "photo-1470770841072-f978cf4d019e",
    "photo-1464822759023-fed622ff2c3b",
    "photo-1472396961693-142e6e269027",
    "photo-1500530855697-b586d89ba3ee",
  ];
  const id = Number(packageData.id_paquete) || index;
  return `https://images.unsplash.com/${photos[Math.abs(id - 1) % photos.length]}?auto=format&fit=crop&w=900&q=80`;
}

function renderPackages() {
  const query = elements.packageSearch.value.trim().toLocaleLowerCase("es");
  const filtered = state.packages.filter((item) => {
    const destinations = (item.destinos || []).map((destination) => destination.nombre || "").join(" ");
    return `${item.nombre || ""} ${destinations}`.toLocaleLowerCase("es").includes(query);
  });

  elements.packageGrid.replaceChildren();
  elements.packageEmpty.hidden = filtered.length > 0;
  if (!filtered.length) return;

  filtered.forEach((item, index) => {
    const card = document.createElement("article");
    card.className = "package-card";

    const visual = document.createElement("div");
    visual.className = "package-visual";
    visual.style.backgroundImage = `url("${imageForPackage(item, index)}")`;

    const number = document.createElement("span");
    number.className = "package-number";
    number.textContent = String(index + 1).padStart(2, "0");
    visual.append(number);

    const availability = document.createElement("span");
    availability.className = "package-availability";
    availability.textContent = `${item.cupo_disponible ?? item.cupo_maximo ?? 0} lugares`;
    visual.append(availability);

    const content = document.createElement("div");
    content.className = "package-content";
    const location = document.createElement("span");
    location.className = "package-location";
    location.textContent = (item.destinos || []).map((destination) => destination.zona || destination.nombre).filter(Boolean).slice(0, 2).join(" · ") || "CHILE";
    const title = document.createElement("h3");
    title.textContent = item.nombre || "Aventura por descubrir";
    const meta = document.createElement("div");
    meta.className = "package-meta";
    const date = document.createElement("span");
    date.textContent = `◷ ${formatDate(item.fecha_salida)}`;
    const duration = document.createElement("span");
    duration.textContent = `⌖ ${(item.destinos || []).length || "Varios"} destinos`;
    meta.append(date, duration);

    const footer = document.createElement("div");
    footer.className = "package-footer";
    const price = document.createElement("div");
    price.className = "package-price";
    const priceLabel = document.createElement("small");
    priceLabel.textContent = "por persona";
    const priceValue = document.createElement("strong");
    priceValue.textContent = formatPrice(item.precio_persona);
    price.append(priceLabel, priceValue);

    const reserve = document.createElement("button");
    reserve.className = "reserve-button";
    reserve.type = "button";
    reserve.textContent = "↗";
    reserve.setAttribute("aria-label", `Reservar ${item.nombre || "paquete"}`);
    reserve.disabled = Number(item.cupo_disponible ?? item.cupo_maximo ?? 0) <= 0;
    reserve.addEventListener("click", () => openBooking(item));

    footer.append(price, reserve);
    content.append(location, title, meta, footer);
    card.append(visual, content);
    elements.packageGrid.append(card);
  });
}

function renderDestinations() {
  elements.destinationList.replaceChildren();
  const destinations = state.destinations.slice(0, 6);
  if (!destinations.length) {
    const empty = document.createElement("p");
    empty.className = "muted-message";
    empty.textContent = "Aún no hay destinos disponibles.";
    elements.destinationList.append(empty);
    return;
  }

  destinations.forEach((destination) => {
    const item = document.createElement("article");
    item.className = "destination-item";
    const icon = document.createElement("span");
    icon.className = "destination-icon";
    icon.setAttribute("aria-hidden", "true");
    icon.textContent = "⌖";
    const text = document.createElement("span");
    const name = document.createElement("strong");
    name.textContent = destination.nombre || "Destino";
    const zone = document.createElement("small");
    zone.textContent = destination.zona || `${destination.duracion_dias || 1} días de aventura`;
    text.append(name, zone);
    item.append(icon, text);
    elements.destinationList.append(item);
  });
}

async function refreshData() {
  setConnection(false, "Conectando con la API…");
  const results = await Promise.allSettled([
    apiRequest("/api/destinos"),
    apiRequest("/api/paquetes"),
    apiRequest("/api/indicadores"),
  ]);

  const [destinationsResult, packagesResult, indicatorsResult] = results;
  const hasDataEndpoint = destinationsResult.status === "fulfilled" || packagesResult.status === "fulfilled";
  setConnection(hasDataEndpoint, hasDataEndpoint ? "API conectada" : "API sin conexión");

  if (destinationsResult.status === "fulfilled") {
    state.destinations = Array.isArray(destinationsResult.value) ? destinationsResult.value : [];
    renderDestinations();
  } else {
    elements.destinationList.textContent = "No pudimos cargar destinos. Verifica la URL y que la API esté activa.";
    elements.destinationList.className = "destination-list muted-message";
  }

  if (packagesResult.status === "fulfilled") {
    state.packages = Array.isArray(packagesResult.value) ? packagesResult.value : [];
    renderPackages();
  } else {
    elements.packageGrid.replaceChildren();
    const error = document.createElement("p");
    error.className = "loading-card";
    error.textContent = "No pudimos cargar los paquetes. Revisa la dirección de tu API e inténtalo de nuevo.";
    elements.packageGrid.append(error);
    elements.packageEmpty.hidden = true;
  }

  if (indicatorsResult.status === "fulfilled") {
    renderIndicators(indicatorsResult.value);
  } else {
    setIndicator("#stat-destinations", state.destinations.length);
    setIndicator("#stat-packages", state.packages.length);
    setIndicator("#stat-travelers", 0);
  }

  if (!hasDataEndpoint) {
    showToast("No hay conexión con la API. Configura su dirección al final de la página.");
  } else if (indicatorsResult.status === "rejected") {
    console.warn("No se pudo cargar /api/indicadores:", indicatorsResult.reason);
  }
}

function openBooking(packageData) {
  state.selectedPackage = packageData;
  document.querySelector("#booking-title").textContent = packageData.nombre || "Una aventura te espera";
  document.querySelector("#booking-description").textContent =
    `${formatPrice(packageData.precio_persona)} por persona · Salida ${formatDate(packageData.fecha_salida)}.`;
  const people = document.querySelector("#booking-people");
  people.max = String(packageData.cupo_disponible ?? packageData.cupo_maximo ?? 1);
  people.value = "1";
  elements.bookingMessage.textContent = "";
  elements.bookingMessage.classList.remove("success");
  elements.bookingDialog.showModal();
}

elements.apiForm.addEventListener("submit", (event) => {
  event.preventDefault();
  const url = apiBaseUrl();
  try {
    const parsed = new URL(url);
    if (!["http:", "https:"].includes(parsed.protocol)) throw new Error("protocol");
  } catch {
    showToast("Escribe una dirección válida, por ejemplo https://mi-api.vercel.app");
    return;
  }
  localStorage.setItem("viajes-api-url", url);
  refreshData();
});

elements.packageSearch.addEventListener("input", renderPackages);
document.querySelector("#dialog-close").addEventListener("click", () => elements.bookingDialog.close());
elements.bookingDialog.addEventListener("click", (event) => {
  if (event.target === elements.bookingDialog) elements.bookingDialog.close();
});

elements.bookingForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const submitButton = elements.bookingForm.querySelector('[type="submit"]');
  const data = new FormData(elements.bookingForm);
  const payload = {
    id_usuario: Number(data.get("id_usuario")),
    id_paquete: Number(state.selectedPackage?.id_paquete),
    cantidad_personas: Number(data.get("cantidad_personas")),
  };

  elements.bookingMessage.textContent = "";
  submitButton.disabled = true;
  try {
    const result = await apiRequest("/api/reservas", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    elements.bookingMessage.textContent = result.mensaje || "¡Reserva confirmada!";
    elements.bookingMessage.classList.add("success");
    showToast(result.mensaje || "¡Tu reserva fue confirmada!");
    await refreshData();
    window.setTimeout(() => elements.bookingDialog.close(), 1200);
  } catch (error) {
    elements.bookingMessage.classList.remove("success");
    elements.bookingMessage.textContent = error.message || "No se pudo completar la reserva.";
  } finally {
    submitButton.disabled = false;
  }
});

elements.apiUrl.value = localStorage.getItem("viajes-api-url") || DEFAULT_API_URL;
document.querySelector("#current-year").textContent = String(new Date().getFullYear());
refreshData();
