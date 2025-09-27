#!/usr/bin/env python3
"""
DNS management script for cvideo-click-api custom domains.
Helps with DNS setup and troubleshooting for *.apps.cvideo.click domains.
"""

import sys
import boto3
from typing import List, Optional
from botocore.exceptions import ClientError
from subprocess_utils import run_secure_command, find_executable


def get_nameservers() -> Optional[List[str]]:
    """Get Route 53 nameservers for apps.cvideo.click."""
    try:
        route53 = boto3.client("route53")

        # Find the hosted zone
        response = route53.list_hosted_zones()
        zones = response.get("HostedZones", [])

        apps_zone = None
        for zone in zones:
            if zone["Name"] == "apps.cvideo.click.":
                apps_zone = zone
                break

        if not apps_zone:
            print("❌ Route 53 hosted zone for apps.cvideo.click not found")
            return None

        zone_id = apps_zone["Id"].split("/")[-1]

        # Get nameservers
        response = route53.get_hosted_zone(Id=zone_id)
        nameservers = response.get("DelegationSet", {}).get("NameServers", [])

        return list(nameservers) if nameservers else None

    except ClientError as e:
        print(f"❌ Error getting nameservers: {e}")
        return None


def show_dns_setup_instructions() -> None:
    """Show DNS setup instructions for parent domain."""
    print("🔧 DNS SETUP INSTRUCTIONS")
    print("=" * 50)
    print()
    print("To set up custom domains under *.apps.cvideo.click, you need to:")
    print()
    print("1. Configure the parent domain (cvideo.click) to delegate the")
    print("   'apps' subdomain to the Route 53 nameservers below.")
    print()
    print("2. Add NS records in your parent domain DNS configuration:")
    print()

    nameservers = get_nameservers()
    if nameservers:
        print("   Domain: apps.cvideo.click")
        print("   Type: NS")
        print("   Values:")
        for ns in nameservers:
            print(f"     {ns}")
    else:
        print("   ❌ Could not retrieve nameservers (deploy infrastructure first)")

    print()
    print("3. Wait for DNS propagation (5-30 minutes)")
    print()
    print("4. Test with: dig NS apps.cvideo.click")
    print()
    print("Example DNS configuration in your parent domain provider:")
    print("┌─────────────────┬──────┬─────────────────────────────────┐")
    print("│ Name            │ Type │ Value                           │")
    print("├─────────────────┼──────┼─────────────────────────────────┤")
    if nameservers:
        for i, ns in enumerate(nameservers):
            name = "apps" if i == 0 else ""
            print(f"│ {name:<15} │ NS   │ {ns:<31} │")
    else:
        print("│ apps            │ NS   │ <nameserver-1>                  │")
        print("│                 │ NS   │ <nameserver-2>                  │")
        print("│                 │ NS   │ <nameserver-3>                  │")
        print("│                 │ NS   │ <nameserver-4>                  │")
    print("└─────────────────┴──────┴─────────────────────────────────┘")


def test_dns_delegation() -> bool:
    """Test if DNS delegation is working."""
    print("\n🔍 Testing DNS delegation...")

    try:
        # Find dig executable securely
        dig_path = find_executable("dig")
        if not dig_path:
            print("❌ dig command not found in PATH")
            return False

        # Test NS record resolution
        exit_code, stdout, stderr = run_secure_command(
            [dig_path, "+short", "NS", "apps.cvideo.click"],
            timeout=10,
            capture_output=True,
        )

        if exit_code != 0:
            print("❌ dig command failed")
            return False

        ns_records = [
            line.strip(".") for line in stdout.strip().split("\n") if line.strip()
        ]

        if not ns_records:
            print("❌ No NS records found for apps.cvideo.click")
            print("   DNS delegation is not configured yet")
            return False

        print("✅ DNS delegation working!")
        print("   NS records found:")
        for ns in ns_records:
            print(f"     • {ns}")

        # Compare with expected nameservers
        expected_ns = get_nameservers()
        if expected_ns:
            expected_ns_clean = [ns.rstrip(".") for ns in expected_ns]
            if set(ns_records) == set(expected_ns_clean):
                print("✅ NS records match Route 53 nameservers")
            else:
                print("⚠️  NS records don't match Route 53 nameservers")
                print("   This might be due to DNS caching")

        return True

    except TimeoutError:
        print("❌ DNS query timed out")
        return False
    except FileNotFoundError:
        print("⚠️  'dig' command not found, skipping DNS test")
        print(
            "   Install dig with: brew install bind (macOS) or "
            "apt-get install dnsutils (Linux)"
        )
        return True
    except Exception as e:
        print(f"❌ DNS test failed: {e}")
        return False


