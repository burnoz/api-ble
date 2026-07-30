pipeline {
    agent any

    environment {
        GCP_PROJECT_ID  = "${env.GCP_PROJECT_ID}"
        GCP_REGION      = "${env.GCP_REGION}"

        ARTIFACT_REPO   = 'api-ble-repo'
        IMAGE_NAME      = 'api-ble'
        SERVICE_NAME    = 'api-ble-service'
        
        REGISTRY_URL    = "${GCP_REGION}-docker.pkg.dev/${GCP_PROJECT_ID}/api-ble-repo/api-ble"
    }

    stages {
        stage ('Checkout') {
            steps {
                checkout scm
            }
        }

        stage ('Tests') {
            steps {
                sh '''
                    set -e
                    python3 -m venv venv
                    . venv/bin/activate
                    pip install -r requirements.txt
                    python -m unittest tests/test_api_leaves.py
                '''
            }
        }

        stage ('Build Docker Image') {
            steps {
                sh "docker build -t ${REGISTRY_URL}:${BUILD_NUMBER} -t ${REGISTRY_URL}:latest ."
            }
        }

        stage ('Authenticate & Push') {
            steps {
                withCredentials([file(credentialsId: 'gcp-service-account-key', variable: 'GCP_KEY_FILE')]) {
                    sh '''
                        set -e

                        gcloud auth activate-service-account --key-file=$GCP_KEY_FILE 
                        gcloud config set project ${GCP_PROJECT_ID}
                        gcloud auth configure-docker ${GCP_REGION}-docker.pkg.dev --quiet

                        docker push ${REGISTRY_URL}:${BUILD_NUMBER}
                        docker push ${REGISTRY_URL}:latest
                    '''
                }
            }
        }

        stage ('Deploy to Cloud Run') {
            when {
                branch 'main'
            }

            steps {
                withCredentials([file(credentialsId: 'gcp-service-account-key', variable: 'GCP_KEY_FILE')]) {
                    sh '''
                        set -e
                        
                        gcloud auth activate-service-account --key-file=$GCP_KEY_FILE 
                        gcloud config set project ${GCP_PROJECT_ID}

                        gcloud run deploy ${SERVICE_NAME} \
                            --image ${REGISTRY_URL}:${BUILD_NUMBER} \
                            --platform managed \
                            --region ${GCP_REGION} \
                            --allow-unauthenticated \
                            --quiet
                    '''
                }
            }
        }
    }

    post {
        always {
            sh "docker rmi ${REGISTRY_URL}:${BUILD_NUMBER} || true"
        }

        success {
            echo 'Build and push successful!'
            githubNotify context: 'Jenkins CI', description: 'Build passed!', status: 'SUCCESS'
        }

        failure {
            echo 'Build or push failed.'
            githubNotify context: 'Jenkins CI', description: 'Build failed!', status: 'FAILURE'
        }
    }
}