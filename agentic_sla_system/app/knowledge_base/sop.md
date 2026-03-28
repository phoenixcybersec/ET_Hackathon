# Standard Operating Procedures (SOP) — IT Helpdesk

## SOP-001: Network Connectivity Issue
**Category:** Network
**Steps:**
1. Verify physical cable or WiFi connection
2. Ping gateway: `ping 192.168.1.1`
3. Flush DNS: `ipconfig /flushdns`
4. Restart network adapter
5. If unresolved → escalate to Network Team
**SLA:** Resolution within 4 hours for Critical, 8 hours for High

## SOP-002: VPN Not Working
**Category:** Network
**Steps:**
1. Check VPN client version (must be >= 5.0)
2. Clear VPN cache and reconnect
3. Verify user credentials in Active Directory
4. Check firewall rules for VPN port 1194/443
5. If unresolved → escalate to IT Security Team
**SLA:** Resolution within 2 hours (business critical)

## SOP-003: Software Not Responding / Crash
**Category:** Software
**Steps:**
1. Restart the application
2. Clear application cache
3. Check for pending OS updates
4. Reinstall if crash persists
5. Collect crash logs from Event Viewer
**SLA:** Resolution within 6 hours

## SOP-004: Hardware Failure (Laptop/Desktop)
**Category:** Hardware
**Steps:**
1. Run hardware diagnostics
2. Check for overheating — clean vents
3. Test with external peripherals disconnected
4. If HDD failure → initiate backup immediately
5. Raise replacement request if beyond repair
**SLA:** Replacement within 24 hours for Critical users

## SOP-005: Access / Permission Issue
**Category:** Access
**Steps:**
1. Verify user role in Active Directory
2. Check group policy assignments
3. Re-apply permissions via admin console
4. If MFA issue → reset MFA token
**SLA:** Resolution within 1 hour

## SOP-006: Product / Physical Damage
**Category:** Hardware
**Steps:**
1. Document damage with photos
2. Check warranty status
3. Raise insurance/replacement claim
4. Provide temporary device if available
**SLA:** Resolution within 48 hours