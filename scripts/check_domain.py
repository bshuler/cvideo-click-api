#!/usr/bin/env python3
"""
Domain validation script for cvideo-click-api.
Checks custom domain configuration, DNS propagation, and certificate status.
"""

import sys
import boto3
import socket
import ssl
from typing import Dict, Any
from botocore.exceptions import ClientError


def check_route53_zone() -> bool:
    """Check Route 53 hosted zone for apps.cvideo.click."""
    print("🌐 Checking Route 53 hosted zone...")

    try:
        route53 = boto3.client("route53")

        # List hosted zones
        response = route53.list_hosted_zones()
        zones = response.get("HostedZones", [])

        apps_zone = None
        for zone in zones:
            if zone["Name"] == "apps.cvideo.click.":
                apps_zone = zone
                break

        if not apps_zone:
            print("❌ Route 53 hosted zone for apps.cvideo.click not found")
            return False

        zone_id = apps_zone["Id"].split("/")[-1]
        print(f"✅ Route 53 zone found: {zone_id}")

        # Get name servers
        response = route53.get_hosted_zone(Id=zone_id)
        nameservers = response.get("DelegationSet", {}).get("NameServers", [])

        print("📋 Name servers:")
        for ns in nameservers:
            print(f"   • {ns}")

        return True

    except ClientError as e:
        error_code = e.response.get("Error", {}).get("Code")
        print(f"❌ Route 53 error ({error_code}): {e}")
        return False


def check_acm_certificate() -> bool:
    """Check ACM certificate for *.apps.cvideo.click."""
    print("\n🔒 Checking ACM certificate...")

    try:
        acm = boto3.client("acm")

        # List certificates
        response = acm.list_certificates()
        certificates = response.get("CertificateSummaryList", [])

        apps_cert = None
        for cert in certificates:
            if cert["DomainName"] == "apps.cvideo.click":
                apps_cert = cert
                break

        if not apps_cert:
            print("❌ ACM certificate for *.apps.cvideo.click not found")
            return False

        cert_arn = apps_cert["CertificateArn"]
        print(f"✅ Certificate found: {cert_arn.split('/')[-1]}")

        # Get certificate details
        response = acm.describe_certificate(CertificateArn=cert_arn)
        cert_details = response["Certificate"]

        status = cert_details["Status"]
        status_icon = (
            "✅"
            if status == "ISSUED"
            else ("⏳" if status == "PENDING_VALIDATION" else "❌")
        )
        print(f"   Status: {status_icon} {status}")

        # Show domain validation
        domain_validations = cert_details.get("DomainValidationOptions", [])
        for validation in domain_validations:
            domain = validation["DomainName"]
            validation_status = validation["ValidationStatus"]
            validation_icon = (
                "✅"
                if validation_status == "SUCCESS"
                else ("⏳" if validation_status == "PENDING_VALIDATION" else "❌")
            )
            print(f"   {domain}: {validation_icon} {validation_status}")

        return bool(status == "ISSUED")

    except ClientError as e:
        error_code = e.response.get("Error", {}).get("Code")
        print(f"❌ ACM error ({error_code}): {e}")
        return False


def check_api_gateway_domain() -> bool:
    """Check API Gateway custom domain configuration."""
    print("\n🚪 Checking API Gateway custom domain...")

    try:
        apigateway = boto3.client("apigateway")

        # List domain names
        response = apigateway.get_domain_names()
        domains = response.get("items", [])

        api_domains = [d for d in domains if "apps.cvideo.click" in d["domainName"]]

        if not api_domains:
            print("❌ No API Gateway domains found for apps.cvideo.click")
            return False

        for domain in api_domains:
            domain_name = domain["domainName"]
            status = domain.get("domainNameStatus", "UNKNOWN")
            status_icon = (
                "✅"
                if status == "AVAILABLE"
                else ("⏳" if status in ["UPDATING", "PENDING"] else "❌")
            )

            print(f"✅ Domain: {domain_name}")
            print(f"   Status: {status_icon} {status}")

            # Check certificate
            cert_arn = domain.get("regionalCertificateArn", "")
            if cert_arn:
                print(f"   Certificate: {cert_arn.split('/')[-1]}")

            # Check target domain
            target_domain = domain.get("regionalDomainName", "")
            if target_domain:
                print(f"   Target: {target_domain}")

        return True

    except ClientError as e:
        error_code = e.response.get("Error", {}).get("Code")
        print(f"❌ API Gateway error ({error_code}): {e}")
        return False


def check_dns_propagation(domain: str) -> bool:
    """Check DNS propagation for custom domain."""
    print(f"\n🔍 Checking DNS propagation for {domain}...")

    try:
        # Check A record resolution
        result = socket.gethostbyname(domain)
        print(f"✅ DNS A record: {domain} → {result}")

        # Check if it resolves to API Gateway
        if "execute-api" in result or "amazonaws.com" in result:
            print("✅ Resolves to AWS API Gateway")
        else:
            print("⚠️  Does not appear to resolve to AWS API Gateway")

        return True

    except socket.gaierror as e:
        print(f"❌ DNS resolution failed: {e}")
        return False


