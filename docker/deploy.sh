#!/bin/bash

# PiedPiper Bot デプロイスクリプト
# TARファイルを生成せず、パイプでイメージを直接MicroK8sにインポート
# 使用方法: ./docker/deploy.sh [version]
# 例: ./docker/deploy.sh v0.1.2

set -e

VERSION=${1:-v0.1.2}
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_ROOT"

echo "=========================================="
echo "Deploying PiedPiper Bot - Version: $VERSION"
echo "=========================================="

# 1. ディスク容量チェック
echo ""
echo "[1/6] Checking disk space..."
AVAILABLE_SPACE=$(df /var/lib/docker 2>/dev/null | awk 'NR==2 {print $4}' || df . | awk 'NR==2 {print $4}')
REQUIRED_SPACE=$((2 * 1024 * 1024))  # 2GB in KB

if [ "$AVAILABLE_SPACE" -lt "$REQUIRED_SPACE" ]; then
  echo "⚠ Warning: Low disk space available ($(($AVAILABLE_SPACE / 1024 / 1024))GB)"
  echo "  Cleaning up old Docker resources and TAR files..."
  
  # 古いTARファイルを削除
  rm -f docker/images/*.tar 2>/dev/null || true
  
  # 古いDockerイメージをプルーニングするREMOTE
  docker system prune -af --filter "until=72h" 2>/dev/null || true
fi

# 2. Dockerイメージをビルド
echo ""
echo "[2/6] Building Docker images..."
echo "  - Building PiedPiper Bot..."
docker build -t piedpiper-bot:$VERSION -t piedpiper-bot:latest -f docker/Dockerfile .

echo "  - Building PostgreSQL..."
docker build -t digitart-bot-postgres:$VERSION -t digitart-bot-postgres:latest -f docker/Dockerfile.postgres .

# 3. MicroK8sにイメージをインポート（パイプで直接ストリーム）
echo ""
echo "[3/6] Importing images to MicroK8s (streaming via pipe)..."
echo "  - Loading PiedPiper Bot image..."
docker save piedpiper-bot:$VERSION piedpiper-bot:latest | microk8s ctr images import - 2>/dev/null || \
  docker save piedpiper-bot:$VERSION piedpiper-bot:latest | sudo microk8s ctr images import -

echo "  - Loading PostgreSQL image..."
docker save digitart-bot-postgres:$VERSION digitart-bot-postgres:latest | microk8s ctr images import - 2>/dev/null || \
  docker save digitart-bot-postgres:$VERSION digitart-bot-postgres:latest | sudo microk8s ctr images import -

# 4. K8sマニフェストのイメージタグを更新
echo ""
echo "[4/6] Updating image tags in manifests..."
if [ -f k8s/piedpiper-bot.yaml ]; then
  sed -i "s|image: piedpiper-bot:.*|image: piedpiper-bot:$VERSION|" k8s/piedpiper-bot.yaml
  echo "  ✓ Updated piedpiper-bot.yaml"
fi

if [ -f k8s/postgres.yaml ]; then
  sed -i "s|image: digitart-bot-postgres:.*|image: digitart-bot-postgres:$VERSION|" k8s/postgres.yaml
  echo "  ✓ Updated postgres.yaml"
fi

# 5. Kubernetesにデプロイ
echo ""
echo "[5/6] Deploying to Kubernetes..."
echo "  - Applying Secret..."
if [ -f k8s/postgres-secret.yaml ]; then
  microk8s kubectl apply -f k8s/postgres-secret.yaml
fi

echo "  - Applying Persistent Volumes..."
if [ -f k8s/pv-pvc.yaml ]; then
  microk8s kubectl apply -f k8s/pv-pvc.yaml
fi

echo "  - Applying PostgreSQL..."
if [ -f k8s/postgres.yaml ]; then
  microk8s kubectl apply -f k8s/postgres.yaml
fi

echo "  - Applying Bot Deployment..."
if [ -f k8s/piedpiper-bot.yaml ]; then
  microk8s kubectl apply -f k8s/piedpiper-bot.yaml
fi

# 6. Pod の確認と再起動
echo ""
echo "[6/6] Verifying deployment..."
echo "  - Rolling restart deployments..."
for deployment in piedpiper-bot digitart-bot-postgres; do
  DEPLOY_EXIST=$(microk8s kubectl get deployment $deployment 2>/dev/null | tail -1 || echo "")
  if [ ! -z "$DEPLOY_EXIST" ]; then
    echo "  - Restarting $deployment..."
    microk8s kubectl rollout restart deployment/$deployment
  fi
done

echo ""
echo "Waiting for rollouts to complete..."
for deployment in piedpiper-bot digitart-bot-postgres; do
  DEPLOY_EXIST=$(microk8s kubectl get deployment $deployment 2>/dev/null | tail -1 || echo "")
  if [ ! -z "$DEPLOY_EXIST" ]; then
    microk8s kubectl rollout status deployment/$deployment --timeout=5m 2>/dev/null || {
      echo "⚠ Timeout or deployment not found: $deployment"
    }
  fi
done

# デプロイ完了
echo ""
echo "=========================================="
echo "✅ Deployment completed successfully!"
echo "=========================================="
echo ""
echo "Deployed images (Version: $VERSION):"
echo "  - piedpiper-bot:$VERSION"
echo "  - digitart-bot-postgres:$VERSION"
echo ""
echo "Next steps:"
echo "  1. Check deployment status:"
echo "     microk8s kubectl get pods"
echo "     microk8s kubectl get deployments"
echo ""
echo "  2. View logs:"
echo "     microk8s kubectl logs -f deployment/piedpiper-bot"
echo "     microk8s kubectl logs -f deployment/digitart-bot-postgres"
echo ""
echo "  3. Clean up old Docker resources (optional):"
echo "     docker system prune -a"
echo ""
echo "=========================================="
microk8s kubectl apply -f k8s/pv-pvc.yaml
microk8s kubectl apply -f k8s/postgres.yaml

echo "  Waiting for PostgreSQL to be ready..."
microk8s kubectl wait --for=condition=ready pod -l app=postgres --timeout=90s

microk8s kubectl apply -f k8s/piedpiper-bot.yaml

# Bot pod を再起動（イメージ更新を反映）
microk8s kubectl rollout restart deployment/piedpiper-bot

echo ""
echo "=========================================="
echo "Deployment completed successfully!"
echo "=========================================="
echo ""
echo "Deployed images:"
echo "  - piedpiper-bot:$VERSION"
echo "  - digitart-bot-postgres:$VERSION"
echo ""
echo "Check deployment status:"
echo "  microk8s kubectl get pods"
echo "  microk8s kubectl get services"
