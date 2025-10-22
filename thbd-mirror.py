
import os
import sys
import subprocess
import requests
from urllib.parse import urlparse
from bs4 import BeautifulSoup
from tqdm import tqdm
from time import sleep


class Colors:
    YELLOW = '\033[93m'
    GREEN = '\033[92m'
    RED = '\033[91m'
    RESET = '\033[0m'

VERSION = "1.0.0"


BANNER = f"""
{Colors.YELLOW}
{Colors.RESET}
 ████████ ██   ██ ██████  ██████  
    ██    ██   ██ ██   ██ ██   ██ 
    ██    ███████ ██████  ██   ██ 
    ██    ██   ██ ██   ██ ██   ██ 
    ██    ██   ██ ██████  ██████  
                                            
                                            
{Colors.GREEN}A fast, simple tool for website cloning, recon, and LFI checks. Version: {VERSION}{Colors.RESET}
{Colors.YELLOW}Author: mrzico69 | GitHub: https://github.com/mrzico69
{Colors.RESET}
"""

HELP_TEXT = f"""
{Colors.YELLOW}THBD Site Cloner - Usage Examples:{Colors.RESET}

1. Interactive mode (menu):
   python3 thbd_cloner.py

2. Clone site with auto LFI wordlist + preview:
   python3 thbd_cloner.py --url https://example.com --preview

3. Use custom LFI wordlist:
   python3 thbd_cloner.py --url https://example.com --custom-lfi wordlists/my_lfi.txt

4. Auto update tool:
   python3 thbd_cloner.py --auto-update

{Colors.YELLOW}Note:{Colors.RESET} Run without arguments to enter interactive mode.
"""

GITHUB_RAW_SCRIPT_URL = "https://raw.githubusercontent.com/mrzico69/THBD-Mirror/refs/heads/main/thbd-mirror.py"
GITHUB_RAW_LFI_WORDLIST_URL = "https://raw.githubusercontent.com/mrzico69/wordlists/refs/heads/main/lfi-params.txt"
GITHUB_VERSION_URL = "https://raw.githubusercontent.com/mrzico69/THBD-Mirror/refs/heads/main/version.txt"

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def create_result_dir(target_url):
    domain = urlparse(target_url).netloc
    path = os.path.join("results", domain)
    os.makedirs(path, exist_ok=True)
    return path

def clone_website(target_url, path):
    print(f"{Colors.YELLOW}[+] Cloning website with wget...{Colors.RESET}")
    cmd = f"wget --mirror --convert-links --adjust-extension --page-requisites --no-parent -P {path} {target_url}"
    os.system(cmd)
    print(f"{Colors.GREEN}[✔] Website cloned at: {path}{Colors.RESET}")

def wayback_scan(domain, output_path):
    print(f"\n{Colors.YELLOW}[+] Scanning Wayback Machine for exposed files...{Colors.RESET}")
    try:
        urls = subprocess.check_output(["waybackurls", domain], stderr=subprocess.DEVNULL).decode()
        sensitive_exts = [".php", ".bak", ".zip", ".tar", ".gz", ".sql"]
        findings = []
        for line in urls.splitlines():
            if any(ext in line for ext in sensitive_exts):
                findings.append(line)
        with open(os.path.join(output_path, "wayback_findings.txt"), "w") as f:
            for item in findings:
                f.write(item + "\n")
        print(f"{Colors.GREEN}[✔] Wayback scan done! Found {len(findings)} files. Saved to wayback_findings.txt{Colors.RESET}")
    except Exception:
        print(f"{Colors.RED}[!] Wayback scan failed or 'waybackurls' tool not installed.{Colors.RESET}")

def download_wordlist(url, save_path):
    print(f"{Colors.YELLOW}[+] Downloading LFI wordlist from GitHub...{Colors.RESET}")
    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        with open(save_path, "w") as f:
            f.write(r.text)
        print(f"{Colors.GREEN}[✔] Wordlist saved to {save_path}{Colors.RESET}")
        return True
    except Exception as e:
        print(f"{Colors.RED}[!] Failed to download wordlist: {e}{Colors.RESET}")
        return False