def check_ssl_certificate(domain: str, port: int = 443) -> bool:
    """Check SSL certificate for custom domain."""
    print(f"\n🔐 Checking SSL certificate for {domain}...")

    try:
        # Create SSL context
        context = ssl.create_default_context()

        # Connect and get certificate
        with socket.create_connection((domain, port), timeout=10) as sock:
            with context.wrap_socket(sock, server_hostname=domain) as ssock:
                cert = ssock.getpeercert()

                # Check certificate details
                # Extract certificate details (SSL cert parsing is complex)
                subject = dict(x[0] for x in cert.get("subject", []))  # type: ignore
                common_name = subject.get("commonName", "")

                print("✅ SSL certificate found")
                print(f"   Common Name: {common_name}")
                issuer_org = dict(  # type: ignore
                    x[0] for x in cert.get("issuer", [])  # type: ignore
                ).get("organizationName", "Unknown")
                print(f"   Issuer: {issuer_org}")

                # Check expiration
                not_after = cert.get("notAfter", "")  # type: ignore
                print(f"   Expires: {not_after}")

                return True

    except Exception as e:
        print(f"❌ SSL certificate check failed: {e}")
        return False


def test_api_endpoint(domain: str) -> bool:
    """Test API endpoint accessibility."""
    print(f"\n🧪 Testing API endpoint: https://{domain}/hello...")

    try:
        import requests

        response = requests.get(f"https://{domain}/hello", timeout=10)
        status_icon = "✅" if response.status_code == 200 else "❌"

        print(f"   {status_icon} HTTP {response.status_code}")

        if response.status_code == 200:
            try:
                data = response.json()
                print(f"   Response: {data}")
            except ValueError:
                print(f"   Response: {response.text[:100]}...")

        return response.status_code == 200

    except ImportError:
        print("⚠️  requests library not available, skipping endpoint test")
        return True
    except Exception as e:
        print(f"❌ API endpoint test failed: {e}")
        return False


def get_terraform_outputs() -> Dict[str, Any]:
    """Get custom domain information from Terraform outputs."""
    print("\n📋 Getting Terraform outputs...")

    try:
        from subprocess_utils import run_secure_command, find_executable
        import json

        # Find terraform executable securely
        terraform_path = find_executable("terraform")
        if not terraform_path:
            raise FileNotFoundError("terraform executable not found in PATH")

        # Run terraform output with secure subprocess
        exit_code, stdout, stderr = run_secure_command(
            [terraform_path, "output", "-json"],
            cwd="terraform",
            timeout=60,
            capture_output=True,
            check=True,
        )

        if exit_code != 0:
            raise RuntimeError(f"terraform command failed: {stderr}")

        outputs = json.loads(stdout)

        # Extract relevant outputs
        domain_info = {}
        for key, value in outputs.items():
            if "domain" in key.lower() or "nameserver" in key.lower():
                domain_info[key] = value.get("value", "")

        print("📋 Domain configuration:")
        for key, value in domain_info.items():
            if isinstance(value, list):
                print(f"   {key}:")
                for item in value:
                    print(f"     • {item}")
            else:
                print(f"   {key}: {value}")

        return domain_info

    except (FileNotFoundError, RuntimeError) as e:
        print(f"❌ Terraform error: {e}")
        return {}
    except Exception as e:
        print(f"❌ Error getting Terraform outputs: {e}")
        return {}


def main() -> None:
    """Run domain validation checks."""
    print("🔍 CVIDEO-CLICK-API Domain Validation")
    print("=" * 50)

    checks = [
        check_route53_zone,
        check_acm_certificate,
        check_api_gateway_domain,
    ]

    # Get domain from Terraform outputs or use default
    terraform_outputs = get_terraform_outputs()
    custom_domain = terraform_outputs.get("custom_domain_url", {})
    if isinstance(custom_domain, str):
        domain = custom_domain.replace("https://", "")
    else:
        domain = "api-dev.apps.cvideo.click"  # Default from terraform.tfvars

    # Run infrastructure checks
    results = []
    for check in checks:
        try:
            result = check()
            results.append(result)
        except Exception as e:
            print(f"❌ Check failed: {e}")
            results.append(False)

    # Run DNS/connectivity checks if infrastructure is ready
    if all(results):
        print(f"\n🌍 Running connectivity checks for {domain}...")
        dns_result = check_dns_propagation(domain)
        if dns_result:
            check_ssl_certificate(domain)
            test_api_endpoint(domain)

    # Summary
    print("\n" + "=" * 50)
    print("📊 SUMMARY")

    passed = sum(results)
    total = len(results)

    if passed == total:
        print(f"✅ All {total} infrastructure checks passed!")
        print(f"🌐 Custom domain should be accessible at: https://{domain}")
    else:
        print(f"❌ {passed}/{total} checks passed")
        print("🔧 Run 'make plan' and 'make remote-deploy' to deploy infrastructure")

    # Exit with appropriate code
    sys.exit(0 if passed == total else 1)


if __name__ == "__main__":
    main()
