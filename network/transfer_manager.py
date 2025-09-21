"""
File Transfer Network Manager
Handles all network operations including file transfer, discovery, and communication
"""

import socket
import threading
import json
import time
import os
import hashlib
import zipfile
import tempfile
from datetime import datetime


class TransferManager:
    def __init__(self, app_instance):
        self.app = app_instance
        self.receiver_socket = None
        self.discovery_socket = None
        self.active_connections = {}
        self.port_pool = list(range(12346, 12366))

    def start_discovery_listener(self):
        """Start discovery service listener"""
        threading.Thread(target=self._discovery_listener, daemon=True).start()

    def _discovery_listener(self):
        """Listen for discovery broadcasts with enhanced response"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.bind(('', 5000))

            while True:
                try:
                    data, addr = sock.recvfrom(2048)
                    request = json.loads(data.decode())

                    if request.get("type") == "discover":
                        response = json.dumps({
                            "type": "announce",
                            "name": self.app.receiver_name.get(),
                            "port": int(self.app.recv_port_entry.get()) if self.app.recv_port_entry.get().isdigit() else 12345,
                            "version": "2.0",
                            "status": "receiving" if self.app.is_receiving else "idle",
                            "timestamp": time.time()
                        }).encode()
                        sock.sendto(response, addr)

                except Exception:
                    continue

        except Exception:
            pass

    def discover_hosts(self):
        """Enhanced host discovery with better UI feedback"""
        threading.Thread(target=self._discover_hosts, daemon=True).start()

    def _discover_hosts(self):
        """Background host discovery with detailed information"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            sock.settimeout(5)

            discovery_msg = json.dumps({
                "type": "discover",
                "sender": self.app.receiver_name.get(),
                "timestamp": time.time()
            }).encode()

            sock.sendto(discovery_msg, ('<broadcast>', 5000))

            discovered = {}
            end_time = time.time() + 5

            while time.time() < end_time:
                try:
                    data, addr = sock.recvfrom(2048)
                    response = json.loads(data.decode())
                    if response.get("type") == "announce":
                        discovered[addr[0]] = {
                            'name': response.get("name", "Unknown"),
                            'port': response.get("port", 12345),
                            'version': response.get("version", "Unknown"),
                            'last_seen': time.time()
                        }
                except socket.timeout:
                    break
                except Exception:
                    continue

            sock.close()

            # Update UI in main thread
            self.app.root.after(
                0, self.app._update_discovered_hosts, discovered)

        except Exception as e:
            self.app.root.after(0, lambda: self.app.log_message(
                self.app.send_log, f"Discovery failed: {e}", 'error'))

    def send_files(self, host, port, files, transfer_id):
        """Main file sending method with multi-threading support"""
        transfer_info = self.app.active_transfers[transfer_id]

        try:
            # Analyze files and determine transfer strategy
            large_files = []
            small_files = []
            total_size = sum(f['size'] for f in files)

            for file_info in files:
                file_size = file_info['size']
                if file_size > self.app.split_threshold:
                    large_files.append(file_info)
                else:
                    small_files.append(file_info)

            # Send transfer metadata
            metadata = {
                'total_files': len(files),
                'total_size': total_size,
                'large_files': len(large_files),
                'small_files': len(small_files),
                'multi_threaded': True,
                'max_threads': self.app.max_threads,
                'chunk_size': self.app.chunk_size,
                'sender_name': self.app.receiver_name.get()
            }

            # Connect and send metadata
            main_sock = socket.socket()
            main_sock.settimeout(int(self.app.timeout_var.get()))
            main_sock.connect((host, port))

            metadata_json = json.dumps(metadata).encode()
            main_sock.send(len(metadata_json).to_bytes(4, 'big'))
            main_sock.send(metadata_json)

            # Wait for receiver confirmation
            confirmation = main_sock.recv(1024).decode()
            if confirmation != "READY":
                raise Exception(
                    "Receiver not ready for multi-threaded transfer")

            # Initialize progress tracking
            self.app.transfer_locks[transfer_id] = threading.Lock()
            self.app.chunk_progress[transfer_id] = {
                'sent': 0,
                'total': total_size,
                'start_time': time.time(),
                'last_update': time.time(),
                'speed_samples': []
            }

            transfer_threads = []
            start_time = time.time()

            # Send small files
            if small_files:
                thread = threading.Thread(target=self._send_small_files,
                                          args=(main_sock, small_files, transfer_id))
                thread.start()
                transfer_threads.append(thread)

            # Send large files using multi-threaded chunks
            for file_info in large_files:
                chunk_threads = self._create_chunk_threads(
                    host, file_info, transfer_id)
                transfer_threads.extend(chunk_threads)

            # Wait for completion
            for thread in transfer_threads:
                thread.join()

            main_sock.send(b"TRANSFER_COMPLETE")
            main_sock.close()

            # Update statistics
            self.app.total_files_sent += len(files)
            self.app.total_bytes_sent += total_size

            duration = time.time() - start_time
            speed = total_size / duration if duration > 0 else 0
            self.app.add_to_history(
                'Sent', files, host, total_size, 'Success', duration)

            self.app.root.after(0, lambda: self.app.log_message(self.app.send_log,
                                                                f"✅ Multi-threaded transfer completed: {len(files)} files ({self.app.format_size(total_size)}) in {duration:.1f}s at {self.app.format_size(speed)}/s", 'success'))

        except Exception as e:
            error_msg = str(e)
            self.app.root.after(0, lambda: self.app.log_message(
                self.app.send_log, f"❌ Multi-threaded send failed: {error_msg}", 'error'))
            self.app.add_to_history(
                'Send Failed', files, host, 0, error_msg, 0)

    def _send_small_files(self, sock, files, transfer_id):
        """Send small files through single connection"""
        try:
            for file_info in files:
                # Send file metadata
                file_metadata = {
                    'name': file_info['name'],
                    'size': file_info['size'],
                    'path': file_info['path'],
                    'type': 'small_file'
                }

                file_meta_json = json.dumps(file_metadata).encode()
                sock.send(len(file_meta_json).to_bytes(4, 'big'))
                sock.send(file_meta_json)

                # Send file data
                with open(file_info['path'], 'rb') as f:
                    sent = 0
                    while sent < file_info['size']:
                        chunk = f.read(self.app.chunk_size)
                        if not chunk:
                            break
                        sock.send(chunk)
                        sent += len(chunk)

                        # Update progress
                        with self.app.transfer_locks[transfer_id]:
                            self.app.chunk_progress[transfer_id]['sent'] += len(
                                chunk)

        except Exception as e:
            self.app.root.after(0, lambda: self.app.log_message(
                self.app.send_log, f"Error sending small files: {e}", 'error'))

    def _create_chunk_threads(self, host, file_info, transfer_id):
        """Create multiple threads to send file chunks in parallel"""
        file_size = file_info['size']
        min_chunk_size = 100 * 1024 * 1024  # 100MB minimum per thread
        max_threads = min(self.app.max_threads, 4)
        num_threads = min(max_threads, max(1, file_size // min_chunk_size))
        chunk_size_per_thread = file_size // num_threads

        threads = []

        for i in range(num_threads):
            start_byte = i * chunk_size_per_thread
            if i == num_threads - 1:
                end_byte = file_size
            else:
                end_byte = start_byte + chunk_size_per_thread

            port = self.port_pool[i % len(self.port_pool)]

            if i > 0:
                time.sleep(0.1)

            thread = threading.Thread(target=self._send_file_chunk,
                                      args=(host, port, file_info, start_byte, end_byte, i, transfer_id))
            threads.append(thread)
            thread.start()

        return threads

    def _send_file_chunk(self, host, port, file_info, start_byte, end_byte, chunk_id, transfer_id):
        """Send a specific chunk of a file"""
        try:
            sock = socket.socket()
            sock.settimeout(int(self.app.timeout_var.get()))
            sock.connect((host, port))

            # Send chunk metadata
            chunk_metadata = {
                'file_name': file_info['name'],
                'file_path': file_info['path'],
                'chunk_id': chunk_id,
                'start_byte': start_byte,
                'end_byte': end_byte,
                'chunk_size': end_byte - start_byte,
                'type': 'file_chunk'
            }

            chunk_meta_json = json.dumps(chunk_metadata).encode()
            sock.send(len(chunk_meta_json).to_bytes(4, 'big'))
            sock.send(chunk_meta_json)

            # Send chunk data
            with open(file_info['path'], 'rb') as f:
                f.seek(start_byte)
                remaining = end_byte - start_byte

                while remaining > 0:
                    read_size = min(self.app.chunk_size, remaining)
                    chunk = f.read(read_size)
                    if not chunk:
                        break

                    sock.send(chunk)
                    remaining -= len(chunk)

                    # Update progress
                    with self.app.transfer_locks[transfer_id]:
                        self.app.chunk_progress[transfer_id]['sent'] += len(
                            chunk)

            sock.close()

        except Exception as e:
            self.app.root.after(0, lambda: self.app.log_message(
                self.app.send_log, f"Error sending chunk {chunk_id} of {file_info['name']}: {e}", 'error'))

    def start_receiving(self, port):
        """Start file receiving service"""
        self.app.receiver_thread = threading.Thread(
            target=self._receive_files, args=(port,), daemon=True)
        self.app.receiver_thread.start()

    def _receive_files(self, port):
        """Enhanced background file receiving"""
        try:
            self.receiver_socket = socket.socket()
            self.receiver_socket.setsockopt(
                socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.receiver_socket.bind(('', port))
            self.receiver_socket.listen(10)

            while self.app.is_receiving:
                try:
                    conn, addr = self.receiver_socket.accept()
                    if not self.app.is_receiving:
                        break

                    # Handle connection in separate thread
                    threading.Thread(target=self._handle_multi_file_connection,
                                     args=(conn, addr), daemon=True).start()

                except OSError:
                    break

        except Exception as e:
            self.app.root.after(0, lambda: self.app.log_message(
                self.app.recv_log, f"Receiver error: {e}", 'error'))

    def _handle_multi_file_connection(self, conn, addr):
        """Handle incoming multi-threaded transfer"""
        transfer_id = f"recv_{int(time.time())}_{addr[0]}"

        try:
            # Receive transfer metadata
            metadata_size = int.from_bytes(conn.recv(4), 'big')
            metadata = json.loads(conn.recv(metadata_size).decode())

            is_multi_threaded = metadata.get('multi_threaded', False)

            if is_multi_threaded:
                self._handle_multi_threaded_transfer(
                    conn, addr, metadata, transfer_id)
            else:
                self._handle_single_threaded_transfer(
                    conn, addr, metadata, transfer_id)

        except Exception as e:
            self.app.root.after(0, lambda: self.app.log_message(
                self.app.recv_log, f"❌ Connection error: {e}", 'error'))
        finally:
            try:
                conn.close()
            except:
                pass

    def _handle_multi_threaded_transfer(self, conn, addr, metadata, transfer_id):
        """Handle multi-threaded file transfer"""
        try:
            total_files = metadata['total_files']
            total_size = metadata['total_size']
            sender_name = metadata.get('sender_name', addr[0])

            # Check auto-accept
            if not self.app.auto_accept.get():
                accept = self.app.ask_accept_transfer(
                    total_files, total_size, sender_name)
                if not accept:
                    conn.send(b"REJECTED")
                    return

            # Send confirmation
            conn.send(b"READY")

            # Initialize progress tracking
            self.app.transfer_locks[transfer_id] = threading.Lock()
            self.app.chunk_progress[transfer_id] = {
                'received': 0,
                'total': total_size,
                'start_time': time.time(),
                'last_update': time.time(),
                'speed_samples': []
            }

            # Prepare save directory
            save_dir = self._prepare_save_directory(total_files)

            # Start chunk listeners
            self._start_chunk_listeners(save_dir, transfer_id)

            # Handle small files through main connection
            if metadata.get('small_files', 0) > 0:
                self._receive_small_files(conn, save_dir, transfer_id)

            # Wait for completion
            completion_signal = conn.recv(1024)
            if completion_signal == b"TRANSFER_COMPLETE":
                time.sleep(1)  # Allow threads to finish

                all_received = self._get_received_files(save_dir)

                # Update statistics and history
                self.app.total_files_received += len(all_received)
                self.app.total_bytes_received += total_size

                duration = time.time() - \
                    self.app.chunk_progress[transfer_id]['start_time']
                speed = total_size / duration if duration > 0 else 0
                self.app.add_to_history(
                    'Received', all_received, addr[0], total_size, 'Success', duration)

                self.app.root.after(0, lambda: self.app.log_message(self.app.recv_log,
                                                                    f"✅ Multi-threaded receive completed: {len(all_received)} files", 'success'))

        except Exception as e:
            self.app.root.after(0, lambda: self.app.log_message(
                self.app.recv_log, f"❌ Multi-threaded receive error: {e}", 'error'))

        finally:
            # Cleanup
            if transfer_id in self.app.active_transfers:
                del self.app.active_transfers[transfer_id]
            if transfer_id in self.app.transfer_locks:
                del self.app.transfer_locks[transfer_id]
            if transfer_id in self.app.chunk_progress:
                del self.app.chunk_progress[transfer_id]

    def _handle_single_threaded_transfer(self, conn, addr, metadata, transfer_id):
        """Handle traditional single-threaded transfer"""
        # Implementation for backwards compatibility
        pass

    def _prepare_save_directory(self, file_count):
        """Prepare save directory for received files"""
        save_dir = self.app.save_dir_entry.get()
        if self.app.create_subfolders.get() and file_count > 1:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            batch_dir = os.path.join(save_dir, f"batch_{timestamp}")
            os.makedirs(batch_dir, exist_ok=True)
            save_dir = batch_dir
        return save_dir

    def _start_chunk_listeners(self, save_dir, transfer_id):
        """Start listeners on additional ports for chunk connections"""
        for port in self.port_pool:
            threading.Thread(target=self._chunk_listener,
                             args=(port, save_dir, transfer_id), daemon=True).start()

    def _chunk_listener(self, port, save_dir, transfer_id):
        """Listen for chunk connections on a specific port"""
        try:
            sock = socket.socket()
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.bind(('', port))
            sock.listen(1)
            sock.settimeout(30)

            while transfer_id in self.app.active_transfers:
                try:
                    conn, addr = sock.accept()
                    threading.Thread(target=self._handle_chunk_connection,
                                     args=(conn, save_dir, transfer_id), daemon=True).start()
                except socket.timeout:
                    break
                except:
                    break

        except Exception:
            pass
        finally:
            try:
                sock.close()
            except:
                pass

    def _handle_chunk_connection(self, conn, save_dir, transfer_id):
        """Handle individual chunk connection"""
        try:
            # Receive chunk metadata
            metadata_size = int.from_bytes(conn.recv(4), 'big')
            chunk_metadata = json.loads(conn.recv(metadata_size).decode())

            if chunk_metadata['type'] == 'file_chunk':
                self._receive_file_chunk(
                    conn, chunk_metadata, save_dir, transfer_id)

        except Exception as e:
            self.app.root.after(0, lambda: self.app.log_message(
                self.app.recv_log, f"Chunk receive error: {e}", 'error'))
        finally:
            conn.close()

    def _receive_file_chunk(self, conn, chunk_metadata, save_dir, transfer_id):
        """Receive and save a file chunk"""
        try:
            file_name = chunk_metadata['file_name']
            chunk_id = chunk_metadata['chunk_id']
            chunk_size = chunk_metadata['chunk_size']

            # Create chunk file
            chunk_file_path = os.path.join(
                save_dir, f"{file_name}.chunk_{chunk_id}")

            # Receive chunk data
            received = 0
            with open(chunk_file_path, 'wb') as f:
                while received < chunk_size:
                    remaining = chunk_size - received
                    data = conn.recv(min(self.app.chunk_size, remaining))
                    if not data:
                        break
                    f.write(data)
                    received += len(data)

                    # Update progress
                    with self.app.transfer_locks[transfer_id]:
                        self.app.chunk_progress[transfer_id]['received'] += len(
                            data)

            # Check if file can be reassembled
            self._check_and_reassemble_file(file_name, save_dir)

        except Exception as e:
            self.app.root.after(0, lambda: self.app.log_message(
                self.app.recv_log, f"Error receiving chunk: {e}", 'error'))

    def _check_and_reassemble_file(self, file_name, save_dir):
        """Check if all chunks are received and reassemble the file"""
        try:
            # Find all chunk files for this file
            chunk_files = []
            for file in os.listdir(save_dir):
                if file.startswith(f"{file_name}.chunk_"):
                    chunk_id = int(file.split('.chunk_')[1])
                    chunk_files.append(
                        (chunk_id, os.path.join(save_dir, file)))

            if chunk_files:
                # Sort by chunk ID
                chunk_files.sort(key=lambda x: x[0])

                # Reassemble file
                output_path = os.path.join(save_dir, file_name)

                with open(output_path, 'wb') as output_file:
                    for chunk_id, chunk_path in chunk_files:
                        with open(chunk_path, 'rb') as chunk_file:
                            output_file.write(chunk_file.read())
                        os.remove(chunk_path)  # Clean up chunk file

        except Exception as e:
            self.app.root.after(0, lambda: self.app.log_message(
                self.app.recv_log, f"Error reassembling {file_name}: {e}", 'error'))

    def _receive_small_files(self, conn, save_dir, transfer_id):
        """Receive small files through main connection"""
        received_files = []
        try:
            while True:
                try:
                    metadata_size = int.from_bytes(conn.recv(4), 'big')
                    if metadata_size == 0:
                        break
                    file_metadata = json.loads(
                        conn.recv(metadata_size).decode())

                    if file_metadata['type'] != 'small_file':
                        break

                except:
                    break

                file_name = file_metadata['name']
                file_size = file_metadata['size']

                # Receive file data
                file_path = os.path.join(save_dir, file_name)
                file_path = self._get_unique_filename(file_path)

                with open(file_path, 'wb') as f:
                    received = 0
                    while received < file_size:
                        remaining = file_size - received
                        data = conn.recv(min(self.app.chunk_size, remaining))
                        if not data:
                            break
                        f.write(data)
                        received += len(data)

                        # Update progress
                        with self.app.transfer_locks[transfer_id]:
                            self.app.chunk_progress[transfer_id]['received'] += len(
                                data)

                received_files.append(
                    {'name': file_name, 'path': file_path, 'size': file_size})

        except Exception as e:
            self.app.root.after(0, lambda: self.app.log_message(
                self.app.recv_log, f"Error receiving small files: {e}", 'error'))

        return received_files

    def _get_received_files(self, save_dir):
        """Get list of all received files in directory"""
        received_files = []
        try:
            for file_name in os.listdir(save_dir):
                file_path = os.path.join(save_dir, file_name)
                if os.path.isfile(file_path) and not file_name.startswith('.chunk_'):
                    stat = os.stat(file_path)
                    received_files.append({
                        'name': file_name,
                        'path': file_path,
                        'size': stat.st_size
                    })
        except:
            pass
        return received_files

    def _get_unique_filename(self, filepath):
        """Get unique filename to avoid conflicts"""
        if not self.app.overwrite_files.get() and os.path.exists(filepath):
            base, ext = os.path.splitext(filepath)
            counter = 1
            while os.path.exists(f"{base}_{counter}{ext}"):
                counter += 1
            return f"{base}_{counter}{ext}"
        return filepath

    def stop_receiving(self):
        """Stop receiving service"""
        if self.receiver_socket:
            self.receiver_socket.close()

    def get_local_ip(self):
        """Get local IP address"""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                s.connect(('8.8.8.8', 80))
                return s.getsockname()[0]
        except:
            return '127.0.0.1'
