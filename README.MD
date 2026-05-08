# 🦇 Basic Battery Analyzer 
*🇹🇷 [Türkçe dokümantasyon için tıklayın (Turkish Readme)](README_TR.MD)*

A powerful CLI tool that transforms complex Android `dumpsys batterystats` logs into readable, colorized, and meaningful summary reports in seconds.

Designed for developers and power users who want to test the **Deep Sleep** state of their devices, especially after Custom ROM, Kernel (e.g., crDroid, SUSFS), or Root (KernelSU/Magisk) modifications.

## 🚀 Features
* **Bilingual Support:** Full English and Turkish language support via CLI parameter.
* **Deep Sleep Calculation:** Automatically calculates the true deep sleep ratio of your device.
* **Top Drainers:** Lists the hardware and apps that drain your battery the most (in estimated mAh).
* **Smart Bug Detection:** Catches known hardware/kernel wakelock issues (e.g., `error -16`, `smp2p`, `IPA`) and alerts the user.
* **Markdown Export:** Saves reports as clean `.md` files to share in forums or Telegram groups.
* **Filtering:** Option to hide insignificant millisecond-level wakelocks.

## 🛠️ Installation
This tool uses standard Python libraries. No extra packages (`pip install`) are required.
Python 3.x is required.

```bash
git clone https://github.com/trup40/basicbatteryanalyzer.git
cd basicbatteryanalyzer
```

## 📱 How to Get the Log File?
You must pull the battery statistics from your device before using the tool. 
*(Note: For a clean test, it is highly recommended to reset the old data first and let the device sleep for at least 10 minutes before taking the new log.)*

**Method 1: Via PC (ADB - No Root Required)**
Connect your phone to your PC with USB Debugging enabled.
```bash
# 1. Reset old battery stats
adb shell dumpsys batterystats --reset

# 2. Let the device sleep for a while, then pull the log
adb shell dumpsys batterystats > battery_report.txt
```

**Method 2: Via Device (Termux etc. - Root Required)**
```bash
su
# 1. Reset old battery stats
dumpsys batterystats --reset

# 2. Let the device sleep for a while, then pull the log
dumpsys batterystats > battery_report.txt
```

## 💻 Usage
Pass the log file to the script as an argument:

**Standard Analysis (Default English):**
```bash
python basic_battery_analyzer.py battery_report.txt
```

**Run in Turkish with Filters and Markdown Export:**
```bash
python basic_battery_analyzer.py battery_report.txt --lang tr --min-ms 50 --export result.md
```

## ⚙️ Parameters
* `--lang`  : Output language (`en` or `tr`). Default is `en`.
* `--limit` : Maximum number of lines to display per category (Default: 20).
* `--min-ms`: Hides wakelocks shorter than the specified milliseconds.
* `--export`: Saves the color-stripped output as a clean markdown (`.md`) file.


## ☕ Donate

This project is free and open-source. If you find this useful and would like to support the development process, you can buy me a coffee using the crypto addresses below! 🚀

### 🪙 Crypto Donations

| Coin | Network | Wallet Address |
| :--- | :--- | :--- |
| **USDT (Tether)** | **TRC20** (Tron) | `TWxJVQ3PBCd8ZJJVkX2joe8WRGcSCdh8Ws` |
| **BTC (Bitcoin)** | Bitcoin (Bech32)| `bc1q7207qk3wk94a94xvxx43lxawsg69zpm0atvtd8` |
| **ETH (Ethereum)** | ERC20 | `0x1f5A2e35752c6f01c753F334292Fc7635Caeef56` |
| **BNB** | **BSC** (BEP20) | `0x93845c5Fb889C36E072B5683f1616C625C2deBe7` |

> [!IMPORTANT]
> Please ensure that the **Network** selection matches the table exactly. Using the wrong network may result in a permanent loss of funds.

---

**⭐ Star this repository if you find it useful!**
