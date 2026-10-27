# ECS 发布操作

使用 Node.js 24、NestJS/TypeScript、React/Vite 与 RDS MySQL 8。一个镜像同时服务静态前端和 `/api/v1`；Docker 端口仅绑定 `127.0.0.1:3000`，HTTPS 由宿主机 nginx 提供。

## 私密运行配置

`/opt/histree/runtime.env` 应为 0600，目录为 0700，字段见 [配置模板](mysql-runtime.env.example)。数据库、模型与签名凭据只存在运行环境，不进入 Git、Docker build args 或公开 artifact。ECS 使用 RDS 内网 host。无 Supabase 运行配置，无网页登录／管理后台。

## CI 与发布

PR 和部署共用 `application-checks.yml`：冻结安装、前后端 build/lint、回归、隔离 MySQL、旧 SQL 兼容、内容守卫、实际 linux/amd64 镜像验证。当前运行路径见 [架构](../../docs/DEPLOYMENT.md)。

main 发布需要仓库变量 `ECS_DEPLOY_ENABLED=true`、`ECS_INSTANCE_ID`、`ECS_REGION`，以及 `ecs-production` 环境 secret `WORKBENCH_CONFIG`。数据库及模型凭据保留在宿主机，runner 不需要它们。旧 `VITE_SUPABASE_*` 与 `VITE_ASK_API_URL` 仓库变量／secrets 不再被工作流读取。

ECS 从短期签名地址下载七文件 artifact：`image.tar.gz`、`image.tar.gz.sha256`、`compose.yml`、`release.sh`、`verify.mjs`、`release-manifest.json`、`cleanup-releases.py`。下载后验证 artifact digest 和精确文件清单；GitHub token 不发送到 ECS。artifact 保留七天。ECS 在发布验收成功后保留当前版本和最近两个不同提交的成功回滚版本；三份镜像归档校验通过才清理更早的应用镜像与大归档。

`release.sh` 取得独占锁，检查 image 架构/revision 与实际 dsh runtime，启动后验证 MySQL 就绪、SPA 深链接、长卷 SHA-256、公开接口及停用路径。切换验收失败恢复旧镜像；成功后原子更新 `/opt/histree/current-release`。脚本不编辑 nginx、证书或 runtime.env；部署会结束内存中的对话与游戏。

```sh
# repo 为当前已审阅的提交；构建时只传公开 revision。
docker build --platform linux/amd64 -f apps/api/Dockerfile \
  --build-arg HISTREE_REVISION=<40位提交哈希> -t histree-api:<40位提交哈希> .
# 正常生产发布使用 Actions 完整 artifact，再在 ECS 执行：
bash <release>/release.sh /opt/histree/releases/<release-id> histree-api:<40位提交哈希>
```

回滚应用时使用前一 release 的 `.image` 和 `compose.yml`。数据库 schema 更新与史料发布各自独立授权和验证，不随应用自动执行。源库切换档案见 [MySQL 迁移](../../docs/MYSQL_MIGRATION.md)。

## nginx 与域名

当前 IP 网关完整代理应用。初始化脚本 `https-setup.sh` 仅用于没有现有 vhost 的新主机；`open-ip-frontend.sh` 仅适配旧 IP 网关，已开放的网关不需重复执行。域名证书安装脚本保留 pending／serve 两种模式，应用发布不能替用户改变备案状态。生产 TLS 状态以宿主机实际配置与公网验收为准。

## Installing an issued Alibaba Cloud certificate

Download the **Nginx (pem/key)** package. Run the installer on ECS with the PEM full chain and matching private key, keeping them outside Git and Docker images:

```sh
bash deploy/ecs/install-domain-certificate.sh histree.wiki /private/path/fullchain.pem /private/path/private.key
```

The script verifies hostname, expiry, trust chain and key match, installs a private versioned directory under `/opt/histree/tls/histree.wiki/`, and configures `/etc/nginx/conf.d/histree-domain.conf`. It validates nginx and waits for new workers before checking TLS without disabling certificate verification. Failure restores the previous domain vhost. The existing IP gateway and its certificate remain intact. The IP vhost must use `listen 443 ssl default_server;`: literal-IP TLS clients may omit SNI, and otherwise the earlier domain vhost can serve the wrong certificate. The installer checks this prerequisite before making changes. The IP homepage now serves the combined application; the separate pending domain homepage remains 503 until domain publication is enabled.

