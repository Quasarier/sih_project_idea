# Coastal Watch React Build

This is the React/Vite version of the Coastal Watch analyst dashboard. The original vanilla frontend remains in `../frontend/`.

## Run

Install Node.js 20 or newer, then from this directory:

```powershell
npm install
npm run dev
```

Open the local Vite URL shown in the terminal.

## Structure

- `src/App.jsx` - dashboard composition and application state
- `src/main.jsx` - React entrypoint
- `src/styles.css` - responsive visual system
- `package.json` - Vite and React scripts/dependencies

The current UI uses representative Indian west-coast data. API, ML, AIS, and ocean-model integration belongs behind the backend boundaries described in `../docs/architecture.md`.
