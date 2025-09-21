"""
Application Utilities
Common utility functions and helper methods
"""

import os
import platform
import time
import threading
import hashlib
from datetime import datetime
import tkinter as tk


class AppUtils:
    @staticmethod
    def get_local_ip():
        """Get local IP address"""
        import socket
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                s.connect(('8.8.8.8', 80))
                return s.getsockname()[0]
        except:
            return '127.0.0.1'

    @staticmethod
    def format_size(size):
        """Format file size in human readable format"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} TB"

    @staticmethod
    def format_speed(bytes_per_second):
        """Format transfer speed in human readable format"""
        return f"{AppUtils.format_size(bytes_per_second)}/s"

    @staticmethod
    def format_duration(seconds):
        """Format duration in human readable format"""
        if seconds < 60:
            return f"{seconds:.1f}s"
        elif seconds < 3600:
            return f"{seconds/60:.1f}m"
        else:
            return f"{seconds/3600:.1f}h"

    @staticmethod
    def validate_port(port_str):
        """Validate port number"""
        try:
            port = int(port_str)
            return 1024 <= port <= 65535
        except ValueError:
            return False

    @staticmethod
    def validate_ip(ip_str):
        """Validate IP address"""
        try:
            parts = ip_str.split('.')
            return len(parts) == 4 and all(0 <= int(part) <= 255 for part in parts)
        except ValueError:
            return False

    @staticmethod
    def safe_filename(filename):
        """Create a safe filename by removing invalid characters"""
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            filename = filename.replace(char, '_')
        return filename.strip()

    @staticmethod
    def get_system_info():
        """Get system information"""
        return {
            'platform': platform.system(),
            'platform_release': platform.release(),
            'platform_version': platform.version(),
            'architecture': platform.machine(),
            'processor': platform.processor(),
            'python_version': platform.python_version(),
            'hostname': platform.node()
        }

    @staticmethod
    def calculate_eta(start_time, current_progress, total_progress):
        """Calculate estimated time of arrival"""
        if current_progress <= 0:
            return float('inf')

        elapsed = time.time() - start_time
        rate = current_progress / elapsed

        if rate <= 0:
            return float('inf')

        remaining = total_progress - current_progress
        return remaining / rate

    @staticmethod
    def log_message(widget, message, level='info'):
        """Enhanced logging with colors and timestamps"""
        if widget is None:
            return

        timestamp = datetime.now().strftime("%H:%M:%S")
        icons = {'info': 'ℹ️', 'success': '✅', 'error': '❌', 'warning': '⚠️'}
        icon = icons.get(level, 'ℹ️')

        widget.insert(tk.END, f"[{timestamp}] {icon} {message}\n")
        widget.see(tk.END)

        # Color coding
        if level == 'error':
            widget.tag_add("error", f"end-2l linestart", f"end-1l lineend")
            widget.tag_config("error", foreground="red")
        elif level == 'success':
            widget.tag_add("success", f"end-2l linestart", f"end-1l lineend")
            widget.tag_config("success", foreground="green")
        elif level == 'warning':
            widget.tag_add("warning", f"end-2l linestart", f"end-1l lineend")
            widget.tag_config("warning", foreground="orange")

    @staticmethod
    def play_notification():
        """Play system notification sound"""
        try:
            if platform.system() == "Windows":
                import winsound
                winsound.MessageBeep()
            elif platform.system() == "Darwin":  # macOS
                os.system("afplay /System/Library/Sounds/Glass.aiff")
            else:  # Linux
                os.system("paplay /usr/share/sounds/alsa/Front_Left.wav")
        except:
            pass

    @staticmethod
    def open_folder(path):
        """Open folder in file manager"""
        if os.path.exists(path):
            if platform.system() == "Windows":
                os.startfile(path)
            elif platform.system() == "Darwin":  # macOS
                os.system(f"open '{path}'")
            else:  # Linux
                os.system(f"xdg-open '{path}'")

    @staticmethod
    def get_available_port(start_port=12345, max_attempts=100):
        """Find an available port starting from start_port"""
        import socket
        for port in range(start_port, start_port + max_attempts):
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.bind(('', port))
                    return port
            except OSError:
                continue
        return None

    @staticmethod
    def center_window(window, width=None, height=None):
        """Center a window on the screen"""
        window.update_idletasks()

        if width is None:
            width = window.winfo_width()
        if height is None:
            height = window.winfo_height()

        x = (window.winfo_screenwidth() // 2) - (width // 2)
        y = (window.winfo_screenheight() // 2) - (height // 2)

        window.geometry(f'{width}x{height}+{x}+{y}')


class ProgressTracker:
    """Thread-safe progress tracking utility"""

    def __init__(self, total_size):
        self.total_size = total_size
        self.current_progress = 0
        self.start_time = time.time()
        self.last_update = time.time()
        self.speed_samples = []
        self.lock = threading.Lock()

    def update(self, bytes_transferred):
        """Update progress with bytes transferred"""
        with self.lock:
            self.current_progress += bytes_transferred
            current_time = time.time()

            # Calculate speed
            elapsed = current_time - self.start_time
            if elapsed > 0:
                current_speed = self.current_progress / elapsed
                self.speed_samples.append(current_speed)

                # Keep only recent samples
                if len(self.speed_samples) > 10:
                    self.speed_samples.pop(0)

    def get_progress_info(self):
        """Get current progress information"""
        with self.lock:
            percentage = (self.current_progress / self.total_size) * \
                100 if self.total_size > 0 else 0

            # Calculate average speed
            avg_speed = sum(self.speed_samples) / \
                len(self.speed_samples) if self.speed_samples else 0

            # Calculate ETA
            if avg_speed > 0:
                remaining = self.total_size - self.current_progress
                eta = remaining / avg_speed
            else:
                eta = float('inf')

            return {
                'percentage': percentage,
                'current': self.current_progress,
                'total': self.total_size,
                'speed': avg_speed,
                'eta': eta,
                'elapsed': time.time() - self.start_time
            }


class ThreadSafeCounter:
    """Thread-safe counter utility"""

    def __init__(self, initial_value=0):
        self.value = initial_value
        self.lock = threading.Lock()

    def increment(self, amount=1):
        """Increment counter by amount"""
        with self.lock:
            self.value += amount
            return self.value

    def decrement(self, amount=1):
        """Decrement counter by amount"""
        with self.lock:
            self.value -= amount
            return self.value

    def get(self):
        """Get current value"""
        with self.lock:
            return self.value

    def set(self, value):
        """Set value"""
        with self.lock:
            self.value = value
            return self.value


class EventManager:
    """Simple event management system"""

    def __init__(self):
        self.handlers = {}
        self.lock = threading.Lock()

    def subscribe(self, event_type, handler):
        """Subscribe to an event type"""
        with self.lock:
            if event_type not in self.handlers:
                self.handlers[event_type] = []
            self.handlers[event_type].append(handler)

    def unsubscribe(self, event_type, handler):
        """Unsubscribe from an event type"""
        with self.lock:
            if event_type in self.handlers:
                try:
                    self.handlers[event_type].remove(handler)
                except ValueError:
                    pass

    def emit(self, event_type, data=None):
        """Emit an event"""
        with self.lock:
            handlers = self.handlers.get(event_type, []).copy()

        # Call handlers outside the lock to avoid deadlocks
        for handler in handlers:
            try:
                handler(data)
            except Exception as e:
                print(f"Error in event handler for {event_type}: {e}")


class NetworkUtils:
    """Network-related utility functions"""

    @staticmethod
    def get_network_interfaces():
        """Get available network interfaces"""
        import socket
        interfaces = []

        try:
            hostname = socket.gethostname()
            local_ip = socket.gethostbyname(hostname)
            interfaces.append({
                'name': 'Local',
                'ip': local_ip,
                'hostname': hostname
            })
        except:
            pass

        # Add localhost
        interfaces.append({
            'name': 'Localhost',
            'ip': '127.0.0.1',
            'hostname': 'localhost'
        })

        return interfaces

    @staticmethod
    def test_connection(host, port, timeout=5):
        """Test connection to a host and port"""
        import socket
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            result = sock.connect_ex((host, port))
            sock.close()
            return result == 0
        except:
            return False

    @staticmethod
    def is_port_available(port, host='localhost'):
        """Check if a port is available"""
        import socket
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.bind((host, port))
                return True
        except OSError:
            return False


class FileHasher:
    """Utility for calculating file hashes"""

    @staticmethod
    def calculate_hash(file_path, algorithm='sha256', chunk_size=8192):
        """Calculate hash of a file"""
        try:
            hash_obj = hashlib.new(algorithm)
            with open(file_path, 'rb') as f:
                while chunk := f.read(chunk_size):
                    hash_obj.update(chunk)
            return hash_obj.hexdigest()
        except Exception:
            return None

    @staticmethod
    def verify_hash(file_path, expected_hash, algorithm='sha256'):
        """Verify file hash"""
        calculated_hash = FileHasher.calculate_hash(file_path, algorithm)
        return calculated_hash == expected_hash if calculated_hash else False


class MemoryMonitor:
    """Simple memory usage monitoring"""

    @staticmethod
    def get_memory_usage():
        """Get current memory usage"""
        try:
            import psutil
            process = psutil.Process()
            memory_info = process.memory_info()
            return {
                'rss': memory_info.rss,
                'vms': memory_info.vms,
                'percent': process.memory_percent()
            }
        except ImportError:
            return {'rss': 0, 'vms': 0, 'percent': 0}

    @staticmethod
    def format_memory(bytes_value):
        """Format memory size in human readable format"""
        return AppUtils.format_size(bytes_value)
