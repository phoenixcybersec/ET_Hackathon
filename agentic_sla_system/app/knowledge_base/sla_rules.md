# SLA Rules — IT Helpdesk & Infrastructure

## General SLA Policy
- SLA clock starts from the moment a ticket is created in Odoo
- Business hours: 9:00 AM – 6:00 PM IST (Mon–Sat)
- Critical & High priority tickets: 24x7 coverage
- All breaches are logged, reviewed monthly, and penalized as per contract

---

## SLA-001: Network Connectivity Issue
**Category:** Network
**Priority:** High
**Response Time:** 30 minutes
**Resolution Time:** 4 hours (Critical) | 8 hours (High)
**Breach Penalty:** Rs.8,000 per breach
**Escalation Path:** Network Team → IT Manager
**Notes:** If ping to gateway fails after restart, escalate immediately

---

## SLA-002: VPN Not Working
**Category:** Network
**Priority:** Critical
**Response Time:** 15 minutes
**Resolution Time:** 2 hours
**Breach Penalty:** Rs.12,000 per breach
**Escalation Path:** IT Security Team → CISO
**Notes:** Business-critical; remote employees blocked without VPN

---

## SLA-003: Software Not Responding / Crash
**Category:** Software
**Priority:** Medium
**Response Time:** 1 hour
**Resolution Time:** 6 hours
**Breach Penalty:** Rs.5,000 per breach
**Escalation Path:** L1 Support → L2 Software Team
**Notes:** Crash logs from Event Viewer mandatory before escalation

---

## SLA-004: Hardware Failure (Laptop/Desktop)
**Category:** Hardware
**Priority:** High
**Response Time:** 30 minutes
**Resolution Time:** 24 hours (Critical users) | 48 hours (Standard users)
**Breach Penalty:** Rs.10,000 per breach
**Escalation Path:** IT Asset Team → Procurement
**Notes:** Temporary device must be issued within 4 hours for Critical users

---

## SLA-005: Access / Permission Issue
**Category:** Access
**Priority:** High
**Response Time:** 15 minutes
**Resolution Time:** 1 hour
**Breach Penalty:** Rs.7,000 per breach
**Escalation Path:** IT Admin → Active Directory Team
**Notes:** MFA resets require identity verification before action

---

## SLA-006: Product / Physical Damage
**Category:** Hardware
**Priority:** Medium
**Response Time:** 2 hours
**Resolution Time:** 48 hours
**Breach Penalty:** Rs.5,000 per breach
**Escalation Path:** IT Asset Team → Insurance/Vendor
**Notes:** Photos and damage report mandatory; warranty check before claim

---

## SLA-007: RAM / Memory Utilization Exceeding Threshold
**Category:** Infrastructure / Compute
**Priority:** High
**Response Time:** 15 minutes
**Resolution Time:** 1 hour
**Breach Penalty:** Rs.15,000 per breach
**Escalation Path:** AI Agent (AUTO-FIX) → DevOps Engineer → Infrastructure Manager
**Auto-Fix Condition:** AI confidence >= 0.85 → EC2 scale-up executed automatically
**Escalation Condition:** AI confidence < 0.85 OR instance already at max type
**Notes:**
- EC2 will be stopped during resize — expect 3–5 min downtime
- Minikube pods will restart automatically after EC2 comes back up
- Always verify RAM headroom post-fix: `free -h`
- Scale-up map: t3.medium → t3.large → t3.xlarge → t3.2xlarge

---

## SLA-008: Storage / Disk Volume Exceeding Threshold
**Category:** Infrastructure / Storage
**Priority:** High
**Response Time:** 15 minutes
**Resolution Time:** 2 hours
**Breach Penalty:** Rs.10,000 per breach
**Escalation Path:** AI Agent (AUTO-FIX) → DevOps Engineer → Infrastructure Manager
**Auto-Fix Condition:** AI confidence >= 0.85 → New EBS volume created, attached, and mounted
**Escalation Condition:** AI confidence < 0.85 OR AWS API failure
**Notes:**
- New EBS volume: 50GB gp3, mounted at /mnt/data
- Volume tagged with ticket ID for traceability
- fstab updated with `nofail` to prevent boot issues
- Verify post-fix: `df -h` and `lsblk`

---

## SLA-009: Pod Resource Request Increase (Minikube on EC2)
**Category:** Kubernetes / Application
**Priority:** Medium
**Response Time:** 30 minutes
**Resolution Time:** 2 hours
**Breach Penalty:** Rs.5,000 per breach
**Escalation Path:** AI Agent (AUTO-FIX) → DevOps Engineer → Application Owner
**Auto-Fix Condition:** AI confidence >= 0.80 → kubectl patch executed via SSH
**Escalation Condition:** AI confidence < 0.80 OR deployment not found
**Notes:**
- Deployment name must be present in ticket subject or description
- Default values applied if not specified: cpu=500m/1000m, mem=512Mi/1Gi
- Rollout status checked before marking ticket resolved
- Rollback via: `kubectl rollout undo deployment/<name>`

---

## SLA Breach Summary Table

| SLA ID | Issue Type                        | Response | Resolution | Penalty       |
|--------|-----------------------------------|----------|------------|---------------|
| SLA-001 | Network Connectivity             | 30 min   | 4–8 hrs    | Rs.8,000      |
| SLA-002 | VPN Not Working                  | 15 min   | 2 hrs      | Rs.12,000     |
| SLA-003 | Software Crash                   | 1 hr     | 6 hrs      | Rs.5,000      |
| SLA-004 | Hardware Failure                 | 30 min   | 24–48 hrs  | Rs.10,000     |
| SLA-005 | Access / Permission              | 15 min   | 1 hr       | Rs.7,000      |
| SLA-006 | Physical Damage                  | 2 hrs    | 48 hrs     | Rs.5,000      |
| SLA-007 | RAM Utilization High             | 15 min   | 1 hr       | Rs.15,000     |
| SLA-008 | Storage Volume High              | 15 min   | 2 hrs      | Rs.10,000     |
| SLA-009 | Pod Resource Request Increase    | 30 min   | 2 hrs      | Rs.5,000      |