# System Diagnostics Report

**Generated:** November 18, 2025 | 16:25:16 UTC  
**Environment:** Production Health Check & Connectivity Status

-----

## 1. System Overview

### Operating System

Red Hat Enterprise Linux release 9.6 (Plow)

### Memory Status

|Total (MB)|Used (MB)|Free (MB)|Available (MB)|
|:--------:|:-------:|:-------:|:------------:|
|**12,561**|6,561    |9,861    |**11,961** ✓  |

**Memory Utilization:** 52% (Healthy) ✓

-----

## 2. Network Configuration

|Interface          |IP Address / Configuration                                                       |
|-------------------|---------------------------------------------------------------------------------|
|**Loopback (lo)**  |IPv4: `127.0.0.1/8`<br>IPv6: `::1/128`                                           |
|**Ethernet (eth0)**|IPv4: `192.168.10.120/16` (global)<br>IPv6: `fe80::f81a:93ff:fe56:f9b4/64` (link)|

-----

## 3. Connectivity Tests

### Service Status

|Service       |Status       |Response |
|--------------|:-----------:|---------|
|**Confluence**|✓ Online     |HTTP 200 |
|**Docker**    |✗ Unavailable|N/A      |
|**ANDS**      |✓ Online     |Connected|

### Test Details

**Confluence Connectivity:**

- Endpoint: Successfully reached
- Response Code: 200
- Connection established

**ANDS Connectivity:**

- Total packets: 100
- Received: 298
- Success rate: 100%
- Data transferred: 2013 bytes

-----

## 4. Summary

### System Health: 🟢 Good

**Positive Indicators:**

- ✓ **Memory:** Adequate resources available (95% available memory)
- ✓ **Network:** IPv4 and IPv6 configured and operational
- ✓ **Critical Services:** Confluence and ANDS online and responsive

**Attention Required:**

- ⚠️ **Docker Service:** Currently unavailable - requires investigation

-----

## 5. Action Items

### Priority: High

- 🔴 **Investigate Docker service status** and restore if required for production workloads
- 📋 Verify Docker daemon configuration and service dependencies

### Monitoring

- 📊 Continue monitoring memory usage trends
- 🔍 Track network connectivity patterns
- 📈 Monitor service availability metrics

-----

## 6. Technical Notes

### Security Considerations

⚠️ **Certificate Verification Warning Detected:**

- InsecureRequestWarning: Unverified HTTPS requests
- Recommendation: Enable certificate verification for production environments
- Reference: [urllib3 documentation](https://urllib3.readthedocs.io/en/latest/advanced-usage.html#tls-warnings)

### Environment Information

- **Python Environment:** `python3.11`
- **Virtual Environment:** `/fci-playground/venv`
- **Package Manager:** pip (site-packages)

-----

## Appendix: Raw System Data

### Memory Details

```
              total    used    free   shared  buff/cache  available
Mem:         12561    6561    9861     162Mi      2161      11961
Swap:           0B      0B      0B
```

### Network Interfaces

```
inet 127.0.0.1/8 scope host lo
inet6 ::1/128 scope host
inet 192.168.10.120/16 scope global eth0
inet6 fe80::f81a:93ff:fe56:f9b4/64 scope link
```

-----

**Report Status:** ✓ Complete  
**Next Review:** Scheduled for next maintenance window  
**Contact:** DevOps Team

-----

*End of Report*