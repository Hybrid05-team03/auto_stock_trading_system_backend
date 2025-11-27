pipeline {
    agent none

    environment {
        // [1] 경로 설정
        BASE_DIR = "/data/auto_stock_trading_system_backend"
        // Git에서 복사되어 올 .env 파일의 절대 경로
        ENV_FILE = "/data/auto_stock_trading_system_backend/auto_stock/.env"
        VENV     = "/data/auto_stock_trading_system_backend/myvenv"

        // [2] 추가할 비밀키 (Credentials)
        KIS_APP_KEY_REAL      = credentials('KIS_APP_KEY_REAL')
        KIS_APP_SECRET_REAL   = credentials('KIS_APP_SECRET_REAL')
        KIS_APP_KEY           = credentials('KIS_APP_KEY')
        KIS_APP_SECRET        = credentials('KIS_APP_SECRET')
        KIS_ACCOUNT_NO        = credentials('KIS_ACCOUNT_NO')
        KIS_ACCOUNT_NO_REAL   = credentials('KIS_ACCOUNT_NO_REAL')
    }

    stages {
        stage('Deploy & Install') {
            matrix {
                axes {
                    axis {
                        name 'TARGET_NODE'
                        values 'web01.hb05.local', 'web02.hb05.local'
                    }
                }

                agent { label "${TARGET_NODE}" }

                stages {
                    stage('Process per Node') {
                        steps {
                            echo "--- [ ${TARGET_NODE} ] 배포 시작 ---"
                            checkout scm

                            sh """
                                echo "[ 1 ] 소스 코드 복사 (덮어쓰기)"
                                sudo mkdir -p ${BASE_DIR}
                                # 현재 워크스페이스의 모든 파일(하위 .env 포함)을 서버로 복사
                                sudo cp -rf * ${BASE_DIR}/

                                echo "[ 2 ] .env 파일에 비밀키 추가 (Append)"
                                # 파일 존재 체크 없이 바로 뒤에 내용을 붙입니다.

                                echo "" | sudo tee -a ${ENV_FILE}
                                echo "KIS_APP_KEY_REAL=${KIS_APP_KEY_REAL}"      | sudo tee -a ${ENV_FILE}
                                echo "KIS_APP_SECRET_REAL=${KIS_APP_SECRET_REAL}"| sudo tee -a ${ENV_FILE}
                                echo "KIS_APP_KEY=${KIS_APP_KEY}"                 | sudo tee -a ${ENV_FILE}
                                echo "KIS_APP_SECRET=${KIS_APP_SECRET}"           | sudo tee -a ${ENV_FILE}
                                echo "KIS_ACCOUNT_NO=${KIS_ACCOUNT_NO}"           | sudo tee -a ${ENV_FILE}
                                echo "KIS_ACCOUNT_NO_REAL=${KIS_ACCOUNT_NO_REAL}" | sudo tee -a ${ENV_FILE}

                                # 권한 설정
                                sudo chmod 600 ${ENV_FILE}
                                sudo chown apache:apache ${ENV_FILE}
                                sudo chown -R apache:apache ${BASE_DIR}

                                echo "[ 3 ] 가상환경 재설정 (Clean Install)"
                                sudo /usr/bin/python3.11 -m venv --clear ${VENV}
                                sudo chown -R apache:apache ${VENV}

                                # 패키지 설치
                                sudo ${VENV}/bin/pip install --upgrade pip
                                sudo ${VENV}/bin/pip install -r ${BASE_DIR}/auto_stock/requirements.txt
                                sudo chown -R apache:apache ${VENV}
                            """
                        }
                    }
                }
            }
        }

        stage('DB Migrate & Restart') {
            agent { label 'web01.hb05.local' }
            steps {
                script {
                    echo "[ START ] DB 마이그레이션 및 재기동"

                    sh """
                        # [ 4 ] DB 마이그레이션
                        echo "DB Migration 수행..."
                        cd ${BASE_DIR}/auto_stock

                        # .env 파일을 로드하여 환경변수 주입 후 migrate 실행
                        sudo bash -c "set -a && source ${ENV_FILE} && set +a && ${VENV}/bin/python manage.py migrate"

                        # [ 5 ] Pacemaker 리소스 재기동
                        echo "Cluster Resources 재기동..."
                        sudo pcs resource restart ha_celery_worker
                        sudo pcs resource restart ha_celery_beat
                        sudo pcs resource restart ha_kis_socket
                        sudo pcs resource restart ha_auto_stock

                        echo "=== 전체 배포 완료 ==="
                    """
                }
            }
        }
    }
}