def lfi_scan(target_url, wordlist_path, output_path):
    print(f"\n{Colors.YELLOW}[+] Running LFI scan using wordlist: {wordlist_path}{Colors.RESET}")
    try:
        with open(wordlist_path) as f:
            params = [line.strip() for line in f if line.strip() and not line.startswith("#")]
    except Exception:
        print(f"{Colors.RED}[!] Could not read LFI wordlist.{Colors.RESET}")
        return
    
    payload = "../../../../etc/passwd"
    findings = []
    for param in tqdm(params, desc="Scanning params"):
        test_url = f"{target_url}?{param}={payload}"
        try:
            r = requests.get(test_url, timeout=5)
            if "root:x:" in r.text:
                findings.append(test_url)
        except requests.RequestException:
            pass
    with open(os.path.join(output_path, "lfi_results.txt"), "w") as f:
        for item in findings:
            f.write(item + "\n")
    print(f"{Colors.GREEN}[✔] LFI scan finished! Found {len(findings)} possible vulns. Saved to lfi_results.txt{Colors.RESET}")

def preview_server(path):
    print(f"\n{Colors.YELLOW}[→] Starting preview server at http://127.0.0.1:8080 ... Press Ctrl+C to stop.{Colors.RESET}")
    os.chdir(path)
    try:
        os.system("python3 -m http.server 8080")
    except KeyboardInterrupt:
        print("\n[!] Preview server stopped.")

def get_remote_version():
    try:
        r = requests.get(GITHUB_VERSION_URL, timeout=10)
        r.raise_for_status()
        return r.text.strip()
    except:
        return None

def auto_update():
    print(f"{Colors.YELLOW}[+] Checking for updates...{Colors.RESET}")
    remote_version = get_remote_version()
    if not remote_version:
        print(f"{Colors.RED}[!] Failed to fetch remote version info.{Colors.RESET}")
        return
    if remote_version == VERSION:
        print(f"{Colors.GREEN}[✔] You already have the latest version ({VERSION}).{Colors.RESET}")
        return

    print(f"{Colors.YELLOW}[!] New version available: {remote_version}. Updating...{Colors.RESET}")
    try:
        r = requests.get(GITHUB_RAW_SCRIPT_URL, timeout=10)
        r.raise_for_status()
        script_code = r.text
        with open(__file__, 'w') as f:
            f.write(script_code)
        print(f"{Colors.GREEN}[✔] Update applied. Please restart the tool.{Colors.RESET}")
        sys.exit(0)
    except Exception as e:
        print(f"{Colors.RED}[!] Update failed: {e}{Colors.RESET}")

