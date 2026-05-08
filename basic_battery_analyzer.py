import sys
import argparse
import re

# Terminal color codes
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

# Localization (i18n) dictionary
STRINGS = {
    "en": {
        "file_err": "File read error:",
        "title": "🕵️‍♂️ BASIC BATTERY ANALYZER REPORT",
        "stats": "[GENERAL STATISTICS]",
        "deep_sleep": "Deep Sleep Ratio: ",
        "bat_time": "Time on Battery:  ",
        "screen_off": "Screen Off Time:  ",
        "wifi_sleep": "Wi-Fi Sleep Time: ",
        "drainers": "[TOP POWER DRAINERS (Estimated mAh)]",
        "no_record": "No records found. (The device might be in a perfect deep sleep!)",
        "info": "INFO",
        "saved": "✔️ Report successfully saved: ",
        "export_err": "Export error: ",
        "not_found_val": "Not Found",
        "calc_err_val": "Could not calculate"
    },
    "tr": {
        "file_err": "Dosya okuma hatası:",
        "title": "🕵️‍♂️ BASIC BATTERY ANALYZER RAPORU",
        "stats": "[GENEL İSTATİSTİKLER]",
        "deep_sleep": "Deep Sleep Oranı: ",
        "bat_time": "Bataryada Süre:   ",
        "screen_off": "Ekran Kapalı:     ",
        "wifi_sleep": "Wi-Fi Uyku:       ",
        "drainers": "[EN ÇOK GÜÇ TÜKETENLER (Tahmini mAh)]",
        "no_record": "Kayıt bulunamadı. (Cihaz kusursuz bir derin uykuda olabilir!)",
        "info": "BİLGİ",
        "saved": "✔️ Rapor başarıyla kaydedildi: ",
        "export_err": "Dışa aktarma hatası: ",
        "not_found_val": "Bulunamadı",
        "calc_err_val": "Hesaplanamadı"
    }
}

# Known bugs dictionary with bilingual descriptions
BUG_DICT = {
    "error -16": {
        "en": "Sensor (SPI) sleep resistance. Usually caused by DT2W/AOD.",
        "tr": "Sensör (SPI) uyku direnci. Genellikle DT2W/AOD kaynaklıdır."
    },
    "error -11": {
        "en": "Wi-Fi chip busy (EAGAIN). Temporary network wake.",
        "tr": "Wi-Fi çipi meşgul (EAGAIN). Geçici bir ağ uyanması."
    },
    "smp2p": {
        "en": "Modem crash! Firmware/Kernel mismatch (e.g., Airplane Mode bug).",
        "tr": "Modem kilitlenmesi! Firmware ile Kernel uyuşmazlığı (Örn: Uçak Modu bug'ı)."
    },
    "IPA": {
        "en": "Cellular data (Modem) sleep abort.",
        "tr": "Hücresel veri (Modem) uyku iptali."
    },
    "rmnet": {
        "en": "Mobile data interface wake.",
        "tr": "Mobil veri arayüzü uyanması."
    },
    "a80000.spi": {
        "en": "Touchscreen/Fingerprint sensor wake.",
        "tr": "Dokunmatik/Parmak izi sensörü uyanması."
    }
}

def remove_ansi_colors(text):
    """Removes terminal color codes for Markdown export."""
    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    return ansi_escape.sub('', text)

def print_and_store(text, output_list):
    """Prints to console and appends to the export list."""
    print(text)
    output_list.append(remove_ansi_colors(text))

def extract_general_stats(lines, lang):
    """Extracts general battery and sleep durations from the raw log."""
    loc = STRINGS[lang]
    stats = {
        "bat_time": loc["not_found_val"],
        "screen_off": loc["not_found_val"],
        "wifi_sleep": loc["not_found_val"],
        "deep_sleep": loc["calc_err_val"]
    }
    
    for line in lines:
        if "Time on battery:" in line and "realtime" in line:
            parts = line.split("Time on battery:")[1].split("realtime")
            stats["bat_time"] = parts[0].strip()
            
            if "uptime" in line:
                try:
                    uptime_percent = re.search(r'\(([\d,.]+)\%\)\s*uptime', line).group(1)
                    uptime_float = float(uptime_percent.replace(',', '.'))
                    deep_sleep_val = 100.0 - uptime_float
                    stats["deep_sleep"] = f"%{deep_sleep_val:.1f}"
                except:
                    pass

        elif "Time on battery screen off:" in line and "realtime" in line:
            stats["screen_off"] = line.split("Time on battery screen off:")[1].split("realtime")[0].strip()
        elif "WiFi Sleep time:" in line:
            stats["wifi_sleep"] = line.split("WiFi Sleep time:")[1].strip()
            
    return stats

