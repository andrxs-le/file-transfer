"""
User Interface Components
Handles all UI-related functionality including tabs, widgets, and interactions
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import platform
from datetime import datetime


class UIManager:
    def __init__(self, app_instance):
        self.app = app_instance
        self.setup_style()

    def setup_style(self):
        """Configure modern styling"""
        style = ttk.Style()
        style.theme_use('clam')

        # Configure colors and fonts
        style.configure('Title.TLabel', font=('Arial', 14, 'bold'))
        style.configure('Subtitle.TLabel', font=('Arial', 10, 'bold'))
        style.configure('Status.TLabel', font=('Arial', 9), foreground='#666')
        style.configure('Success.TLabel', font=(
            'Arial', 9), foreground='#2d5016')
        style.configure('Error.TLabel', font=(
            'Arial', 9), foreground='#cc0000')
        style.configure('Warning.TLabel', font=(
            'Arial', 9), foreground='#cc6600')

    def setup_main_ui(self):
        """Setup the main UI with modern design"""
        # Main container with padding
        main_frame = ttk.Frame(self.app.root, padding="10")
        main_frame.pack(fill='both', expand=True)

        # Title with version
        title_frame = ttk.Frame(main_frame)
        title_frame.pack(fill='x', pady=(0, 10))

        title_label = ttk.Label(
            title_frame, text="File Transfer", style='Title.TLabel')
        title_label.pack(side='left')

        version_label = ttk.Label(
            title_frame, text="v1.0", style='Status.TLabel')
        version_label.pack(side='right')

        # Notebook for tabs
        self.app.notebook = ttk.Notebook(main_frame)
        self.app.notebook.pack(fill='both', expand=True)

        # Create tabs
        self.create_sender_tab()
        self.create_receiver_tab()
        self.create_monitor_tab()
        self.create_settings_tab()
        self.create_history_tab()

        # Status bar
        self.create_status_bar(main_frame)

    def create_sender_tab(self):
        """Create enhanced sender tab with multi-file support"""
        sender_frame = ttk.Frame(self.app.notebook, padding="10")
        self.app.notebook.add(sender_frame, text='Send Files')

        # Connection section
        self._create_connection_section(sender_frame)

        # File selection section
        self._create_file_selection_section(sender_frame)

        # Transfer options
        self._create_transfer_options_section(sender_frame)

        # Transfer section
        self._create_transfer_control_section(sender_frame)

    def _create_connection_section(self, parent):
        """Create connection section for sender tab"""
        conn_frame = ttk.LabelFrame(parent, text="Connection", padding="10")
        conn_frame.pack(fill='x', pady=(0, 10))

        # Host discovery with refresh
        discovery_header = ttk.Frame(conn_frame)
        discovery_header.pack(fill='x')

        ttk.Label(discovery_header, text="Available Receivers:",
                  style='Subtitle.TLabel').pack(side='left')
        ttk.Button(discovery_header, text="Refresh",
                   command=self.app.discover_hosts, width=10).pack(side='right')

        # Host list with details
        host_frame = ttk.Frame(conn_frame)
        host_frame.pack(fill='x', pady=5)

        # Create Treeview for better host display
        columns = ('Name', 'IP', 'Status', 'Last Seen')
        self.app.host_tree = ttk.Treeview(
            host_frame, columns=columns, show='headings', height=4)

        for col in columns:
            self.app.host_tree.heading(col, text=col)
            self.app.host_tree.column(col, width=100)

        host_scroll = ttk.Scrollbar(
            host_frame, orient='vertical', command=self.app.host_tree.yview)
        self.app.host_tree.configure(yscrollcommand=host_scroll.set)

        self.app.host_tree.pack(side='left', fill='both', expand=True)
        host_scroll.pack(side='right', fill='y')

        # Manual entry and port
        manual_frame = ttk.Frame(conn_frame)
        manual_frame.pack(fill='x', pady=5)

        ttk.Label(manual_frame, text="Manual IP:").pack(side='left')
        self.app.manual_host_entry = ttk.Entry(manual_frame, width=15)
        self.app.manual_host_entry.pack(side='left', padx=(5, 20))

        ttk.Label(manual_frame, text="Port:").pack(side='left')
        self.app.sender_port_entry = ttk.Entry(manual_frame, width=8)
        self.app.sender_port_entry.insert(0, "12345")
        self.app.sender_port_entry.pack(side='left', padx=(5, 0))

    def _create_file_selection_section(self, parent):
        """Create file selection section"""
        file_frame = ttk.LabelFrame(
            parent, text="File Selection", padding="10")
        file_frame.pack(fill='x', pady=(0, 10))

        # File selection buttons
        file_btn_frame = ttk.Frame(file_frame)
        file_btn_frame.pack(fill='x', pady=(0, 5))

        ttk.Button(file_btn_frame, text="Add Files",
                   command=self.app.add_files).pack(side='left')
        ttk.Button(file_btn_frame, text="Add Folder",
                   command=self.app.add_folder).pack(side='left', padx=(5, 0))
        ttk.Button(file_btn_frame, text="Remove Selected",
                   command=self.app.remove_selected_files).pack(side='left', padx=(5, 0))
        ttk.Button(file_btn_frame, text="Clear All",
                   command=self.app.clear_files).pack(side='left', padx=(5, 0))

        # Selected files list
        files_list_frame = ttk.Frame(file_frame)
        files_list_frame.pack(fill='both', expand=True, pady=5)

        ttk.Label(files_list_frame, text="Selected Files:",
                  style='Subtitle.TLabel').pack(anchor='w')

        # Treeview for files
        file_columns = ('Name', 'Size', 'Type', 'Path')
        self.app.files_tree = ttk.Treeview(
            files_list_frame, columns=file_columns, show='headings', height=4)

        for col in file_columns:
            self.app.files_tree.heading(col, text=col)
            if col == 'Path':
                self.app.files_tree.column(col, width=200)
            else:
                self.app.files_tree.column(col, width=100)

        files_scroll = ttk.Scrollbar(
            files_list_frame, orient='vertical', command=self.app.files_tree.yview)
        self.app.files_tree.configure(yscrollcommand=files_scroll.set)

        self.app.files_tree.pack(side='left', fill='both', expand=True)
        files_scroll.pack(side='right', fill='y')

        # Add context menu for file removal
        self._setup_files_context_menu()

        # File info summary
        self.app.file_summary = ttk.Label(
            file_frame, text="No files selected", style='Status.TLabel')
        self.app.file_summary.pack(anchor='w', pady=2)

    def _setup_files_context_menu(self):
        """Setup context menu for files tree"""
        self.app.files_context_menu = tk.Menu(self.app.root, tearoff=0)
        self.app.files_context_menu.add_command(
            label="Remove Selected", command=self.app.remove_selected_files)
        self.app.files_context_menu.add_separator()
        self.app.files_context_menu.add_command(
            label="Clear All", command=self.app.clear_files)

        # Bind events for file removal
        self.app.files_tree.bind(
            "<Button-3>", self.app.show_files_context_menu)
        self.app.files_tree.bind("<Delete>", self.app.on_delete_key)
        self.app.files_tree.bind("<Double-1>", self.app.on_file_double_click)

    def _create_transfer_options_section(self, parent):
        """Create transfer options section"""
        options_frame = ttk.LabelFrame(
            parent, text="Transfer Options", padding="10")
        options_frame.pack(fill='x', pady=(0, 10))

        options_grid = ttk.Frame(options_frame)
        options_grid.pack(fill='x')

        ttk.Checkbutton(options_grid, text="Compress files",
                        variable=self.app.compression_enabled).pack(side='left')
        ttk.Checkbutton(options_grid, text="Encrypt transfer",
                        variable=self.app.encryption_enabled).pack(side='left', padx=(20, 0))

    def _create_transfer_control_section(self, parent):
        """Create transfer control section"""
        transfer_frame = ttk.LabelFrame(
            parent, text="Transfer Control", padding="10")
        transfer_frame.pack(fill='both', expand=True)

        # Progress display
        progress_frame = ttk.Frame(transfer_frame)
        progress_frame.pack(fill='x', pady=(0, 10))

        self.app.send_progress = ttk.Progressbar(
            progress_frame, mode='determinate')
        self.app.send_progress.pack(fill='x')

        progress_info = ttk.Frame(progress_frame)
        progress_info.pack(fill='x', pady=2)

        self.app.send_status = ttk.Label(
            progress_info, text="Ready to send", style='Status.TLabel')
        self.app.send_status.pack(side='left')

        self.app.send_speed = ttk.Label(
            progress_info, text="", style='Status.TLabel')
        self.app.send_speed.pack(side='right')

        # Control buttons
        button_frame = ttk.Frame(transfer_frame)
        button_frame.pack(fill='x', pady=(0, 10))

        self.app.send_button = ttk.Button(
            button_frame, text="Send Files", command=self.app.send_files)
        self.app.send_button.pack(side='left')

        self.app.cancel_send_button = ttk.Button(
            button_frame, text="Cancel", command=self.app.cancel_send, state='disabled')
        self.app.cancel_send_button.pack(side='left', padx=(5, 0))

        # Transfer log
        self._create_log_section(transfer_frame, "send_log")

    def create_receiver_tab(self):
        """Create enhanced receiver tab"""
        receiver_frame = ttk.Frame(self.app.notebook, padding="10")
        self.app.notebook.add(receiver_frame, text='Receive Files')

        # Identity section
        self._create_identity_section(receiver_frame)

        # Configuration section
        self._create_config_section(receiver_frame)

        # Control section
        self._create_receiver_control_section(receiver_frame)

        # Received files log
        log_frame = ttk.LabelFrame(
            receiver_frame, text="Received Files", padding="10")
        log_frame.pack(fill='both', expand=True)

        self._create_log_section(log_frame, "recv_log")

    def _create_identity_section(self, parent):
        """Create identity section for receiver tab"""
        identity_frame = ttk.LabelFrame(
            parent, text="Receiver Identity", padding="10")
        identity_frame.pack(fill='x', pady=(0, 10))

        name_frame = ttk.Frame(identity_frame)
        name_frame.pack(fill='x')

        ttk.Label(name_frame, text="Display Name:").pack(side='left')
        name_entry = ttk.Entry(
            name_frame, textvariable=self.app.receiver_name, width=25)
        name_entry.pack(side='left', padx=(5, 0))

        ttk.Button(name_frame, text="Save",
                   command=self.app.save_settings).pack(side='right')

        ttk.Label(identity_frame, text="This name will be shown to senders during discovery",
                  style='Status.TLabel').pack(anchor='w', pady=(5, 0))

    def _create_config_section(self, parent):
        """Create configuration section for receiver tab"""
        config_frame = ttk.LabelFrame(
            parent, text="Configuration", padding="10")
        config_frame.pack(fill='x', pady=(0, 10))

        # Port and directory
        config_row1 = ttk.Frame(config_frame)
        config_row1.pack(fill='x')

        ttk.Label(config_row1, text="Port:").pack(side='left')
        self.app.recv_port_entry = ttk.Entry(config_row1, width=8)
        self.app.recv_port_entry.insert(0, "12345")
        self.app.recv_port_entry.pack(side='left', padx=(5, 20))

        ttk.Label(config_row1, text="Max File Size (MB):").pack(side='left')
        self.app.size_limit_var = tk.StringVar(value="1024")
        size_spinbox = ttk.Spinbox(
            config_row1, from_=1, to=10240, textvariable=self.app.size_limit_var, width=8)
        size_spinbox.pack(side='left', padx=(5, 0))

        # Directory selection
        self._create_directory_selection(config_frame)

        # Auto-accept and notifications
        auto_frame = ttk.Frame(config_frame)
        auto_frame.pack(fill='x', pady=5)

        ttk.Checkbutton(auto_frame, text="Auto-accept transfers",
                        variable=self.app.auto_accept).pack(side='left')
        ttk.Checkbutton(auto_frame, text="Sound notifications",
                        variable=self.app.notification_sound).pack(side='left', padx=(20, 0))

    def _create_directory_selection(self, parent):
        """Create directory selection section"""
        dir_frame = ttk.Frame(parent)
        dir_frame.pack(fill='x', pady=5)

        ttk.Label(dir_frame, text="Save Directory:").pack(anchor='w')
        dir_entry_frame = ttk.Frame(dir_frame)
        dir_entry_frame.pack(fill='x', pady=2)

        self.app.save_dir_entry = ttk.Entry(dir_entry_frame)
        self.app.save_dir_entry.insert(0, os.path.expanduser("~/Downloads"))
        self.app.save_dir_entry.pack(side='left', fill='x', expand=True)

        ttk.Button(dir_entry_frame, text="Browse",
                   command=self.app.browse_directory).pack(side='right', padx=(5, 0))

    def _create_receiver_control_section(self, parent):
        """Create receiver control section"""
        control_frame = ttk.LabelFrame(
            parent, text="Receiver Control", padding="10")
        control_frame.pack(fill='x', pady=(0, 10))

        button_frame = ttk.Frame(control_frame)
        button_frame.pack(fill='x')

        self.app.start_button = ttk.Button(
            button_frame, text="Start Receiving", command=self.app.start_receiving)
        self.app.start_button.pack(side='left')

        self.app.stop_button = ttk.Button(
            button_frame, text="Stop Receiving", command=self.app.stop_receiving, state='disabled')
        self.app.stop_button.pack(side='left', padx=(5, 0))

        self.app.open_folder_button = ttk.Button(
            button_frame, text="Open Folder", command=self.app.open_save_folder)
        self.app.open_folder_button.pack(side='right')

        # Status display
        status_frame = ttk.Frame(control_frame)
        status_frame.pack(fill='x', pady=5)

        self.app.receiver_status = ttk.Label(
            status_frame, text="Not receiving", style='Status.TLabel')
        self.app.receiver_status.pack(side='left')

        self.app.receiver_stats = ttk.Label(
            status_frame, text="", style='Status.TLabel')
        self.app.receiver_stats.pack(side='right')

    def create_monitor_tab(self):
        """Create enhanced monitoring tab"""
        monitor_frame = ttk.Frame(self.app.notebook, padding="10")
        self.app.notebook.add(monitor_frame, text='Monitor')

        # Statistics section
        self._create_statistics_section(monitor_frame)

        # Active transfers
        self._create_active_transfers_section(monitor_frame)

    def _create_statistics_section(self, parent):
        """Create statistics section"""
        stats_frame = ttk.LabelFrame(
            parent, text="Transfer Statistics", padding="10")
        stats_frame.pack(fill='x', pady=(0, 10))

        stats_grid = ttk.Frame(stats_frame)
        stats_grid.pack(fill='x')

        # Create statistics labels
        self.app.stats_labels = {}
        stats_items = [
            ("Files Sent:", "files_sent"),
            ("Files Received:", "files_received"),
            ("Data Sent:", "data_sent"),
            ("Data Received:", "data_received"),
            ("Active Transfers:", "active_transfers")
        ]

        for i, (label, key) in enumerate(stats_items):
            row = i // 3
            col = i % 3

            ttk.Label(stats_grid, text=label, style='Status.TLabel').grid(
                row=row*2, column=col, sticky='w', padx=(0, 20))
            self.app.stats_labels[key] = ttk.Label(
                stats_grid, text="0", style='Subtitle.TLabel')
            self.app.stats_labels[key].grid(
                row=row*2+1, column=col, sticky='w', padx=(0, 20))

    def _create_active_transfers_section(self, parent):
        """Create active transfers section"""
        active_frame = ttk.LabelFrame(
            parent, text="Active Transfers", padding="10")
        active_frame.pack(fill='both', expand=True)

        # Control buttons
        control_frame = ttk.Frame(active_frame)
        control_frame.pack(fill='x', pady=(0, 5))

        ttk.Button(control_frame, text="Refresh",
                   command=self.app.refresh_monitor).pack(side='left')
        ttk.Button(control_frame, text="Cancel All",
                   command=self.app.cancel_all_transfers).pack(side='left', padx=(5, 0))

        # Transfer tree
        columns = ('Direction', 'File', 'Peer',
                   'Progress', 'Speed', 'ETA', 'Status')
        self.app.transfer_tree = ttk.Treeview(
            active_frame, columns=columns, show='headings', height=12)

        for col in columns:
            self.app.transfer_tree.heading(col, text=col)
            if col == 'File':
                self.app.transfer_tree.column(col, width=150)
            elif col == 'Progress':
                self.app.transfer_tree.column(col, width=80)
            else:
                self.app.transfer_tree.column(col, width=100)

        tree_scroll = ttk.Scrollbar(
            active_frame, orient='vertical', command=self.app.transfer_tree.yview)
        self.app.transfer_tree.configure(yscrollcommand=tree_scroll.set)

        self.app.transfer_tree.pack(side='left', fill='both', expand=True)
        tree_scroll.pack(side='right', fill='y')

        # Context menu for transfers
        self._setup_transfer_context_menu()

    def _setup_transfer_context_menu(self):
        """Setup context menu for transfer tree"""
        self.app.transfer_context_menu = tk.Menu(self.app.root, tearoff=0)
        self.app.transfer_context_menu.add_command(
            label="Cancel Transfer", command=self.app.cancel_selected_transfer)
        self.app.transfer_context_menu.add_command(
            label="Details", command=self.app.show_transfer_details)

        self.app.transfer_tree.bind("<Button-3>", self.app.show_context_menu)

    def create_settings_tab(self):
        """Create settings tab"""
        settings_frame = ttk.Frame(self.app.notebook, padding="10")
        self.app.notebook.add(settings_frame, text='Settings')

        # Network settings
        self._create_network_settings(settings_frame)

        # Discovery settings
        self._create_discovery_settings(settings_frame)

        # File handling settings
        self._create_file_handling_settings(settings_frame)

        # Apply settings button
        ttk.Button(settings_frame, text="Apply Settings",
                   command=self.app.apply_settings).pack(pady=20)

    def _create_network_settings(self, parent):
        """Create network settings section"""
        network_frame = ttk.LabelFrame(
            parent, text="Network Settings", padding="10")
        network_frame.pack(fill='x', pady=(0, 10))

        # Buffer size
        ttk.Label(network_frame, text="Buffer Size (KB):").pack(anchor='w')
        self.app.buffer_size_var = tk.StringVar(value="16")
        buffer_spinbox = ttk.Spinbox(
            network_frame, from_=1, to=1024, textvariable=self.app.buffer_size_var, width=10)
        buffer_spinbox.pack(anchor='w', pady=2)

        # Timeout settings
        ttk.Label(network_frame, text="Connection Timeout (seconds):").pack(
            anchor='w', pady=(10, 0))
        self.app.timeout_var = tk.StringVar(value="30")
        timeout_spinbox = ttk.Spinbox(
            network_frame, from_=5, to=300, textvariable=self.app.timeout_var, width=10)
        timeout_spinbox.pack(anchor='w', pady=2)

        # Multi-threading settings
        ttk.Label(network_frame, text="Max Parallel Threads:").pack(
            anchor='w', pady=(10, 0))
        self.app.max_threads_var = tk.StringVar(value="4")
        threads_spinbox = ttk.Spinbox(
            network_frame, from_=1, to=8, textvariable=self.app.max_threads_var, width=10)
        threads_spinbox.pack(anchor='w', pady=2)

        ttk.Label(network_frame, text="Split Threshold (MB):").pack(
            anchor='w', pady=(10, 0))
        self.app.split_threshold_var = tk.StringVar(value="200")
        threshold_spinbox = ttk.Spinbox(
            network_frame, from_=50, to=1000, textvariable=self.app.split_threshold_var, width=10)
        threshold_spinbox.pack(anchor='w', pady=2)

    def _create_discovery_settings(self, parent):
        """Create discovery settings section"""
        discovery_frame = ttk.LabelFrame(
            parent, text="Discovery Settings", padding="10")
        discovery_frame.pack(fill='x', pady=(0, 10))

        self.app.auto_discover = tk.BooleanVar(value=True)
        ttk.Checkbutton(discovery_frame, text="Auto-discover on startup",
                        variable=self.app.auto_discover).pack(anchor='w')

        self.app.discovery_interval_var = tk.StringVar(value="30")
        ttk.Label(discovery_frame, text="Discovery Interval (seconds):").pack(
            anchor='w', pady=(10, 0))
        interval_spinbox = ttk.Spinbox(
            discovery_frame, from_=10, to=300, textvariable=self.app.discovery_interval_var, width=10)
        interval_spinbox.pack(anchor='w', pady=2)

    def _create_file_handling_settings(self, parent):
        """Create file handling settings section"""
        file_frame = ttk.LabelFrame(parent, text="File Handling", padding="10")
        file_frame.pack(fill='x', pady=(0, 10))

        self.app.overwrite_files = tk.BooleanVar(value=False)
        ttk.Checkbutton(file_frame, text="Overwrite existing files",
                        variable=self.app.overwrite_files).pack(anchor='w')

        self.app.create_subfolders = tk.BooleanVar(value=True)
        ttk.Checkbutton(file_frame, text="Create subfolders for batch transfers",
                        variable=self.app.create_subfolders).pack(anchor='w')

    def create_history_tab(self):
        """Create transfer history tab"""
        history_frame = ttk.Frame(self.app.notebook, padding="10")
        self.app.notebook.add(history_frame, text='History')

        # Control buttons
        control_frame = ttk.Frame(history_frame)
        control_frame.pack(fill='x', pady=(0, 10))

        ttk.Button(control_frame, text="Refresh",
                   command=self.app.refresh_history).pack(side='left')
        ttk.Button(control_frame, text="Export Log",
                   command=self.app.export_history).pack(side='left', padx=(5, 0))
        ttk.Button(control_frame, text="Clear History",
                   command=self.app.clear_history).pack(side='left', padx=(5, 0))

        # History tree
        history_columns = ('Timestamp', 'Direction', 'File(s)',
                           'Peer', 'Size', 'Status', 'Duration')
        self.app.history_tree = ttk.Treeview(
            history_frame, columns=history_columns, show='headings')

        for col in history_columns:
            self.app.history_tree.heading(col, text=col)
            if col == 'File(s)':
                self.app.history_tree.column(col, width=200)
            else:
                self.app.history_tree.column(col, width=100)

        history_scroll = ttk.Scrollbar(
            history_frame, orient='vertical', command=self.app.history_tree.yview)
        self.app.history_tree.configure(yscrollcommand=history_scroll.set)

        self.app.history_tree.pack(side='left', fill='both', expand=True)
        history_scroll.pack(side='right', fill='y')

    def create_status_bar(self, parent):
        """Create enhanced status bar"""
        status_frame = ttk.Frame(parent)
        status_frame.pack(fill='x', pady=(10, 0))

        separator = ttk.Separator(status_frame, orient='horizontal')
        separator.pack(fill='x', pady=(0, 5))

        status_info = ttk.Frame(status_frame)
        status_info.pack(fill='x')

        self.app.status_label = ttk.Label(
            status_info, text="Ready", style='Status.TLabel')
        self.app.status_label.pack(side='left')

        # Network info
        from network.transfer_manager import TransferManager
        transfer_manager = TransferManager(self.app)
        self.app.network_label = ttk.Label(
            status_info, text=f"IP: {transfer_manager.get_local_ip()}", style='Status.TLabel')
        self.app.network_label.pack(side='right')

    def _create_log_section(self, parent, log_name):
        """Create log section with scrollable text widget"""
        log_container = ttk.Frame(parent)
        log_container.pack(fill='both', expand=True)

        log_widget = tk.Text(log_container, height=6,
                             font=('Courier', 9), wrap='word')
        log_scroll = ttk.Scrollbar(
            log_container, orient='vertical', command=log_widget.yview)
        log_widget.configure(yscrollcommand=log_scroll.set)

        log_widget.pack(side='left', fill='both', expand=True)
        log_scroll.pack(side='right', fill='y')

        # Store log widget reference
        setattr(self.app, log_name, log_widget)

    def update_files_display(self):
        """Update the files display tree"""
        # Clear existing items
        for item in self.app.files_tree.get_children():
            self.app.files_tree.delete(item)

        total_size = 0
        for file_info in self.app.selected_files:
            size_str = self._format_size(file_info['size'])
            total_size += file_info['size']

            self.app.files_tree.insert('', 'end', values=(
                file_info['name'],
                size_str,
                file_info['type'].split(
                    '/')[0] if '/' in file_info['type'] else file_info['type'],
                file_info['path']
            ))

        # Update summary
        count = len(self.app.selected_files)
        if count == 0:
            self.app.file_summary.config(text="No files selected")
        else:
            total_str = self._format_size(total_size)
            self.app.file_summary.config(
                text=f"{count} files selected • Total size: {total_str}")

    def _format_size(self, size):
        """Format file size in human readable format"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} TB"

    def show_error_dialog(self, title, message):
        """Show error dialog"""
        messagebox.showerror(title, message)

    def show_info_dialog(self, title, message):
        """Show info dialog"""
        messagebox.showinfo(title, message)

    def show_warning_dialog(self, title, message):
        """Show warning dialog"""
        messagebox.showwarning(title, message)

    def ask_yes_no(self, title, message):
        """Ask yes/no question"""
        return messagebox.askyesno(title, message)

    def browse_files(self, title="Select Files", filetypes=None):
        """Browse for files"""
        if filetypes is None:
            filetypes = [("All files", "*.*")]
        return filedialog.askopenfilenames(title=title, filetypes=filetypes)

    def browse_folder(self, title="Select Folder"):
        """Browse for folder"""
        return filedialog.askdirectory(title=title)

    def browse_save_file(self, title="Save As", defaultextension=".txt", filetypes=None):
        """Browse for save file location"""
        if filetypes is None:
            filetypes = [("Text files", "*.txt"), ("All files", "*.*")]
        return filedialog.asksaveasfilename(title=title, defaultextension=defaultextension, filetypes=filetypes)
