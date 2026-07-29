pipeline {
    agent any

    // Checkout code
    stage ('Checkout') {
        steps {
            checkout scm
        }
    }

    // tests
    stage ('Tests') {
        steps {
            sh '''
                python3 -m venv venv
                source venv/bin/activate
                pip install -r requirements.txt
                python -m unittest tests/test_api_ble.py
            '''
        }
    }
}