def extract_top_drainers(lines):
    """Finds the top power draining components from 'Estimated power use'."""
    power_stats = []
    capturing = False
    
    for line in lines:
        if "Estimated power use (mAh):" in line:
            capturing = True
            continue
        
        if capturing:
            stripped = line.strip()
            if not stripped or line.startswith("0:") or "CPU scaling" in line:
                break
            if any(x in stripped for x in ["Capacity:", "Global", "(on battery", "(not on battery"]):
                continue
            
            match = re.search(r'^([a-zA-Z0-9_\s]+):\s*([\d.]+)', stripped)
            if match:
                name = match.group(1).strip()
                val = float(match.group(2))
                if val > 0.001: 
                    power_stats.append((name, val))
                    
    power_stats.sort(key=lambda x: x[1], reverse=True)
    return power_stats[:3] 

def parse_time_and_filter(text, min_ms):
    """Filters wake locks based on the minimum millisecond threshold."""
    if min_ms <= 0:
        return True
    
    if re.search(r'\b\d+[hms]\b(?!s)', text) and not re.search(r'^\d+ms$', text.strip()):
        if 's' in text or 'm' in text or 'h' in text:
             if not all(part.endswith('ms') for part in text.split() if part[0].isdigit()):
                 return True

    match = re.search(r'(\d+)\s*ms', text)
    if match:
        val = int(match.group(1))
        return val >= min_ms
    
    return True 

def parse_batterystats(filepath, limit, min_ms, export_path, lang):
    output_lines = []
    loc = STRINGS[lang]
    
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
    except Exception as e:
        print(f"{Colors.RED}{loc['file_err']} {e}{Colors.RESET}")
        return
    
    print_and_store(f"\n{Colors.BOLD}{Colors.CYAN}" + "="*65 + Colors.RESET, output_lines)
    print_and_store(f"{Colors.BOLD}{Colors.GREEN} {loc['title']} {Colors.RESET}", output_lines)
    print_and_store(f"{Colors.BOLD}{Colors.CYAN}" + "="*65 + Colors.RESET, output_lines)

    # General Statistics
    genel = extract_general_stats(lines, lang)
    print_and_store(f"\n{Colors.BOLD}{Colors.YELLOW}{loc['stats']}{Colors.RESET}", output_lines)
    print_and_store("-" * 65, output_lines)
    print_and_store(f" 💤 {Colors.BOLD}{loc['deep_sleep']}{Colors.RESET} {genel['deep_sleep']}", output_lines)
    print_and_store(f" 🔋 {Colors.BOLD}{loc['bat_time']}{Colors.RESET} {genel['bat_time']}", output_lines)
    print_and_store(f" 📱 {Colors.BOLD}{loc['screen_off']}{Colors.RESET} {genel['screen_off']}", output_lines)
    print_and_store(f" 🛜  {Colors.BOLD}{loc['wifi_sleep']}{Colors.RESET} {genel['wifi_sleep']}", output_lines)

    # Top Drainers
    drainers = extract_top_drainers(lines)
    if drainers:
        print_and_store(f"\n{Colors.BOLD}{Colors.RED}{loc['drainers']}{Colors.RESET}", output_lines)
        print_and_store("-" * 65, output_lines)
        for name, val in drainers:
            print_and_store(f" ⚡ {Colors.BOLD}{name}{Colors.RESET}: {val} mAh", output_lines)

    # Parse Wakelocks
    targets = {
        "KERNEL WAKELOCKS": ["All kernel wake locks:", "Kernel wake locks:"],
        "PARTIAL WAKELOCKS": ["All partial wake locks:", "Partial wake locks:"],
        "WAKEUP REASONS": ["Wakeup reasons:", "All wakeup reasons:"]
    }

    for title, triggers in targets.items():
        print_and_store(f"\n{Colors.BOLD}{Colors.CYAN}[{title}]{Colors.RESET}", output_lines)
        print_and_store("-" * 65, output_lines)
        
        captured = []
        capturing = False
        
        for line in lines:
            stripped = line.strip()
            
            if not capturing:
                for trigger in triggers:
                    if stripped.startswith(trigger):
                        capturing = True
                        break
                continue
            
            if capturing:
                if line.startswith("  ") or line.startswith("\t"):
                    if stripped and any(x in stripped for x in ["realtime", "times", "ms", "hr", "Abort"]):
                        if parse_time_and_filter(stripped, min_ms):
                            captured.append(stripped)
                elif not stripped:
                    continue
                else:
                    capturing = False
        
        if captured:
            for val in captured[:limit]:
                output_line = f" -> {val}"
                
                bug_found = False
                for bug_key, bug_data in BUG_DICT.items():
                    if bug_key in val:
                        output_line = output_line.replace(bug_key, f"{Colors.RED}{bug_key}{Colors.RESET}")
                        output_line += f" {Colors.YELLOW}[{loc['info']}: {bug_data[lang]}]{Colors.RESET}"
                        bug_found = True
                
                if not bug_found and re.search(r'\b\d+[hms]\b(?!s)', val):
                     output_line = output_line.replace("realtime", f"{Colors.BLUE}realtime{Colors.RESET}")
                
                print_and_store(output_line, output_lines)
        else:
            print_and_store(f"   {Colors.GREEN}{loc['no_record']}{Colors.RESET}", output_lines)

    # Markdown Export
    if export_path:
        try:
            with open(export_path, 'w', encoding='utf-8') as f:
                f.write("```markdown\n")
                f.write("\n".join(output_lines))
                f.write("\n```\n")
            print(f"\n{Colors.GREEN}{loc['saved']} {export_path}{Colors.RESET}")
        except Exception as e:
            print(f"\n{Colors.RED}{loc['export_err']} {e}{Colors.RESET}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Basic Battery Analyzer - CLI Tool")
    parser.add_argument("file", help="The dumpsys batterystats log file / İncelenecek log dosyası")
    parser.add_argument("--limit", type=int, default=20, help="Max lines per category (Default: 20)")
    parser.add_argument("--min-ms", type=int, default=0, help="Filter out wakelocks shorter than this ms / Milisaniye filtresi")
    parser.add_argument("--export", type=str, help="Export to a markdown file / Markdown olarak kaydet")
    parser.add_argument("--lang", type=str, choices=["en", "tr"], default="en", help="Language / Dil seçimi (en/tr)")
    
    args = parser.parse_args()

