#!/bin/sh

# Git 저장소의 최상위 디렉토리로 이동
cd "$(dirname "$0")"

# 1. 모든 변경사항 스테이징
git add .

# 2. 커밋 메시지 입력받기
echo "커밋 메시지를 입력하세요:"
read commit_message

# 입력된 메시지가 비어있는지 확인
if [ -z "$commit_message" ]; then
    echo "커밋 메시지가 비어있어 커밋을 취소합니다."
    exit 1
fi

# 3. 커밋 생성
# -m 옵션에 변수를 직접 전달하여 여러 줄을 처리
git commit -m "$commit_message"

# 4. 원격 저장소에 푸시
echo "원격 저장소에 푸시합니다..."
git push

echo "업로드가 완료되었습니다."
