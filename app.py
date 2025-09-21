"""
Advanced File Transfer Application - Modular Version
Main application class that coordinates all components
"""

import tkinter as tk
from tkinter import messagebox
import threading
import time
import platform
from datetime import datetime

# Import modular components
from network.transfer_manager import TransferManager
from ui.ui_manager import UIManager
from utils.file_manager import FileManager
from utils.settings_manager import SettingsManager
from utils.app_utils import AppUtils, ProgressTracker, EventManager


class AdvancedFileTransferApp:
    def __init__(self, root):
        self.root = root
        self.root.title("File Transfer")
        self.root.geometry("900x700")
        self.root.minsize(800, 600)

        # Initialize variables
        self._initialize_variables()

        # Initialize component managers
        self.transfer_manager = TransferManager(self)
        self.ui_manager = UIManager(self)
        self.file_manager = FileManager(self)
        self.settings_manager = SettingsManager(self)
        self.event_manager = EventManager()

        # Setup UI
        self.ui_manager.setup_main_ui()

        # Initialize services
        self._initialize_services()

        # Load settings
        self.settings_manager.load_settings()

    def _initialize_variables(self):
        """Initialize all application variables"""
        # Basic settings
        self.receiver_name = tk.StringVar(value=platform.node())
        self.compression_enabled = tk.BooleanVar(value=True)
        self.encryption_enabled = tk.BooleanVar(value=False)
        self.auto_accept = tk.BooleanVar(value=False)
        self.notification_sound = tk.BooleanVar(value=True)
        self.overwrite_files = tk.BooleanVar(value=False)
        self.create_subfolders = tk.BooleanVar(value=True)
        self.auto_discover = tk.BooleanVar(value=True)

        # Network settings
        self.size_limit_var = tk.StringVar(value="1024")
        self.buffer_size_var = tk.StringVar(value="16")
        self.timeout_var = tk.StringVar(value="30")
        self.max_threads_var = tk.StringVar(value="4")
        self.split_threshold_var = tk.StringVar(value="200")
        self.discovery_interval_var = tk.StringVar(value="30")

        # Transfer configuration
        self.max_file_size = 1024 * 1024 * 1024 * 1024  # 1TB
        self.chunk_size = 1024 * 1024  # 1MB
        self.max_threads = 4
        self.split_threshold = 100 * 1024 * 1024  # 100MB
        self.progress_update_interval = 0.1

        # Transfer tracking
        self.active_transfers = {}
        self.transfer_locks = {}
        self.chunk_progress = {}
        self.selected_files = []

        # State variables
        self.is_receiving = False
        self.receiver_socket = None
        self.receiver_thread = None

        # Statistics
        self.total_files_sent = 0
        self.total_files_received = 0
        self.total_bytes_sent = 0
        self.total_bytes_received = 0

        # Performance tracking
        self.last_progress_update = 0

    def _initialize_services(self):
        """Initialize background services"""
        # Start discovery listener
        self.transfer_manager.start_discovery_listener()

        # Start monitor update loop
        self.update_monitor()

        # Subscribe to events
        self.event_manager.subscribe(
            'transfer_started', self._on_transfer_started)
        self.event_manager.subscribe(
            'transfer_completed', self._on_transfer_completed)
        self.event_manager.subscribe(
            'transfer_failed', self._on_transfer_failed)

    # File management methods
    def add_files(self):
        """Add multiple files to selection"""
        files = self.ui_manager.browse_files()
        if files:
            added_files = self.file_manager.add_files(files)
            self.ui_manager.update_files_display()
            self.log_message(
                self.send_log, f"Added {len(added_files)} files to selection")

    def add_folder(self):
        """Add entire folder to selection"""
        folder = self.ui_manager.browse_folder()
        if folder:
            added_files = self.file_manager.add_folder(folder)
            self.ui_manager.update_files_display()
            self.log_message(
                self.send_log, f"Added {len(added_files)} files from folder")

    def clear_files(self):
        """Clear all selected files"""
        self.file_manager.clear_files()
        self.ui_manager.update_files_display()
        self.log_message(self.send_log, "Cleared all selected files")

    def remove_selected_files(self):
        """Remove selected files from the list"""
        selection = self.files_tree.selection()
        if not selection:
            self.ui_manager.show_info_dialog(
                "Info", "Please select files to remove from the list")
            return

        # Get the paths of selected items
        selected_paths = []
        for item in selection:
            values = self.files_tree.item(item)['values']
            if len(values) >= 4:
                selected_paths.append(values[3])

        # Remove files
        removed_count = self.file_manager.remove_selected_files(selected_paths)
        self.ui_manager.update_files_display()

        if removed_count > 0:
            self.log_message(
                self.send_log, f"Removed {removed_count} file(s) from selection")

    # Transfer methods
    def send_files(self):
        """Send multiple files with advanced options"""
        if not self.selected_files:
            self.ui_manager.show_error_dialog(
                "Error", "Please select files first")
            return

        # Get target host
        selection = self.host_tree.selection()
        if selection:
            item = self.host_tree.item(selection[0])
            host = item['values'][1]  # IP column
        else:
            host = self.manual_host_entry.get().strip()

        if not host:
            self.ui_manager.show_error_dialog(
                "Error", "Please select a receiver or enter IP address")
            return

        # Validate port
        try:
            port = int(self.sender_port_entry.get())
        except ValueError:
            self.ui_manager.show_error_dialog("Error", "Invalid port number")
            return

        # Validate files
        issues, total_size = self.file_manager.validate_files(
            self.selected_files)
        if issues:
            self.ui_manager.show_error_dialog(
                "Validation Error", "\\n".join(issues))
            return

        # Prepare transfer
        self.send_button.config(state='disabled')
        self.cancel_send_button.config(state='normal')

        transfer_id = f"send_{int(time.time())}"
        self.active_transfers[transfer_id] = {
            'direction': 'Sending',
            'files': self.selected_files.copy(),
            'peer': host,
            'progress': 0,
            'speed': 0,
            'start_time': time.time(),
            'cancel_event': threading.Event(),
            'status': 'Preparing'
        }

        # Start transfer in background
        threading.Thread(target=self._send_files_wrapper, args=(
            host, port, transfer_id), daemon=True).start()

    def _send_files_wrapper(self, host, port, transfer_id):
        """Wrapper for send_files to handle UI updates"""
        try:
            self.transfer_manager.send_files(
                host, port, self.selected_files, transfer_id)
        finally:
            # Cleanup and reset UI
            self.root.after(0, self._reset_send_ui)

    def _reset_send_ui(self):
        """Reset send UI after transfer completion"""
        self.send_button.config(state='normal')
        self.cancel_send_button.config(state='disabled')
        self.send_progress.config(value=0)
        self.send_speed.config(text="")
        self.send_status.config(text="Ready to send")

    def cancel_send(self):
        """Cancel active send operations"""
        for transfer_id, info in list(self.active_transfers.items()):
            if info['direction'] == 'Sending':
                info['cancel_event'].set()
                self.log_message(
                    self.send_log, "Transfer cancelled", 'warning')

    # Receiving methods
    def start_receiving(self):
        """Start enhanced file receiving service"""
        if self.is_receiving:
            self.ui_manager.show_info_dialog("Info", "Already receiving files")
            return

        try:
            port = int(self.recv_port_entry.get())
            self.max_file_size = int(self.size_limit_var.get()) * 1024 * 1024
            self.chunk_size = int(self.buffer_size_var.get()) * 1024
        except ValueError:
            self.ui_manager.show_error_dialog(
                "Error", "Invalid configuration values")
            return

        self.is_receiving = True
        self.transfer_manager.start_receiving(port)

        self.start_button.config(state='disabled')
        self.stop_button.config(state='normal')
        self.receiver_status.config(text=f"Listening on port {port}")

        self.log_message(
            self.recv_log, f"Started receiving on port {port} (Max: {self.format_size(self.max_file_size)})")

    def stop_receiving(self):
        """Stop receiving service"""
        self.is_receiving = False
        self.transfer_manager.stop_receiving()

        self.start_button.config(state='normal')
        self.stop_button.config(state='disabled')
        self.receiver_status.config(text="Not receiving")

        self.log_message(self.recv_log, "Stopped receiving")

    def ask_accept_transfer(self, file_count, total_size, sender_name):
        """Ask user to accept incoming transfer"""
        return self.ui_manager.ask_yes_no(
            "Incoming Transfer",
            f"Accept {file_count} files ({self.format_size(total_size)}) from {sender_name}?"
        )

    # Discovery methods
    def discover_hosts(self):
        """Discover available hosts"""
        # Clear existing hosts
        for item in self.host_tree.get_children():
            self.host_tree.delete(item)

        self.log_message(self.send_log, "Discovering receivers...")
        self.transfer_manager.discover_hosts()

    def _update_discovered_hosts(self, discovered):
        """Update discovered hosts tree"""
        for ip, info in discovered.items():
            status = "Online"
            last_seen = "Now"

            self.host_tree.insert('', 'end', values=(
                info['name'],
                ip,
                status,
                last_seen
            ))

        self.log_message(self.send_log, f"Found {len(discovered)} receivers")

    # Settings methods
    def browse_directory(self):
        """Browse for save directory"""
        directory = self.ui_manager.browse_folder()
        if directory:
            self.save_dir_entry.delete(0, tk.END)
            self.save_dir_entry.insert(0, directory)

    def open_save_folder(self):
        """Open save folder in file manager"""
        save_dir = self.save_dir_entry.get()
        AppUtils.open_folder(save_dir)

    def save_settings(self):
        """Save current settings"""
        self.settings_manager.save_settings()

    def apply_settings(self):
        """Apply current settings"""
        self.settings_manager.apply_network_settings()

    # Monitoring methods
    def update_monitor(self):
        """Update monitor display"""
        # Update statistics
        if hasattr(self, 'stats_labels'):
            self.stats_labels['files_sent'].config(
                text=str(self.total_files_sent))
            self.stats_labels['files_received'].config(
                text=str(self.total_files_received))
            self.stats_labels['data_sent'].config(
                text=self.format_size(self.total_bytes_sent))
            self.stats_labels['data_received'].config(
                text=self.format_size(self.total_bytes_received))
            self.stats_labels['active_transfers'].config(
                text=str(len(self.active_transfers)))

        # Update transfer tree
        if hasattr(self, 'transfer_tree'):
            # Clear existing items
            for item in self.transfer_tree.get_children():
                self.transfer_tree.delete(item)

            # Add current transfers
            for transfer_id, info in self.active_transfers.items():
                speed_mb = info['speed'] / \
                    (1024 * 1024) if info['speed'] > 0 else 0

                if info['progress'] > 0 and info['speed'] > 0:
                    remaining = 100 - info['progress']
                    eta_seconds = (
                        remaining / info['progress']) * (time.time() - info['start_time'])
                    eta_str = AppUtils.format_duration(eta_seconds)
                else:
                    eta_str = "Calculating..."

                files_info = info.get('files', [])
                if isinstance(files_info, list) and files_info:
                    file_display = files_info[0].get('name', 'Unknown')
                    if len(files_info) > 1:
                        file_display += f" (+{len(files_info)-1} more)"
                else:
                    file_display = "Multiple files"

                self.transfer_tree.insert('', 'end', values=(
                    info['direction'],
                    file_display,
                    info['peer'],
                    f"{info['progress']:.1f}%",
                    f"{speed_mb:.2f} MB/s",
                    eta_str,
                    info.get('status', 'Active')
                ))

        # Update receiver stats
        if self.is_receiving and hasattr(self, 'receiver_stats'):
            stats_text = f"Files: {self.total_files_received} | Data: {self.format_size(self.total_bytes_received)}"
            self.receiver_stats.config(text=stats_text)

        # Schedule next update
        self.root.after(1000, self.update_monitor)

    def refresh_monitor(self):
        """Refresh monitor display"""
        self.update_monitor()

    def cancel_all_transfers(self):
        """Cancel all active transfers"""
        for transfer_id, info in list(self.active_transfers.items()):
            info['cancel_event'].set()
        self.log_message(self.send_log, "All transfers cancelled", 'warning')

    def cancel_selected_transfer(self):
        """Cancel selected transfer from monitor"""
        selection = self.transfer_tree.selection()
        if selection:
            # Implementation for canceling specific transfer
            pass

    def show_transfer_details(self):
        """Show detailed transfer information"""
        selection = self.transfer_tree.selection()
        if selection:
            self.ui_manager.show_info_dialog(
                "Transfer Details", "Transfer details coming soon")

    def show_context_menu(self, event):
        """Show context menu for transfer tree"""
        item = self.transfer_tree.identify_row(event.y)
        if item:
            self.transfer_tree.selection_set(item)
            self.transfer_context_menu.post(event.x_root, event.y_root)

    # History methods
    def add_to_history(self, direction, files, peer, size, status, duration):
        """Add transfer to history"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        if isinstance(files, list):
            if len(files) == 1:
                file_display = files[0].get('name', 'Unknown') if isinstance(
                    files[0], dict) else str(files[0])
            else:
                file_display = f"{len(files)} files"
        else:
            file_display = str(files)

        duration_str = AppUtils.format_duration(
            duration) if duration > 0 else "0s"

        # Add to history tree (if it exists)
        try:
            if hasattr(self, 'history_tree'):
                self.history_tree.insert('', 0, values=(
                    timestamp,
                    direction,
                    file_display,
                    peer,
                    self.format_size(size) if size > 0 else "0 B",
                    status,
                    duration_str
                ))
        except:
            pass

    def refresh_history(self):
        """Refresh history display"""
        pass

    def export_history(self):
        """Export transfer history to file"""
        try:
            filename = self.ui_manager.browse_save_file(
                title="Export History",
                defaultextension=".csv",
                filetypes=[("CSV files", "*.csv"), ("Text files", "*.txt")]
            )
            if filename:
                with open(filename, 'w') as f:
                    f.write(
                        "Timestamp,Direction,Files,Peer,Size,Status,Duration\\n")
                    if hasattr(self, 'history_tree'):
                        for item in self.history_tree.get_children():
                            values = self.history_tree.item(item)['values']
                            f.write(",".join(str(v) for v in values) + "\\n")
                self.ui_manager.show_info_dialog(
                    "Export", f"History exported to {filename}")
        except Exception as e:
            self.ui_manager.show_error_dialog(
                "Error", f"Failed to export history: {e}")

    def clear_history(self):
        """Clear transfer history"""
        if self.ui_manager.ask_yes_no("Clear History", "Are you sure you want to clear all transfer history?"):
            if hasattr(self, 'history_tree'):
                for item in self.history_tree.get_children():
                    self.history_tree.delete(item)
            self.ui_manager.show_info_dialog(
                "History", "Transfer history cleared")

    # Event handlers
    def show_files_context_menu(self, event):
        """Show context menu for files tree"""
        item = self.files_tree.identify_row(event.y)
        if item:
            self.files_tree.selection_set(item)
            self.files_context_menu.post(event.x_root, event.y_root)

    def on_delete_key(self, event):
        """Handle Delete key press to remove selected files"""
        self.remove_selected_files()

    def on_file_double_click(self, event):
        """Handle double-click to remove file from selection"""
        item = self.files_tree.identify_row(event.y)
        if item:
            self.files_tree.selection_set(item)
            if self.ui_manager.ask_yes_no("Remove File", "Remove this file from selection?", default='no'):
                self.remove_selected_files()

    def _on_transfer_started(self, data):
        """Handle transfer started event"""
        pass

    def _on_transfer_completed(self, data):
        """Handle transfer completed event"""
        if self.notification_sound.get():
            AppUtils.play_notification()

    def _on_transfer_failed(self, data):
        """Handle transfer failed event"""
        pass

    # Utility methods
    def format_size(self, size):
        """Format file size in human readable format"""
        return AppUtils.format_size(size)

    def log_message(self, widget, message, level='info'):
        """Log message to widget"""
        AppUtils.log_message(widget, message, level)

    def cleanup(self):
        """Clean up resources on shutdown"""
        self.is_receiving = False

        if hasattr(self.transfer_manager, 'receiver_socket') and self.transfer_manager.receiver_socket:
            try:
                self.transfer_manager.receiver_socket.close()
            except:
                pass

        # Cancel all active transfers
        for transfer_id, info in self.active_transfers.items():
            info['cancel_event'].set()

        # Save settings before exit
        try:
            self.settings_manager.save_settings()
        except:
            pass


def main():
    """Main application entry point"""
    root = tk.Tk()

    # Center window on screen
    AppUtils.center_window(root, 900, 700)

    # Create and configure application
    app = AdvancedFileTransferApp(root)

    # Handle window closing
    def on_closing():
        if messagebox.askokcancel("Quit", "Do you want to quit? All active transfers will be cancelled."):
            app.cleanup()
            root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_closing)

    # Start auto-discovery if enabled
    if app.auto_discover.get():
        root.after(2000, app.discover_hosts)

    # Start the application
    try:
        root.mainloop()
    except KeyboardInterrupt:
        app.cleanup()
    except Exception as e:
        messagebox.showerror("Fatal Error", f"Application error: {e}")
        app.cleanup()


if __name__ == "__main__":
    main()
