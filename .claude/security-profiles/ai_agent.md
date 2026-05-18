# AI Agent Security Profile

## Threat Model
AI agents operating with tool access face direct prompt injection (malicious user messages crafted to hijack agent behavior) and indirect prompt injection (adversarial content in tool outputs or external data sources). Tool scope creep allows agents to invoke capabilities beyond their declared purpose. Capability escalation chains multiple tool calls to reach resources the agent was not intended to access. System prompt leakage exposes internal instructions to users. SSRF via tool calls lets the agent be directed to fetch internal or cloud-metadata URLs. Output trust boundary violations occur when tool outputs are trusted and acted upon without validation, enabling second-order injections.

## Architect Checklist
- [ ] Tool permission scoping enforced at the agent level — each tool declares a capability set and the agent runtime refuses calls outside that set (least capability principle)
- [ ] System prompt treated as confidential; instructions to reveal the system prompt must be refused by design, not just by prompt instruction
- [ ] All tool outputs parsed against a strict schema before the agent acts on them; free-text tool outputs not interpolated into subsequent prompts verbatim
- [ ] SSRF prevention on all tool-invoked URLs: allowlist of permitted hosts/schemes, block access to link-local and metadata addresses (169.254.x.x, fd00::/8, etc.)
- [ ] Agent action logs (tool calls + parameters + outputs) retained for audit and anomaly detection

## Review Checklist
- [ ] Tools cannot exceed their declared capability scope — verify no tool grants filesystem, network, or shell access beyond what is documented and reviewed
- [ ] User input does not override system prompt directives; test with common injection phrases ("ignore previous instructions", "you are now DAN")
- [ ] Tool outputs parsed and validated before further use — no raw tool output string passed as a prompt instruction
- [ ] Sensitive data (credentials, PII, internal configs) not present in agent-visible context unless strictly necessary; context minimization reviewed
- [ ] All privileged tool calls (write, delete, external network) require explicit user confirmation or are rate-limited
