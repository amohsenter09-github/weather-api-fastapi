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
const statusEl = document.getElementById("status");
const result = document.getElementById("result");
const placesEl = document.getElementById("places");
let lastLocation = null;

function showError(message) {
  statusEl.hidden = false;
  statusEl.className = "status error";
  statusEl.textContent = message;
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
  `;
  result.hidden = false;
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

loadPlaces();
