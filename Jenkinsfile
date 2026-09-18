pipeline {
    agent any

    environment {
        APP_NAME = 'aus-legal-rag'
        IMAGE_TAG = "${BUILD_NUMBER}"
        IMAGE_NAME = "${APP_NAME}:${IMAGE_TAG}"

        SONAR_SCANNER_HOME = tool 'SonarQube-Scanner'
    }

    stages {

        stage('Build') {
            steps {
                echo "Building Docker image: ${IMAGE_NAME}"

                bat """
                    docker build -t ${IMAGE_NAME} .
                    docker tag ${IMAGE_NAME} ${APP_NAME}:latest
                """

                echo "Docker build completed successfully."
            }
        }

        stage('Test') {
            steps {
                echo 'Running automated Python tests in a clean Python 3.11 container...'

                bat '''
                    docker run --rm ^
                      -v "%CD%:/workspace" ^
                      -w /workspace ^
                      python:3.11-slim ^
                      sh -c "pip install --no-cache-dir -r requirements.txt -r requirements-dev.txt && python -m pytest -v --junitxml=test-results.xml --cov=. --cov-report=xml"
                '''
            }

            post {
                always {
                    junit testResults: 'test-results.xml', allowEmptyResults: true
                    archiveArtifacts artifacts: 'coverage.xml', allowEmptyArchive: true
                }
            }
        }

        stage('Code Quality') {
            steps {
                echo 'Running SonarCloud code quality analysis...'

                withCredentials([
                    string(
                        credentialsId: 'SONAR_TOKEN',
                        variable: 'SONAR_TOKEN'
                    )
                ]) {
                    bat '''
                        "%SONAR_SCANNER_HOME%\\bin\\sonar-scanner.bat" ^
                          -Dsonar.token=%SONAR_TOKEN% ^
                          -Dsonar.qualitygate.wait=true
                    '''
                }
            }
        }

        stage('Security') {
            steps {
                echo 'Running Python dependency security scan with pip-audit...'

                bat '''
                    docker run --rm ^
                      -v "%CD%:/workspace" ^
                      -w /workspace ^
                      python:3.11-slim ^
                      sh -c "pip install --no-cache-dir -r requirements.txt -r requirements-dev.txt >/dev/null && python -m pip_audit -r requirements.txt --format=json --output=pip-audit-report.json --progress-spinner off; exit 0"
                '''

                echo 'Running Docker image security scan with Trivy...'

                bat '''
                    docker run --rm ^
                      -v //var/run/docker.sock:/var/run/docker.sock ^
                      -v "%CD%:/workspace" ^
                      aquasec/trivy:latest ^
                      image --format json --output /workspace/trivy-report.json --severity HIGH,CRITICAL --exit-code 0 %IMAGE_NAME%
                '''

                echo 'Security scans completed.'
            }

            post {
                always {
                    archiveArtifacts artifacts: 'pip-audit-report.json, trivy-report.json',
                        allowEmptyArchive: false
                }
            }
        }

        stage('Deploy') {
            steps {
                echo "Deploying ${IMAGE_NAME} to staging environment..."

                echo 'Removing previous staging container if it exists...'

                bat '''
                    docker rm -f aus-legal-rag-staging >NUL 2>&1 || exit /b 0
                '''

                echo 'Starting new staging container...'

                bat """
                    docker run -d ^
                      --name aus-legal-rag-staging ^
                      -p 8081:8000 ^
                      ${IMAGE_NAME}
                """

                echo 'Waiting for staging application to become healthy...'

                bat '''
                    powershell -NoProfile -ExecutionPolicy Bypass -Command "$ErrorActionPreference='Stop'; for($i=0; $i -lt 12; $i++) { try { $response=Invoke-WebRequest -Uri 'http://localhost:8081/health' -UseBasicParsing -TimeoutSec 3; if($response.StatusCode -eq 200) { Write-Host $response.Content; exit 0 } } catch { Start-Sleep -Seconds 5 } }; Write-Error 'Staging health check failed'; exit 1"
                '''

                echo 'Staging deployment and health check completed successfully.'
            }
        }

        stage('Release') {
            steps {
                echo 'Production release requires manual approval.'

                input message: 'Approve release to production?', ok: 'Release'

                echo "Releasing ${IMAGE_NAME} to production..."

                bat '''
                    docker rm -f aus-legal-rag-production >NUL 2>&1 || exit /b 0
                '''

                bat """
                    docker run -d ^
                      --name aus-legal-rag-production ^
                      -p 8082:8000 ^
                      ${IMAGE_NAME}
                """

                echo 'Production container started successfully.'
            }
        }

        stage('Monitoring') {
            steps {
                echo 'Monitoring production application...'

                echo 'Checking live production resource metrics...'

                bat '''
                    docker stats aus-legal-rag-production --no-stream --format "{{json .}}" > monitoring-stats.json
                '''

                bat '''
                    powershell -NoProfile -ExecutionPolicy Bypass -Command "$ErrorActionPreference='Stop'; $stats=Get-Content 'monitoring-stats.json' -Raw | ConvertFrom-Json; $cpu=[double](($stats.CPUPerc -replace '[^0-9.]','')); $mem=[double](($stats.MemPerc -replace '[^0-9.]','')); Write-Host ('CPU usage: ' + $cpu + '%%'); Write-Host ('Memory usage: ' + $mem + '%%'); if($cpu -gt 80 -or $mem -gt 80) { Write-Error 'ALERT: Resource usage exceeded 80%% threshold'; exit 1 }"
                '''

                echo 'Checking production health...'

                bat '''
                    powershell -NoProfile -ExecutionPolicy Bypass -Command "$ErrorActionPreference='Stop'; for($i=0; $i -lt 12; $i++) { try { $response=Invoke-WebRequest -Uri 'http://localhost:8082/health' -UseBasicParsing -TimeoutSec 5; if($response.StatusCode -eq 200) { Write-Host 'Production health response:'; Write-Host $response.Content; exit 0 } } catch { Write-Host 'Production application is not ready yet. Waiting 5 seconds...'; Start-Sleep -Seconds 5 } }; Write-Error 'Production monitoring health check failed'; exit 1"
                '''

                echo 'Simulating a production incident...'

                bat '''
                    docker stop aus-legal-rag-production
                '''

                echo 'Checking whether monitoring detects the production failure...'

                bat '''
                    powershell -NoProfile -ExecutionPolicy Bypass -Command "$ErrorActionPreference='Stop'; try { $response=Invoke-WebRequest -Uri 'http://localhost:8082/health' -UseBasicParsing -TimeoutSec 5; Write-Host ('Unexpected response received: HTTP ' + $response.StatusCode); Write-Host 'ALERT: Production application remained reachable during incident simulation'; exit 1 } catch { Write-Host 'ALERT: Production application is unavailable as expected. Monitoring detected the incident successfully.'; exit 0 }"
                '''

                echo 'Checking production container state after incident simulation...'

                bat '''
                    docker inspect --format="{{.State.Status}}" aus-legal-rag-production
                '''

                echo 'Recovering production application...'

                bat '''
                    docker start aus-legal-rag-production
                '''

                echo 'Waiting for production recovery...'

                bat '''
                    powershell -NoProfile -ExecutionPolicy Bypass -Command "$ErrorActionPreference='Stop'; for($i=0; $i -lt 12; $i++) { try { $response=Invoke-WebRequest -Uri 'http://localhost:8082/health' -UseBasicParsing -TimeoutSec 5; if($response.StatusCode -eq 200) { Write-Host 'Production recovery health response:'; Write-Host $response.Content; exit 0 } } catch { Write-Host 'Production application is recovering... Waiting 5 seconds...'; Start-Sleep -Seconds 5 } }; Write-Error 'Production recovery failed'; exit 1"
                '''

                bat '''
                    docker inspect --format="{{.State.Status}}" aus-legal-rag-production
                '''

                echo 'Production monitoring, alert simulation, and recovery completed successfully.'
            }

            post {
                failure {
                    echo 'ALERT: Production monitoring detected a real failure.'
                }
            }
        }
    }
}
