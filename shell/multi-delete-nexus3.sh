#!/bin/bash
# 用法: ./delete-nexus-version.sh <repo> <groupId> <artifactId> <version>

if [ $# -ne 4 ]; then
  echo "用法: $0 <repository> <groupId> <artifactId> <version>"
  exit 1
fi

REPO=$1
GROUP=$2
ARTIFACT=$3
VERSION=$4

USER="你的用户名"
PASS="你的密码"
NEXUS_URL="https://repo.td.com"

echo "查找组件: repo=$REPO, group=$GROUP, artifact=$ARTIFACT, version=$VERSION"

# 调用 Nexus Search API 查找所有 componentId
COMPONENTS=$(curl -s -u $USER:$PASS \
  "$NEXUS_URL/service/rest/v1/search?repository=$REPO&group=$GROUP&name=$ARTIFACT&version=$VERSION" \
  | jq -r '.items[].id')

if [ -z "$COMPONENTS" ]; then
  echo "⚠️ 没有找到匹配的 componentId，可能版本号写错或 SNAPSHOT 实际存的是带时间戳的版本。"
  exit 1
fi

for CID in $COMPONENTS; do
  echo "🗑 删除 component: $CID"
  curl -u $USER:$PASS -X DELETE "$NEXUS_URL/service/rest/v1/components/$CID"
done

echo "✅ 删除完成"