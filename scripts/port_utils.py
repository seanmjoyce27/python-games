"""
Port management utilities for Python Game Builder
"""
import socket
import subprocess
import time
import os
import signal


def is_port_in_use(port, host='127.0.0.1'):
    """
    Check if a port is currently in use

    Args:
        port (int): Port number to check
        host (str): Host address (default: '127.0.0.1')

    Returns:
        bool: True if port is in use, False otherwise
    """
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(1)
        try:
            sock.bind((host, port))
            return False
        except (OSError, socket.error):
            return True


def get_process_on_port(port):
    """
    Get the PID of the process using a port

    Args:
        port (int): Port number

    Returns:
        list: List of PIDs using the port
    """
    try:
        result = subprocess.run(
            ['lsof', '-ti', f':{port}'],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.stdout.strip():
            return [int(pid) for pid in result.stdout.strip().split('\n')]
        return []
    except (FileNotFoundError, subprocess.TimeoutExpired, ValueError):
        return []


def kill_process_on_port(port, force=False):
    """
    Kill process(es) using a specific port

    Args:
        port (int): Port number
        force (bool): Use SIGKILL instead of SIGTERM

    Returns:
        bool: True if successful, False otherwise
    """
    pids = get_process_on_port(port)

    if not pids:
        return True

    sig = signal.SIGKILL if force else signal.SIGTERM

    for pid in pids:
        try:
            os.kill(pid, sig)
            print(f"Killed process {pid} on port {port}")
        except ProcessLookupError:
            pass  # Process already dead
        except PermissionError:
            print(f"Permission denied to kill process {pid}")
            return False

    # Wait for processes to die
    time.sleep(0.5)

    # Check if port is now free
    if is_port_in_use(port):
        if not force:
            # Try force kill
            return kill_process_on_port(port, force=True)
        return False

    return True


def cleanup_port(port):
    """
    Ensure a port is available by killing any process using it

    Args:
        port (int): Port number to clean up

    Returns:
        bool: True if port is now available
    """
    if not is_port_in_use(port):
        print(f"✅ Port {port} is already available")
        return True

    print(f"🔍 Port {port} is in use, cleaning up...")

    if kill_process_on_port(port):
        print(f"✅ Port {port} is now available")
        return True
    else:
        print(f"❌ Failed to free port {port}")
        return False


def wait_for_port(port, timeout=10, host='127.0.0.1'):
    """
    Wait for a port to become available

    Args:
        port (int): Port number
        timeout (int): Maximum seconds to wait
        host (str): Host address

    Returns:
        bool: True if port became available, False if timeout
    """
    start_time = time.time()

    while time.time() - start_time < timeout:
        if not is_port_in_use(port, host):
            return True
        time.sleep(0.1)

    return False


def find_available_port(start_port=None, max_attempts=100):
    """
    Find an available port
    """
    if start_port is None:
        start_port = int(os.environ.get('PORT', 8443))

    Args:
        start_port (int): Port to start searching from
        max_attempts (int): Maximum number of ports to try

    Returns:
        int or None: Available port number or None if not found
    """
    for port in range(start_port, start_port + max_attempts):
        if not is_port_in_use(port):
            return port
    return None


if __name__ == '__main__':
    import sys

    if len(sys.argv) > 1:
        port = int(sys.argv[1])
    else:
        port = int(os.environ.get('PORT', 8443))

    print(f"Port Cleanup Utility for Python Game Builder")
    print(f"=" * 50)

    if cleanup_port(port):
        sys.exit(0)
    else:
        sys.exit(1)
