# Hypr-Voice Operations Documentation

Complete operational documentation for deploying, managing, and maintaining Hypr-Voice.

## Documentation Overview

This section provides comprehensive guides for the deployment, operation, and maintenance of Hypr-Voice in production environments.

## Documentation Structure

```
docs/operations/
├── README.md                    # This file
├── deployment.md                # Deployment guide
├── system-requirements.md       # Hardware/software requirements
├── service-management.md        # Service startup/stop/restart
├── monitoring.md                # Health checks and monitoring
├── logging.md                   # Logging configuration
├── backup-recovery.md           # Backup and recovery procedures
├── performance-tuning.md        # Performance optimization
└── security.md                  # Security hardening
```

## Quick Start

### For First-Time Deployment

1. **Review System Requirements**
   - Read [system-requirements.md](system-requirements.md)
   - Verify your environment meets requirements
   - Install dependencies

2. **Deploy Services**
   - Follow [deployment.md](deployment.md)
   - Choose deployment method (local, container, cloud)
   - Configure environment variables

3. **Start Services**
   - Use [service-management.md](service-management.md)
   - Verify all services are healthy
   - Run health checks

4. **Setup Monitoring**
   - Configure [monitoring.md](monitoring.md)
   - Setup alerting
   - Create dashboards

### For Ongoing Operations

- **Service Issues**: Check [service-management.md](service-management.md)
- **Performance**: Review [performance-tuning.md](performance-tuning.md)
- **Security**: Follow [security.md](security.md)
- **Backups**: Use [backup-recovery.md](backup-recovery.md)
- **Logs**: Analyze with [logging.md](logging.md)

## Document Summaries

### [deployment.md](deployment.md)
Complete deployment guide covering:
- Local development deployment
- Containerized deployment (Docker)
- Cloud deployment (AWS, GCP, Azure)
- Production deployment
- Environment configuration
- Troubleshooting deployment issues

### [system-requirements.md](system-requirements.md)
Detailed hardware and software requirements:
- Minimum/recommended/high-performance configurations
- Operating system compatibility
- Network and storage requirements
- Audio subsystem requirements
- GPU requirements (optional)
- Resource estimation

### [service-management.md](service-management.md)
Comprehensive service management:
- Starting/stopping/restarting services
- Systemd integration
- Process management
- Service dependencies
- Auto-start configuration
- Troubleshooting service issues

### [monitoring.md](monitoring.md)
Monitoring and observability:
- Health check endpoints
- Metrics collection (Prometheus)
- Log aggregation (Loki)
- Performance monitoring
- Alerting setup (AlertManager)
- Dashboard creation (Grafana)
- Integration with monitoring tools

### [logging.md](logging.md)
Logging configuration and management:
- Log configuration (Python, YAML)
- Log locations and formats
- Log rotation (logrotate)
- Log analysis techniques
- Centralized logging (ELK, Loki)
- Log retention policies
- Debug logging

### [backup-recovery.md](backup-recovery.md)
Backup and disaster recovery:
- Backup strategies (full, incremental)
- Automated backup scripts
- Cloud backup solutions (S3, GCS, B2)
- Recovery procedures
- Disaster recovery planning
- Backup testing and verification
- Retention policies

### [performance-tuning.md](performance-tuning.md)
Performance optimization guide:
- System-level tuning (kernel, CPU, memory)
- Application-level tuning (FastAPI, Uvicorn)
- Whisper optimization (models, quantization)
- Transcription performance
- TTS performance
- Network optimization
- Memory and CPU optimization
- Performance testing

### [security.md](security.md)
Security hardening procedures:
- API key management
- Network security (firewall, SSL/TLS)
- Application security (input validation, rate limiting)
- Authentication and authorization (JWT, RBAC)
- Data protection (encryption)
- System hardening
- Audit logging
- Vulnerability management
- Compliance (GDPR, SOC 2)

## Common Operational Tasks

### Daily Operations

```bash
# Check service health
./scripts/start_everything.sh status

# Review logs
tail -f /tmp/hybrid-whisper-server.log

# Monitor resources
htop

# Check backups
ls -lh /opt/hypr-voice/backups/
```

### Weekly Operations

```bash
# Review security logs
grep -i "error\|warning" /opt/hypr-voice/logs/*.log

# Test backup restoration
./scripts/test_backup.sh /opt/hypr-voice/backups/latest

# Performance review
./scripts/benchmark.sh
```

### Monthly Operations

```bash
# Update dependencies
pip list --outdated
pip install --upgrade <package>

# Security scan
safety check --file requirements.txt

# Review retention policies
find /opt/hypr-voice/backups -mtime +30 -ls

# Capacity planning
df -h
free -h
```

