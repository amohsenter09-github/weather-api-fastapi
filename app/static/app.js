const codes = {
  0: "Clear",
  1: "Mainly clear",
  2: "Partly cloudy",
  3: "Overcast",
  45: "Fog",
  51: "Drizzle",
  61: "Rain",
  71: "Snow",
  80: "Showers",
  95: "Thunderstorm",
};

const form = document.getElementById("form");
const saveBtn = document.getElementById("save");
const locateBtn = document.getElementById("locate");
const statusEl = document.getElementById("status");
const result = document.getElementById("result");
const placesEl = document.getElementById("places");
let lastLocation = null;

function showError(message) {
  statusEl.hidden = false;
  statusEl.className = "status error";
  statusEl.textContent = message;
}

function hourLabel(iso) {
  if (!iso) return "";
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return iso.slice(11, 16);
  return date.toLocaleTimeString([], { hour: "2-digit" });
}

function dayLabel(iso) {
  if (!iso) return "";
  const date = new Date(`${iso}T00:00:00`);
  if (Number.isNaN(date.getTime())) return iso;
  return date.toLocaleDateString([], { weekday: "short", month: "short", day: "numeric" });
}

function renderForecast(data) {
  const hours = (data.hourly || []).slice(0, 12);
  const days = data.daily || [];
  const hourly = hours.map((row) => `
    <div class="stat">
      <span>${hourLabel(row.time)}</span>
      <strong>${row.temperature ?? "–"}°</strong>
      <span>${row.precipitation_probability ?? "–"}% rain</span>
    </div>
  `).join("");
  const daily = days.map((row) => `
    <div class="stat">
      <span>${dayLabel(row.date)}</span>
      <strong>${row.temperature_min ?? "–"}° / ${row.temperature_max ?? "–"}°</strong>
      <span>${codes[row.weathercode] || "Forecast"} · ${row.precipitation_probability_max ?? "–"}%</span>
    </div>
  `).join("");
  return `
    ${hourly ? `<p class="meta">Next 12 hours</p><div class="grid forecast">${hourly}</div>` : ""}
    ${daily ? `<p class="meta">7-day</p><div class="grid forecast">${daily}</div>` : ""}
  `;
}

function renderWeather(data) {
  const weather = data.current_weather || data.observation || {};
  const location = data.location || {};
  const temp = weather.temperature ?? "–";
  const place = location.name || lastLocation?.name || `${location.latitude ?? ""}, ${location.longitude ?? ""}`;
  result.innerHTML = `
    <p class="temp">${temp}°</p>
    <p class="meta">${codes[weather.weathercode] || "Current weather"} · ${place}</p>
    <div class="grid">
      <div class="stat"><span>Wind</span><strong>${weather.windspeed ?? "–"} km/h</strong></div>
      <div class="stat"><span>Direction</span><strong>${weather.winddirection ?? "–"}°</strong></div>
    </div>
    ${renderForecast(data)}
  `;
  result.hidden = false;
}

async function checkNearbyAlerts(lat, lon) {
  const resp = await fetch(`/alerts/evaluate?latitude=${lat}&longitude=${lon}`);
  const data = await resp.json().catch(() => ({}));
  if (!resp.ok || !data.triggered_alerts?.length) return;
  const lines = data.triggered_alerts.map((alert) => `${alert.metric} ${alert.operator} ${alert.threshold}`).join(", ");
  showError(`Nearby alert: ${lines}`);
}

