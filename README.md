# NSE Weekly Low Scanner

Automated NSE stock scanner — tracks weekly lows, break levels, and RSI.

## Files

| File | Purpose |
|------|---------|
| `scanner.py` | Python script — fetches data, writes `output/data.json` + `output/data.csv` |
| `symbols.txt` | Your watchlist — one NSE symbol per line |
| `stock_scanner.html` | Live browser dashboard — open this file in Chrome/Edge |
| `.github/workflows/scanner.yml` | GitHub Actions — runs automatically |

## How to use

### 1. Browser dashboard (no server needed)
Open `stock_scanner.html` in Chrome. Type your symbols, click **Refresh**. Data is fetched live from Yahoo Finance via the browser — no Python needed.

### 2. GitHub Actions automation
1. Push this repo to GitHub.
2. Go to **Actions** tab → **NSE Weekly Low Scanner** → click **Run workflow** for a manual run.
3. The workflow also runs automatically **Mon–Fri at 9:00 AM IST**.
4. After each run, `output/data.json` and `output/data.csv` are committed back to the repo.

### 3. Load GitHub data in the HTML dashboard
Once you have data in `output/data.json` (via GitHub Actions), you can fetch it directly.  
Replace the Yahoo Finance fetch in `stock_scanner.html` with:
```js
const resp = await fetch('https://raw.githubusercontent.com/YOUR_USERNAME/YOUR_REPO/main/output/data.json');
const json = await resp.json();
allData = json.data;
renderTable();
```

## Columns explained

| Column | Meaning |
|--------|---------|
| W-3L / W-2L / W-1L / CWL | Weekly low of each week (3 weeks ago → current) |
| W-3LB / W-2LB / W-1LB | Did the *next* week break that week's low? |
| BC | Did last close break the current week's low? |
| W-3CH% / W-2CH% / W-1CH% | % change in weekly close. **Red = low was broken that week** |
| LDC | Last day close |
| LDL | Last day low |
| DIFF%FWL | % from last close to W-1 low |
| DIFF%FLDL | % from last close to last day low |
| RSI14 | 14-period Wilder RSI |

## Schedule
Edit `.github/workflows/scanner.yml` to change the cron time:
```yaml
- cron: '30 3 * * 1-5'   # 9:00 AM IST = 3:30 UTC, Mon–Fri
```
