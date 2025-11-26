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
                    // 2. 소스 코드 배포 (파일 복사)
                    sh """
                        sudo mkdir -p ${PROJECT_DIR}
                        sudo cp -r * ${PROJECT_DIR}/
                        sudo chown -R apache:apache ${PROJECT_DIR}
                    """
                }
            }
        }

        stage('Run Services with Env Vars') {
            steps {
                // JENKINS_NODE_COOKIE: 프로세스 종료 방지
                withEnv(['JENKINS_NODE_COOKIE=dontKillMe']) {
                    sh """
                        # 기존 프로세스 정리
                        sudo pkill -f 'celery -A auto_stock' || true
                        sudo pkill -f 'kis_ws_client' || true
                        sudo pkill -f 'uvicorn auto_stock.asgi' || true
                        sleep 2
                        
                        cd ${PROJECT_DIR}/auto_stock

                        sudo -E ${VENV}/bin/python manage.py makemigrates
                        sudo -E ${VENV}/bin/python manage.py migrate

                        # 환경변수가 메모리에 주입된 상태로 프로세스가 뜹니다.
                        sudo -E nohup ${VENV}/bin/celery -A auto_stock worker -l info > ../celery_worker.log 2>&1 &
                        sudo -E nohup ${VENV}/bin/celery -A auto_stock beat -l info > ../celery_beat.log 2>&1 &
                        sudo -E nohup ${VENV}/bin/python -m kis.websocket.util.kis_ws_client > ../ws_client.log 2>&1 &

                        # Uvicorn 실행
                        sudo -E nohup ${VENV}/bin/uvicorn auto_stock.asgi:application --host 0.0.0.0 --port 8000 > ../uvicorn.log 2>&1 &
                    """
                }
            }
        }
    }
}