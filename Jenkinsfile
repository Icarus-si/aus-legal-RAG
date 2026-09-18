pipeline {
    agent any

    environment {
        APP_NAME = 'aus-legal-rag'
        IMAGE_TAG = "${BUILD_NUMBER}"
        IMAGE_NAME = "${APP_NAME}:${IMAGE_TAG}"
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
                echo 'Running automated Python tests...'

                bat '''
                    py -m pytest -v --junitxml=test-results.xml --cov=. --cov-report=xml
                '''
            }

            post {
                always {
                    junit 'test-results.xml'
                    archiveArtifacts artifacts: 'coverage.xml', allowEmptyArchive: true
                }
            }
        }

        stage('Code Quality') {
            steps {
                echo 'Code Quality stage will be configured next.'
            }
        }

        stage('Security') {
            steps {
                echo 'Security stage will be configured next.'
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
