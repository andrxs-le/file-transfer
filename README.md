# File Transfer

This is a powerful and user-friendly file transfer application built with Python and `tkinter`. It allows for seamless transfer of files and folders between computers on the same network.

## Features

- **Intuitive GUI:** A clean and modern user interface with separate tabs for sending, receiving, monitoring, and settings.
- **Auto Discovery:** Automatically discovers other users on the network running the application.
- **Multi-File & Folder Transfer:** Send multiple files or entire folders in a single batch.
- **Real-time Monitoring:** Track active transfers with progress bars, speed indicators, and estimated time of arrival (ETA).
- **Transfer History:** Keep a log of all your past transfers for easy reference.
- **Customizable Settings:** Configure your display name, default save locations, and network parameters.
- **Cross-Platform:** Built with standard Python libraries, making it compatible with Windows, macOS, and Linux.
- **Multi-threaded**: Handles multiple transfers simultaneously without freezing the UI.

## Screenshots

| Send Tab                           | Receive Tab                              |
| ---------------------------------- | ---------------------------------------- |
| ![Send Tab](assets/send%20tab.png) | ![Receive Tab](assets/receive%20tab.png) |

| Monitor Tab                              | History Tab                              |
| ---------------------------------------- | ---------------------------------------- |
| ![Monitor Tab](assets/monitor%20tab.png) | ![History Tab](assets/history%20tab.png) |

| Settings Tab                               |
| ------------------------------------------ |
| ![Settings Tab](assets/settings%20tab.png) |

## Getting Started

### Prerequisites

- Python 3.6 or higher
- No external libraries are needed for the basic functionality.

### Installation & Running

1. **Clone the repository:**

   ```sh
   git clone https://github.com/whoisjayd/file-transfer.git
   cd file-transfer
   ```

2. **Run the application:**
   ```sh
   python app.py
   ```

## How to Use

### Sending Files

1.  Navigate to the **Send Files** tab.
2.  The application will automatically scan for available receivers. You can also manually enter an IP address.
3.  Click **Add Files** or **Add Folder** to select what you want to send.
4.  Select a receiver from the list or enter the IP manually.
5.  Click **Send Files**.

### Receiving Files

1.  Go to the **Receive Files** tab.
2.  Set your display name and the directory where you want to save incoming files.
3.  Click **Start Receiving**. The application will now listen for incoming connections.
4.  You will be prompted to accept or decline incoming transfers unless you have enabled auto-accept in the settings.

### Monitoring

- The **Monitor** tab shows all active transfers, their progress, speed, and ETA.

### History

- The **History** tab provides a log of all completed or failed transfers.

## Code Structure

The project is organized into a modular structure:

- `app.py`: The main application entry point.
- `ui/`: Contains the `UIManager` responsible for all GUI components.
- `network/`: Includes the `TransferManager` which handles all networking logic.
- `utils/`: A collection of helper modules for file management, settings, and other utilities.
- `assets/`: Contains images and other resources for the application.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
