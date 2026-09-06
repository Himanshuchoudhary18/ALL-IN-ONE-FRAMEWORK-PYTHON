pipeline {
    agent any
    stages {
        stage('Install') {
            steps {
                script {
                    if (isUnix()) {
                        sh 'python3 -m venv .venv && .venv/bin/python -m pip install -e ".[dev]"'
                    } else {
                        bat 'py -3 -m venv .venv && .venv\\Scripts\\python -m pip install -e ".[dev]"'
                    }
                }
            }
        }
        stage('Verify') {
            steps {
                script {
                    if (isUnix()) {
                        sh '.venv/bin/python -m pytest -n 2'
                    } else {
                        bat '.venv\\Scripts\\python -m pytest -n 2'
                    }
                }
            }
        }
    }
    post {
        always {
            junit allowEmptyResults: true, testResults: 'reports/junit.xml'
            archiveArtifacts allowEmptyArchive: true, artifacts: 'reports/**'
        }
    }
}
