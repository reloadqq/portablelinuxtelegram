
#!/usr/bin/env python3

import os
import sys
import time
import shutil
import base64
import zipfile
import requests
from pathlib import Path
from dotenv import load_dotenv
from types import SimpleNamespace
import traceback
import subprocess
import random
from urllib.parse import quote


load_dotenv(os.getenv('ENV_FILE', '.env'))

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    CYAN = '\033[96m'
    MAGENTA = '\033[95m'
    WHITE = '\033[97m'
    BOLD = '\033[1m'
    RESET = '\033[0m'
    PURPLE = '\033[38;5;129m'
    PINK = '\033[38;5;201m'

def gradient_text(text):
    lines = text.splitlines()
    colored_lines = []
    colors = [129, 135, 141, 147, 163, 199, 201]
    for i, line in enumerate(lines):
        color_idx = colors[min(i, len(colors)-1)]
        colored_lines.append(f'\033[38;5;{color_idx}m{line}{Colors.RESET}')
    return "\n".join(colored_lines)

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')


def get_key():
   
    try:
        import msvcrt
       
        while True:
            ch = msvcrt.getwch()
            if ch == '\r': return '\r'
            elif ch == '\x1b': 
                ch += msvcrt.getwch() + msvcrt.getwch()
                if ch == '\x1b[A': return 'UP'
                if ch == '\x1b[B': return 'DOWN'
                return 'ESC'
            elif ord(ch) == 27: return 'ESC'
            else: return ch
    except ImportError:
        import tty, termios
      
        fd = sys.stdin.fileno()
        old = termios.tcgetattr(fd)
        try:
            tty.setraw(fd)
            ch = sys.stdin.read(1)
            if ch == '\x1b': 
                seq = sys.stdin.read(2)
                if seq == '[A': return 'UP'
                if seq == '[B': return 'DOWN'
                return 'ESC'
            elif ch == '\x03': raise KeyboardInterrupt # Ctrl+C
            return ch
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old)


def menu_arrow(options, title="MENU", multi=False):
    if not options:
        clear_screen()
        print(gradient_text(r"""
 _      _                                 _____    _        ______
| |    | |                               (____ \  | |       / _____)
| |__ | |  ___    ____    ____  _   _    _    \ \ | |      | /
|  __)| | / _ \ |  _ \  / _  )| | | |  | |   | || |      | |
| |    | || |_| || | | |( (/ / | |_| |  | |__/ / | |_____ | \_____
|_|    |_| \___/ |_| |_| \____) \__  |  |_____/  |_______) \______)"""))
        print(f"\n{Colors.YELLOW}No options available.{Colors.RESET}")
        print(f"{Colors.MAGENTA}[Enter] Continue... {Colors.RESET}", end="")
        input()
        return -1

    selected = 0
    selected_items = set()
    banner_raw = r"""
 _      _                                 _____    _        ______
| |    | |                               (____ \  | |       / _____)
| |__ | |  ___    ____    ____  _   _    _    \ \ | |      | /
|  __)| | / _ \ |  _ \  / _  )| | | |  | |   | || |      | |
| |    | || |_| || | | |( (/ / | |_| |  | |__/ / | |_____ | \_____
|_|    |_| \___/ |_| |_| \____) \__  |  |_____/  |_______) \______)"""

    while True:
        clear_screen()
        print(gradient_text(banner_raw))
        border = Colors.PURPLE
        print(f"{border}┌──────────────────────────────────────────┐{Colors.RESET}")
        print(f"{border}│ {Colors.BOLD}{Colors.WHITE}{title.center(40)}{Colors.RESET}{border} │{Colors.RESET}")
        print(f"{border}├──────────────────────────────────────────┤{Colors.RESET}")

        for i, opt in enumerate(options):
            is_sel = (i == selected)
            prefix = f"  {Colors.PINK}→{Colors.RESET} " if is_sel else "    "
            label = opt
            if multi:
                mark = f"{Colors.GREEN}[✔]{Colors.RESET}" if i in selected_items else "[ ]"
                label = f"{mark} {opt}"
            
            if is_sel:
                print(f"{prefix}{Colors.BOLD}{Colors.WHITE}{label:<35}{Colors.RESET}{border}│{Colors.RESET}")
            else:
                color = Colors.CYAN if not (multi and i in selected_items) else Colors.YELLOW
                print(f"{prefix}{color}{label:<35}{Colors.RESET}{border}│{Colors.RESET}")

        print(f"{border}└──────────────────────────────────────────┘{Colors.RESET}")
        print(f"{Colors.MAGENTA} [↑/↓] Навигация | [Enter] Выбрать | [Esc] Назад {Colors.RESET}")
        if multi: print(f"{Colors.MAGENTA} [Space] Отметить {Colors.RESET}")

        key = get_key()
        if key == 'UP': selected = (selected - 1) % len(options)
        elif key == 'DOWN': selected = (selected + 1) % len(options)
        elif key == ' ' and multi:
            if selected in selected_items: selected_items.remove(selected)
            else: selected_items.add(selected)
        elif key == '\r': return list(selected_items) if multi else selected
        elif key == 'ESC': return -1