import sys
import argparse
import re

# Terminal color codes
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

# Localization (i18n) dictionary
STRINGS = {
    "en": {
        "file_err": "File read error:",
        "title": "🕵️‍♂️ BASIC BATTERY ANALYZER REPORT",
        "stats": "[GENERAL STATISTICS]",
        "deep_sleep": "Deep Sleep Ratio: ",
        "bat_time": "Time on Battery:  ",
        "screen_off": "Screen Off Time:  ",
        "wifi_sleep": "Wi-Fi Sleep Time: ",
        "drainers": "[TOP POWER DRAINERS (Estimated mAh)]",
        "no_record": "No records found. (The device might be in a perfect deep sleep!)",
        "info": "INFO",
        "saved": "✔️ Report successfully saved: ",
        "export_err": "Export error: ",
        "not_found_val": "Not Found",
        "calc_err_val": "Could not calculate"
    },
    "tr": {
        "file_err": "Dosya okuma hatası:",
        "title": "🕵️‍♂️ BASIC BATTERY ANALYZER RAPORU",
        "stats": "[GENEL İSTATİSTİKLER]",
        "deep_sleep": "Derin Uyku Oranı: ",
        "bat_time": "Bataryada Süre:   ",
        "screen_off": "Ekran Kapalı:     ",
        "wifi_sleep": "Wi-Fi Uyku:       ",
        "drainers": "[EN ÇOK GÜÇ TÜKETENLER (Tahmini mAh)]",
        "no_record": "Kayıt bulunamadı. (Cihaz kusursuz bir derin uykuda olabilir!)",
        "info": "BİLGİ",
        "saved": "✔️ Rapor başarıyla kaydedildi: ",
        "export_err": "Dışa aktarma hatası: ",
        "not_found_val": "Bulunamadı",
        "calc_err_val": "Hesaplanamadı"
    }
}

