# DMS Mobile App

Smartphone client for the Document Management System (Sprint 5, task 7), built with
**React Native + Expo (SDK 58)** and **Expo Router** (file-based navigation).

It offers the same features as the web UI:

- document list with status, category filter (with counts) and pull-to-refresh
- full-text search (Elasticsearch, fuzzy)
- create categories
- upload a PDF from the phone (Files app / iCloud Drive), with optional title and category
- document details: edit title, change category, open the PDF, delete
- additionally shows the **GenAI summary** of a document

> **AI-assisted development:** as required by the assignment, this app was generated with an AI coding
> tool (Claude by Anthropic) and then reviewed, run on a real device and tested manually by the team.

## Project structure

```text
mobile-app/
├── app/                      # screens; the file path is the route (Expo Router)
│   ├── _layout.jsx           # navigation stack (upload opens as a modal sheet)
│   ├── index.jsx             # dashboard: search, category filter, document list
│   ├── upload.jsx            # upload form
│   └── documents/[id].jsx    # document details
├── src/
│   ├── api/                  # REST client (timeouts, error handling) + endpoints
│   ├── components/           # reusable UI components
│   ├── utils/                # formatting, validation, filters (same rules as the web UI)
│   ├── config.js             # resolves the REST API address
│   └── theme.js              # colors, spacing, typography
└── index.js                  # entry point -> expo-router
```

## How the app finds the backend

A phone cannot reach `localhost` of the PC. In development, the app uses the PC's Wi-Fi address,
which Expo Go already knows because it loads the app from there, and calls the API **through nginx on
port 80** (`http://<pc-ip>/api`), exactly like the web UI.

To use a different address (e.g. tunnel mode or a backend on another machine), copy `.env.example` to
`.env` and set `EXPO_PUBLIC_API_URL`.

## Run the app (iPhone with Expo Go)

**Requirements**

- Node.js LTS (22 or newer)
- the backend running: `docker compose up -d` in the repository root
- **Expo Go** from the App Store with support for **SDK 58** (Expo Go supports only one SDK version)
- iPhone and PC in the **same Wi-Fi**

**Start**

```bash
cd src/mobile-app
npm install
npm start          # = expo start --port 8082 (port 8081 is taken by the REST API)
```

**Open the app on the iPhone** (one of these):

- scan the QR code in the terminal with the iPhone **camera** and tap "Open in Expo Go"
- type the `exp://…:8082` address shown in the terminal into **Safari** and open it in Expo Go
- sign in with the same Expo account on both sides (`npx expo login` on the PC); the project then
  appears under "Development servers" in Expo Go

Allow **"Local Network"** access when iOS asks; without it, the app cannot reach the PC.

> The app is made for iOS/Android only. `npm run web` does not work (web packages are not installed);
> in the browser, use the web UI at `http://localhost`.

## Development

- Add packages **only** with `npx expo install <package>`. It picks the version that matches SDK 58;
  plain `npm install <package>` can cause version conflicts (`ERESOLVE`).
- Do **not** run `npm audit fix --force`: it upgrades packages beyond what SDK 58 supports.
- `npx expo-doctor` checks the project for version and configuration problems.

## Technical notes

- **Uploads:** since Expo SDK 57, the global `fetch` is `expo/fetch`, which rejects React Native's classic
  `{ uri, name, type }` form parts ("Unsupported FormDataPart implementation"). The app therefore sends an
  `expo-file-system` `File` and copies it under the picked file name first, so the server receives the
  original name instead of the document picker's random cache name.
- **Error handling:** requests time out after 15 s (uploads after 120 s); network and nginx gateway errors
  (502/503/504) show a readable message, error messages of the REST API are shown as they are. The
  original error is logged to the Metro terminal (`[api] … failed`).

## Troubleshooting

| Problem | Solution |
|---|---|
| No QR code in the terminal | Git Bash does not show it. Run `npm start` in PowerShell, or type the `exp://` address into Safari on the iPhone. |
| "Signed in to Expo Go … but not signed in to Expo CLI" | Run `npx expo login` with the same account, or open the app via QR code / `exp://` address. |
| "The server is not reachable…" | Open `http://<pc-ip>/` in Safari on the iPhone. If the web UI does not load either, check the backend and the Windows firewall (allow inbound port 80, Wi-Fi network profile set to *Private*). |
| Expo Go does not load the app | Same Wi-Fi? Firewall prompt for Node.js allowed on private networks? Try `npx expo start --port 8082 --tunnel` and set `EXPO_PUBLIC_API_URL`. |
| "Project is incompatible with this version of Expo Go" | Expo Go supports only one SDK version. Upgrade the project with `npx expo install expo@latest`, then `npx expo install --fix`. |
| `ERESOLVE` error during install | Use `npx expo install <package>` instead of `npm install <package>`. |
| Find the PC's IP address | `ipconfig` → "Wireless LAN adapter WLAN" → IPv4 address |