class GitHubAPI:
    BASE_URL = 'https://api.github.com'

    def __init__(self, config):
        self.config = config
        self.headers = {
            'Authorization': f"token {config.GITHUB_TOKEN}",
            'Accept': 'application/vnd.github.v3+json',
            'User-Agent': 'DataSyncClient'
        }

    def get_contents(self, path=''):
        url = f"{self.BASE_URL}/repos/{self.config.REPO_OWNER}/{self.config.REPO_NAME}/contents/{path}"
        try:
            r = requests.get(url, headers=self.headers, timeout=30)
            r.raise_for_status()
            return r.json()
        except Exception as e:
            print(f"{Colors.RED}GitHub API Error: {e}{Colors.RESET}")
            return []

    def upload_file(self, local_path, repo_path):
        encoded_path = quote(repo_path, safe='/').replace('+', '%2B')
        url = f"{self.BASE_URL}/repos/{self.config.REPO_OWNER}/{self.config.REPO_NAME}/contents/{encoded_path}"
        try:
            with open(local_path, 'rb') as f:
                content = base64.b64encode(f.read()).decode('utf-8')
            
            r_get = requests.get(url, headers=self.headers, timeout=10)
            sha = None
            if r_get.status_code == 200:
                sha = r_get.json().get('sha')

            payload = {'message': f'Sync {repo_path}', 'content': content}
            if sha: payload['sha'] = sha

            r = requests.put(url, headers=self.headers, json=payload, timeout=60)
            r.raise_for_status()
            return True
        except Exception as e:
            print(f"{Colors.RED}Upload Failed: {e}{Colors.RESET}")
            return False

    def download_file(self, repo_path, local_path):
      
        encoded_path = quote(repo_path, safe='/').replace('+', '%2B')
        url = f"{self.BASE_URL}/repos/{self.config.REPO_OWNER}/{self.config.REPO_NAME}/contents/{encoded_path}"
        try:
            r = requests.get(url, headers=self.headers, timeout=30)
            if r.status_code == 404:
                print(f"{Colors.RED}File not found{Colors.RESET}")
                return False
            if r.status_code == 403:
                print(f"{Colors.RED}Forbidden{Colors.RESET}")
                return False
            if r.status_code != 200:
                print(f"{Colors.RED}Error {r.status_code}{Colors.RESET}")
                return False
            r.raise_for_status()
            data = r.json()

            Path(local_path).parent.mkdir(parents=True, exist_ok=True)

            if isinstance(data, dict) and 'download_url' in data:
                download_url = data['download_url']
                with requests.get(download_url, stream=True, timeout=60) as raw_r:
                    raw_r.raise_for_status()
                    with open(local_path, 'wb') as f:
                        for chunk in raw_r.iter_content(chunk_size=8192):
                            if chunk: f.write(chunk)
                if Path(local_path).stat().st_size == 0:
                    print(f"{Colors.RED}Empty file{Colors.RESET}")
                    return False
                return True
            
            elif isinstance(data, dict) and 'content' in data:
                content = base64.b64decode(data['content'])
                if len(content) == 0:
                    print(f"{Colors.RED}Empty file{Colors.RESET}")
                    return False
                with open(local_path, 'wb') as f:
                    f.write(content)
                return True

            else:
                print(f"{Colors.RED}Unexpected format{Colors.RESET}")
                return False

        except requests.exceptions.HTTPError as e:
            print(f"{Colors.RED}HTTP Error: {e}{Colors.RESET}")
            return False
        except Exception as e:
            print(f"{Colors.RED}Error: {e}{Colors.RESET}")
            return False

    def delete_path(self, path):
        url = f"{self.BASE_URL}/repos/{self.config.REPO_OWNER}/{self.config.REPO_NAME}/contents/{path}"
        try:
            r_get = requests.get(url, headers=self.headers, timeout=10)
            if r_get.status_code != 200: return False
            
            data = r_get.json()
            if isinstance(data, dict) and 'sha' in data:
                r_del = requests.delete(url, headers=self.headers, 
                                        json={'message': f'Delete {path}', 'sha': data['sha']}, timeout=10)
                return r_del.status_code in [200, 204]
            elif isinstance(data, list):
                for item in data: self.delete_path(item['path'])
                return True
            return False
        except: return False


