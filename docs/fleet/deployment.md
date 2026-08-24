# Deployment

Docker Compose: set `SHIFTIQ_MCP_API_KEY`, then run `docker compose --profile fleet up --build mcp`. The optional service is non-root, capability-dropped, read-only except its workspace volume/tmpfs, resource-limited, and exposes readiness/liveness endpoints. Put a trusted TLS proxy/load balancer in front of port 8001.

Kubernetes: adapt `deploy/kubernetes/shiftiq-mcp.yaml`, create the `shiftiq-mcp` Secret, publish the image, and configure an HTTPS Ingress. Use network policy/egress control, encrypted persistent storage, secret rotation, and one replica unless operation storage is moved to a shared transactional backend.

AWS is optional: the same container can run on ECS/Fargate or EKS behind an HTTPS ALB with Secrets Manager and encrypted EFS/EBS. No AWS service is required by ShiftIQ.

Fleet self-hosting is currently account-gated/Beta; contact LangChain for production readiness and BYOC/self-hosted topology. This repository deploys ShiftIQ MCP independently of where Fleet runs.
