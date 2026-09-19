pipeline {

    agent any

    environment {
        IMAGE_NAME = 'aus-legal-rag'
        STAGING_CONTAINER = 'aus-legal-rag-staging'
        PRODUCTION_CONTAINER = 'aus-legal-rag-production'
        STAGING_PORT = '8081'
        PRODUCTION_PORT = '8082'
    }

    stages {

        // ============================================================
        // 1. BUILD
        // ============================================================
        stage('Build') {
            steps {

                echo 'Building Docker image...'

                bat """
                    docker build -t %IMAGE_NAME%:${BUILD_NUMBER} .
                    docker tag %IMAGE_NAME%:${BUILD_NUMBER} %IMAGE_NAME%:latest
                """

                echo 'Docker image built successfully.'

                bat """
                    docker images %IMAGE_NAME%
                """
            }
        }

        // ============================================================
        // 2. TEST
        // ============================================================
        stage('Test') {
            steps {

                echo 'Running automated tests in a clean Python environment...'

                bat '''
                    docker run --rm ^
                      -v "%CD%:/workspace" ^
                      -w /workspace ^
                      -e PYTHONPATH=/workspace ^
                      python:3.11 ^
                      bash -c "pip install --no-cache-dir -r requirements.txt && pip install --no-cache-dir pytest pytest-cov && PYTHONPATH=/workspace python -m pytest -v --junitxml=test-results.xml --cov=app --cov-report=xml:coverage.xml"
                '''

                echo 'Automated tests completed.'
            }

            post {
                always {

                    junit(
                        testResults: 'test-results.xml',
                        allowEmptyResults: true
                    )

                    archiveArtifacts(
                        artifacts: 'coverage.xml',
                        allowEmptyArchive: true
                    )
                }
            }
        }

        // ============================================================
        // 3. CODE QUALITY
        // ============================================================
        stage('Code Quality') {
            steps {

                echo 'Running SonarCloud code quality analysis...'

                script {

                    def scannerHome = tool 'SonarQube-Scanner'

                    withCredentials([
                        string(
                            credentialsId: 'SONAR_TOKEN',
                            variable: 'SONAR_TOKEN'
                        )
                    ]) {

                        bat """
                            "${scannerHome}\\bin\\sonar-scanner.bat" ^
                              -Dsonar.projectKey=Icarus-si_aus-legal-RAG ^
                              -Dsonar.organization=icarus-si ^
                              -Dsonar.host.url=https://sonarcloud.io ^
                              -Dsonar.token=%SONAR_TOKEN% ^
                              -Dsonar.sources=. ^
                              -Dsonar.tests=. ^
                              -Dsonar.python.version=3.11 ^
                              -Dsonar.qualitygate.wait=true
                        """
                    }
                }

                echo 'SonarCloud analysis completed.'
            }
        }

        // ============================================================
        // 4. SECURITY
        // ============================================================
        stage('Security') {
            steps {

                echo 'Running dependency vulnerability scan with pip-audit...'

                bat '''
                    docker run --rm ^
                      -v "%CD%:/workspace" ^
                      -w /workspace ^
                      python:3.11 ^
                      bash -c "pip install --no-cache-dir pip-audit && pip-audit -r requirements.txt --format json > pip-audit-report.json; exit 0"
                '''

                echo 'pip-audit scan completed.'

                archiveArtifacts(
                    artifacts: 'pip-audit-report.json',
                    allowEmptyArchive: true
                )

                echo 'Running Trivy security scan on Docker image...'

                bat '''
                    docker run --rm ^
                      -v //var/run/docker.sock:/var/run/docker.sock ^
                      -v "%CD%:/workspace" ^
                      aquasec/trivy:latest ^
                      image ^
                      --severity HIGH,CRITICAL ^
                      --exit-code 0 ^
                      --format json ^
                      --output /workspace/trivy-report.json ^
                      %IMAGE_NAME%:${BUILD_NUMBER}
                '''

                echo 'Trivy scan completed.'

                archiveArtifacts(
                    artifacts: 'trivy-report.json',
                    allowEmptyArchive: true
                )
            }

            post {
                always {

                    echo 'Security scan stage completed.'
                }
            }
        }

        // ============================================================
        // 5. DEPLOY
        // ============================================================
        stage('Deploy') {
            steps {

                echo 'Deploying application to staging environment...'

                bat '''
                    docker rm -f aus-legal-rag-staging >NUL 2>&1 || exit /b 0
                '''

                bat """
                    docker run -d ^
                      --name aus-legal-rag-staging ^
                      -p %STAGING_PORT%:8000 ^
                      %IMAGE_NAME%:${BUILD_NUMBER}
                """

                echo 'Waiting for staging application to become healthy...'

                bat '''
                    powershell -NoProfile -ExecutionPolicy Bypass -Command "$ErrorActionPreference='Stop'; for($i=0; $i -lt 12; $i++) { try { $response=Invoke-WebRequest -Uri 'http://localhost:8081/health' -UseBasicParsing -TimeoutSec 5; if($response.StatusCode -eq 200) { Write-Host 'Staging health check passed:'; Write-Host $response.Content; exit 0 } } catch { Write-Host 'Staging application is starting...'; Start-Sleep -Seconds 5 } }; Write-Error 'Staging deployment failed health check'; exit 1"
                '''

                echo 'Staging deployment successful.'
            }
        }

        // ============================================================
        // 6. RELEASE
        // ============================================================
        stage('Release') {
            steps {

                input(
                    message: 'Approve promotion of the staging Docker image to production?',
                    ok: 'Deploy to Production'
                )

                echo 'Production release approved.'

                bat '''
                    docker rm -f aus-legal-rag-production >NUL 2>&1 || exit /b 0
                '''

                bat """
                    docker run -d ^
                      --name aus-legal-rag-production ^
                      -p %PRODUCTION_PORT%:8000 ^
                      %IMAGE_NAME%:${BUILD_NUMBER}
                """

                echo 'Waiting for production application to become healthy...'

                bat '''
                    powershell -NoProfile -ExecutionPolicy Bypass -Command "$ErrorActionPreference='Stop'; for($i=0; $i -lt 12; $i++) { try { $response=Invoke-WebRequest -Uri 'http://localhost:8082/health' -UseBasicParsing -TimeoutSec 5; if($response.StatusCode -eq 200) { Write-Host 'Production health check passed:'; Write-Host $response.Content; exit 0 } } catch { Write-Host 'Production application is starting...'; Start-Sleep -Seconds 5 } }; Write-Error 'Production deployment failed health check'; exit 1"
                '''

                echo 'Production release completed successfully.'
            }
        }

        // ============================================================
        // 7. MONITORING
        // ============================================================
        stage('Monitoring') {
            steps {

                echo 'Starting Prometheus and Alertmanager monitoring stack...'

                withCredentials([
                    string(
                        credentialsId: 'ALERT_WEBHOOK_URL',
                        variable: 'ALERT_WEBHOOK_URL'
                    )
                ]) {

                    writeFile file: 'alertmanager.yml', text: '''global:
  resolve_timeout: 1m

route:
  receiver: "webhook-notification"
  group_wait: 5s
  group_interval: 10s
  repeat_interval: 1h

receivers:
  - name: "webhook-notification"
    webhook_configs:
      - url: "__ALERT_WEBHOOK_URL__"
        send_resolved: true
'''

                    bat '''
                        powershell -NoProfile -ExecutionPolicy Bypass -Command "$path='alertmanager.yml'; $content=Get-Content $path -Raw; $content=$content.Replace('__ALERT_WEBHOOK_URL__',$env:ALERT_WEBHOOK_URL); [System.IO.File]::WriteAllText($path,$content,(New-Object System.Text.UTF8Encoding($false)))"
                    '''
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

                    archiveArtifacts(
                        artifacts: 'monitoring-stats.json, docker-cpu-count.txt',
                        allowEmptyArchive: true
                    )
                }

                failure {
                    echo 'ALERT: Monitoring or alerting detected a pipeline failure.'
                }
            }
        }
    }

    // ================================================================
    // PIPELINE POST ACTIONS
    // ================================================================
    post {

        success {
            echo '================================================='
            echo 'PIPELINE COMPLETED SUCCESSFULLY'
            echo 'All 7 DevOps stages completed.'
            echo 'Build -> Test -> Code Quality -> Security -> Deploy -> Release -> Monitoring'
            echo '================================================='
        }

        failure {
            echo '================================================='
            echo 'PIPELINE FAILED'
            echo 'Check the failed stage and Jenkins console output.'
            echo '================================================='
        }

        always {
            echo 'Jenkins pipeline execution completed.'
        }
    }
}