class App:
    def __init__(self):
        self.config = SimpleNamespace(
            GITHUB_TOKEN=os.getenv('GITHUB_TOKEN', ''),
            REPO_OWNER=os.getenv('REPO_OWNER', ''),
            REPO_NAME=os.getenv('REPO_NAME', ''),
            TARGET_FOLDER=os.getenv('TARGET_FOLDER', './data'),
            TEMP_FOLDER_NAME=os.getenv('TEMP_FOLDER_NAME', 'tdata'),
            CLIENT_LAUNCH_COMMAND=os.getenv('CLIENT_LAUNCH_COMMAND', 'start cmd /c dir') # Changed default for Windows compatibility
        )
        
        if not all([self.config.GITHUB_TOKEN, self.config.REPO_OWNER, self.config.REPO_NAME]):
            raise RuntimeError("Missing env vars: GITHUB_TOKEN, REPO_OWNER, REPO_NAME")

        Path(self.config.TARGET_FOLDER).mkdir(parents=True, exist_ok=True)
        self.api = GitHubAPI(self.config)

    def upload(self):
        folder = Path(self.config.TARGET_FOLDER)
        items = sorted([d.name for d in folder.iterdir()])
        sel = menu_arrow(items, "ZIP & UPLOAD", multi=True)
        if not sel or sel == -1: return

        for i in sel:
            name = items[i]
            target = folder / name
            if target.is_dir():
                zip_path = Path(f"{name}.zip")
                print(f"{Colors.YELLOW}Zipping {name}...{Colors.RESET}")
                try:
                    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                        for root, _, files in os.walk(target):
                            for file in files:
                                f_path = Path(root) / file
                                arcname = f_path.relative_to(target)
                                zipf.write(f_path, arcname)
                    
                    if self.api.upload_file(str(zip_path), str(zip_path)):
                        print(f"{Colors.GREEN}Uploaded: {zip_path}{Colors.RESET}")
                    os.remove(zip_path)
                except Exception as e:
                    print(f"{Colors.RED}Error: {e}{Colors.RESET}")
            elif target.is_file():
                if self.api.upload_file(str(target), name):
                    print(f"{Colors.GREEN}Uploaded: {name}{Colors.RESET}")
        time.sleep(2)

    def download(self):
        repo_files = self.api.get_contents()
        if not repo_files: return
        
        # Filter only files
        names = [f['name'] for f in repo_files if f.get('type') == 'file']
        if not names:
            print(f"{Colors.YELLOW}No files found in repository.{Colors.RESET}")
            time.sleep(2)
            return

        sel = menu_arrow(names, "DOWNLOAD & UNZIP", multi=True)
        if not sel or sel == -1: return

        success_count = 0
        for i in sel:
            name = names[i]
            temp_path = Path(name).with_suffix(Path(name).suffix + '.dl_tmp')
            
            print(f"{Colors.YELLOW}Downloading {name}...{Colors.RESET}")
            
            if self.api.download_file(name, str(temp_path)):
                
                if not temp_path.exists():
                    print(f"{Colors.RED}Error: File was not created.{Colors.RESET}")
                    continue
                if temp_path.stat().st_size == 0:
                    print(f"{Colors.RED}Error: Downloaded file is EMPTY ({name}). Skipping.{Colors.RESET}")
                    temp_path.unlink(missing_ok=True)
                    continue
              
                if name.endswith('.zip'):
                    if not zipfile.is_zipfile(temp_path):
                        print(f"{Colors.RED}Error: File '{name}' is NOT a valid ZIP archive (Header mismatch).{Colors.RESET}")
                        temp_path.unlink(missing_ok=True)
                        continue
                    
                    extract_path = Path(self.config.TARGET_FOLDER) / name.replace('.zip', '')
                    extract_path.mkdir(parents=True, exist_ok=True)
                    
                    try:
                        with zipfile.ZipFile(temp_path, 'r') as zf:
                            zf.extractall(extract_path)
                        print(f"{Colors.GREEN}Extracted to {extract_path.name}{Colors.RESET}")
                        success_count += 1
                    except zipfile.BadZipFile as e:
                        print(f"{Colors.RED}Error: Archive corrupted internally: {e}{Colors.RESET}")
                    except Exception as e:
                        print(f"{Colors.RED}Extraction Error: {e}{Colors.RESET}")
                
                else:
                    
                    final_path = Path(self.config.TARGET_FOLDER) / name
                    try:
                        shutil.move(str(temp_path), str(final_path))
                        print(f"{Colors.GREEN}Saved: {name}{Colors.RESET}")
                        success_count += 1
                    except Exception as e:
                        print(f"{Colors.RED}Move Error: {e}{Colors.RESET}")
            
            else:
                print(f"{Colors.RED}Failed to download {name}.{Colors.RESET}")
            
            # Cleanup temp file
            if temp_path.exists():
                temp_path.unlink(missing_ok=True)

        if success_count == 0:
            print(f"{Colors.YELLOW}No files were successfully processed.{Colors.RESET}")
        time.sleep(2)

    def launch_session(self):
        folder = Path(self.config.TARGET_FOLDER)
        items = sorted([d.name for d in folder.iterdir() if d.is_dir()])
        idx = menu_arrow(items + ["Cancel"], "LAUNCH SESSION")
        if idx == -1 or idx == len(items): return

        original = folder / items[idx]
        temp = folder / self.config.TEMP_FOLDER_NAME

        try:
            if temp.exists(): shutil.rmtree(temp)
            os.rename(original, temp)
            print(f"{Colors.GREEN}Active Session: {self.config.TEMP_FOLDER_NAME}{Colors.RESET}")
            
            
            proc = subprocess.Popen(self.config.CLIENT_LAUNCH_COMMAND, shell=True)
            
            input(f"\n{Colors.YELLOW}Press Enter to restore folder...{Colors.RESET}")
            
            if proc.poll() is None:
                proc.terminate()
                try:
                    proc.wait(timeout=3)
                except:
                    proc.kill()
            
            os.rename(temp, original)
        except Exception as e:
            print(f"{Colors.RED}Error: {e}{Colors.RESET}")
            if temp.exists():
                try: shutil.move(temp, original)
                except: pass
        time.sleep(1)

    def weblaunch(self):
        repo_files = self.api.get_contents()
        if not repo_files: return
        names = [f['name'] for f in repo_files if f.get('type') == 'file']
        if not names:
            print(f"{Colors.YELLOW}No files found in repository.{Colors.RESET}")
            time.sleep(2)
            return

        idx = menu_arrow(names, "WEB LAUNCH")
        if idx == -1: return

        name = names[idx]
        if not name.endswith('.zip'):
            print(f"{Colors.RED}Only .zip files supported for web launch.{Colors.RESET}")
            time.sleep(2)
            return

        folder = Path(self.config.TARGET_FOLDER)
        folder.mkdir(parents=True, exist_ok=True)

        session_name = name.replace('.zip', '')
        extract_path = folder / session_name
        temp_path = folder / (session_name + '.zip')

        print(f"{Colors.YELLOW}Downloading {name}...{Colors.RESET}")
        
        if not self.api.download_file(name, str(temp_path)):
            print(f"{Colors.RED}Download failed.{Colors.RESET}")
            time.sleep(2)
            return

        if temp_path.stat().st_size == 0:
            print(f"{Colors.RED}Downloaded file is empty.{Colors.RESET}")
            temp_path.unlink(missing_ok=True)
            time.sleep(2)
            return

        if not zipfile.is_zipfile(temp_path):
            print(f"{Colors.RED}Not a valid ZIP archive.{Colors.RESET}")
            temp_path.unlink(missing_ok=True)
            time.sleep(2)
            return

        if extract_path.exists(): shutil.rmtree(extract_path)
        extract_path.mkdir(parents=True, exist_ok=True)

        try:
            with zipfile.ZipFile(temp_path, 'r') as zf:
                zf.extractall(extract_path)
            print(f"{Colors.GREEN}Extracted to {session_name}{Colors.RESET}")
        except Exception as e:
            print(f"{Colors.RED}Extraction error: {e}{Colors.RESET}")
            temp_path.unlink(missing_ok=True)
            time.sleep(2)
            return

        temp_path.unlink(missing_ok=True)

        original = extract_path
        temp_session = folder / 'tdata'

        try:
            if temp_session.exists(): shutil.rmtree(temp_session)
            os.rename(original, temp_session)
            print(f"{Colors.GREEN}Launching session...{Colors.RESET}")

            proc = subprocess.Popen(self.config.CLIENT_LAUNCH_COMMAND, shell=True)

            while proc.poll() is None:
                time.sleep(1)

            print(f"{Colors.YELLOW}Session closed. Cleaning up...{Colors.RESET}")

            random_name = ''.join(random.choice('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789') for _ in range(random.randint(8, 16)))
            new_path = folder / random_name

            if temp_session.exists():
                os.rename(temp_session, new_path)
                print(f"{Colors.CYAN}Renamed to {random_name}{Colors.RESET}")

            shutil.rmtree(new_path)
            print(f"{Colors.GREEN}Session deleted.{Colors.RESET}")

        except Exception as e:
            print(f"{Colors.RED}Error: {e}{Colors.RESET}")
            if temp_session.exists():
                try: shutil.move(temp_session, original)
                except: pass
        time.sleep(2)

    def delete(self):
        repo_files = self.api.get_contents()
        if not repo_files: return
        names = [f['name'] for f in repo_files]
        sel = menu_arrow(names, "DELETE FROM REPO", multi=True)
        if not sel or sel == -1: return
        
        for i in sel:
            print(f"{Colors.RED}Deleting {names[i]}...{Colors.RESET}")
            self.api.delete_path(names[i])
        time.sleep(1)

    def run(self):
        while True:
            choice = menu_arrow(["Upload (ZIP)", "Download (UNZIP)", "Launch Session", "Web Launch", "Delete", "Exit"], "MANAGER")
            if choice == 0: self.upload()
            elif choice == 1: self.download()
            elif choice == 2: self.launch_session()
            elif choice == 3: self.weblaunch()
            elif choice == 4: self.delete()
            elif choice == 5 or choice == -1: break

if __name__ == '__main__':
    try:
        App().run()
    except Exception as e:
        print(f"{Colors.RED}\nCRITICAL ERROR:\n{e}{Colors.RESET}")
        if hasattr(traceback, 'print_exc'):
            traceback.print_exc()
        time.sleep(5)
        sys.exit(1)
