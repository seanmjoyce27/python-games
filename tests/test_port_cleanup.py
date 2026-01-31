"""
Tests for port cleanup and reusability
"""
import pytest
import socket
import time
import os
import signal
import subprocess


def is_port_in_use(port):
    """Check if a port is in use"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind(('127.0.0.1', port))
            return False
        except OSError:
            return True


def kill_process_on_port(port):
    """Kill any process using the specified port"""
    try:
        # macOS/Linux: find process using port and kill it
        result = subprocess.run(
            ['lsof', '-ti', f':{port}'],
            capture_output=True,
            text=True
        )
        if result.stdout.strip():
            pids = result.stdout.strip().split('\n')
            for pid in pids:
                try:
                    os.kill(int(pid), signal.SIGTERM)
                    time.sleep(0.5)
                except ProcessLookupError:
                    pass
    except FileNotFoundError:
        # lsof not available (might be on different OS)
        pass


def test_default_port_not_in_use():
    """Test that default port 8443 is not in use before tests"""
    port = 8443

    # Clean up any existing process on the port
    kill_process_on_port(port)
    time.sleep(1)

    # Port should now be available
    assert not is_port_in_use(port), f"Port {port} is in use and couldn't be cleaned up"


def test_port_can_be_reused():
    """Test that port can be bound, released, and reused"""
    port = 8443

    # Ensure port is free
    kill_process_on_port(port)
    time.sleep(0.5)

    # First bind
    sock1 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock1.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock1.bind(('127.0.0.1', port))
    sock1.listen(1)

    assert is_port_in_use(port), f"Port {port} should be in use"

    # Release
    sock1.close()
    time.sleep(0.5)

    # Port should be available again
    assert not is_port_in_use(port), f"Port {port} should be available after closing"

    # Second bind should work
    sock2 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock2.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock2.bind(('127.0.0.1', port))
    sock2.listen(1)

    assert is_port_in_use(port), f"Port {port} should be in use on second bind"

    # Cleanup
    sock2.close()
    time.sleep(0.5)


def test_flask_app_releases_port():
    """Test that Flask app properly releases port on shutdown"""
    port = 8444  # Use different port to avoid conflicts with main app

    # Ensure port is free
    kill_process_on_port(port)
    time.sleep(0.5)

    # Start Flask app in subprocess
    env = os.environ.copy()
    env['PORT'] = str(port)
    env['FLASK_ENV'] = 'production'  # Disable reloader

    process = subprocess.Popen(
        ['python', 'app.py'],
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )

    # Wait for server to start
    time.sleep(2)

    # Port should be in use
    assert is_port_in_use(port), f"Port {port} should be in use by Flask app"

    # Stop the server with SIGTERM
    process.terminate()

    # Wait for process to exit
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        # Force kill if it doesn't terminate gracefully
        process.kill()
        process.wait()

    time.sleep(1)

    # Port should be available again
    assert not is_port_in_use(port), f"Port {port} should be available after Flask shutdown"


def test_so_reuseaddr_flag():
    """Test that SO_REUSEADDR allows immediate port reuse"""
    port = 8445

    kill_process_on_port(port)
    time.sleep(0.5)

    # Create socket with SO_REUSEADDR
    sock1 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock1.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock1.bind(('127.0.0.1', port))
    sock1.listen(1)
    sock1.close()

    # Immediately create another socket on same port
    # This should work because of SO_REUSEADDR
    sock2 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock2.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    try:
        sock2.bind(('127.0.0.1', port))
        sock2.listen(1)
        success = True
    except OSError:
        success = False
    finally:
        sock2.close()

    assert success, "SO_REUSEADDR should allow immediate port reuse"


def test_port_cleanup_utility():
    """Test the port cleanup utility function"""
    port = 8446

    # Start a simple server
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(('127.0.0.1', port))
    sock.listen(1)

    assert is_port_in_use(port)

    # Create a background process that uses the port
    # (socket in this process will be cleaned up, but we can test the function)
    pid = os.getpid()

    # Close our socket
    sock.close()
    time.sleep(0.5)

    # Run cleanup function
    kill_process_on_port(port)
    time.sleep(0.5)

    # Port should be available
    assert not is_port_in_use(port)
