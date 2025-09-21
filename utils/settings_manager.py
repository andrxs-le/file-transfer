"""
Settings and Configuration Manager
Handles application settings, preferences, and configuration persistence
"""

import json
import os
import platform
from datetime import datetime


class SettingsManager:
    def __init__(self, app_instance):
        self.app = app_instance
        self.settings_file = os.path.join(
            os.path.expanduser("~"), ".file_transfer_settings.json")
        self.default_settings = self._get_default_settings()

    def _get_default_settings(self):
        """Get default application settings"""
        return {
            'receiver_name': platform.node(),
            'save_directory': os.path.expanduser("~/Downloads"),
            'port': '12345',
            'size_limit': '1024',
            'buffer_size': '16',
            'timeout': '30',
            'max_threads': '4',
            'split_threshold': '200',
            'auto_accept': False,
            'compression_enabled': True,
            'encryption_enabled': False,
            'notification_sound': True,
            'overwrite_files': False,
            'create_subfolders': True,
            'auto_discover': True,
            'discovery_interval': '30',
            'theme': 'default',
            'language': 'en',
            'log_level': 'info',
            'history_retention_days': 30,
            'backup_settings': True
        }

    def load_settings(self):
        """Load saved settings from file"""
        try:
            if os.path.exists(self.settings_file):
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    settings = json.load(f)

                # Merge with defaults to handle new settings
                merged_settings = self.default_settings.copy()
                merged_settings.update(settings)

                self._apply_settings_to_ui(merged_settings)

                return merged_settings
            else:
                # First run - create default settings file
                self.save_settings(self.default_settings)
                self._apply_settings_to_ui(self.default_settings)
                return self.default_settings

        except Exception as e:
            self.app.log_message(
                getattr(self.app, 'send_log', None), f"Failed to load settings: {e}", 'error')
            # Fall back to defaults
            self._apply_settings_to_ui(self.default_settings)
            return self.default_settings

    def save_settings(self, settings=None):
        """Save current settings to file"""
        try:
            if settings is None:
                settings = self._get_current_settings()

            # Create backup of existing settings
            if self.default_settings.get('backup_settings', True) and os.path.exists(self.settings_file):
                backup_file = f"{self.settings_file}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                try:
                    import shutil
                    shutil.copy2(self.settings_file, backup_file)
                except Exception:
                    pass  # Backup failed, but continue with save

            # Save settings
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(settings, f, indent=2, ensure_ascii=False)

            self.app.ui_manager.show_info_dialog(
                "Settings", "Settings saved successfully")
            return True

        except Exception as e:
            self.app.ui_manager.show_error_dialog(
                "Error", f"Failed to save settings: {e}")
            return False

    def _get_current_settings(self):
        """Get current settings from UI"""
        try:
            return {
                'receiver_name': self.app.receiver_name.get(),
                'save_directory': self.app.save_dir_entry.get(),
                'port': self.app.recv_port_entry.get(),
                'size_limit': self.app.size_limit_var.get(),
                'buffer_size': self.app.buffer_size_var.get(),
                'timeout': self.app.timeout_var.get(),
                'max_threads': getattr(self.app, 'max_threads_var', type('MockVar', (), {'get': lambda: "4"})()).get(),
                'split_threshold': getattr(self.app, 'split_threshold_var', type('MockVar', (), {'get': lambda: "200"})()).get(),
                'auto_accept': self.app.auto_accept.get(),
                'compression_enabled': self.app.compression_enabled.get(),
                'encryption_enabled': self.app.encryption_enabled.get(),
                'notification_sound': self.app.notification_sound.get(),
                'overwrite_files': self.app.overwrite_files.get(),
                'create_subfolders': self.app.create_subfolders.get(),
                'auto_discover': getattr(self.app, 'auto_discover', type('MockVar', (), {'get': lambda: True})()).get(),
                'discovery_interval': getattr(self.app, 'discovery_interval_var', type('MockVar', (), {'get': lambda: "30"})()).get(),
                'last_saved': datetime.now().isoformat()
            }
        except Exception as e:
            self.app.log_message(getattr(
                self.app, 'send_log', None), f"Error getting current settings: {e}", 'error')
            return self.default_settings

    def _apply_settings_to_ui(self, settings):
        """Apply loaded settings to UI elements"""
        try:
            # Basic settings
            if hasattr(self.app, 'receiver_name'):
                self.app.receiver_name.set(settings.get(
                    'receiver_name', self.default_settings['receiver_name']))

            # UI elements that might not be initialized yet
            if hasattr(self.app, 'save_dir_entry'):
                self.app.save_dir_entry.delete(0, 'end')
                self.app.save_dir_entry.insert(0, settings.get(
                    'save_directory', self.default_settings['save_directory']))

            if hasattr(self.app, 'recv_port_entry'):
                self.app.recv_port_entry.delete(0, 'end')
                self.app.recv_port_entry.insert(0, settings.get(
                    'port', self.default_settings['port']))

            # StringVar settings
            if hasattr(self.app, 'size_limit_var'):
                self.app.size_limit_var.set(settings.get(
                    'size_limit', self.default_settings['size_limit']))

            if hasattr(self.app, 'buffer_size_var'):
                self.app.buffer_size_var.set(settings.get(
                    'buffer_size', self.default_settings['buffer_size']))

            if hasattr(self.app, 'timeout_var'):
                self.app.timeout_var.set(settings.get(
                    'timeout', self.default_settings['timeout']))

            # BooleanVar settings
            if hasattr(self.app, 'auto_accept'):
                self.app.auto_accept.set(settings.get(
                    'auto_accept', self.default_settings['auto_accept']))

            if hasattr(self.app, 'compression_enabled'):
                self.app.compression_enabled.set(settings.get(
                    'compression_enabled', self.default_settings['compression_enabled']))

            if hasattr(self.app, 'encryption_enabled'):
                self.app.encryption_enabled.set(settings.get(
                    'encryption_enabled', self.default_settings['encryption_enabled']))

            if hasattr(self.app, 'notification_sound'):
                self.app.notification_sound.set(settings.get(
                    'notification_sound', self.default_settings['notification_sound']))

            if hasattr(self.app, 'overwrite_files'):
                self.app.overwrite_files.set(settings.get(
                    'overwrite_files', self.default_settings['overwrite_files']))

            if hasattr(self.app, 'create_subfolders'):
                self.app.create_subfolders.set(settings.get(
                    'create_subfolders', self.default_settings['create_subfolders']))

        except Exception as e:
            self.app.log_message(
                getattr(self.app, 'send_log', None), f"Error applying settings: {e}", 'error')

    def apply_network_settings(self):
        """Apply network-related settings to application variables"""
        try:
            self.app.chunk_size = int(self.app.buffer_size_var.get()) * 1024
            self.app.max_file_size = int(
                self.app.size_limit_var.get()) * 1024 * 1024
            self.app.max_threads = int(getattr(self.app, 'max_threads_var', type(
                'MockVar', (), {'get': lambda: "4"})()).get())
            self.app.split_threshold = int(getattr(self.app, 'split_threshold_var', type(
                'MockVar', (), {'get': lambda: "200"})()).get()) * 1024 * 1024

            self.save_settings()
            self.app.ui_manager.show_info_dialog(
                "Settings", "Network settings applied successfully")
            return True

        except Exception as e:
            self.app.ui_manager.show_error_dialog(
                "Error", f"Failed to apply network settings: {e}")
            return False

    def export_settings(self, file_path=None):
        """Export current settings to a file"""
        try:
            if file_path is None:
                file_path = self.app.ui_manager.browse_save_file(
                    title="Export Settings",
                    defaultextension=".json",
                    filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
                )

            if file_path:
                settings = self._get_current_settings()
                settings['exported_on'] = datetime.now().isoformat()
                settings['exported_by'] = 'Advanced File Transfer Pro v2.0'

                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(settings, f, indent=2, ensure_ascii=False)

                self.app.ui_manager.show_info_dialog(
                    "Export", f"Settings exported to {file_path}")
                return True

        except Exception as e:
            self.app.ui_manager.show_error_dialog(
                "Export Error", f"Failed to export settings: {e}")
            return False

    def import_settings(self, file_path=None):
        """Import settings from a file"""
        try:
            if file_path is None:
                file_path = self.app.ui_manager.browse_files(
                    title="Import Settings",
                    filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
                )

            if file_path and len(file_path) > 0:
                file_path = file_path[0]  # browse_files returns a tuple

                with open(file_path, 'r', encoding='utf-8') as f:
                    imported_settings = json.load(f)

                # Validate imported settings
                if self._validate_settings(imported_settings):
                    # Merge with current settings
                    current_settings = self._get_current_settings()
                    current_settings.update(imported_settings)

                    # Apply to UI
                    self._apply_settings_to_ui(current_settings)

                    # Save merged settings
                    self.save_settings(current_settings)

                    self.app.ui_manager.show_info_dialog(
                        "Import", "Settings imported successfully")
                    return True
                else:
                    self.app.ui_manager.show_error_dialog(
                        "Import Error", "Invalid settings file format")
                    return False

        except Exception as e:
            self.app.ui_manager.show_error_dialog(
                "Import Error", f"Failed to import settings: {e}")
            return False

    def _validate_settings(self, settings):
        """Validate imported settings"""
        if not isinstance(settings, dict):
            return False

        # Check for required fields
        required_fields = ['receiver_name', 'save_directory', 'port']
        for field in required_fields:
            if field not in settings:
                return False

        # Validate data types and ranges
        try:
            port = int(settings.get('port', 12345))
            if not (1024 <= port <= 65535):
                return False

            size_limit = int(settings.get('size_limit', 1024))
            if size_limit <= 0:
                return False

            buffer_size = int(settings.get('buffer_size', 16))
            if not (1 <= buffer_size <= 1024):
                return False

            timeout = int(settings.get('timeout', 30))
            if not (5 <= timeout <= 300):
                return False

        except (ValueError, TypeError):
            return False

        return True

    def reset_to_defaults(self):
        """Reset all settings to default values"""
        try:
            if self.app.ui_manager.ask_yes_no("Reset Settings",
                                              "Are you sure you want to reset all settings to defaults?\nThis cannot be undone."):

                # Apply default settings to UI
                self._apply_settings_to_ui(self.default_settings)

                # Save defaults
                self.save_settings(self.default_settings)

                # Apply network settings
                self.apply_network_settings()

                self.app.ui_manager.show_info_dialog(
                    "Reset", "Settings reset to defaults successfully")
                return True

        except Exception as e:
            self.app.ui_manager.show_error_dialog(
                "Reset Error", f"Failed to reset settings: {e}")
            return False

    def get_setting(self, key, default=None):
        """Get a specific setting value"""
        try:
            current_settings = self._get_current_settings()
            return current_settings.get(key, default)
        except Exception:
            return default

    def set_setting(self, key, value):
        """Set a specific setting value"""
        try:
            current_settings = self._get_current_settings()
            current_settings[key] = value

            # Apply to UI if the setting has a corresponding UI element
            self._apply_setting_to_ui(key, value)

            return True
        except Exception as e:
            self.app.log_message(getattr(
                self.app, 'send_log', None), f"Failed to set setting {key}: {e}", 'error')
            return False

    def _apply_setting_to_ui(self, key, value):
        """Apply a single setting to its corresponding UI element"""
        try:
            setting_ui_map = {
                'receiver_name': 'receiver_name',
                'auto_accept': 'auto_accept',
                'compression_enabled': 'compression_enabled',
                'encryption_enabled': 'encryption_enabled',
                'notification_sound': 'notification_sound',
                'overwrite_files': 'overwrite_files',
                'create_subfolders': 'create_subfolders',
                'size_limit': 'size_limit_var',
                'buffer_size': 'buffer_size_var',
                'timeout': 'timeout_var'
            }

            ui_element_name = setting_ui_map.get(key)
            if ui_element_name and hasattr(self.app, ui_element_name):
                ui_element = getattr(self.app, ui_element_name)
                if hasattr(ui_element, 'set'):
                    ui_element.set(value)
                elif hasattr(ui_element, 'delete') and hasattr(ui_element, 'insert'):
                    # Entry widget
                    ui_element.delete(0, 'end')
                    ui_element.insert(0, str(value))

        except Exception as e:
            self.app.log_message(getattr(self.app, 'send_log', None),
                                 f"Failed to apply setting {key} to UI: {e}", 'error')

    def cleanup_old_backups(self, max_backups=5):
        """Clean up old backup files"""
        try:
            backup_dir = os.path.dirname(self.settings_file)
            backup_pattern = os.path.basename(self.settings_file) + '.backup_'

            backup_files = []
            for file in os.listdir(backup_dir):
                if file.startswith(backup_pattern):
                    full_path = os.path.join(backup_dir, file)
                    backup_files.append(
                        (full_path, os.path.getmtime(full_path)))

            # Sort by modification time (newest first)
            backup_files.sort(key=lambda x: x[1], reverse=True)

            # Remove old backups
            for file_path, _ in backup_files[max_backups:]:
                try:
                    os.remove(file_path)
                except Exception:
                    pass  # Ignore if file cannot be removed

        except Exception:
            pass  # Ignore cleanup errors

    def validate_current_settings(self):
        """Validate current settings and fix any issues"""
        issues = []

        try:
            # Check save directory
            save_dir = self.app.save_dir_entry.get() if hasattr(
                self.app, 'save_dir_entry') else self.default_settings['save_directory']
            if not os.path.exists(save_dir):
                try:
                    os.makedirs(save_dir, exist_ok=True)
                except Exception:
                    issues.append(f"Cannot create save directory: {save_dir}")

            # Check port
            try:
                port = int(self.app.recv_port_entry.get() if hasattr(
                    self.app, 'recv_port_entry') else self.default_settings['port'])
                if not (1024 <= port <= 65535):
                    issues.append(f"Invalid port number: {port}")
            except ValueError:
                issues.append("Port must be a valid number")

            # Check size limit
            try:
                size_limit = int(self.app.size_limit_var.get() if hasattr(
                    self.app, 'size_limit_var') else self.default_settings['size_limit'])
                if size_limit <= 0:
                    issues.append("Size limit must be positive")
            except ValueError:
                issues.append("Size limit must be a valid number")

            return issues

        except Exception as e:
            return [f"Error validating settings: {e}"]
