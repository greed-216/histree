# ECS deployment

Build `apps/api/Dockerfile` for `linux/amd64`, then `docker save | gzip`. The ECS host loads this archive without contacting Docker Hub.

Runtime configuration lives only at `/opt/histree/runtime.env` (directory 0700, file 0600):

- SUPABASE_URL / SUPABASE_ANON_KEY
- DEEPSEEK_API_KEY
- HISTREE_ASK_ENABLED=true
- HISTREE_MODEL=deepseek-flash
- NODE_ENV=production / PORT=3000

Do not upload the Supabase service-role key. Do not commit runtime configuration or include it in an image/artifact.

Each release directory contains `image.tar.gz`, its `sha256sum` file, `compose.yml`, and `release.sh`. Run `bash release.sh /opt/histree/releases/<release> histree-api:<commit>` on the server. The script validates the archive, runs the actual dsh/MCP smoke test, replaces only the Histree API, waits for health, and restores the previous image on startup failure. It retains old release archives for rollback; monitor disk usage. In-memory conversations reset on deploy.

Port 3000 is bound to loopback. Public access requires an HTTPS reverse proxy. Set `TRUST_PROXY=1` only behind one trusted proxy which overwrites forwarded headers. GitHub Pages cannot call a plain HTTP API.

## GitHub Actions

`deploy-api.yml` builds/tests on relevant pushes to main or manual dispatch. Artifacts expire after seven days.

Configure repository variables:

- ECS_INSTANCE_ID: target ECS instance
- ECS_REGION: cn-beijing
- ECS_DEPLOY_ENABLED: true (enable only after a manual production test)

Configure the `ecs-production` environment secret `WORKBENCH_CONFIG` with a dedicated Workbench profile JSON. Prefer a RAM identity scoped to the deployment instance; do not use an account administrator key. Keep DeepSeek and Supabase credentials on the server; the workflow never needs them.

The workflow uploads to a fresh directory on each run, checks the image, and deploys the exact commit tag. Deployments are serialized and never canceled halfway through a release. Protect main and review workflow edits because production deployment credentials are available to this workflow.

After HTTPS is ready, set repository variable `VITE_ASK_API_URL` to `https://<host>/api/v1` and rerun the Pages workflow.

## HTTPS without a domain

Let's Encrypt supports short-lived public-IP certificates. The host needs nginx, Python 3.11, and Certbot 5.4+ in `/opt/histree/certbot`. After explicitly authorizing public TCP 80/443 in the ECS security group, run `bash deploy/ecs/https-setup.sh <public-ip>` on the host. It creates only the Histree nginx configuration and a twice-daily renewal timer. The API stays bound to loopback; nginx exposes only the ask and status routes. Set `TRUST_PROXY=1` in the private runtime environment and redeploy the API.

Check `systemctl list-timers histree-certbot.timer`, run `/opt/histree/certbot/bin/certbot renew --dry-run`, and verify the public HTTPS endpoint before setting `VITE_ASK_API_URL`. Six-day IP certificates require working automatic renewal. See https://letsencrypt.org/2026/03/11/shorter-certs-certbot .