async function loadPlaces() {
  placesEl.innerHTML = "";
  try {
    const response = await fetch("/places");
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || "Could not load places");
    for (const place of data.places || []) {
      const item = document.createElement("li");
      const label = document.createElement("span");
      label.textContent = place.name;
      label.style.cursor = "pointer";
      const actions = document.createElement("span");
      const refresh = document.createElement("button");
      refresh.type = "button";
      refresh.className = "secondary";
      refresh.textContent = "Refresh";
      const del = document.createElement("button");
      del.type = "button";
      del.className = "secondary";
      del.textContent = "Delete";
      label.addEventListener("click", async () => {
        const weatherResp = await fetch(`/weather?latitude=${place.latitude}&longitude=${place.longitude}`);
        const weatherData = await weatherResp.json();
        if (!weatherResp.ok) throw new Error(weatherData.detail || "Weather failed");
        lastLocation = place;
        renderWeather(weatherData);
        await checkNearbyAlerts(place.latitude, place.longitude);
        const histResp = await fetch(`/places/${place.id}/history?limit=5`);
        const hist = await histResp.json();
        if (histResp.ok && hist.observations?.length) {
          const lines = hist.observations.map((o) => `${o.temperature ?? "–"}° at ${o.fetched_at}`).join("<br>");
          result.innerHTML += `<p class="meta">History</p><p class="meta">${lines}</p>`;
        }
      });
      refresh.addEventListener("click", async (event) => {
        event.stopPropagation();
        const resp = await fetch(`/places/${place.id}/refresh`, { method: "POST" });
        const data = await resp.json();
        if (!resp.ok) return showError(data.detail || "Refresh failed");
        lastLocation = place;
        renderWeather({ current_weather: data.observation, location: place });
        if (data.triggered_alerts?.length) {
          showError(`${data.triggered_alerts.length} alert(s) triggered`);
        }
      });
      del.addEventListener("click", async (event) => {
        event.stopPropagation();
        const delResp = await fetch(`/places/${place.id}`, { method: "DELETE" });
        if (!delResp.ok && delResp.status !== 204) return showError("Could not delete place");
        await loadPlaces();
      });
      actions.append(refresh, del);
      item.append(label, actions);
      placesEl.append(item);
    }
  } catch (error) {
    showError(error.message);
  }
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const city = document.getElementById("city").value.trim();
  const latitude = document.getElementById("latitude").value.trim();
  const longitude = document.getElementById("longitude").value.trim();
  const params = new URLSearchParams();
  if (city) params.set("city", city);
  if (latitude) params.set("latitude", latitude);
  if (longitude) params.set("longitude", longitude);
  statusEl.hidden = false;
  statusEl.className = "status";
  statusEl.textContent = "Loading…";
  result.hidden = true;
  try {
    const response = await fetch(`/weather?${params.toString()}`);
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || "Request failed");
    lastLocation = {
      name: data.location?.name || city,
      latitude: data.location?.latitude,
      longitude: data.location?.longitude,
    };
    renderWeather(data);
    statusEl.hidden = true;
    if (data.location?.latitude != null) {
      await checkNearbyAlerts(data.location.latitude, data.location.longitude);
    }
  } catch (error) {
    showError(error.message);
  }
});

saveBtn.addEventListener("click", async () => {
  const city = document.getElementById("city").value.trim();
  const latitude = document.getElementById("latitude").value.trim();
  const longitude = document.getElementById("longitude").value.trim();
  const body = lastLocation
    ? { name: lastLocation.name, latitude: lastLocation.latitude, longitude: lastLocation.longitude }
    : {};
  if (!lastLocation) {
    if (city) body.name = city;
    if (latitude) body.latitude = Number(latitude);
    if (longitude) body.longitude = Number(longitude);
  }
  try {
    const response = await fetch("/places", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    const data = await response.json().catch(() => ({}));
    if (!response.ok) throw new Error(data.detail || "Could not save place");
    await loadPlaces();
  } catch (error) {
    showError(error.message);
  }
});

locateBtn.addEventListener("click", () => {
  if (!navigator.geolocation) return showError("Geolocation is not available");
  statusEl.hidden = false;
  statusEl.className = "status";
  statusEl.textContent = "Locating…";
  navigator.geolocation.getCurrentPosition(
    async (pos) => {
      const lat = pos.coords.latitude;
      const lon = pos.coords.longitude;
      document.getElementById("latitude").value = lat;
      document.getElementById("longitude").value = lon;
      document.getElementById("city").value = "";
      const response = await fetch(`/weather?latitude=${lat}&longitude=${lon}`);
      const data = await response.json();
      if (!response.ok) return showError(data.detail || "Weather failed");
      lastLocation = { name: "My location", latitude: lat, longitude: lon };
      renderWeather(data);
      statusEl.hidden = true;
      await checkNearbyAlerts(lat, lon);
    },
    () => showError("Could not read your location"),
    { enableHighAccuracy: true, timeout: 10000 },
  );
});

loadPlaces();