Default `pending` mode returns HTTP 503 with the ICP filing pending message. After filing/access readiness and publication authorization, pass `serve` as the fourth argument using the installed full chain and key paths. Configure the ECS AI Origin before public acceptance testing. Temporary upload copies can be removed after installation; preserve the active version for rollback.

As of 2026-10-08, the Alibaba Cloud certificate is installed and valid until **2027-01-06 07:59:59 Asia/Shanghai**. Server-side verification by normal domain resolution succeeded; public TLS handshakes from the current network failed, so public reachability is unverified. Root-domain nginx is in `pending` mode; the certificate also covers www, whose DNS/vhost setup is not part of this cutover.

Renew/reissue this certificate through Alibaba Cloud and rerun the installer before expiry. The existing Certbot timer renews the IP certificate only. Do not run `domain-setup.sh` over the imported domain certificate.

## Existing IP frontend gateway

The IP entry point `https://123.56.189.146/` serves the full frontend and regular `/api/v1` routes. To enable it on the existing Histree IP vhost:

```sh
bash deploy/ecs/open-ip-frontend.sh 123.56.189.146
```

The script checks the application build, saves the previous IP nginx configuration in `/opt/histree/nginx-backups/`, replaces only the old homepage 404 rule with an application proxy, retains existing AI routes and access logs, and validates TLS/deep links with bounded reload waits. It restores the backup on failure. The signed anonymous AI boundary remains enforced. The independent domain vhost stays in pending mode.

ECS `HISTREE_AI_ALLOWED_ORIGINS` includes the IP and approved domain origins. Do not put gateway or model secrets in the browser.

## HTTPS without a domain

Let's Encrypt supports short-lived public-IP certificates. The host needs nginx, Python 3.11, and Certbot 5.4+ in `/opt/histree/certbot`. After explicitly authorizing public TCP 80/443 in the ECS security group, run `bash deploy/ecs/https-setup.sh <public-ip>` on the host. It creates only the Histree nginx configuration and a twice-daily renewal timer. The API stays bound to loopback; nginx serves the combined frontend/API and preserves the ask/status and guessing-game locations. Application releases never edit nginx; certificate and renewal settings are preserved. Set `TRUST_PROXY=1` in the private runtime environment and redeploy the API.

Check `systemctl list-timers histree-certbot.timer`, run `/opt/histree/certbot/bin/certbot renew --dry-run`, and verify the HTTPS origin from the gateway. Six-day IP certificates require working automatic renewal. See https://letsencrypt.org/2026/03/11/shorter-certs-certbot .

## 发布文件保留策略

保留三个不同提交的镜像、`image.tar.gz`、校验和、compose 与 manifest。重复尝试同一提交不占用回滚名额。所有容器引用的镜像（包括已停止任务）、非标准应用镜像、数据库、配置、证书、迁移备份与小型历史元数据均保留；不运行 Docker prune。

`cleanup-releases.py` 默认只读，持有与部署相同的锁；`--apply` 才执行。清理前校验回滚归档哈希、镜像 revision/架构、当前指针与容器状态；每次删除前检查目标未变化。仅删除标准 release 目录中的旧 `image.tar.gz` 与重复 `bundle.zip`，以及没有容器引用的旧 `histree-api:<revision>` 镜像。保留版本的 ZIP 在 TAR 校验后也可删除。三份可用回滚版本不足或校验不通过时停止，不自动缩减保留数量。

清单与逐步结果写入宿主机 `cleanup-audits/`；清理后复核容器身份、启动时间和 MySQL 健康。清理失败会使发布任务报告失败，但不会回滚已验收的新应用。失败发布不会触发清理。更早的构建不再提供本机即时回滚，需要从对应提交重建。

```sh
python3 <release>/cleanup-releases.py                  # 只读清单及 plan_sha256
python3 <release>/cleanup-releases.py --apply --expect-plan <plan_sha256>
```
