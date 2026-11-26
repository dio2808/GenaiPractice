---
name: weather-reporter
description: Fetches current weather for cities and formats clear, actionable weather summaries. Use whenever the user asks about weather, temperature, or forecasts.
---

# Weather Reporter Instructions

When a user asks about the weather:

1. **Extract locations:** Identify every city mentioned in the prompt. If no city is specified, ask the user which city they want to check before calling any tool.
2. **Fetch conditions:** Call `get_weather` for each requested city.
3. **Format the response:**
   - Lead with the current condition for each city.
   - Keep the summary concise and easy to scan.
   - Suggest practical advice based on the reported condition (for example, sun protection or indoor alternatives).