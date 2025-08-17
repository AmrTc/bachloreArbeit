#!/usr/bin/env python3
"""
Test multiple possible IP addresses for PostgreSQL connection
"""

import socket
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_ip_connectivity(host, port=5432, timeout=5):
    """Test if an IP address is reachable."""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((host, port))
        sock.close()
        
        if result == 0:
            logger.info(f"✅ {host}:{port} - REACHABLE")
            return True
        else:
            logger.warning(f"❌ {host}:{port} - NOT REACHABLE (error code: {result})")
            return False
            
    except Exception as e:
        logger.error(f"❌ {host}:{port} - ERROR: {e}")
        return False

def main():
    """Test multiple possible IP addresses."""
    logger.info("🌐 Testing multiple IP addresses for PostgreSQL connection...")
    
    # List of possible IP addresses to test
    possible_ips = [
        "34.59.248.159",  # Current IP from your config
        "34.42.123.45",   # Previous IP mentioned
        "34.69.19.208",   # Outgoing IP from your screenshot
        "10.0.0.1",       # Common private IP
        "172.16.0.1",     # Common private IP
        "192.168.1.1"     # Common private IP
    ]
    
    logger.info("📋 Testing the following IP addresses:")
    for ip in possible_ips:
        logger.info(f"   - {ip}")
    
    logger.info("")
    
    reachable_ips = []
    for ip in possible_ips:
        if test_ip_connectivity(ip):
            reachable_ips.append(ip)
    
    logger.info("")
    if reachable_ips:
        logger.info("🎉 Reachable IP addresses:")
        for ip in reachable_ips:
            logger.info(f"   ✅ {ip}")
        logger.info("")
        logger.info("💡 Update your configuration files with one of these IP addresses.")
    else:
        logger.error("❌ No IP addresses are reachable!")
        logger.error("🔍 This could mean:")
        logger.error("   - The Google Cloud SQL instance is not running")
        logger.error("   - The instance is not configured for public access")
        logger.error("   - Firewall rules are blocking access")
        logger.error("   - The instance is in a different region/network")
        logger.error("")
        logger.error("💡 Try checking the Google Cloud Console for the current status.")

if __name__ == "__main__":
    main()