def check_domain_resolution() -> None:
    """Check resolution of specific subdomains."""
    print("\n🔍 Checking subdomain resolution...")

    # Get custom domain from Terraform
    try:
        # Find terraform executable securely
        terraform_path = find_executable("terraform")
        if not terraform_path:
            print("❌ terraform command not found in PATH")
            return

        exit_code, stdout, stderr = run_secure_command(
            [terraform_path, "output", "-raw", "custom_domain_url"],
            cwd="terraform",
            timeout=10,
            capture_output=True,
        )

        if exit_code == 0:
            domain_url = stdout.strip()
            domain = domain_url.replace("https://", "")

            print(f"Testing: {domain}")

            # Test A record
            try:
                # Find dig executable securely
                dig_path = find_executable("dig")
                if not dig_path:
                    print("❌ dig command not found in PATH")
                    return

                exit_code, stdout, stderr = run_secure_command(
                    [dig_path, "+short", "A", domain],
                    timeout=10,
                    capture_output=True,
                )

                if exit_code == 0 and stdout.strip():
                    a_records = stdout.strip().split("\n")
                    print(f"✅ A record: {domain}")
                    for record in a_records:
                        print(f"     → {record.strip()}")
                else:
                    print(f"❌ No A record found for {domain}")

            except Exception as e:
                print(f"❌ Error checking A record: {e}")

    except Exception as e:
        print(f"⚠️  Could not get custom domain from Terraform: {e}")


def show_troubleshooting() -> None:
    """Show troubleshooting information."""
    print("\n🔧 TROUBLESHOOTING")
    print("=" * 50)
    print()
    print("Common issues and solutions:")
    print()
    print("1. DNS delegation not working:")
    print("   • Verify NS records are configured in parent domain")
    print("   • Wait for DNS propagation (5-30 minutes)")
    print("   • Test with: dig NS apps.cvideo.click")
    print()
    print("2. Certificate validation failing:")
    print("   • DNS delegation must be working first")
    print("   • Check Route 53 validation records")
    print("   • Wait for ACM validation (5-30 minutes)")
    print()
    print("3. Custom domain not resolving:")
    print("   • Ensure infrastructure is deployed")
    print("   • Check API Gateway custom domain status")
    print("   • Verify Route 53 A record is created")
    print()
    print("4. SSL certificate errors:")
    print("   • Wait for certificate validation")
    print("   • Check ACM certificate status in AWS Console")
    print("   • Ensure wildcard certificate covers subdomain")
    print()
    print("Commands to check status:")
    print("   make domain-check       # Check domain configuration")
    print("   make plan              # Preview infrastructure changes")
    print("   make remote-deploy     # Deploy infrastructure")
    print("   dig NS apps.cvideo.click    # Test DNS delegation")
    print("   dig A api-dev.apps.cvideo.click  # Test subdomain resolution")


def main() -> None:
    """Main DNS management function."""
    if len(sys.argv) < 2:
        print("🌐 CVIDEO-CLICK-API DNS Management")
        print("=" * 50)
        print()
        print("Usage: python scripts/dns_management.py <command>")
        print()
        print("Commands:")
        print("  setup      Show DNS setup instructions")
        print("  test       Test DNS delegation and resolution")
        print("  troubleshoot  Show troubleshooting information")
        print()
        sys.exit(1)

    command = sys.argv[1].lower()

    if command == "setup":
        show_dns_setup_instructions()
    elif command == "test":
        print("🌐 CVIDEO-CLICK-API DNS Testing")
        print("=" * 50)

        # Test DNS delegation
        delegation_ok = test_dns_delegation()

        # Test domain resolution if delegation works
        if delegation_ok:
            check_domain_resolution()

        print("\n📊 Summary:")
        if delegation_ok:
            print("✅ DNS delegation is working")
            print("🌐 Your custom domains should be accessible")
        else:
            print("❌ DNS delegation not configured")
            print("🔧 Run 'python scripts/dns_management.py setup' for instructions")

    elif command == "troubleshoot":
        show_troubleshooting()

    else:
        print(f"❌ Unknown command: {command}")
        print("Available commands: setup, test, troubleshoot")
        sys.exit(1)


if __name__ == "__main__":
    main()
