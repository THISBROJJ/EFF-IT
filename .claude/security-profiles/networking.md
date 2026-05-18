# Networking Security Profile

## Threat Model
Network-layer threats include unnecessary open ports that expand the attack surface for service exploitation, TLS misconfiguration (weak cipher suites, expired certificates, TLS 1.0/1.1 support) enabling downgrade and interception attacks, lateral movement once a single host is compromised if the network is flat or overly permissive, gaps in secrets rotation leaving long-lived credentials that can be exploited after a breach, and firewall rule sprawl where rules accumulate over time without review and create unintended access paths.

## Architect Checklist
- [ ] Minimal port exposure: only ports required for the service are opened; all others blocked by default at the security group or firewall level
- [ ] TLS 1.2 minimum enforced on all endpoints; TLS 1.3 preferred where supported; weak cipher suites (RC4, 3DES, NULL, EXPORT) explicitly disabled
- [ ] Secrets rotation schedule defined for all credentials (certificates, API keys, service account passwords) with automated rotation where possible
- [ ] Network segmentation plan documents trust zones; services communicate only with peers they need to reach (microsegmentation or security group rules)
- [ ] Egress filtering defined: outbound traffic restricted to known destinations; unexpected egress is alertable

## Review Checklist
- [ ] No unnecessary open ports — current port exposure documented and justified for each service
- [ ] TLS version and cipher suite configuration documented; tested with a tool such as testssl.sh or SSL Labs
- [ ] All credentials rotated from defaults; no default passwords on network devices, databases, or services
- [ ] Egress filtering rules in place and reviewed; overly broad 0.0.0.0/0 egress rules flagged for justification
- [ ] Firewall and security group rules reviewed for staleness; rules not used in the past 90 days flagged for removal
