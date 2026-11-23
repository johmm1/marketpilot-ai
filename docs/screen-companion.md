# MARKETPILOT AI — Screen Companion

## Intended workflow
1. Sign in to the MARKETPILOT web dashboard.
2. Open MetaTrader, a broker web terminal, or another charting platform.
3. In the **Live Screen Companion** panel, choose **Share a screen or window** and select the trading window.
4. Choose **Analyse this chart now** for a one-off review, or enable automatic review at an interval.
5. Read the visual assessment: BUY / SELL / WAIT, instrument/timeframe recognition, descriptive entry/stop/target zones, reasoning, and risk warnings.
6. Verify every observation and price level on the broker platform. Place any trade yourself unless a separately authorised broker execution integration has been built and tested.
7. Press **Stop sharing** when finished.

## Windows companion
The Electron shell uses the hosted dashboard by default. From the repository root:
```powershell
cd desktop
npm install
npm run package:win
```
The Windows installer is emitted under `desktop/release`. To use a different dashboard URL, set `MARKETPILOT_WEB_URL` before packaging/running.

The desktop app presents a native source picker before screen capture begins. The web dashboard also requests screen sharing only after the user presses the share button.

## Backend configuration
Set `OPENAI_API_KEY` only in the Render backend environment. `OPENAI_MODEL` must name a model available to the configured OpenAI account that supports image input. Never put the key in frontend environment variables or commit it to Git.

The authenticated endpoint is `POST /api/visual-analysis`. It accepts a JPEG/PNG/WebP data URL from the signed-in user's screen companion and returns a structured visual assessment. Screenshots are processed for the request and are not intentionally written to the application database or logs.

## Important limitations
- This is screenshot interpretation, not a guaranteed market-data feed. The model can misread chart labels, prices, candles, indicators, or timeframe.
- Continuous review sends repeated screenshots and may incur OpenAI usage costs. The user chooses the interval and can stop sharing at any time.
- Screen sharing does not grant broker API access or permission to execute orders.
- The current MT5 bridge is a read-only demo snapshot integration. It is not a live order execution connector.
- Live execution remains disabled. No trade is placed by the visual-analysis endpoint.
- Do not share screens containing passwords, recovery codes, payment details, or unrelated private information.