## Service Ports Reference

| Port | Service | Protocol | Purpose |
|------|---------|----------|---------|
| 9099 | Hybrid Whisper | HTTP/WebSocket | Transcription |
| 9093 | Orchestrator | HTTP/WebSocket | Agent routing |
| 9091 | Context WebSocket | WebSocket | Context management |
| 9095 | Wispr Flow API | HTTP/WebSocket | Cloud transcription |
| 8934 | Web UI Bridge | WebSocket | Proxy service |
| 8933 | Web UI | HTTP | Frontend |
| 9100 | Metrics | HTTP | Prometheus metrics |

## Quick Reference Commands

### Service Management

```bash
# Start all services
./scripts/start_everything.sh start

# Stop all services
./scripts/start_everything.sh stop

# Restart all services
./scripts/start_everything.sh stop && ./scripts/start_everything.sh start

# Check status
./scripts/start_everything.sh status
```

### Health Checks

```bash
# Quick health check
curl http://localhost:9099/health

# All services
for port in 9099 9093 9091 9095; do
    curl http://localhost:$port/health
done
```

### Logs

```bash
# Hybrid server
tail -f /tmp/hybrid-whisper-server.log

# Orchestrator
tail -f /tmp/hypr-voice-orchestrator.log

# Wispr Flow
tail -f logs/wispr_flow.log

# All logs
tail -f /tmp/hypr-voice*.log logs/*.log
```

### Systemd Services

```bash
# Status
sudo systemctl status hypr-voice-hybrid

# Start/Stop/Restart
sudo systemctl start hypr-voice-hybrid
sudo systemctl stop hypr-voice-hybrid
sudo systemctl restart hypr-voice-hybrid

# Logs
sudo journalctl -u hypr-voice-hybrid -f
```

## Troubleshooting Flowchart

```
Service Issue?
    │
    ├─► Check service status
    │   └─► ./scripts/start_everything.sh status
    │
    ├─► Check health endpoints
    │   └─► curl http://localhost:9099/health
    │
    ├─► Check logs
    │   └─► tail -f /tmp/hybrid-whisper-server.log
    │
    ├─► Check resources
    │   ├─► htop (CPU/memory)
    │   ├─► df -h (disk)
    │   └─► netstat -tlnp (ports)
    │
    ├─► Restart service
    │   └─► ./scripts/start_hybrid_server.sh restart
    │
    └─► Check documentation
        └─► Review specific service guide
```

## Best Practices

### Deployment

1. **Environment Separation**
   - Use different `.env` files for dev/staging/prod
   - Never share API keys between environments
   - Use version control for configuration

2. **Incremental Rollout**
   - Test in staging first
   - Monitor closely after deployment
   - Have rollback plan ready

3. **Documentation**
   - Document custom configurations
   - Keep runbooks updated
   - Maintain change log

### Monitoring

1. **Proactive Monitoring**
   - Set up alerts before incidents occur
   - Monitor trends, not just thresholds
   - Review dashboards regularly

2. **Log Management**
   - Use structured logging (JSON)
   - Include correlation IDs
   - Centralize logs for analysis

### Security

1. **Principle of Least Privilege**
   - Use dedicated service accounts
   - Minimize API key scopes
   - Rotate credentials regularly

2. **Defense in Depth**
   - Multiple security layers
   - Assume breach mentality
   - Regular security audits

### Backup

1. **3-2-1 Rule**
   - 3 copies of data
   - 2 different media types
   - 1 offsite backup

2. **Test Restorations**
   - Regular restore drills
   - Verify backup integrity
   - Document recovery procedures

## Support and Resources

### Documentation

- [Main Documentation](../README.md)
- [API Reference](../api/API_REFERENCE.md)
- [Development Guide](../development/ARCHITECTURE.md)

### Community

- GitHub Issues: Report bugs and feature requests
- Discussions: Ask questions and share knowledge

### Professional Support

For enterprise support, custom integrations, or consulting services, please contact the maintainers.

## Changelog

### 2024-01-26
- Initial operations documentation
- Complete deployment guide
- Service management documentation
- Monitoring and logging setup
- Backup and recovery procedures
- Performance tuning guide
- Security hardening procedures

## Contributing

To improve the operations documentation:

1. Update the relevant markdown file
2. Add examples and use cases
3. Test procedures in actual environment
4. Submit pull request with changes

## License

This documentation is part of the Hypr-Voice project and follows the same license.

---

**Last Updated**: 2024-01-26
**Version**: 0.2.0
**Maintainer**: Hypr-Voice Team