# Known bugs dictionary with bilingual descriptions
BUG_DICT = {
    "error -16": {
        "en": "Sensor (SPI) sleep resistance. Usually caused by DT2W/AOD.",
        "tr": "Sensör (SPI) uyku direnci. Genellikle DT2W/AOD kaynaklıdır."
    },
    "error -11": {
        "en": "Wi-Fi chip busy (EAGAIN). Temporary network wake.",
        "tr": "Wi-Fi çipi meşgul (EAGAIN). Geçici bir ağ uyanması."
    },
    "smp2p": {
        "en": "Modem crash! Firmware/Kernel mismatch (e.g., Airplane Mode bug).",
        "tr": "Modem kilitlenmesi! Firmware ile Kernel uyuşmazlığı (Örn: Uçak Modu bug'ı)."
    },
    "IPA": {
        "en": "Cellular data (Modem) sleep abort.",
        "tr": "Hücresel veri (Modem) uyku iptali."
    },
    "rmnet": {
        "en": "Mobile data interface wake.",
        "tr": "Mobil veri arayüzü uyanması."
    },
    "a80000.spi": {
        "en": "Touchscreen/Fingerprint sensor wake.",
        "tr": "Dokunmatik/Parmak izi sensörü uyanması."
    }
}

def remove_ansi_colors(text):
    """Removes terminal color codes for Markdown export."""
    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    return ansi_escape.sub('', text)

def print_and_store(text, output_list):
    """Prints to console and appends to the export list."""
    print(text)
    output_list.append(remove_ansi_colors(text))

def extract_general_stats(lines, lang):
    """Extracts general battery and sleep durations from the raw log."""
    loc = STRINGS[lang]
    stats = {
        "bat_time": loc["not_found_val"],
        "screen_off": loc["not_found_val"],
        "wifi_sleep": loc["not_found_val"],
        "deep_sleep": loc["calc_err_val"]
    }
    
    for line in lines:
        if "Time on battery:" in line and "realtime" in line:
            parts = line.split("Time on battery:")[1].split("realtime")
            stats["bat_time"] = parts[0].strip()
            
            if "uptime" in line:
                try:
                    uptime_percent = re.search(r'\(([\d,.]+)\%\)\s*uptime', line).group(1)
                    uptime_float = float(uptime_percent.replace(',', '.'))
                    deep_sleep_val = 100.0 - uptime_float
                    stats["deep_sleep"] = f"%{deep_sleep_val:.1f}"
                except:
                    pass

        elif "Time on battery screen off:" in line and "realtime" in line:
            stats["screen_off"] = line.split("Time on battery screen off:")[1].split("realtime")[0].strip()
        elif "WiFi Sleep time:" in line:
            stats["wifi_sleep"] = line.split("WiFi Sleep time:")[1].strip()
            
    return stats

def extract_top_drainers(lines):
    """Finds the top power draining components from 'Estimated power use'."""
    power_stats = []
    capturing = False
    
    for line in lines:
        if "Estimated power use (mAh):" in line:
            capturing = True
            continue
        
        if capturing:
            stripped = line.strip()
            if not stripped or line.startswith("0:") or "CPU scaling" in line:
                break
            if any(x in stripped for x in ["Capacity:", "Global", "(on battery", "(not on battery"]):
                continue
            
            match = re.search(r'^([a-zA-Z0-9_\s]+):\s*([\d.]+)', stripped)
            if match:
                name = match.group(1).strip()
                val = float(match.group(2))
                if val > 0.001: 
                    power_stats.append((name, val))
                    
    power_stats.sort(key=lambda x: x[1], reverse=True)
    return power_stats[:3] 

def parse_time_and_filter(text, min_ms):
    """Filters wake locks based on the minimum millisecond threshold."""
    if min_ms <= 0:
        return True
    
    if re.search(r'\b\d+[hms]\b(?!s)', text) and not re.search(r'^\d+ms$', text.strip()):
        if 's' in text or 'm' in text or 'h' in text:
             if not all(part.endswith('ms') for part in text.split() if part[0].isdigit()):
                 return True

    match = re.search(r'(\d+)\s*ms', text)
    if match:
        val = int(match.group(1))
        return val >= min_ms
    
    return True 

