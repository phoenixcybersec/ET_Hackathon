# SLA Rules — Phoenix IT Helpdesk

## Priority Definitions

| Priority | Response Time | Resolution Time | Example Issues |
|----------|--------------|-----------------|----------------|
| Critical | 15 minutes   | 2 hours         | Server down, full outage, data loss |
| High     | 30 minutes   | 4 hours         | VPN down, email not working, key system slow |
| Medium   | 2 hours      | 8 hours         | Software crash, printer issue, slow internet |
| Low      | 4 hours      | 24 hours        | Password reset, minor UI bug, general query |

## SLA Breach Rules
- If ticket is unresolved beyond resolution time → auto-escalate to Team Lead
- If ticket is unresolved beyond 2x resolution time → escalate to Department Head
- Critical tickets unresolved > 2 hours → page on-call engineer immediately

## Team Routing Rules
- **Network issues** → IT Team
- **Software/App issues** → IT Team
- **Hardware/Device issues** → IT Team + Procurement
- **Access/Permissions** → IT Security Team
- **Customer complaints** → Customer Care Team
- **Billing/Payments** → Finance Team

## Cost Impact
- Each SLA breach costs ₹5,000 in penalty per ticket (enterprise clients)
- Critical SLA breach → ₹25,000 penalty + escalation report required
- Monthly SLA target: 95% tickets resolved within SLA window