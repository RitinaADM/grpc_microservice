pipeline {
    agent any
    triggers {
        githubPush()
    }
    stages {
        stage('Clone repo') {
            steps {
                checkout scm
            }
        }

        stage('Run script') {
            steps {
                echo "Запускаем наш скрипт..."
                sh 'chmod +x deploy.sh && ./deploy.sh'
            }
        }
    }
}
