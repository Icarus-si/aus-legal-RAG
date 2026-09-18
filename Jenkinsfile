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
                echo 'Deploy stage will be configured next.'
            }
        }

        stage('Release') {
            steps {
                echo 'Release stage will be configured next.'
            }
        }

        stage('Monitoring') {
            steps {
                echo 'Monitoring stage will be configured next.'
            }
        }
    }
}
