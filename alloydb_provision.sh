#!/bin/bash
# 🛠️ AlloyDB Cluster & Instance 생성 스크립트

GCLOUD_BIN="/Users/jungwoonlee/google-cloud-sdk/bin/gcloud"
PROJECT_ID="jwlee-argolis-202104"
VPC_NAME="jwlee-vpc-001"
USER_IP="210.207.40.218"
DB_PASSWORD="DefaultSearch_1234" # 테스트용 비밀번호 (지정 가능)

echo "=== 🚀 [AlloyDB 프로비저닝 가동] ==="
$GCLOUD_BIN config set project $PROJECT_ID

# 1. 클러스터 생성 (이미 생성됨)
# echo "\n[1/2] Creating AlloyDB Cluster (alloydb-search-cluster)..."
# $GCLOUD_BIN alloydb clusters create alloydb-search-cluster \
#     --region=asia-northeast3 \
#     --network=$VPC_NAME \
#     --password=$DB_PASSWORD

# 2. 인스턴스 생성
echo "\n[2/2] Creating Primary Instance with Public IP (alloydb-search-instance)..."
$GCLOUD_BIN alloydb instances create alloydb-search-instance \
    --cluster=alloydb-search-cluster \
    --region=asia-northeast3 \
    --instance-type=PRIMARY \
    --cpu-count=2 \
    --assign-inbound-public-ip=ASSIGN_IPV4 \
    --authorized-external-networks=$USER_IP/32 \
    --database-flags=password.enforce_complexity=on \
    --availability-type=ZONAL

echo "\n=== 🎉 인프라 생성 부트스트랩 완료! ==="
echo "Host IP는 생성 이후 Google Cloud Console 혹은 gcloud alloydb instances describe 로 확인 가능합니다."
