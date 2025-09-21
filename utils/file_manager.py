"""
File Management Utilities
Handles file operations, validation, and information gathering
"""

import os
import mimetypes
import hashlib
import zipfile
import tempfile
from datetime import datetime
from pathlib import Path


class FileManager:
    def __init__(self, app_instance):
        self.app = app_instance

    def get_file_info(self, file_path):
        """Get comprehensive file information"""
        try:
            stat = os.stat(file_path)
            size = stat.st_size
            mime_type, _ = mimetypes.guess_type(file_path)

            return {
                'path': file_path,
                'name': os.path.basename(file_path),
                'size': size,
                'type': mime_type or 'Unknown',
                'modified': datetime.fromtimestamp(stat.st_mtime)
            }
        except Exception as e:
            return {
                'path': file_path,
                'name': os.path.basename(file_path),
                'size': 0,
                'type': 'Error',
                'modified': datetime.now(),
                'error': str(e)
            }

    def add_files(self, file_paths):
        """Add multiple files to selection"""
        added_files = []
        for file_path in file_paths:
            if file_path not in [f['path'] for f in self.app.selected_files]:
                file_info = self.get_file_info(file_path)
                self.app.selected_files.append(file_info)
                added_files.append(file_info)
        return added_files

    def add_folder(self, folder_path):
        """Add entire folder to selection"""
        added_files = []
        try:
            for root, dirs, files in os.walk(folder_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    if file_path not in [f['path'] for f in self.app.selected_files]:
                        file_info = self.get_file_info(file_path)
                        self.app.selected_files.append(file_info)
                        added_files.append(file_info)
        except Exception as e:
            self.app.log_message(
                self.app.send_log, f"Error adding folder: {e}", 'error')
        return added_files

    def clear_files(self):
        """Clear all selected files"""
        self.app.selected_files.clear()

    def remove_selected_files(self, selected_paths):
        """Remove selected files from the list"""
        original_count = len(self.app.selected_files)
        self.app.selected_files = [
            f for f in self.app.selected_files if f['path'] not in selected_paths]
        removed_count = original_count - len(self.app.selected_files)
        return removed_count

    def validate_files(self, files):
        """Validate selected files before transfer"""
        issues = []
        total_size = 0

        for file_info in files:
            file_path = file_info['path']

            # Check if file exists
            if not os.path.exists(file_path):
                issues.append(f"File not found: {file_info['name']}")
                continue

            # Check if file is readable
            if not os.access(file_path, os.R_OK):
                issues.append(f"Cannot read file: {file_info['name']}")
                continue

            # Update size if changed
            try:
                current_size = os.path.getsize(file_path)
                if current_size != file_info['size']:
                    file_info['size'] = current_size
                total_size += current_size
            except Exception as e:
                issues.append(f"Cannot get size for {file_info['name']}: {e}")

        # Check total size against limit
        if total_size > self.app.max_file_size:
            issues.append(
                f"Total size too large: {self.format_size(total_size)}")

        return issues, total_size

    def create_archive(self, files, transfer_id):
        """Create zip archive of selected files"""
        temp_dir = tempfile.gettempdir()
        archive_name = f"transfer_{transfer_id}_{int(datetime.now().timestamp())}.zip"
        archive_path = os.path.join(temp_dir, archive_name)

        try:
            with zipfile.ZipFile(archive_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for file_info in files:
                    # Use relative path in archive
                    arcname = os.path.basename(file_info['path'])
                    zipf.write(file_info['path'], arcname)
            return archive_path
        except Exception as e:
            if os.path.exists(archive_path):
                os.remove(archive_path)
            raise e

    def extract_archive(self, archive_path, extract_dir):
        """Extract zip archive to directory"""
        try:
            with zipfile.ZipFile(archive_path, 'r') as zipf:
                zipf.extractall(extract_dir)
            return True
        except Exception as e:
            self.app.log_message(
                self.app.recv_log, f"Failed to extract archive: {e}", 'error')
            return False

    def calculate_file_hash(self, file_path, algorithm='sha256'):
        """Calculate hash for file integrity verification"""
        try:
            hash_obj = hashlib.new(algorithm)
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_obj.update(chunk)
            return hash_obj.hexdigest()
        except Exception as e:
            self.app.log_message(
                self.app.send_log, f"Failed to calculate hash for {file_path}: {e}", 'error')
            return None

    def verify_file_integrity(self, file_path, expected_hash, algorithm='sha256'):
        """Verify file integrity using hash"""
        calculated_hash = self.calculate_file_hash(file_path, algorithm)
        return calculated_hash == expected_hash if calculated_hash else False

    def get_unique_filename(self, filepath):
        """Get unique filename to avoid conflicts"""
        if not self.app.overwrite_files.get() and os.path.exists(filepath):
            base, ext = os.path.splitext(filepath)
            counter = 1
            while os.path.exists(f"{base}_{counter}{ext}"):
                counter += 1
            return f"{base}_{counter}{ext}"
        return filepath

    def format_size(self, size):
        """Format file size in human readable format"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} TB"

    def get_directory_size(self, directory):
        """Calculate total size of directory"""
        total_size = 0
        try:
            for dirpath, dirnames, filenames in os.walk(directory):
                for filename in filenames:
                    filepath = os.path.join(dirpath, filename)
                    try:
                        total_size += os.path.getsize(filepath)
                    except (OSError, IOError):
                        pass
        except Exception:
            pass
        return total_size

    def is_safe_path(self, path):
        """Check if path is safe (no directory traversal)"""
        try:
            resolved = os.path.realpath(path)
            return not resolved.startswith('..')
        except:
            return False

    def sanitize_filename(self, filename):
        """Sanitize filename to remove unsafe characters"""
        # Remove or replace unsafe characters
        unsafe_chars = '<>:"/\\|?*'
        for char in unsafe_chars:
            filename = filename.replace(char, '_')

        # Remove leading/trailing spaces and dots
        filename = filename.strip(' .')

        # Ensure filename is not empty
        if not filename:
            filename = "unnamed_file"

        # Limit length
        if len(filename) > 255:
            name, ext = os.path.splitext(filename)
            filename = name[:250] + ext

        return filename

    def get_file_type_info(self, file_path):
        """Get detailed file type information"""
        mime_type, encoding = mimetypes.guess_type(file_path)

        # Common file categories
        if mime_type:
            main_type = mime_type.split('/')[0]
            categories = {
                'image': 'Image',
                'video': 'Video',
                'audio': 'Audio',
                'text': 'Text',
                'application': 'Application'
            }
            category = categories.get(main_type, 'Other')
        else:
            category = 'Unknown'

        return {
            'mime_type': mime_type,
            'encoding': encoding,
            'category': category
        }

    def create_backup(self, file_path):
        """Create backup of existing file"""
        if os.path.exists(file_path):
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = f"{file_path}.backup_{timestamp}"
            try:
                import shutil
                shutil.copy2(file_path, backup_path)
                return backup_path
            except Exception as e:
                self.app.log_message(
                    self.app.recv_log, f"Failed to create backup: {e}", 'warning')
        return None

    def cleanup_temp_files(self, temp_files):
        """Clean up temporary files"""
        for file_path in temp_files:
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
            except Exception as e:
                self.app.log_message(
                    self.app.send_log, f"Failed to cleanup {file_path}: {e}", 'warning')

    def get_disk_space(self, path):
        """Get available disk space for given path"""
        try:
            if os.name == 'nt':  # Windows
                import shutil
                total, used, free = shutil.disk_usage(path)
                return {'total': total, 'used': used, 'free': free}
            else:  # Unix/Linux
                statvfs = os.statvfs(path)
                total = statvfs.f_frsize * statvfs.f_blocks
                free = statvfs.f_frsize * statvfs.f_available
                used = total - free
                return {'total': total, 'used': used, 'free': free}
        except Exception:
            return {'total': 0, 'used': 0, 'free': 0}

    def check_disk_space(self, required_size, target_path):
        """Check if there's enough disk space"""
        disk_info = self.get_disk_space(target_path)
        return disk_info['free'] >= required_size
