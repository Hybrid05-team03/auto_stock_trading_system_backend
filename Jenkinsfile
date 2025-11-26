pipeline {
    agent { label 'web' }

    environment {
        // 1. Jenkins Credentials에서 값을 꺼내 환경 변수로 설정
        KIS_APP_KEY_REAL = credentials('KIS_APP_KEY_REAL')
        KIS_APP_SECRET_REAL = credentials('KIS_APP_SECRET_REAL')
        KIS_APP_KEY = credentials('KIS_APP_KEY')
        KIS_APP_SECRET = credentials('KIS_APP_SECRET')
        KIS_ACCOUNT_NO = credentials('KIS_ACCOUNT_NO')
        KIS_ACCOUNT_NO_REAL = credentials('KIS_ACCOUNT_NO_REAL')
        
        PROJECT_DIR = "/data/auto_stock_trading_system_backend"
        VENV = "/data/auto_stock_trading_system_backend/myvenv"
    }

    stages {
        stage('Checkout') {
            steps { checkout scm }
        }

        stage('Deploy & Setup') {
            steps {
                script {
                    sh """
                        sudo mkdir -p ${PROJECT_DIR}
                        sudo cp -r * ${PROJECT_DIR}/
                        sudo chown -R apache:apache ${PROJECT_DIR}
                    """
                }
            }
        }

        stage('Setup & Run Services') {
            steps {
                withEnv(['JENKINS_NODE_COOKIE=dontKillMe']) {
                    sh """
                        echo "[ START ] 서비스 설정 및 재기동"
                        
                        # 1. 가상환경이 없으면 생성 (안전장치)
                        if [ ! -d "${VENV}" ]; then
                            echo "가상환경 생성 중..."
                            sudo /usr/bin/python3.11 -m venv ${VENV}
                            sudo chown -R apache:apache ${VENV}
                        fi

                        # 2. 필수 패키지 설치
                        # bin/python3.11 대신 bin/pip 사용
                        sudo -E ${VENV}/bin/pip install --upgrade pip
                        sudo -E ${VENV}/bin/pip install -r ${PROJECT_DIR}/auto_stock/requirements.txt

                        # 3. 기존 프로세스 종료
                        sudo pkill -f 'celery -A auto_stock' || true
                        sudo pkill -f 'kis_ws_client' || true
                        sudo pkill -f 'uvicorn auto_stock.asgi' || true
                        sleep 2

                        cd ${PROJECT_DIR}/auto_stock

                        # 4. DB 마이그레이션 (makemigrations는 삭제함)
                        sudo -E ${VENV}/bin/python manage.py makemigrations
                        sudo -E ${VENV}/bin/python manage.py migrate

                        # 5. 백그라운드 서비스 실행
                        # 중요: bin/python3.11 -> bin/python 으로 변경
                        
                        sudo -E nohup ${VENV}/bin/celery -A auto_stock worker -l info > ../celery_worker.log 2>&1 &
                        sudo -E nohup ${VENV}/bin/celery -A auto_stock beat -l info > ../celery_beat.log 2>&1 &
                        sudo -E nohup ${VENV}/bin/python -m kis.websocket.util.kis_ws_client > ../ws_client.log 2>&1 &
                        
                        sudo -E nohup ${VENV}/bin/uvicorn auto_stock.asgi:application --host 0.0.0.0 --port 8000 > ../uvicorn.log 2>&1 &
                        
                        echo "=== 배포 완료 ==="
                    """
                }
            }
        }
    }
}