def interactive_menu():
    while True:
        clear_screen()
        print(BANNER)
        print("Select an option:")
        print("  [1] Clone Website")
        print("  [2] Run LFI Scan (auto wordlist)")
        print("  [3] Full Auto (Clone + Wayback + LFI)")
        print("  [4] Start Preview Server")
        print("  [5] Auto Update Tool")
        print("  [6] Exit")
        choice = input(f"\n{Colors.YELLOW}Enter choice [1-6]: {Colors.RESET}").strip()
        if choice == '1':
            target = input("Enter target URL (e.g. https://example.com): ").strip()
            if not target.startswith("http"):
                target = "https://" + target
            path = create_result_dir(target)
            clone_website(target, path)
            input(f"\n{Colors.YELLOW}Press Enter to continue...{Colors.RESET}")
        elif choice == '2':
            target = input("Enter target URL (e.g. https://example.com): ").strip()
            if not target.startswith("http"):
                target = "https://" + target
            path = create_result_dir(target)
            wordlist_path = os.path.join("wordlists", "lfi-params.txt")
            if not os.path.exists(wordlist_path):
                os.makedirs("wordlists", exist_ok=True)
                downloaded = download_wordlist(GITHUB_RAW_LFI_WORDLIST_URL, wordlist_path)
                if not downloaded:
                    input(f"{Colors.RED}Cannot proceed without LFI wordlist. Press Enter to continue.{Colors.RESET}")
                    continue
            lfi_scan(target, wordlist_path, path)
            input(f"\n{Colors.YELLOW}Press Enter to continue...{Colors.RESET}")
        elif choice == '3':
            target = input("Enter target URL (e.g. https://example.com): ").strip()
            if not target.startswith("http"):
                target = "https://" + target
            path = create_result_dir(target)
            clone_website(target, path)
            wayback_scan(urlparse(target).netloc, path)
            wordlist_path = os.path.join("wordlists", "lfi-params.txt")
            if not os.path.exists(wordlist_path):
                os.makedirs("wordlists", exist_ok=True)
                download_wordlist(GITHUB_RAW_LFI_WORDLIST_URL, wordlist_path)
            lfi_scan(target, wordlist_path, path)
            input(f"\n{Colors.YELLOW}Press Enter to continue...{Colors.RESET}")
        elif choice == '4':
            domain = input("Enter domain directory name (e.g. example.com): ").strip()
            path = os.path.join("results", domain)
            if os.path.exists(path):
                preview_server(path)
            else:
                input(f"{Colors.RED}Directory not found. Clone site first.{Colors.RESET}")
        elif choice == '5':
            auto_update()
            input(f"\n{Colors.YELLOW}Press Enter to continue...{Colors.RESET}")
        elif choice == '6':
            print(f"{Colors.GREEN}Exiting... Stay safe bro!{Colors.RESET}")
            sys.exit(0)
        else:
            input(f"{Colors.RED}Invalid option! Press Enter to try again.{Colors.RESET}")

def one_liner_mode(args):
    target = args.get('--url')
    if not target:
        print(f"{Colors.RED}Error: --url argument is required in one-liner mode.{Colors.RESET}")
        sys.exit(1)
    if not target.startswith("http"):
        target = "https://" + target
    path = create_result_dir(target)
    
    custom_lfi = args.get('--custom-lfi')
    preview = args.get('--preview') is not None
    auto_update_flag = args.get('--auto-update') is not None
    
    if auto_update_flag:
        auto_update()
        return
    
    clone_website(target, path)
    wayback_scan(urlparse(target).netloc, path)
    
    if custom_lfi:
        if not os.path.exists(custom_lfi):
            print(f"{Colors.RED}Custom LFI wordlist not found: {custom_lfi}{Colors.RESET}")
            sys.exit(1)
        lfi_scan(target, custom_lfi, path)
    else:
        wordlist_path = os.path.join("wordlists", "lfi-params.txt")
        if not os.path.exists(wordlist_path):
            os.makedirs("wordlists", exist_ok=True)
            downloaded = download_wordlist(GITHUB_RAW_LFI_WORDLIST_URL, wordlist_path)
            if not downloaded:
                print(f"{Colors.RED}Failed to download default LFI wordlist. Exiting.{Colors.RESET}")
                sys.exit(1)
        lfi_scan(target, wordlist_path, path)
    
    if preview:
        preview_server(path)

def parse_args():
    args = {}
    skip_next = False
    for i, arg in enumerate(sys.argv[1:]):
        if skip_next:
            skip_next = False
            continue
        if arg.startswith('--'):
            if arg == '--help':
                print(HELP_TEXT)
                sys.exit(0)
            if arg in ['--preview', '--auto-update']:
                args[arg] = True
            else:
                if i+2 <= len(sys.argv)-1:
                    args[arg] = sys.argv[i+2]
                    skip_next = True
                else:
                    print(f"{Colors.RED}Error: {arg} requires a value.{Colors.RESET}")
                    sys.exit(1)
    return args

def main():
    clear_screen()
    print(BANNER)
    if len(sys.argv) > 1:
        args = parse_args()
        one_liner_mode(args)
    else:
        interactive_menu()

if __name__ == "__main__":
    main()
