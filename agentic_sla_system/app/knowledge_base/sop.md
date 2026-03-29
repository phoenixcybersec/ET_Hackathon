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

---

## SOP-007: RAM / Memory Utilization Exceeding Threshold
**Category:** Infrastructure / Compute
**Issue Trigger:** EC2 server RAM usage exceeds defined threshold (e.g. > 85%)
**AI Decision:** AUTO-FIX (confidence >= 0.85) | ESCALATE (confidence < 0.85)
**Steps:**
1. Detect RAM utilization alert from Grafana/Prometheus
2. Verify current EC2 instance type via AWS CLI
3. Stop the EC2 instance gracefully
4. Modify instance type to next tier in scale-up map:
   - t3.medium → t3.large
   - t3.large → t3.xlarge
   - t3.xlarge → t3.2xlarge
   - t3.2xlarge → ESCALATE (already at max)
5. Start the EC2 instance and wait for running state
6. Verify new public IP and SSH connectivity
7. Confirm RAM headroom: `free -h`
8. Update ticket with new instance type and resolution details

**Script:** `ec2_scale_up_ram.sh` (AWS CLI — stop → modify → start)
**Execution Method:** AWS CLI using IAM Access Key + Secret Key
**Rollback:** Re-run with original instance type as TARGET_INSTANCE_TYPE
**SLA:** Response: 15 min | Resolution: 1 hr
**Breach Penalty:** Rs.15,000 per breach

---

## SOP-008: Storage / Disk Volume Exceeding Threshold
**Category:** Infrastructure / Storage
**Issue Trigger:** EC2 disk usage exceeds defined threshold (e.g. > 80%)
**AI Decision:** AUTO-FIX (confidence >= 0.85) | ESCALATE (confidence < 0.85)
**Steps:**
1. Detect storage utilization alert from Grafana/Prometheus
2. Create a new EBS gp3 volume (default: 50GB) in the same AZ as EC2
3. Wait for volume to become available
4. Attach volume to EC2 instance at device `/dev/xvdf`
5. Wait for volume to show as in-use
6. SSH into EC2 instance
7. Format the new volume: `sudo mkfs -t ext4 /dev/xvdf`
8. Create mount point and mount: `sudo mount /dev/xvdf /mnt/data`
9. Persist mount in `/etc/fstab` with `nofail` flag
10. Verify with `df -h` and `lsblk`
11. Update ticket with volume ID and mount point

**Script Part 1:** `ebs_create_attach.sh` (AWS CLI — create → attach)
**Script Part 2:** `ebs_mount.sh` (SSH on EC2 — mkfs → mount → fstab)
**Execution Method:** AWS CLI + SSH using IAM credentials and PEM key
**Rollback:** Detach and delete volume via AWS CLI if mount fails
**SLA:** Response: 15 min | Resolution: 2 hrs
**Breach Penalty:** Rs.10,000 per breach

---

## SOP-009: Pod Resource Request Increase (Minikube on EC2)
**Category:** Kubernetes / Application
**Issue Trigger:** Pod CPU/memory requests are too low causing throttling or eviction
**AI Decision:** AUTO-FIX (confidence >= 0.80) | HUMAN-REVIEW (confidence < 0.80)
**Steps:**
1. Detect pod resource issue from ticket (throttling, OOMKilled, eviction)
2. Extract deployment name and namespace from ticket fields
3. SSH into EC2 production server
4. Fetch current resource config:
   `kubectl get deployment <name> -n <ns> -o jsonpath="{.spec.template.spec.containers[*].resources}"`
5. Patch deployment with new resource requests and limits:
   `kubectl patch deployment <name> -n <ns> --type='json' -p='[...]'`
6. Wait for rollout to complete:
   `kubectl rollout status deployment/<name> -n <ns> --timeout=120s`
7. Verify pod status and resource config
8. Confirm pod is Running and not throttled
9. Update ticket with patched values

**Default Resource Values (overridden by ticket if specified):**
- CPU Request: 500m | CPU Limit: 1000m
- Memory Request: 512Mi | Memory Limit: 1Gi

**Script:** `patch_pod_resources.sh` (kubectl patch via SSH)
**Execution Method:** SSH into EC2 using PEM key → kubectl on Minikube
**Rollback:** `kubectl rollout undo deployment/<name> -n <namespace>`
**SLA:** Response: 30 min | Resolution: 2 hrs
**Breach Penalty:** Rs.5,000 per breach