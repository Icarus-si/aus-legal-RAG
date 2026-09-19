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

                echo 'Starting Prometheus and Alertmanager monitoring stack...'

                withCredentials([
                    string(
                        credentialsId: 'ALERT_WEBHOOK_URL',
                        variable: 'ALERT_WEBHOOK_URL'
                    )
                ]) {
                    writeFile file: 'alertmanager.yml', text: """global:
  resolve_timeout: 1m

route:
  receiver: "webhook-notification"
  group_wait: 5s
  group_interval: 10s
  repeat_interval: 1h

receivers:
  - name: "webhook-notification"
    webhook_configs:
      - url: "${env.ALERT_WEBHOOK_URL}"
        send_resolved: true
"""
                }

                echo 'Removing previous monitoring containers if they exist...'

                bat '''
                    docker rm -f prometheus >NUL 2>&1 || exit /b 0
                    docker rm -f alertmanager >NUL 2>&1 || exit /b 0
                '''

                echo 'Starting Alertmanager...'

                bat '''
                    docker run -d ^
                      --name alertmanager ^
                      -p 9093:9093 ^
                      -v "%CD%\\alertmanager.yml:/etc/alertmanager/alertmanager.yml" ^
                      prom/alertmanager
                '''

                echo 'Starting Prometheus...'

                bat '''
                    docker run -d ^
                      --name prometheus ^
                      -p 9090:9090 ^
                      -v "%CD%\\prometheus.yml:/etc/prometheus/prometheus.yml" ^
                      -v "%CD%\\prometheus_rules.yml:/etc/prometheus/prometheus_rules.yml" ^
                      prom/prometheus
                '''

                echo 'Waiting for Prometheus and Alertmanager to become ready...'

                bat '''
                    powershell -NoProfile -ExecutionPolicy Bypass -Command "$ErrorActionPreference='Stop'; for($i=0; $i -lt 12; $i++) { try { Invoke-WebRequest -Uri 'http://localhost:9090/-/ready' -UseBasicParsing -TimeoutSec 3 | Out-Null; Invoke-WebRequest -Uri 'http://localhost:9093/-/ready' -UseBasicParsing -TimeoutSec 3 | Out-Null; Write-Host 'Prometheus and Alertmanager are ready.'; exit 0 } catch { Start-Sleep -Seconds 5 } }; Write-Error 'Monitoring services failed to become ready'; exit 1"
                '''

                echo 'Checking Prometheus to Alertmanager connection...'

                bat '''
                    powershell -NoProfile -ExecutionPolicy Bypass -Command "$ErrorActionPreference='Stop'; $response=Invoke-RestMethod -Uri 'http://localhost:9090/api/v1/alertmanagers'; $active=$response.data.activeAlertmanagers; if($active.Count -lt 1) { Write-Error 'Prometheus has no active Alertmanager connection'; exit 1 }; Write-Host 'Active Alertmanager:'; $active | ConvertTo-Json"
                '''

                echo 'Checking live production metrics endpoint...'

                bat '''
                    powershell -NoProfile -ExecutionPolicy Bypass -Command "$ErrorActionPreference='Stop'; $response=Invoke-WebRequest -Uri 'http://localhost:8082/metrics' -UseBasicParsing -TimeoutSec 5; if($response.StatusCode -ne 200) { Write-Error 'Production metrics endpoint failed'; exit 1 }; Write-Host 'Production /metrics endpoint is healthy.'"
                '''

                echo 'Checking production health...'

                bat '''
                    powershell -NoProfile -ExecutionPolicy Bypass -Command "$ErrorActionPreference='Stop'; $response=Invoke-WebRequest -Uri 'http://localhost:8082/health' -UseBasicParsing -TimeoutSec 5; if($response.StatusCode -ne 200) { Write-Error 'Production health check failed'; exit 1 }; Write-Host $response.Content"
                '''

                echo 'Checking live production resource metrics...'

                bat '''
                    docker stats aus-legal-rag-production --no-stream --format "{{json .}}" > monitoring-stats.json
                '''

                bat '''
                    docker info --format "{{.NCPU}}" > docker-cpu-count.txt
                '''

                bat '''
                    powershell -NoProfile -ExecutionPolicy Bypass -Command "$ErrorActionPreference='Stop'; $stats=Get-Content 'monitoring-stats.json' -Raw | ConvertFrom-Json; $hostCpu=[double](Get-Content 'docker-cpu-count.txt' -Raw).Trim(); $rawCpu=[double](($stats.CPUPerc -replace '[^0-9.]','')); $normalizedCpu=$rawCpu / $hostCpu; $mem=[double](($stats.MemPerc -replace '[^0-9.]','')); Write-Host ('Docker raw CPU usage: ' + $rawCpu); Write-Host ('Normalized CPU usage: ' + [math]::Round($normalizedCpu,2)); Write-Host ('Memory usage: ' + $mem); if($normalizedCpu -gt 80 -or $mem -gt 80) { Write-Error 'ALERT: Normalized resource usage exceeded 80 threshold'; exit 1 }"
                '''

                echo 'Simulating a production outage for Prometheus and Alertmanager...'

                bat '''
                    docker stop aus-legal-rag-production
                '''

                echo 'Waiting for Prometheus to detect the production outage...'

                bat '''
                    powershell -NoProfile -ExecutionPolicy Bypass -Command "$ErrorActionPreference='Stop'; Start-Sleep -Seconds 50; $alerts=Invoke-RestMethod -Uri 'http://localhost:9093/api/v2/alerts'; $match=$alerts | Where-Object { $_.labels.alertname -eq 'AusLegalRAGDown' -and $_.status.state -eq 'active' }; if(-not $match) { Write-Error 'Alertmanager did not receive the AusLegalRAGDown firing alert'; exit 1 }; Write-Host 'ALERT: Alertmanager received AusLegalRAGDown successfully.'; $match | ConvertTo-Json -Depth 10"
                '''

                echo 'Production outage detected successfully.'

                echo 'Checking production container state...'

                bat '''
                    docker inspect --format="{{.State.Status}}" aus-legal-rag-production
                '''

                echo 'Recovering production application...'

                bat '''
                    docker start aus-legal-rag-production
                '''

                echo 'Waiting for production recovery...'

                bat '''
                    powershell -NoProfile -ExecutionPolicy Bypass -Command "$ErrorActionPreference='Stop'; for($i=0; $i -lt 12; $i++) { try { $response=Invoke-WebRequest -Uri 'http://localhost:8082/health' -UseBasicParsing -TimeoutSec 5; if($response.StatusCode -eq 200) { Write-Host 'Production recovery health response:'; Write-Host $response.Content; exit 0 } } catch { Write-Host 'Production application is recovering...'; Start-Sleep -Seconds 5 } }; Write-Error 'Production recovery failed'; exit 1"
                '''

                echo 'Waiting for Alertmanager to resolve the outage alert...'

                bat '''
                    powershell -NoProfile -ExecutionPolicy Bypass -Command "$ErrorActionPreference='Stop'; for($i=0; $i -lt 12; $i++) { Start-Sleep -Seconds 5; $alerts=Invoke-RestMethod -Uri 'http://localhost:9093/api/v2/alerts'; $match=$alerts | Where-Object { $_.labels.alertname -eq 'AusLegalRAGDown' -and $_.status.state -eq 'active' }; if(-not $match) { Write-Host 'Alertmanager alert resolved successfully.'; exit 0 } }; Write-Error 'Alertmanager alert did not resolve after production recovery'; exit 1"
                '''

                echo 'Checking final production state...'

                bat '''
                    docker inspect --format="{{.State.Status}}" aus-legal-rag-production
                '''

                echo 'Monitoring, Prometheus alerting, Alertmanager notification, incident detection, and recovery completed successfully.'
            }

            post {
                always {
                    archiveArtifacts artifacts: 'monitoring-stats.json, docker-cpu-count.txt',
                        allowEmptyArchive: true
                }

                failure {
                    echo 'ALERT: Monitoring or alerting detected a pipeline failure.'
                }
            }
        }
    }
}