#!/bin/bash

# 本番環境デプロイスクリプト
# 使用方法: ./docker/deploy.sh [version]
# 例: ./docker/deploy.sh v0.1.0

set -e

VERSION=${1:-v0.1.0}
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_ROOT"

echo "=========================================="
echo "Deploying PiedPiper Bot - Version: $VERSION"
echo "=========================================="

# 1. Dockerイメージをビルド
echo ""
echo "[1/5] Building Docker images..."
echo "  - Building bot..."
docker build -t piedpiper-bot:$VERSION -f docker/Dockerfile .

echo "  - Building postgres..."
docker build -t digitart-bot-postgres:$VERSION -f docker/Dockerfile.postgres .

# 2. イメージをtarファイルに保存
echo ""
echo "[2/5] Saving images to tar files..."
mkdir -p docker/images
docker save piedpiper-bot:$VERSION > docker/images/piedpiper-bot.tar
docker save digitart-bot-postgres:$VERSION > docker/images/digitart-bot-postgres.tar

# 3. MicroK8sにイメージをインポート
echo ""
echo "[3/5] Importing images to MicroK8s..."
sudo microk8s ctr images import docker/images/piedpiper-bot.tar
sudo microk8s ctr images import docker/images/digitart-bot-postgres.tar

# 4. K8sマニフェストのイメージタグを更新
echo ""
echo "[4/5] Updating image tags in manifests..."
sed -i "s|image: piedpiper-bot:.*|image: piedpiper-bot:$VERSION|" k8s/piedpiper-bot.yaml
sed -i "s|image: digitart-bot-postgres:.*|image: digitart-bot-postgres:$VERSION|" k8s/postgres.yaml

# 5. Kubernetesにデプロイ
echo ""
echo "[5/5] Deploying to Kubernetes..."
microk8s kubectl apply -f k8s/postgres-secret.yaml
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
