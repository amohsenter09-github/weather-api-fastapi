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
const statusEl = document.getElementById("status");
const result = document.getElementById("result");

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
    const weather = data.current_weather || {};
    const location = data.location || {};
    const place = [location.name, location.admin1, location.country].filter(Boolean).join(", ")
      || `${location.latitude}, ${location.longitude}`;
    result.innerHTML = `
      <p class="temp">${weather.temperature ?? "–"}°</p>
      <p class="meta">${codes[weather.weathercode] || "Current weather"} · ${place}</p>
      <div class="grid">
        <div class="stat"><span>Wind</span><strong>${weather.windspeed ?? "–"} km/h</strong></div>
        <div class="stat"><span>Direction</span><strong>${weather.winddirection ?? "–"}°</strong></div>
      </div>
    `;
    result.hidden = false;
    statusEl.hidden = true;
  } catch (error) {
    statusEl.className = "status error";
    statusEl.textContent = error.message;
  }
});