def parse_batterystats(filepath, limit, min_ms, export_path, lang):
    output_lines = []
    loc = STRINGS[lang]
    
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
    except Exception as e:
        print(f"{Colors.RED}{loc['file_err']} {e}{Colors.RESET}")
        return
    
    print_and_store(f"\n{Colors.BOLD}{Colors.CYAN}" + "="*65 + Colors.RESET, output_lines)
    print_and_store(f"{Colors.BOLD}{Colors.GREEN} {loc['title']} {Colors.RESET}", output_lines)
    print_and_store(f"{Colors.BOLD}{Colors.CYAN}" + "="*65 + Colors.RESET, output_lines)

    # General Statistics
    genel = extract_general_stats(lines, lang)
    print_and_store(f"\n{Colors.BOLD}{Colors.YELLOW}{loc['stats']}{Colors.RESET}", output_lines)
    print_and_store("-" * 65, output_lines)
    print_and_store(f" 💤 {Colors.BOLD}{loc['deep_sleep']}{Colors.RESET} {genel['deep_sleep']}", output_lines)
    print_and_store(f" 🔋 {Colors.BOLD}{loc['bat_time']}{Colors.RESET} {genel['bat_time']}", output_lines)
    print_and_store(f" 📱 {Colors.BOLD}{loc['screen_off']}{Colors.RESET} {genel['screen_off']}", output_lines)
    print_and_store(f" 🛜  {Colors.BOLD}{loc['wifi_sleep']}{Colors.RESET} {genel['wifi_sleep']}", output_lines)

    # Top Drainers
    drainers = extract_top_drainers(lines)
    if drainers:
        print_and_store(f"\n{Colors.BOLD}{Colors.RED}{loc['drainers']}{Colors.RESET}", output_lines)
        print_and_store("-" * 65, output_lines)
        for name, val in drainers:
            print_and_store(f" ⚡ {Colors.BOLD}{name}{Colors.RESET}: {val} mAh", output_lines)

    # Parse Wakelocks
    targets = {
        "KERNEL WAKELOCKS": ["All kernel wake locks:", "Kernel wake locks:"],
        "PARTIAL WAKELOCKS": ["All partial wake locks:", "Partial wake locks:"],
        "WAKEUP REASONS": ["Wakeup reasons:", "All wakeup reasons:"]
    }

    for title, triggers in targets.items():
        print_and_store(f"\n{Colors.BOLD}{Colors.CYAN}[{title}]{Colors.RESET}", output_lines)
        print_and_store("-" * 65, output_lines)
        
        captured = []
        capturing = False
        
        for line in lines:
            stripped = line.strip()
            
            if not capturing:
                for trigger in triggers:
                    if stripped.startswith(trigger):
                        capturing = True
                        break
                continue
            
            if capturing:
                if line.startswith("  ") or line.startswith("\t"):
                    if stripped and any(x in stripped for x in ["realtime", "times", "ms", "hr", "Abort"]):
                        if parse_time_and_filter(stripped, min_ms):
                            captured.append(stripped)
                elif not stripped:
                    continue
                else:
                    capturing = False
        
        if captured:
            for val in captured[:limit]:
                output_line = f" -> {val}"
                
                bug_found = False
                for bug_key, bug_data in BUG_DICT.items():
                    if bug_key in val:
                        output_line = output_line.replace(bug_key, f"{Colors.RED}{bug_key}{Colors.RESET}")
                        output_line += f" {Colors.YELLOW}[{loc['info']}: {bug_data[lang]}]{Colors.RESET}"
                        bug_found = True
                
                if not bug_found and re.search(r'\b\d+[hms]\b(?!s)', val):
                     output_line = output_line.replace("realtime", f"{Colors.BLUE}realtime{Colors.RESET}")
                
                print_and_store(output_line, output_lines)
        else:
            print_and_store(f"   {Colors.GREEN}{loc['no_record']}{Colors.RESET}", output_lines)

    # Markdown Export
    if export_path:
        try:
            with open(export_path, 'w', encoding='utf-8') as f:
                f.write("```markdown\n")
                f.write("\n".join(output_lines))
                f.write("\n```\n")
            print(f"\n{Colors.GREEN}{loc['saved']} {export_path}{Colors.RESET}")
        except Exception as e:
            print(f"\n{Colors.RED}{loc['export_err']} {e}{Colors.RESET}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Basic Battery Analyzer - CLI Tool")
    parser.add_argument("file", help="The dumpsys batterystats log file / İncelenecek log dosyası")
    parser.add_argument("--limit", type=int, default=20, help="Max lines per category (Default: 20)")
    parser.add_argument("--min-ms", type=int, default=0, help="Filter out wakelocks shorter than this ms / Milisaniye filtresi")
    parser.add_argument("--export", type=str, help="Export to a markdown file / Markdown olarak kaydet")
    parser.add_argument("--lang", type=str, choices=["en", "tr"], default="en", help="Language / Dil seçimi (en/tr)")
    
    args = parser.parse_args()
    parse_batterystats(args.file, args.limit, args.min_ms, args.export, args.lang)