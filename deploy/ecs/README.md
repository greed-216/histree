# ECS deployment: frontend + API

Build `apps/api/Dockerfile` for `linux/amd64` with public build arguments `VITE_SUPABASE_URL` and `VITE_SUPABASE_ANON_KEY`, then `docker save | gzip`. This single image contains the React frontend and NestJS API. NestJS serves the frontend from `/app/apps/web/dist` via `HISTREE_WEB_ROOT`; browser routes use `/` and application requests use `/api/v1`. Database and authentication remain on Supabase. The deployed AI gateway on Supabase retains identity and quota enforcement. The ECS host loads this archive without contacting Docker Hub.

Runtime configuration lives only at `/opt/histree/runtime.env` (directory 0700, file 0600):

- SUPABASE_URL / SUPABASE_ANON_KEY
- DEEPSEEK_API_KEY
- HISTREE_ASK_ENABLED=true
- HISTREE_MODEL=deepseek-flash
- HISTREE_GATEWAY_SECRET: shared only with the Supabase ai-gateway function
- NODE_ENV=production / PORT=3000

Do not upload the Supabase service-role key. Do not commit runtime configuration or include it in an image/artifact.

Each release directory contains `image.tar.gz`, its `sha256sum` file, `compose.yml`, and `release.sh`. Run `bash release.sh /opt/histree/releases/<release> histree-api:<commit>` on the server. The script validates the archive, runs the actual dsh/MCP smoke test, replaces the Histree application, waits for frontend and API health, and restores the previous image on startup failure. It retains old release archives for rollback; monitor disk usage. In-memory conversations reset on deploy.

Port 3000 is bound to loopback. Public access requires an HTTPS reverse proxy. Set `TRUST_PROXY=1` only behind one trusted proxy which overwrites forwarded headers.

## GitHub Actions

`deploy-api.yml` builds/tests both applications on relevant pushes to main or manual dispatch. `deploy.yml` keeps GitHub Pages available only by manual dispatch. Artifacts expire after seven days.

Configure repository variables:

- ECS_INSTANCE_ID: target ECS instance
- ECS_REGION: cn-beijing
- ECS_DEPLOY_ENABLED: true (enable only after a manual production test)

Configure the `ecs-production` environment secret `WORKBENCH_CONFIG` with a dedicated Workbench profile JSON. Prefer a RAM identity scoped to the deployment instance; do not use an account administrator key. Keep DeepSeek and Supabase credentials on the server; the workflow never needs them.

The workflow creates a fresh directory on each run. ECS downloads the tested GitHub artifact through a short-lived signed URL; the GitHub token stays on the runner. Before extraction it verifies the artifact digest and exact file list, then checks the image and deploys the exact commit tag. This avoids slow or timed-out runner-to-OSS uploads. Deployments are serialized and never canceled halfway through a release. Protect main and review workflow edits because production deployment credentials are available to this workflow.

Browsers call Supabase `ai-gateway`; the ECS URL and shared secret exist only in server configuration. Follow [AI gateway deployment](../../docs/AI_GATEWAY.md) for migration, function secrets, cutover and verification.

## histree.wiki

1. The existing Beijing ECS public address is `123.56.189.146` (verify before reuse). Complete ICP filing/access requirements before serving the domain from mainland China.
2. At the DNS provider, point the root `@` A record to the target ECS public IP. Remove conflicting parking/AAAA records if they point elsewhere. Allow public TCP 80/443; keep port 3000 on loopback.
3. Build with the same public Supabase URL/anonymous key used by the frontend. Never pass service-role, gateway or model credentials as build arguments.
4. Deploy the combined application with `release.sh`. Verify the frontend and API on loopback before adding the domain.
5. Use the issued Alibaba Cloud Nginx certificate with `install-domain-certificate.sh` as documented below. Use default `pending` mode during ICP filing, and `serve` only after filing/access readiness and publication authorization. The existing IP gateway is preserved. `domain-setup.sh` is a separate Let's Encrypt alternative for domains without an imported certificate; do not run it over the installed Alibaba Cloud certificate.
6. Add `https://histree.wiki` to the Supabase `ai-gateway` secret `HISTREE_ALLOWED_ORIGINS`, retaining existing allowed origins. Add the new origin to Supabase Auth Site URL/redirect configuration if using email/OAuth links. Do not disable gateway identity or quotas.
7. Verify root/deep links, static assets, public records, AI status and login at `https://histree.wiki`. Missing `/api/v1` routes and missing assets must return 404, rather than the frontend shell.

Example build (variables contain only public browser configuration):

```sh
docker build --platform linux/amd64 -f apps/api/Dockerfile \
  --build-arg VITE_SUPABASE_URL --build-arg VITE_SUPABASE_ANON_KEY \
  -t histree-api:<release> .
```

The frontend is immutable per release: changing public build configuration requires a rebuild. Server-only configuration stays in `/opt/histree/runtime.env`. Local Vite and manual Pages builds retain the `/histree/` base unless `VITE_BASE_PATH=/` is specified.

## Installing an issued Alibaba Cloud certificate

Download the **Nginx (pem/key)** package. Run the installer on ECS with the PEM full chain and matching private key, keeping them outside Git and Docker images:

```sh
bash deploy/ecs/install-domain-certificate.sh histree.wiki /private/path/fullchain.pem /private/path/private.key
```

The script verifies hostname, expiry, trust chain and key match, installs a private versioned directory under `/opt/histree/tls/histree.wiki/`, and configures `/etc/nginx/conf.d/histree-domain.conf`. It validates nginx and waits for new workers before checking TLS without disabling certificate verification. Failure restores the previous domain vhost. The existing IP gateway and its certificate remain intact.

Default `pending` mode returns HTTP 503 with the ICP filing pending message. After filing/access readiness and publication authorization, pass `serve` as the fourth argument using the installed full chain and key paths. Configure the Supabase gateway Origin and applicable Auth callbacks before public acceptance testing. Temporary upload copies can be removed after installation; preserve the active version for rollback.

As of 2026-10-08, the Alibaba Cloud certificate is installed and valid until **2027-01-06 07:59:59 Asia/Shanghai**. Server-side verification by normal domain resolution succeeded; public TLS handshakes from the current network failed, so public reachability is unverified. Root-domain nginx is in `pending` mode; the certificate also covers www, whose DNS/vhost setup is not part of this cutover.

Renew/reissue this certificate through Alibaba Cloud and rerun the installer before expiry. The existing Certbot timer renews the IP certificate only. Do not run `domain-setup.sh` over the imported domain certificate.

## HTTPS without a domain

Let's Encrypt supports short-lived public-IP certificates. The host needs nginx, Python 3.11, and Certbot 5.4+ in `/opt/histree/certbot`. After explicitly authorizing public TCP 80/443 in the ECS security group, run `bash deploy/ecs/https-setup.sh <public-ip>` on the host. It creates only the Histree nginx configuration and a twice-daily renewal timer. The API stays bound to loopback; nginx exposes only the ask and status routes plus the three guessing-game endpoints (`guess/status`, `guess/start`, `guess/act`). Existing gateways receive these exact game routes during a release; certificate and renewal settings are preserved. Set `TRUST_PROXY=1` in the private runtime environment and redeploy the API.

Check `systemctl list-timers histree-certbot.timer`, run `/opt/histree/certbot/bin/certbot renew --dry-run`, and verify the HTTPS origin from the gateway. Six-day IP certificates require working automatic renewal. See https://letsencrypt.org/2026/03/11/shorter-certs-certbot .
